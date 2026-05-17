#!/usr/bin/env python
"""Summarize generation top-k ablation reports."""

from __future__ import annotations

import csv
import json
from pathlib import Path


REPORTS = [
    ("dense_top5", Path("eval/results/generation_dense_top5_both.json")),
    ("dense_top8", Path("eval/results/generation_dense_top8_both.json")),
    ("dense_top10", Path("eval/results/generation_dense_top10_both.json")),
    ("hybrid_top10", Path("eval/results/generation_hybrid_top10_both.json")),
]

OUT_CSV = Path("eval/results/generation_topk_ablation_summary.csv")
OUT_MD = Path("eval/results/generation_topk_ablation_summary.md")


def load_row(name: str, path: Path) -> dict[str, object]:
    report = json.loads(path.read_text(encoding="utf-8"))
    agg = report["aggregate"]
    return {
        "setting": name,
        "query_count": agg["query_count"],
        "retrieval_source_hit@k": agg["retrieval_source_hit@k"],
        "retrieval_source_mrr@k": agg["retrieval_source_mrr@k"],
        "retrieval_source_coverage@k": agg["retrieval_source_coverage@k"],
        "rag_citation_coverage": agg["rag_avg_citation_expected_coverage"],
        "vanilla_avg_ms": agg["vanilla_avg_generation_ms"],
        "rag_generation_avg_ms": agg["rag_avg_generation_ms"],
        "rag_total_avg_ms": agg["rag_avg_total_ms"],
    }


def fmt(value: object) -> str:
    if isinstance(value, float):
        return f"{value:.4f}"
    return str(value)


def main() -> int:
    rows = [load_row(name, path) for name, path in REPORTS]

    headers = list(rows[0].keys())

    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    with OUT_CSV.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=headers)
        writer.writeheader()
        writer.writerows(rows)

    lines = []
    lines.append("| " + " | ".join(headers) + " |")
    lines.append("| " + " | ".join(["---"] * len(headers)) + " |")
    for row in rows:
        lines.append("| " + " | ".join(fmt(row[key]) for key in headers) + " |")

    OUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(f"Wrote {OUT_CSV}")
    print(f"Wrote {OUT_MD}")
    print()
    print(OUT_MD.read_text(encoding="utf-8"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
