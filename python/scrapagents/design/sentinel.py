"""Deterministic Gate Sentinel: risk lane and H1/H2 auto-sign eligibility.

Judgement-free compliance checks over discovery/assessment/blueprint/review.
A source is ``eligible_for_auto_sign`` only when every applicable rule is green.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Literal

import yaml

from scrapagents.design import evidence, review
from scrapagents.design.markdown import bullets, is_filled, lookup, table_rows
from scrapagents.dossier import load_dossier

Lane = Literal["green", "yellow", "red"]
SENTINEL_SIGNER = "gate-sentinel"

_OPEN_LICENSE = re.compile(
    r"(cc\s*by|creative\s+commons|open\s+data|public\s+domain|allow:\s*\*|open\s+licen[cs]e)",
    re.I,
)
_RESTRICTIVE = re.compile(
    r"("
    r"prohibido\s+cualquier\s+extracci[oó]n\s+automatizada|"
    r"prohibited\s+automated|"
    r"scraping\s+is\s+prohibited|"
    r"must\s+not\s+scrape|"
    r"no\s+automated\s+access|"
    r"unauthorized\s+scraping|"
    r"disallow:\s*/\s*$|"
    r"robots\.txt[^\n]*disallow:\s*/"
    r")",
    re.I | re.M,
)
_MASKING = re.compile(
    r"(mask|anonymi[sz]e|strip|not_extracted|producto\s*oi\s+must\s+mask|enmascar)",
    re.I,
)
_VERDICT_APPROVE = re.compile(r"(?m)^Verdict:\s*approve\s*$")


@dataclass
class RuleResult:
    name: str
    gate: str  # h1 | h2
    lane: Lane
    detail: str


@dataclass
class SentinelReport:
    ingestion_id: str
    phase: str
    lane: Lane
    eligible_for_auto_sign: bool
    rules: list[RuleResult] = field(default_factory=list)
    blockers: list[str] = field(default_factory=list)

    @property
    def h1_eligible(self) -> bool:
        return self.eligible_for_auto_sign and all(
            r.lane == "green" for r in self.rules if r.gate == "h1"
        )

    @property
    def h2_eligible(self) -> bool:
        return self.eligible_for_auto_sign and all(
            r.lane == "green" for r in self.rules if r.gate in {"h1", "h2"}
        )


def _worst(*lanes: Lane) -> Lane:
    order = {"green": 0, "yellow": 1, "red": 2}
    return max(lanes, key=lambda lane: order[lane])


def _load_yaml(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {}
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    return data if isinstance(data, dict) else {}


def rule_legal_tos(discovery: str, assessment: str) -> RuleResult:
    text = f"{discovery}\n{assessment}"
    legal = lookup(bullets(assessment), "Legal / ToS risk") or ""
    if _RESTRICTIVE.search(text):
        return RuleResult(
            "legal_tos",
            "h1",
            "red",
            "restrictive anti-automation / scraping phrase detected in discovery or assessment",
        )
    if _OPEN_LICENSE.search(text) or re.search(r"\blow\b", legal, re.I):
        return RuleResult(
            "legal_tos",
            "h1",
            "green",
            "open license / permissive robots or low legal risk stated",
        )
    return RuleResult(
        "legal_tos",
        "h1",
        "yellow",
        "no clear open license and no hard ban; human Macro-H1 / manual H1 required",
    )


def rule_anti_bot(discovery: str) -> RuleResult:
    rows = table_rows(discovery, "| Date")
    if not rows:
        return RuleResult("anti_bot", "h1", "yellow", "no probe evidence table")
    blocked = []
    for row in rows:
        if len(row) < 5:
            continue
        value = row[4].strip().lower()
        if value in {"captcha", "waf"}:
            blocked.append(f"{row[1]} ({value})")
    if blocked:
        return RuleResult(
            "anti_bot",
            "h1",
            "red",
            "blocking probe(s): " + "; ".join(blocked[:5]),
        )
    return RuleResult("anti_bot", "h1", "green", "probes present with blocked_by none/error only")


def rule_privacy(dossier_dir: Path, assessment: str) -> RuleResult:
    personal = lookup(bullets(assessment), "Personal data") or ""
    if not is_filled(personal) or personal.lower().startswith("no"):
        return RuleResult("privacy_lopdp", "h1", "green", "assessment reports no personal data")

    contracts = list(dossier_dir.glob("contract*.yml")) + list(
        (dossier_dir / "contracts").glob("*.yml") if (dossier_dir / "contracts").is_dir() else []
    )
    if not contracts:
        return RuleResult(
            "privacy_lopdp",
            "h1",
            "yellow",
            "personal data yes but no draft contract yet to verify masking policy",
        )

    ok = False
    details: list[str] = []
    for path in contracts:
        data = _load_yaml(path)
        if data.get("personal_data") is not True:
            details.append(f"{path.name}: personal_data is not true")
            continue
        has_not_extracted = bool(data.get("not_extracted"))
        blueprint = (dossier_dir / "blueprint.yml").read_text(encoding="utf-8")
        has_mask = bool(_MASKING.search(blueprint)) or has_not_extracted
        # column-level purpose / personal classification also counts
        for col in data.get("columns") or []:
            if isinstance(col, dict) and col.get("classification") in {"personal", "sensitive"}:
                if col.get("purpose") or has_mask:
                    has_mask = True
        if has_mask:
            ok = True
        else:
            details.append(f"{path.name}: missing not_extracted / masking / purpose policy")

    if ok:
        return RuleResult(
            "privacy_lopdp",
            "h1",
            "green",
            "personal_data true with not_extracted and/or masking policy",
        )
    return RuleResult(
        "privacy_lopdp",
        "h1",
        "yellow",
        "; ".join(details) or "personal data without masking policy",
    )


def rule_infra_blueprint(dossier_dir: Path) -> list[RuleResult]:
    results: list[RuleResult] = []
    blueprint = _load_yaml(dossier_dir / "blueprint.yml")
    if not blueprint:
        return [
            RuleResult("infra_blueprint", "h2", "yellow", "blueprint.yml missing or empty"),
        ]

    airflow = blueprint.get("airflow") or {}
    slots = airflow.get("pool_slots")
    if slots == 1:
        results.append(RuleResult("pool_slots", "h2", "green", "airflow.pool_slots is 1"))
    else:
        results.append(
            RuleResult(
                "pool_slots",
                "h2",
                "red" if slots not in (None, 1) else "yellow",
                f"airflow.pool_slots must be 1 (got {slots!r})",
            )
        )

    datasets = blueprint.get("datasets") or {}
    modes = []
    for name, ds in datasets.items():
        if not isinstance(ds, dict):
            continue
        persistence = ds.get("persistence") or {}
        modes.append((name, persistence.get("mode")))
    if not modes:
        results.append(RuleResult("persistence_mode", "h2", "yellow", "no datasets.persistence"))
    elif all(mode == "changes" for _, mode in modes):
        results.append(
            RuleResult(
                "persistence_mode",
                "h2",
                "green",
                "all datasets use persistence.mode: changes",
            )
        )
    else:
        bad = ", ".join(f"{n}={m!r}" for n, m in modes if m != "changes")
        results.append(
            RuleResult(
                "persistence_mode",
                "h2",
                "red",
                f"persistence.mode must be changes ({bad})",
            )
        )

    state_type = load_dossier(dossier_dir).state.get("source_type")
    source_type = str(blueprint.get("source_type") or state_type)
    stealth = ((blueprint.get("runtime") or {}).get("extractor") or {}).get("stealth")
    if source_type == "web":
        if stealth is True:
            results.append(
                RuleResult("stealth", "h2", "green", "web source with stealth: true")
            )
        else:
            results.append(
                RuleResult(
                    "stealth",
                    "h2",
                    "red",
                    f"web source requires stealth: true (got {stealth!r})",
                )
            )
    else:
        results.append(
            RuleResult(
                "stealth",
                "h2",
                "green",
                f"source_type={source_type} (stealth N/A)",
            )
        )

    return results


def rule_review_verdict(dossier_dir: Path) -> RuleResult:
    path = dossier_dir / "review.md"
    if not path.is_file():
        return RuleResult("arch_review", "h2", "yellow", "review.md missing")
    if not review.review_is_current(dossier_dir):
        return RuleResult("arch_review", "h2", "yellow", "review.md missing, stale, or not pass")
    text = path.read_text(encoding="utf-8")
    if _VERDICT_APPROVE.search(text):
        return RuleResult("arch_review", "h2", "green", "review current with Verdict: approve")
    return RuleResult("arch_review", "h2", "yellow", "review pass but Verdict: approve not found")


def evaluate(dossier_dir: Path) -> SentinelReport:
    """Run all sentinel rules for a dossier and compute the overall lane."""

    dossier = load_dossier(dossier_dir)
    phase = str(dossier.state.get("phase"))
    discovery = (dossier_dir / "discovery.md").read_text(encoding="utf-8")
    assessment = (dossier_dir / "assessment.md").read_text(encoding="utf-8")

    rules: list[RuleResult] = [
        rule_legal_tos(discovery, assessment),
        rule_anti_bot(discovery),
        rule_privacy(dossier_dir, assessment),
    ]

    # H2 rules when blueprint exists (phase blueprint+)
    if (dossier_dir / "blueprint.yml").is_file() and phase in {
        "blueprint",
        "implement",
        "verify",
        "done",
    }:
        rules.extend(rule_infra_blueprint(dossier_dir))
        rules.append(rule_review_verdict(dossier_dir))
    elif phase == "assessment":
        # H2 not applicable yet; eligibility for H1 only needs H1 greens.
        pass

    blockers: list[str] = []
    if phase == "assessment":
        blockers.extend(evidence.assessment_issues(assessment))
    if phase == "blueprint":
        blockers.extend(evidence.assessment_issues(assessment))

    lane = _worst(*(r.lane for r in rules)) if rules else "yellow"
    if any(r.lane == "red" for r in rules):
        eligible = False
    elif phase == "assessment":
        eligible = all(r.lane == "green" for r in rules if r.gate == "h1") and not blockers
    elif phase == "blueprint":
        eligible = all(r.lane == "green" for r in rules) and not blockers
        if not review.review_is_current(dossier_dir):
            eligible = False
            blockers.append("review.md is missing or stale")
    else:
        eligible = all(r.lane == "green" for r in rules)

    return SentinelReport(
        ingestion_id=dossier_dir.name,
        phase=phase,
        lane=lane,
        eligible_for_auto_sign=eligible and lane == "green",
        rules=rules,
        blockers=blockers,
    )


def render_report(report: SentinelReport, *, via: str | None = None) -> str:
    lines = [
        f"# Gate Sentinel: {report.ingestion_id}",
        "",
        f"- Phase: {report.phase}",
        f"- Lane: {report.lane}",
        f"- eligible_for_auto_sign: {'true' if report.eligible_for_auto_sign else 'false'}",
    ]
    if via:
        lines.append(f"- via: {via}")
    lines += [
        "",
        "## Rules",
        "",
        "| Gate | Rule | Lane | Detail |",
        "| :--- | :--- | :--- | :--- |",
    ]
    for rule in report.rules:
        detail = rule.detail.replace("|", "/")
        lines.append(f"| {rule.gate} | {rule.name} | {rule.lane} | {detail} |")
    lines += ["", "## Blockers"]
    if report.blockers:
        lines.extend(f"- {b}" for b in report.blockers)
    else:
        lines.append("- none")
    lines.append("")
    return "\n".join(lines)


def write_report(
    dossier_dir: Path,
    report: SentinelReport | None = None,
    *,
    via: str | None = None,
) -> SentinelReport:
    report = report or evaluate(dossier_dir)
    (dossier_dir / "sentinel.md").write_text(
        render_report(report, via=via), encoding="utf-8", newline="\n"
    )
    return report


def parse_eligible(sentinel_md: str) -> bool:
    match = re.search(r"(?m)^- eligible_for_auto_sign:\s*(true|false)\s*$", sentinel_md)
    return bool(match and match.group(1) == "true")


def parse_lane(sentinel_md: str) -> Lane | None:
    match = re.search(r"(?m)^- Lane:\s*(green|yellow|red)\s*$", sentinel_md)
    return match.group(1) if match else None  # type: ignore[return-value]
