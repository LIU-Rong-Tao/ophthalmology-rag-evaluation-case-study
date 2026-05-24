#!/usr/bin/env python
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any


POLICY_COST = {
    "dense_top10": 1.0,
    "dense50_rerank10": 3.0,
    "multi_query_dense_top10": 4.0,
    "multi_query_rerank10": 5.0,
    "abstain": 0.5,
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="运行 HotpotQA fixed search policy ablation 的轻量模拟版。"
    )
    parser.add_argument(
        "--input",
        required=True,
        help="HotpotQA 风格 JSON 文件，第一版只需要 question 和 supporting_facts 字段。",
    )
    parser.add_argument(
        "--output",
        default="agentic_rl/results/hotpot_fixed_policy_ablation.csv",
        help="输出 CSV 路径。",
    )
    parser.add_argument(
        "--lambda-cost",
        type=float,
        default=0.1,
        help="search cost 惩罚系数。",
    )
    return parser.parse_args()


def load_cases(path: Path) -> list[dict[str, Any]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        for key in ("data", "examples", "cases", "test_cases"):
            if key in data and isinstance(data[key], list):
                return data[key]
    raise ValueError(f"不支持的数据格式：{path}")


def normalize_title(value: Any) -> str:
    return str(value).strip().lower()


def gold_sources(case: dict[str, Any]) -> set[str]:
    facts = case.get("supporting_facts", [])
    sources: set[str] = set()
    for item in facts:
        if isinstance(item, list) and item:
            sources.add(normalize_title(item[0]))
        elif isinstance(item, dict):
            title = item.get("title") or item.get("source") or item.get("doc_title")
            if title:
                sources.add(normalize_title(title))
    return sources


def simulate_policy_retrieval(policy: str, gold: set[str]) -> set[str]:
    """轻量模拟不同 search policy 的 evidence 覆盖能力。"""
    if policy == "abstain":
        return set()
    if not gold:
        return set()

    ordered = sorted(gold)
    if policy == "dense_top10":
        return set(ordered[:1])
    if policy == "dense50_rerank10":
        return set(ordered[:2])
    if policy == "multi_query_dense_top10":
        keep = max(1, len(ordered) - 1)
        return set(ordered[:keep])
    if policy == "multi_query_rerank10":
        return set(ordered)

    raise ValueError(f"未知 policy：{policy}")


def evidence_coverage(retrieved: set[str], gold: set[str]) -> float:
    if not gold:
        return 0.0
    return len(retrieved & gold) / len(gold)


def main() -> int:
    args = parse_args()
    cases = load_cases(Path(args.input))

    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)

    rows = []
    for idx, case in enumerate(cases, start=1):
        question = case.get("question") or case.get("query") or ""
        gold = gold_sources(case)

        for policy, cost in POLICY_COST.items():
            retrieved = simulate_policy_retrieval(policy, gold)
            coverage = evidence_coverage(retrieved, gold)
            reward = coverage - args.lambda_cost * cost

            rows.append(
                {
                    "case_id": case.get("_id") or case.get("id") or idx,
                    "question": question,
                    "gold_source_count": len(gold),
                    "policy": policy,
                    "evidence_coverage": f"{coverage:.4f}",
                    "search_cost": f"{cost:.2f}",
                    "reward": f"{reward:.4f}",
                }
            )

    with output.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "case_id",
                "question",
                "gold_source_count",
                "policy",
                "evidence_coverage",
                "search_cost",
                "reward",
            ],
        )
        writer.writeheader()
        writer.writerows(rows)

    print(f"写入 {output}，共 {len(rows)} 条 policy-case 结果。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
