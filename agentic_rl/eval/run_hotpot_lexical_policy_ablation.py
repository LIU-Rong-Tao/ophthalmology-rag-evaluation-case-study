from __future__ import annotations

import argparse
import csv
import json
import math
import re
from collections import Counter
from pathlib import Path
from typing import Any


POLICY_COST = {
    "lexical_top10": 1.0,
    "lexical_top50_rerank10": 3.0,
    "multi_query_lexical_top10": 4.0,
    "multi_query_rerank10": 5.0,
    "abstain": 0.5,
}


STOPWORDS = {
    "the", "a", "an", "of", "in", "on", "at", "to", "for", "with", "and", "or",
    "is", "are", "was", "were", "be", "been", "being", "by", "from", "as",
    "that", "this", "which", "what", "who", "whom", "whose", "when", "where",
    "why", "how", "did", "do", "does", "has", "have", "had", "it", "its",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="运行 HotpotQA lexical retrieval fixed policy ablation。"
    )
    parser.add_argument("--input", required=True, help="标准化 HotpotQA subset JSON。")
    parser.add_argument(
        "--output",
        default="agentic_rl/results/hotpot_lexical_policy_ablation_dev100.csv",
        help="输出 CSV 路径。",
    )
    parser.add_argument("--lambda-cost", type=float, default=0.1)
    return parser.parse_args()


def tokenize(text: str) -> list[str]:
    return [
        t
        for t in re.findall(r"[a-zA-Z0-9]+", text.lower())
        if t not in STOPWORDS and len(t) > 1
    ]


def lexical_score(query: str, title: str) -> float:
    q = Counter(tokenize(query))
    t = Counter(tokenize(title))
    if not q or not t:
        return 0.0

    overlap = sum(min(q[w], t[w]) for w in q.keys() & t.keys())
    title_norm = math.sqrt(sum(v * v for v in t.values()))
    query_norm = math.sqrt(sum(v * v for v in q.values()))
    return overlap / (title_norm * query_norm)


def retrieve_titles(question: str, context_titles: list[str], top_k: int) -> list[str]:
    scored = []
    for title in context_titles:
        scored.append((lexical_score(question, title), title))
    scored.sort(key=lambda x: (-x[0], x[1].lower()))
    return [title for score, title in scored[:top_k] if score > 0]


def expand_query(question: str) -> list[str]:
    tokens = tokenize(question)
    entity_like = [t for t in tokens if len(t) >= 4]
    return [
        question,
        " ".join(entity_like),
    ]


def policy_retrieve(policy: str, case: dict[str, Any]) -> set[str]:
    question = case.get("question", "")
    context_titles = case.get("context_titles", [])

    if policy == "abstain":
        return set()

    if policy == "lexical_top10":
        return set(retrieve_titles(question, context_titles, top_k=10))

    if policy == "lexical_top50_rerank10":
        # v0 使用 lexical score 近似 rerank：先取 50，再保留前 10。
        candidates = retrieve_titles(question, context_titles, top_k=50)
        return set(candidates[:10])

    if policy == "multi_query_lexical_top10":
        retrieved = set()
        for q in expand_query(question):
            retrieved.update(retrieve_titles(q, context_titles, top_k=10))
        return retrieved

    if policy == "multi_query_rerank10":
        retrieved = set()
        for q in expand_query(question):
            retrieved.update(retrieve_titles(q, context_titles, top_k=50)[:10])
        return retrieved

    raise ValueError(f"未知 policy：{policy}")


def normalize_title(title: Any) -> str:
    return str(title).strip().lower()


def evidence_coverage(retrieved: set[str], gold: set[str]) -> float:
    if not gold:
        return 0.0
    retrieved_norm = {normalize_title(x) for x in retrieved}
    return len(retrieved_norm & gold) / len(gold)


def main() -> int:
    args = parse_args()
    cases = json.loads(Path(args.input).read_text(encoding="utf-8"))

    rows = []
    for case in cases:
        gold = {normalize_title(x) for x in case.get("gold_titles", [])}
        for policy, cost in POLICY_COST.items():
            retrieved = policy_retrieve(policy, case)
            coverage = evidence_coverage(retrieved, gold)
            reward = coverage - args.lambda_cost * cost
            rows.append(
                {
                    "case_id": case.get("id", ""),
                    "question": case.get("question", ""),
                    "gold_titles": " | ".join(case.get("gold_titles", [])),
                    "policy": policy,
                    "retrieved_count": len(retrieved),
                    "evidence_coverage": f"{coverage:.4f}",
                    "search_cost": f"{cost:.2f}",
                    "reward": f"{reward:.4f}",
                }
            )

    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "case_id",
                "question",
                "gold_titles",
                "policy",
                "retrieved_count",
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
