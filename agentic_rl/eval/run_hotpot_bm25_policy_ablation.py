#!/usr/bin/env python3
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
    "bm25_top2": 1.0,
    "bm25_top5": 2.0,
    "bm25_top10": 4.0,
    "multi_query_bm25_top5": 4.5,
    "abstain": 0.5,
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run BM25 fixed policy ablation on HotpotQA full-context subset."
    )
    parser.add_argument(
        "--input",
        default="agentic_rl/results/hotpot_dev_subset_100_full_context.json",
    )
    parser.add_argument(
        "--output",
        default="agentic_rl/results/hotpot_bm25_policy_ablation_dev100.csv",
    )
    parser.add_argument("--lambda-cost", type=float, default=0.1)
    return parser.parse_args()


def tokenize(text: str) -> list[str]:
    return re.findall(r"[a-z0-9]+", text.lower())


def load_cases(path: Path) -> list[dict[str, Any]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(data, list):
        return data
    for key in ("data", "examples", "cases", "test_cases"):
        if isinstance(data, dict) and isinstance(data.get(key), list):
            return data[key]
    raise ValueError(f"Unsupported input format: {path}")


def normalize_title(value: Any) -> str:
    return str(value).strip().lower()


def gold_titles(case: dict[str, Any]) -> set[str]:
    titles = set()
    for item in case.get("supporting_facts", []):
        if isinstance(item, list) and item:
            titles.add(normalize_title(item[0]))
        elif isinstance(item, dict):
            title = item.get("title") or item.get("source") or item.get("doc_title")
            if title:
                titles.add(normalize_title(title))
    return titles


def context_docs(case: dict[str, Any]) -> list[dict[str, str]]:
    docs = []
    for item in case.get("context", []):
        if not isinstance(item, list) or len(item) < 2:
            continue
        title = str(item[0])
        sentences = item[1] if isinstance(item[1], list) else []
        body = " ".join(str(s) for s in sentences)
        text = f"{title} {title} {body}"
        docs.append({"title": title, "text": text})
    return docs


def idf(docs_tokens: list[list[str]]) -> dict[str, float]:
    n_docs = len(docs_tokens)
    df = Counter()
    for tokens in docs_tokens:
        df.update(set(tokens))
    return {
        term: math.log(1 + (n_docs - freq + 0.5) / (freq + 0.5))
        for term, freq in df.items()
    }


def bm25_scores(query: str, docs: list[dict[str, str]]) -> list[tuple[dict[str, str], float]]:
    docs_tokens = [tokenize(doc["text"]) for doc in docs]
    query_terms = tokenize(query)
    if not docs or not query_terms:
        return [(doc, 0.0) for doc in docs]

    idf_map = idf(docs_tokens)
    avgdl = sum(len(t) for t in docs_tokens) / max(len(docs_tokens), 1)
    k1 = 1.5
    b = 0.75

    scored = []
    for doc, tokens in zip(docs, docs_tokens):
        tf = Counter(tokens)
        dl = len(tokens) or 1
        score = 0.0
        for term in query_terms:
            freq = tf.get(term, 0)
            if freq == 0:
                continue
            denom = freq + k1 * (1 - b + b * dl / avgdl)
            score += idf_map.get(term, 0.0) * freq * (k1 + 1) / denom
        scored.append((doc, score))

    return sorted(scored, key=lambda x: x[1], reverse=True)


def expanded_queries(question: str) -> list[str]:
    tokens = tokenize(question)
    keyword_query = " ".join(t for t in tokens if len(t) > 3)
    quoted_parts = re.findall(r'"([^"]+)"', question)

    queries = [question]
    if keyword_query and keyword_query != question.lower():
        queries.append(keyword_query)
    queries.extend(quoted_parts)

    seen = set()
    unique = []
    for query in queries:
        clean = query.strip()
        if clean and clean not in seen:
            unique.append(clean)
            seen.add(clean)
    return unique


def retrieve(policy: str, case: dict[str, Any]) -> set[str]:
    if policy == "abstain":
        return set()

    docs = context_docs(case)
    if not docs:
        return set()

    question = case.get("question") or case.get("query") or ""

    if policy in {"bm25_top2", "bm25_top5", "bm25_top10"}:
        top_k = {"bm25_top2": 2, "bm25_top5": 5, "bm25_top10": 10}[policy]
        scored = bm25_scores(question, docs)
        return {normalize_title(doc["title"]) for doc, _ in scored[:top_k]}

    if policy == "multi_query_bm25_top5":
        merged: dict[str, tuple[dict[str, str], float]] = {}
        for query in expanded_queries(question):
            for rank, (doc, score) in enumerate(bm25_scores(query, docs), start=1):
                title = normalize_title(doc["title"])
                merged_score = score + 1.0 / rank
                if title not in merged or merged_score > merged[title][1]:
                    merged[title] = (doc, merged_score)

        ranked = sorted(merged.values(), key=lambda x: x[1], reverse=True)
        return {normalize_title(doc["title"]) for doc, _ in ranked[:5]}

    raise ValueError(f"Unknown policy: {policy}")


def coverage(retrieved: set[str], gold: set[str]) -> float:
    if not gold:
        return 0.0
    return len(retrieved & gold) / len(gold)


def main() -> int:
    args = parse_args()
    cases = load_cases(Path(args.input))

    rows = []
    for idx, case in enumerate(cases, start=1):
        question = case.get("question") or case.get("query") or ""
        gold = gold_titles(case)

        for policy, cost in POLICY_COST.items():
            retrieved = retrieve(policy, case)
            cov = coverage(retrieved, gold)
            reward = cov - args.lambda_cost * cost

            rows.append(
                {
                    "case_id": case.get("_id") or case.get("id") or idx,
                    "question": question,
                    "gold_source_count": len(gold),
                    "policy": policy,
                    "retrieved_count": len(retrieved),
                    "evidence_coverage": f"{cov:.4f}",
                    "search_cost": f"{cost:.2f}",
                    "reward": f"{reward:.4f}",
                }
            )

    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    print(f"wrote {output}, rows={len(rows)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
