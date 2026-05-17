#!/usr/bin/env python
"""Export selected vanilla vs RAG answer cases to Markdown."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def parse_args():
    parser = argparse.ArgumentParser(description="Export generation comparison cases.")
    parser.add_argument("--input", default="eval/results/generation_dense_top10_both.json")
    parser.add_argument("--output", default="eval/results/generation_case_studies.md")
    parser.add_argument("--case-ids", default="2,6", help="1-based case ids, comma separated.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    report = json.loads(Path(args.input).read_text(encoding="utf-8"))
    case_ids = [int(item.strip()) for item in args.case_ids.split(",") if item.strip()]

    lines = []
    lines.append("# Generation Case Studies")
    lines.append("")
    lines.append(f"Source report: `{args.input}`")
    lines.append("")

    for case_id in case_ids:
        item = report["results"][case_id - 1]
        retrieval = item.get("retrieval", {})
        vanilla = item.get("vanilla", {})
        rag = item.get("rag", {})

        lines.append(f"## Case {case_id}")
        lines.append("")
        lines.append(f"**Query:** {item['query']}")
        lines.append("")
        lines.append("**Expected Sources:**")
        for source in item.get("expected_sources", []):
            lines.append(f"- {source}")
        lines.append("")

        lines.append("**Retrieved Sources:**")
        for source in dict.fromkeys(retrieval.get("retrieved_sources", [])):
            lines.append(f"- {source}")
        lines.append("")

        citation_map = rag.get("citation_map", {})
        if citation_map:
            lines.append("**Citation Map:**")
            for marker, source in citation_map.items():
                lines.append(f"- [{marker}] {source}")
            lines.append("")

        lines.append("**Retrieval Metrics:**")
        metrics = retrieval.get("metrics", {})
        for key, value in metrics.items():
            lines.append(f"- {key}: {value:.4f}")
        lines.append("")

        lines.append("**Vanilla Answer:**")
        lines.append("")
        lines.append(vanilla.get("answer", "").strip())
        lines.append("")

        lines.append("**RAG Answer:**")
        lines.append("")
        lines.append(rag.get("answer", "").strip())
        lines.append("")

        lines.append("**Citation Metrics:**")
        for key, value in rag.get("citation_metrics", {}).items():
            lines.append(f"- {key}: {value:.4f}")
        lines.append("")

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(f"Wrote {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
