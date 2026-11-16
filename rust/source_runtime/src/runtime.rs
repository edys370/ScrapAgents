//! The `SourceRuntime` pipeline.
//!
//! Every payload is written to RustFS Landing first: structured documents (JSON, XML, HTML, CSV)
//! and complex binaries (PDF, DOCX). Only those binaries then go through Apache Tika, and the
//! extracted text is written back to RustFS next to the raw object. Typed PostgreSQL `bronze`
//! rows are loaded from the object read back out of RustFS, never from the request buffer.

use crate::bronze::{batch_id, extract_rows, Registry};
use crate::hashing::hash_bytes;
use crate::sinks::{BronzeBatch, BronzeSink, LandingSink, SinkError, TextExtractor};
use crate::triage::{classify, route, Hints, PayloadKind, Route, Structured};

/// One payload received from a Python extractor.
pub struct Payload<'a> {
    pub source: &'a str,
    pub dataset: &'a str,
    /// Partition date (`YYYY-MM-DD`) chosen by the caller so the runtime stays deterministic.
    pub ingest_date: &'a str,
    pub bytes: &'a [u8],
    pub hints: Hints<'a>,
}

#[derive(Debug, PartialEq, Eq)]
pub struct Outcome {
    pub sha256: String,
    pub size: usize,
    pub landing_key: String,
    pub route: Route,
    /// Landing key of the Tika text, only for `Route::Tika`.
    pub text_key: Option<String>,
    /// Typed bronze table the records were loaded into, with how many records the payload held.
    pub bronze_load: Option<BronzeLoad>,
}

#[derive(Debug, PartialEq, Eq)]
pub struct BronzeLoad {
    pub table: String,
    pub rows: usize,
}

pub struct SourceRuntime<L, B, T> {
    pub landing: L,
    pub bronze: B,
    pub tika: T,
    pub registry: Registry,
}

/// Hive-style Landing key, immutable and content-addressed.
pub fn landing_key(source: &str, dataset: &str, ingest_date: &str, sha256: &str) -> String {
    format!("source={source}/dataset={dataset}/dt={ingest_date}/sha256={sha256}")
}

impl<L: LandingSink, B: BronzeSink, T: TextExtractor> SourceRuntime<L, B, T> {
    pub fn new(landing: L, bronze: B, tika: T) -> Self {
        Self {
            landing,
            bronze,
            tika,
            registry: Registry::default(),
        }
    }

    /// Datasets with a typed bronze table (design-time `bronze/registry.json`).
    pub fn with_registry(mut self, registry: Registry) -> Self {
        self.registry = registry;
        self
    }

    fn outcome(sha256: String, size: usize, landing_key: String, route: Route) -> Outcome {
        Outcome {
            sha256,
            size,
            landing_key,
            route,
            text_key: None,
            bronze_load: None,
        }
    }

    pub async fn process(&self, payload: &Payload<'_>) -> Result<Outcome, SinkError> {
        let sha256 = hash_bytes(payload.bytes);
        let key = landing_key(
            payload.source,
            payload.dataset,
            payload.ingest_date,
            &sha256,
        );
        let kind = classify(payload.bytes, &payload.hints);
        let decided = route(kind);
        let mut out = Self::outcome(sha256.clone(), payload.bytes.len(), key.clone(), decided);

        // Page → RustFS, for binaries and for structured payloads. Nothing reaches Postgres
        // until this object can be read back.
        self.landing.put(&key, payload.bytes).await?;
        let stored = self.landing.get(&key).await?;
        if stored.as_slice() != payload.bytes {
            return Err(SinkError(format!(
                "landing object {key} does not match the payload"
            )));
        }

        if decided == Route::Tika {
            // Tika reads the object that is already in RustFS. Its plain text is another
            // Landing object; a Tika failure leaves the raw bytes in place and fails the call.
            let text = self
                .tika
                .extract_text(&stored, payload.hints.content_type)
                .await?;
            let text_key = format!("{key}.txt");
            self.landing.put(&text_key, text.as_bytes()).await?;
            out.text_key = Some(text_key);
        }

        match decided {
            Route::Bronze => {
                let format = match kind {
                    PayloadKind::Structured(s) => s,
                    _ => unreachable!("only structured payloads route to bronze"),
                };
                if format == Structured::Json {
                    let doc = match serde_json::from_slice::<serde_json::Value>(&stored) {
                        Ok(doc) => doc,
                        Err(_) => return self.reject(out, payload, "invalid JSON").await,
                    };
                    if let Some(spec) = self.registry.get(payload.source, payload.dataset) {
                        let rows = match extract_rows(spec, &doc) {
                            Ok(rows) => rows,
                            Err(reason) => return self.reject(out, payload, &reason).await,
                        };
                        let batch = BronzeBatch {
                            spec,
                            batch_id: &batch_id(&sha256),
                            landing_uri: &self.landing.uri(&key),
                            rows: &rows,
                        };
                        self.bronze.insert(&batch).await?;
                        out.bronze_load = Some(BronzeLoad {
                            table: spec.table.clone(),
                            rows: rows.len(),
                        });
                    }
                }
            }
            // The raw file and, when Tika ran, its `.txt` are the Landing copies. Typed bronze
            // rows exist only for JSON records read back from that object.
            Route::Tika => {}
            Route::Quarantine => {
                let reason = format!("unrecognised payload ({kind:?})");
                return self.reject(out, payload, &reason).await;
            }
        }
        Ok(out)
    }

    /// The raw bytes are already in Landing; the payload is recorded in quarantine with its reason.
    async fn reject(
        &self,
        mut out: Outcome,
        payload: &Payload<'_>,
        reason: &str,
    ) -> Result<Outcome, SinkError> {
        self.bronze
            .quarantine(payload.source, payload.dataset, &out.sha256, reason)
            .await?;
        out.route = Route::Quarantine;
        out.bronze_load = None;
        Ok(out)
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::sinks::memory::{CountingTika, MemoryBronze, MemoryLanding};

    fn runtime() -> SourceRuntime<MemoryLanding, MemoryBronze, CountingTika> {
        SourceRuntime::new(Default::default(), Default::default(), Default::default())
    }

    /// `demo/records` has the typed table `demo__records` keyed by `id`.
    fn typed_runtime() -> SourceRuntime<MemoryLanding, MemoryBronze, CountingTika> {
        let registry = Registry::from_json(
            r#"{"datasets": {"demo/records": {"table": "demo__records", "keys": ["id"]}}}"#,
        )
        .unwrap();
        runtime().with_registry(registry)
    }

    fn table_rows(
        rt: &SourceRuntime<MemoryLanding, MemoryBronze, CountingTika>,
    ) -> Vec<crate::sinks::memory::MemoryRow> {
        rt.bronze
            .rows
            .lock()
            .unwrap()
            .get("demo__records")
            .cloned()
            .unwrap_or_default()
    }

    fn payload<'a>(bytes: &'a [u8], hints: Hints<'a>) -> Payload<'a> {
        Payload {
            source: "demo",
            dataset: "records",
            ingest_date: "2026-11-09",
            bytes,
            hints,
        }
    }

    #[tokio::test]
    async fn json_goes_to_bronze_and_never_calls_tika() {
        let rt = typed_runtime();
        let out = rt
            .process(&payload(
                b"[{\"id\":1,\"name\":\"a\"},{\"id\":2}]",
                Hints::default(),
            ))
            .await
            .unwrap();
        assert_eq!(out.route, Route::Bronze);
        assert_eq!(*rt.tika.calls.lock().unwrap(), 0);
        assert_eq!(
            out.bronze_load,
            Some(BronzeLoad {
                table: "demo__records".into(),
                rows: 2
            })
        );
        let rows = table_rows(&rt);
        assert_eq!(rows.len(), 2);
        assert_eq!(rows[0].0, ["1"]);
        assert_eq!(rows[0].1, batch_id(&out.sha256));
        assert_eq!(rows[0].2, format!("memory://{}", out.landing_key));
        assert!(rt.landing.0.lock().unwrap().contains_key(&out.landing_key));
        assert!(out
            .landing_key
            .starts_with("source=demo/dataset=records/dt=2026-11-09/"));
    }

    #[tokio::test]
    async fn pdf_calls_tika_once_and_stores_the_text() {
        let rt = runtime();
        let out = rt
            .process(&payload(b"%PDF-1.7 data", Hints::default()))
            .await
            .unwrap();
        assert_eq!(out.route, Route::Tika);
        assert_eq!(*rt.tika.calls.lock().unwrap(), 1);
        let text_key = out.text_key.unwrap();
        let landing = rt.landing.0.lock().unwrap();
        assert_eq!(landing[&out.landing_key], b"%PDF-1.7 data");
        assert_eq!(landing[&text_key], b"extracted text");
        drop(landing);
        assert!(rt.bronze.rows.lock().unwrap().is_empty());
    }

    #[tokio::test]
    async fn unknown_payload_is_kept_raw_and_quarantined() {
        let rt = runtime();
        let out = rt
            .process(&payload(&[0, 1, 2, 3], Hints::default()))
            .await
            .unwrap();
        assert_eq!(out.route, Route::Quarantine);
        assert_eq!(rt.bronze.quarantined.lock().unwrap().len(), 1);
        assert_eq!(*rt.tika.calls.lock().unwrap(), 0);
        assert!(rt.landing.0.lock().unwrap().contains_key(&out.landing_key));
    }

    #[tokio::test]
    async fn same_bytes_get_the_same_key() {
        let rt = runtime();
        let a = rt
            .process(&payload(b"[1]", Hints::default()))
            .await
            .unwrap();
        let b = rt
            .process(&payload(b"[1]", Hints::default()))
            .await
            .unwrap();
        assert_eq!(a.landing_key, b.landing_key);
        assert_eq!(rt.landing.0.lock().unwrap().len(), 1);
    }

    struct FailingTika;

    impl crate::sinks::TextExtractor for FailingTika {
        async fn extract_text(&self, _: &[u8], _: Option<&str>) -> Result<String, SinkError> {
            Err(SinkError("tika down".into()))
        }
    }

    #[tokio::test]
    async fn tika_failure_keeps_the_raw_object_and_skips_bronze() {
        let rt = SourceRuntime::new(
            MemoryLanding::default(),
            MemoryBronze::default(),
            FailingTika,
        );
        let res = rt
            .process(&payload(b"%PDF-1.7 data", Hints::default()))
            .await;
        assert!(res.is_err());
        let landing = rt.landing.0.lock().unwrap();
        assert_eq!(landing.len(), 1);
        assert!(landing.values().any(|bytes| bytes == b"%PDF-1.7 data"));
        assert!(landing.keys().all(|key| !key.ends_with(".txt")));
        drop(landing);
        assert!(rt.bronze.rows.lock().unwrap().is_empty());
        assert!(rt.bronze.quarantined.lock().unwrap().is_empty());
    }

    /// `get` fails after `put`: bronze must not receive rows from the request buffer.
    struct LandingUnread {
        objects: std::sync::Mutex<std::collections::BTreeMap<String, Vec<u8>>>,
    }

    impl crate::sinks::LandingSink for LandingUnread {
        async fn put(&self, key: &str, data: &[u8]) -> Result<(), SinkError> {
            self.objects
                .lock()
                .unwrap()
                .insert(key.to_string(), data.to_vec());
            Ok(())
        }

        async fn get(&self, key: &str) -> Result<Vec<u8>, SinkError> {
            let _ = key;
            Err(SinkError("landing get failed".into()))
        }

        fn uri(&self, key: &str) -> String {
            format!("memory://{key}")
        }
    }

    #[tokio::test]
    async fn bronze_is_not_loaded_when_landing_cannot_be_read_back() {
        let rt = SourceRuntime::new(
            LandingUnread {
                objects: std::sync::Mutex::new(std::collections::BTreeMap::new()),
            },
            MemoryBronze::default(),
            CountingTika::default(),
        )
        .with_registry(
            Registry::from_json(
                r#"{"datasets": {"demo/records": {"table": "demo__records", "keys": ["id"]}}}"#,
            )
            .unwrap(),
        );
        let err = rt
            .process(&payload(b"[{\"id\":1}]", Hints::default()))
            .await
            .unwrap_err();
        assert!(err.to_string().contains("landing get failed"));
        assert!(rt.bronze.rows.lock().unwrap().is_empty());
        assert_eq!(rt.landing.objects.lock().unwrap().len(), 1);
    }

    #[tokio::test]
    async fn malformed_json_is_quarantined_not_inserted() {
        let rt = typed_runtime();
        let out = rt
            .process(&payload(b"{\"a\": ", Hints::default()))
            .await
            .unwrap();
        assert_eq!(out.route, Route::Quarantine);
        assert!(table_rows(&rt).is_empty());
        assert_eq!(rt.bronze.quarantined.lock().unwrap().len(), 1);
    }

    #[tokio::test]
    async fn json_of_an_unregistered_dataset_is_landed_but_not_loaded() {
        let rt = runtime();
        let out = rt
            .process(&payload(b"[{\"id\":1}]", Hints::default()))
            .await
            .unwrap();
        assert_eq!(out.route, Route::Bronze);
        assert_eq!(out.bronze_load, None);
        assert!(rt.bronze.rows.lock().unwrap().is_empty());
        assert!(rt.landing.0.lock().unwrap().contains_key(&out.landing_key));
    }

    #[tokio::test]
    async fn csv_and_html_are_landed_without_a_typed_table() {
        let rt = typed_runtime();
        let csv = Hints {
            content_type: Some("text/csv"),
            filename: None,
        };
        let cases = [
            (&b"a,b\n1,2\n"[..], csv),
            (b"<html><body>x</body></html>", Hints::default()),
        ];
        for (bytes, hints) in cases {
            let out = rt.process(&payload(bytes, hints)).await.unwrap();
            assert_eq!(out.route, Route::Bronze);
            assert_eq!(out.bronze_load, None);
        }
        assert!(rt.bronze.rows.lock().unwrap().is_empty());
    }

    #[tokio::test]
    async fn a_record_without_its_key_quarantines_the_whole_payload() {
        let rt = typed_runtime();
        let out = rt
            .process(&payload(
                b"[{\"id\":1},{\"name\":\"no id\"}]",
                Hints::default(),
            ))
            .await
            .unwrap();
        assert_eq!(out.route, Route::Quarantine);
        assert!(table_rows(&rt).is_empty());
        let quarantined = rt.bronze.quarantined.lock().unwrap();
        assert!(quarantined[0].1.contains("missing or empty key"));
        // The bytes are never lost: they stay in Landing.
        assert!(rt.landing.0.lock().unwrap().contains_key(&out.landing_key));
    }

    #[tokio::test]
    async fn replaying_the_same_payload_adds_no_rows() {
        let rt = typed_runtime();
        let body = b"[{\"id\":1},{\"id\":2}]";
        rt.process(&payload(body, Hints::default())).await.unwrap();
        rt.process(&payload(body, Hints::default())).await.unwrap();
        assert_eq!(table_rows(&rt).len(), 2);
    }

    #[tokio::test]
    async fn changed_payloads_are_new_batches_of_the_same_keys() {
        let rt = typed_runtime();
        rt.process(&payload(b"[{\"id\":1,\"v\":1}]", Hints::default()))
            .await
            .unwrap();
        rt.process(&payload(b"[{\"id\":1,\"v\":2}]", Hints::default()))
            .await
            .unwrap();
        let rows = table_rows(&rt);
        assert_eq!(rows.len(), 2);
        assert_ne!(rows[0].1, rows[1].1);
    }
}
