#!/usr/bin/env python
"""Summarize retrieval ablation JSON reports into CSV and Markdown tables."""

from __future__ import annotations

import csv
import json
from pathlib import Path
from statistics import median


RESULTS = [
    ("hybrid", Path("eval/results/hard_hybrid_top5.json")),
    ("dense", Path("eval/results/hard_dense_top5.json")),
    ("sparse", Path("eval/results/hard_sparse_top5.json")),
]

OUT_CSV = Path("eval/results/retrieval_ablation_summary.csv")
OUT_MD = Path("eval/results/retrieval_ablation_summary.md")


def percentile(values: list[float], pct: float) -> float:
    if not values:
        return 0.0
    sorted_values = sorted(values)
    index = min(len(sorted_values) - 1, int(round((pct / 100) * (len(sorted_values) - 1))))
    return sorted_values[index]


def load_row(mode: str, path: Path) -> dict[str, object]:
    with path.open("r", encoding="utf-8") as file:
        report = json.load(file)

    metrics = report.get("aggregate_metrics", {})
    query_results = report.get("query_results", [])
    elapsed_values = [
        float(item.get("elapsed_ms", 0.0))
        for item in query_results
    ]

    query_count = int(report.get("query_count", len(query_results)))
    total_ms = float(report.get("total_elapsed_ms", 0.0))
    avg_query_ms = sum(elapsed_values) / len(elapsed_values) if elapsed_values else 0.0

    return {
        "mode": mode,
        "query_count": query_count,
        "source_hit@5": float(metrics.get("source_hit_rate", 0.0)),
        "source_mrr@5": float(metrics.get("source_mrr", 0.0)),
        "total_ms": total_ms,
        "avg_query_ms": avg_query_ms,
        "p50_query_ms": float(median(elapsed_values)) if elapsed_values else 0.0,
        "p95_query_ms": percentile(elapsed_values, 95),
    }


def write_csv(rows: list[dict[str, object]]) -> None:
    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "mode",
        "query_count",
        "source_hit@5",
        "source_mrr@5",
        "total_ms",
        "avg_query_ms",
        "p50_query_ms",
        "p95_query_ms",
    ]

    with OUT_CSV.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def fmt(value: object) -> str:
    if isinstance(value, float):
        return f"{value:.4f}"
    return str(value)


def write_markdown(rows: list[dict[str, object]]) -> None:
    headers = [
        "mode",
        "query_count",
        "source_hit@5",
        "source_mrr@5",
        "total_ms",
        "avg_query_ms",
        "p50_query_ms",
        "p95_query_ms",
    ]

    lines = []
    lines.append("| " + " | ".join(headers) + " |")
    lines.append("| " + " | ".join(["---"] * len(headers)) + " |")

    for row in rows:
        lines.append("| " + " | ".join(fmt(row[key]) for key in headers) + " |")

    OUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    rows = [load_row(mode, path) for mode, path in RESULTS]
    write_csv(rows)
    write_markdown(rows)

    print(f"Wrote {OUT_CSV}")
    print(f"Wrote {OUT_MD}")
    print()
    print(OUT_MD.read_text(encoding="utf-8"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
