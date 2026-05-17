#!/usr/bin/env python
"""Summarize generation ablation results."""

from __future__ import annotations

import json
from pathlib import Path

import argparse

def parse_args():
    parser = argparse.ArgumentParser(description="Summarize generation ablation results.")
    parser.add_argument("--input", default="eval/results/generation_dense_top5_both.json")
    parser.add_argument("--output", default=None)
    return parser.parse_args()

def fmt(value: float) -> str:
    return f"{value:.4f}"

def main() -> int:
    args = parse_args()
    input_path = Path(args.input)
    output_path = Path(args.output) if args.output else input_path.with_name(input_path.stem + "_summary.md")
    report = json.loads(input_path.read_text(encoding="utf-8"))
    rows = []

    for index, item in enumerate(report["results"], start=1):
        retrieval = item.get("retrieval", {})
        retrieval_metrics = retrieval.get("metrics", {})
        rag = item.get("rag", {})
        citation_metrics = rag.get("citation_metrics", {})

        expected = item.get("expected_sources", [])
        retrieved = retrieval.get("retrieved_sources", [])

        rows.append({
            "id": index,
            "query": item["query"][:34] + ("..." if len(item["query"]) > 34 else ""),
            "expected_n": len(expected),
            "retrieved_sources": ", ".join(dict.fromkeys(retrieved[:5])),
            "source_hit": float(retrieval_metrics.get("source_hit@k", 0.0)),
            "source_mrr": float(retrieval_metrics.get("source_mrr@k", 0.0)),
            "source_coverage": float(retrieval_metrics.get("source_coverage@k", 0.0)),
            "citation_coverage": float(citation_metrics.get("citation_expected_coverage", 0.0)),
            "vanilla_ms": float(item.get("vanilla", {}).get("elapsed_ms", 0.0)),
            "rag_total_ms": float(rag.get("total_elapsed_ms", 0.0)),
        })

    headers = [
        "id",
        "query",
        "expected_n",
        "source_hit",
        "source_mrr",
        "source_coverage",
        "citation_coverage",
        "vanilla_ms",
        "rag_total_ms",
        "retrieved_sources",
    ]

    lines = []
    lines.append("| " + " | ".join(headers) + " |")
    lines.append("| " + " | ".join(["---"] * len(headers)) + " |")

    for row in rows:
        values = []
        for key in headers:
            value = row[key]
            if isinstance(value, float):
                values.append(fmt(value))
            else:
                values.append(str(value).replace("|", "/"))
        lines.append("| " + " | ".join(values) + " |")

    output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(json.dumps(report["aggregate"], ensure_ascii=False, indent=2))
    print()
    print(output_path.read_text(encoding="utf-8"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
