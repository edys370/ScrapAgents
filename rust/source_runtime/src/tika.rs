//! `TextExtractor` over Apache Tika Server. Only the runtime calls it, only for complex binaries.

use std::time::Duration;

use crate::sinks::{SinkError, TextExtractor};

pub struct HttpTika {
    client: reqwest::Client,
    url: String,
    ocr_language: Option<String>,
}

impl HttpTika {
    pub fn new(base_url: &str) -> Self {
        Self::with_ocr_language(base_url, None)
    }

    pub fn with_ocr_language(base_url: &str, ocr_language: Option<String>) -> Self {
        let client = reqwest::Client::builder()
            .timeout(Duration::from_secs(120))
            .build()
            .expect("reqwest client");
        Self {
            client,
            url: format!("{}/tika", base_url.trim_end_matches('/')),
            ocr_language,
        }
    }
}

impl TextExtractor for HttpTika {
    async fn extract_text(
        &self,
        data: &[u8],
        content_type: Option<&str>,
    ) -> Result<String, SinkError> {
        let mut req = self
            .client
            .put(&self.url)
            .header("Accept", "text/plain")
            .header("Accept-Charset", "utf-8")
            .body(data.to_vec());
        if let Some(ct) = content_type {
            req = req.header("Content-Type", ct);
        }
        if let Some(ref ocr_lang) = self.ocr_language {
            req = req.header("X-Tika-OCRLanguage", ocr_lang);
        }
        let resp = req
            .send()
            .await
            .map_err(|e| SinkError(format!("tika request: {e}")))?;
        let status = resp.status();
        if !status.is_success() {
            return Err(SinkError(format!("tika answered {status}")));
        }
        resp.text()
            .await
            .map_err(|e| SinkError(format!("tika body: {e}")))
    }
}
