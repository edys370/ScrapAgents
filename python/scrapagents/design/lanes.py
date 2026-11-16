"""Macro-H1 lane authorization and risk-matrix reports (Strategic Point 1)."""

from __future__ import annotations

import datetime
from pathlib import Path
from typing import Any

import yaml

from scrapagents.design.sentinel import Lane, SentinelReport, evaluate
from scrapagents.paths import INGESTIONS_DIR, REPO_ROOT

LANES_DIR = INGESTIONS_DIR / "_lanes"
VALID_LANES = frozenset({"green", "yellow", "red"})


def lanes_dir(root: Path | None = None) -> Path:
    return (root or INGESTIONS_DIR) / "_lanes"


def lane_path(lane: str, root: Path | None = None) -> Path:
    if lane not in VALID_LANES:
        raise ValueError(f"lane must be one of: {', '.join(sorted(VALID_LANES))}")
    return lanes_dir(root) / f"{lane}.yml"


def load_lane(lane: str, root: Path | None = None) -> dict[str, Any]:
    path = lane_path(lane, root)
    if not path.is_file():
        return {
            "lane": lane,
            "authorized_by": None,
            "authorized_at": None,
            "ids": [],
            "note": None,
        }
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(data, dict):
        return {"lane": lane, "authorized_by": None, "authorized_at": None, "ids": [], "note": None}
    ids = data.get("ids") or []
    if not isinstance(ids, list):
        ids = []
    return {
        "lane": lane,
        "authorized_by": data.get("authorized_by"),
        "authorized_at": data.get("authorized_at"),
        "ids": [str(i) for i in ids],
        "note": data.get("note"),
    }


def is_authorized(ingestion_id: str, lane: str = "green", root: Path | None = None) -> bool:
    data = load_lane(lane, root)
    if not data.get("authorized_by") or not data.get("authorized_at"):
        return False
    return ingestion_id in set(data.get("ids") or [])


def authorize_lane(
    lane: str,
    ids: list[str],
    *,
    by: str,
    note: str | None = None,
    today: str | None = None,
    root: Path | None = None,
    replace: bool = False,
) -> Path:
    """Record a human Macro-H1 authorization for ``lane`` covering ``ids``."""

    if lane not in VALID_LANES:
        raise ValueError(f"lane must be one of: {', '.join(sorted(VALID_LANES))}")
    if not by.strip():
        raise ValueError("authorize-lane needs BY=<human name>")
    clean = sorted({i.strip() for i in ids if i and i.strip()})
    if not clean:
        raise ValueError("authorize-lane needs at least one ID")

    path = lane_path(lane, root)
    path.parent.mkdir(parents=True, exist_ok=True)
    existing = load_lane(lane, root)
    merged = clean if replace else sorted(set(existing.get("ids") or []) | set(clean))
    stamp = today or datetime.date.today().isoformat()
    payload = {
        "lane": lane,
        "authorized_by": by.strip(),
        "authorized_at": stamp,
        "ids": merged,
        "note": note,
    }
    path.write_text(
        yaml.safe_dump(payload, sort_keys=False, allow_unicode=True),
        encoding="utf-8",
        newline="\n",
    )
    return path


def iter_dossiers(root: Path | None = None) -> list[Path]:
    base = root or INGESTIONS_DIR
    if not base.is_dir():
        return []
    return sorted(
        p
        for p in base.iterdir()
        if p.is_dir() and not p.name.startswith("_") and (p / "state.yml").is_file()
    )


def build_risk_matrix(root: Path | None = None) -> tuple[dict[Lane, list[SentinelReport]], str]:
    """Evaluate every dossier and return reports grouped by lane plus markdown."""

    grouped: dict[Lane, list[SentinelReport]] = {"green": [], "yellow": [], "red": []}
    for dossier in iter_dossiers(root):
        report = evaluate(dossier)
        grouped[report.lane].append(report)

    lines = [
        "# Risk matrix (Gate Sentinel)",
        "",
        "Strategic Point 1 input. Humans authorize the green lane with "
        "`make authorize-lane LANE=green IDS=... BY=...`.",
        "",
        f"- Green: {len(grouped['green'])}",
        f"- Yellow: {len(grouped['yellow'])}",
        f"- Red: {len(grouped['red'])}",
        "",
    ]
    for lane in ("green", "yellow", "red"):
        lines += [
            f"## {lane}",
            "",
            "| ID | Phase | Eligible auto-sign | Notes |",
            "| :--- | :--- | :--- | :--- |",
        ]
        for report in grouped[lane]:  # type: ignore[index]
            bad = [f"{r.name}={r.lane}" for r in report.rules if r.lane != "green"]
            notes = "; ".join(bad) or "all green"
            eligible = "yes" if report.eligible_for_auto_sign else "no"
            lines.append(
                f"| {report.ingestion_id} | {report.phase} | {eligible} | {notes} |"
            )
        if not grouped[lane]:  # type: ignore[index]
            lines.append("| _(none)_ | | | |")
        lines.append("")
    return grouped, "\n".join(lines)


def write_risk_matrix(*, root: Path | None = None, out: Path | None = None) -> Path:
    _, markdown = build_risk_matrix(root)
    target = out or (REPO_ROOT / "build" / "risk_matrix.md")
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(markdown, encoding="utf-8", newline="\n")
    return target
