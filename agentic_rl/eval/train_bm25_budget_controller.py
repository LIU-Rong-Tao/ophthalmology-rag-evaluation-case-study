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


POLICIES = ["bm25_top2", "bm25_top5", "bm25_top10"]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Train a lightweight rule-based BM25 budget controller from oracle best-policy labels."
    )
    parser.add_argument(
        "--cases",
        default="agentic_rl/results/hotpot_dev_subset_100_full_context.json",
    )
    parser.add_argument(
        "--rewards",
        default="agentic_rl/results/hotpot_bm25_policy_ablation_dev100.csv",
    )
    parser.add_argument(
        "--oracle",
        default="agentic_rl/results/bm25_policy_oracle_best_policy_dev100.csv",
    )
    parser.add_argument(
        "--output",
        default="agentic_rl/results/bm25_budget_controller_predictions_dev100.csv",
    )
    parser.add_argument(
        "--summary-output",
        default="agentic_rl/results/bm25_budget_controller_summary.md",
    )
    return parser.parse_args()


def tokenize(text: str) -> list[str]:
    return re.findall(r"[a-z0-9]+", text.lower())


def normalize_title(value: Any) -> str:
    return str(value).strip().lower()


def context_docs(case: dict[str, Any]) -> list[dict[str, str]]:
    docs = []
    for item in case.get("context", []):
        if not isinstance(item, list) or len(item) < 2:
            continue
        title = str(item[0])
        sentences = item[1] if isinstance(item[1], list) else []
        text = f"{title} {title} {' '.join(str(s) for s in sentences)}"
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


def bm25_scores(query: str, docs: list[dict[str, str]]) -> list[float]:
    docs_tokens = [tokenize(doc["text"]) for doc in docs]
    query_terms = tokenize(query)
    if not docs or not query_terms:
        return [0.0 for _ in docs]

    idf_map = idf(docs_tokens)
    avgdl = sum(len(t) for t in docs_tokens) / max(len(docs_tokens), 1)
    k1 = 1.5
    b = 0.75

    scores = []
    for tokens in docs_tokens:
        tf = Counter(tokens)
        dl = len(tokens) or 1
        score = 0.0
        for term in query_terms:
            freq = tf.get(term, 0)
            if freq == 0:
                continue
            denom = freq + k1 * (1 - b + b * dl / avgdl)
            score += idf_map.get(term, 0.0) * freq * (k1 + 1) / denom
        scores.append(score)

    return sorted(scores, reverse=True)


def score_entropy(scores: list[float], top_k: int = 5) -> float:
    vals = [max(s, 0.0) for s in scores[:top_k]]
    total = sum(vals)
    if total <= 0:
        return 0.0
    probs = [v / total for v in vals if v > 0]
    return -sum(p * math.log(p + 1e-12) for p in probs)


def extract_features(case: dict[str, Any]) -> dict[str, float]:
    question = case.get("question") or ""
    tokens = tokenize(question)
    scores = bm25_scores(question, context_docs(case))
    top1 = scores[0] if len(scores) > 0 else 0.0
    top2 = scores[1] if len(scores) > 1 else 0.0
    top5 = scores[4] if len(scores) > 4 else 0.0

    return {
        "query_len": float(len(tokens)),
        "capitalized_count": float(len(re.findall(r"\b[A-Z][a-zA-Z]+\b", question))),
        "quoted_count": float(len(re.findall(r'"[^"]+"', question))),
        "top1_score": top1,
        "top1_top2_gap": top1 - top2,
        "top2_top5_gap": top2 - top5,
        "top5_entropy": score_entropy(scores, top_k=5),
    }


def load_reward_table(path: Path) -> dict[str, dict[str, dict[str, float]]]:
    table: dict[str, dict[str, dict[str, float]]] = {}
    for row in csv.DictReader(path.open(encoding="utf-8")):
        table.setdefault(row["case_id"], {})[row["policy"]] = {
            "reward": float(row["reward"]),
            "coverage": float(row["evidence_coverage"]),
            "cost": float(row["search_cost"]),
        }
    return table


def load_oracle(path: Path) -> dict[str, str]:
    return {
        row["case_id"]: row["best_policy"]
        for row in csv.DictReader(path.open(encoding="utf-8"))
    }


def predict_policy(features: dict[str, float], low_gap_threshold: float, high_entropy_threshold: float) -> str:
    if features["top1_top2_gap"] >= low_gap_threshold and features["top5_entropy"] < high_entropy_threshold:
        return "bm25_top2"
    if features["top5_entropy"] >= high_entropy_threshold:
        return "bm25_top10"
    return "bm25_top5"


def evaluate(
    cases: list[dict[str, Any]],
    reward_table: dict[str, dict[str, dict[str, float]]],
    oracle: dict[str, str],
    low_gap_threshold: float,
    high_entropy_threshold: float,
) -> tuple[float, float, float, float, float]:
    rewards = []
    coverages = []
    costs = []
    regrets = []
    correct = []

    for case in cases:
        case_id = case.get("_id") or case.get("id")
        features = extract_features(case)
        pred = predict_policy(features, low_gap_threshold, high_entropy_threshold)
        pred_result = reward_table[case_id][pred]
        oracle_policy = oracle[case_id]
        oracle_reward = reward_table[case_id][oracle_policy]["reward"]

        rewards.append(pred_result["reward"])
        coverages.append(pred_result["coverage"])
        costs.append(pred_result["cost"])
        regrets.append(oracle_reward - pred_result["reward"])
        correct.append(float(pred == oracle_policy))

    n = len(cases)
    return (
        sum(rewards) / n,
        sum(coverages) / n,
        sum(costs) / n,
        sum(regrets) / n,
        sum(correct) / n,
    )


def main() -> int:
    args = parse_args()

    cases = json.loads(Path(args.cases).read_text(encoding="utf-8"))
    reward_table = load_reward_table(Path(args.rewards))
    oracle = load_oracle(Path(args.oracle))

    features_by_case = {
        (case.get("_id") or case.get("id")): extract_features(case)
        for case in cases
    }

    gap_values = sorted({round(f["top1_top2_gap"], 4) for f in features_by_case.values()})
    entropy_values = sorted({round(f["top5_entropy"], 4) for f in features_by_case.values()})

    candidate_gaps = gap_values[:: max(1, len(gap_values) // 20)] or [0.0]
    candidate_entropies = entropy_values[:: max(1, len(entropy_values) // 20)] or [0.0]

    best = None
    for gap in candidate_gaps:
        for entropy in candidate_entropies:
            metrics = evaluate(cases, reward_table, oracle, gap, entropy)
            mean_reward, mean_coverage, mean_cost, mean_regret, accuracy = metrics
            key = (mean_reward, -mean_regret, accuracy, -mean_cost)
            if best is None or key > best["key"]:
                best = {
                    "key": key,
                    "gap": gap,
                    "entropy": entropy,
                    "metrics": metrics,
                }

    assert best is not None
    low_gap_threshold = best["gap"]
    high_entropy_threshold = best["entropy"]

    rows = []
    action_counts = Counter()
    oracle_counts = Counter()
    for case in cases:
        case_id = case.get("_id") or case.get("id")
        features = features_by_case[case_id]
        pred = predict_policy(features, low_gap_threshold, high_entropy_threshold)
        oracle_policy = oracle[case_id]
        pred_result = reward_table[case_id][pred]
        oracle_reward = reward_table[case_id][oracle_policy]["reward"]

        action_counts[pred] += 1
        oracle_counts[oracle_policy] += 1

        rows.append(
            {
                "case_id": case_id,
                "question": case.get("question", ""),
                "pred_policy": pred,
                "oracle_policy": oracle_policy,
                "pred_reward": f"{pred_result['reward']:.4f}",
                "oracle_reward": f"{oracle_reward:.4f}",
                "regret": f"{oracle_reward - pred_result['reward']:.4f}",
                **{k: f"{v:.4f}" for k, v in features.items()},
            }
        )

    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    mean_reward, mean_coverage, mean_cost, mean_regret, accuracy = best["metrics"]

    summary = []
    summary.append("# BM25 Budget Controller v1")
    summary.append("")
    summary.append("## 目的")
    summary.append("")
    summary.append("本实验训练一个轻量规则式 controller，根据 query 与 BM25 分数特征选择检索预算。")
    summary.append("")
    summary.append("候选 action 为 bm25_top2、bm25_top5、bm25_top10。目标不是提升 BM25 排序本身，而是在 coverage 与 search cost 之间学习预算调度。")
    summary.append("")
    summary.append("## 最优规则参数")
    summary.append("")
    summary.append(f"- top1_top2_gap threshold: {low_gap_threshold:.4f}")
    summary.append(f"- top5_entropy threshold: {high_entropy_threshold:.4f}")
    summary.append("")
    summary.append("## 结果")
    summary.append("")
    summary.append("| metric | value |")
    summary.append("| --- | ---: |")
    summary.append(f"| avg_reward | {mean_reward:.4f} |")
    summary.append(f"| avg_coverage | {mean_coverage:.4f} |")
    summary.append(f"| avg_cost | {mean_cost:.4f} |")
    summary.append(f"| avg_regret_vs_oracle | {mean_regret:.4f} |")
    summary.append(f"| oracle_action_accuracy | {accuracy:.4f} |")
    summary.append("")
    summary.append("## Predicted action distribution")
    summary.append("")
    summary.append("| policy | count |")
    summary.append("| --- | ---: |")
    for policy, count in action_counts.most_common():
        summary.append(f"| {policy} | {count} |")
    summary.append("")
    summary.append("## Oracle action distribution")
    summary.append("")
    summary.append("| policy | count |")
    summary.append("| --- | ---: |")
    for policy, count in oracle_counts.most_common():
        summary.append(f"| {policy} | {count} |")
    summary.append("")

    Path(args.summary_output).write_text("\n".join(summary), encoding="utf-8")

    print(f"wrote predictions: {args.output}")
    print(f"wrote summary: {args.summary_output}")
    print(f"avg_reward={mean_reward:.4f}")
    print(f"avg_coverage={mean_coverage:.4f}")
    print(f"avg_cost={mean_cost:.4f}")
    print(f"avg_regret_vs_oracle={mean_regret:.4f}")
    print(f"oracle_action_accuracy={accuracy:.4f}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
