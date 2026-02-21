from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List


def _rows_by_id(payload: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    out: Dict[str, Dict[str, Any]] = {}
    for r in list(payload.get("results") or []):
        if not isinstance(r, dict):
            continue
        rid = str(r.get("id") or "").strip()
        if rid and rid not in out:
            out[rid] = r
    return out


def _actual(row: Dict[str, Any]) -> Dict[str, Any]:
    return row.get("actual") if isinstance(row.get("actual"), dict) else {}


def build_shadow_diff(v2_payload: Dict[str, Any], v3_payload: Dict[str, Any]) -> Dict[str, Any]:
    v2 = _rows_by_id(v2_payload if isinstance(v2_payload, dict) else {})
    v3 = _rows_by_id(v3_payload if isinstance(v3_payload, dict) else {})
    all_ids = sorted(set(v2.keys()) | set(v3.keys()))
    rows: List[Dict[str, Any]] = []
    improved = 0
    regressed = 0
    unchanged = 0

    for rid in all_ids:
        a = v2.get(rid) or {}
        b = v3.get(rid) or {}
        a_pass = bool(a.get("pass"))
        b_pass = bool(b.get("pass"))
        delta = "unchanged"
        if (not a_pass) and b_pass:
            delta = "improved"
            improved += 1
        elif a_pass and (not b_pass):
            delta = "regressed"
            regressed += 1
        else:
            unchanged += 1

        aa = _actual(a)
        bb = _actual(b)
        rows.append(
            {
                "id": rid,
                "v2_pass": a_pass,
                "v3_pass": b_pass,
                "delta": delta,
                "v2_type": str(aa.get("assistant_type") or ""),
                "v3_type": str(bb.get("assistant_type") or ""),
                "v2_pending_mode": aa.get("pending_mode"),
                "v3_pending_mode": bb.get("pending_mode"),
                "v2_rows": aa.get("rows"),
                "v3_rows": bb.get("rows"),
                "v2_text": str(aa.get("assistant_text") or "")[:220],
                "v3_text": str(bb.get("assistant_text") or "")[:220],
            }
        )

    return {
        "executed_at_utc": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
        "mode": "phase8_shadow_diff",
        "summary": {
            "total_cases": len(all_ids),
            "improved": improved,
            "regressed": regressed,
            "unchanged": unchanged,
        },
        "rows": rows,
    }


def _markdown(payload: Dict[str, Any], v2_path: str, v3_path: str) -> str:
    s = payload.get("summary") if isinstance(payload.get("summary"), dict) else {}
    lines = [
        "# Phase 8 Shadow Diff",
        "",
        f"- Executed: {payload.get('executed_at_utc')}",
        f"- V2 artifact: `{v2_path}`",
        f"- V3 artifact: `{v3_path}`",
        "",
        "## Summary",
        f"- Total: {s.get('total_cases')}",
        f"- Improved: {s.get('improved')}",
        f"- Regressed: {s.get('regressed')}",
        f"- Unchanged: {s.get('unchanged')}",
        "",
        "## Case Deltas",
        "| ID | v2 Pass | v3 Pass | Delta | v2 Type | v3 Type | v2 Pending | v3 Pending |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for r in list(payload.get("rows") or []):
        if not isinstance(r, dict):
            continue
        lines.append(
            f"| {r.get('id')} | {r.get('v2_pass')} | {r.get('v3_pass')} | {r.get('delta')} | "
            f"{r.get('v2_type')} | {r.get('v3_type')} | {r.get('v2_pending_mode')} | {r.get('v3_pending_mode')} |"
        )
    return "\n".join(lines) + "\n"


def main() -> None:
    ap = argparse.ArgumentParser(description="Phase 8 shadow diff report generator (v2 vs v3 raw artifacts).")
    ap.add_argument("--v2-raw", required=True, help="V2 raw artifact path.")
    ap.add_argument("--v3-raw", required=True, help="V3 raw artifact path.")
    ap.add_argument("--output-dir", default="impl_factory/04_automation/logs", help="Output folder.")
    args = ap.parse_args()

    v2_path = Path(args.v2_raw)
    v3_path = Path(args.v3_raw)
    v2 = json.loads(v2_path.read_text(encoding="utf-8"))
    v3 = json.loads(v3_path.read_text(encoding="utf-8"))
    payload = build_shadow_diff(v2, v3)

    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    json_path = out_dir / f"{ts}_phase8_shadow_diff.json"
    md_path = out_dir / f"{ts}_phase8_shadow_diff.md"
    json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    md_path.write_text(_markdown(payload, str(v2_path), str(v3_path)), encoding="utf-8")

    print(f"OUT_JSON={json_path}")
    print(f"OUT_MD={md_path}")
    print(json.dumps(payload.get("summary") or {}, ensure_ascii=False))


if __name__ == "__main__":
    main()

