from __future__ import annotations

import argparse
import csv
from collections import Counter, defaultdict
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Analyze per-case oracle best policy from a fixed-policy reward table."
    )
    parser.add_argument(
        "--input",
        default="agentic_rl/results/hotpot_fixed_policy_ablation_dev100.csv",
    )
    parser.add_argument(
        "--output",
        default="agentic_rl/results/policy_oracle_best_policy_dev100.csv",
    )
    parser.add_argument(
        "--summary-output",
        default="agentic_rl/results/policy_oracle_best_policy_summary.md",
    )
    return parser.parse_args()


def load_rows(path: Path) -> list[dict[str, str]]:
    rows = list(csv.DictReader(path.open(encoding="utf-8")))
    if not rows:
        raise ValueError(f"No rows found in {path}")
    return rows


def to_float(row: dict[str, str], key: str) -> float:
    return float(row.get(key, "0") or 0)


def classify_case(best_policy: str, best_coverage: float, gap_to_second: float) -> str:
    if best_policy == "abstain":
        return "abstain_best"
    if best_policy == "bm25_top2":
        return "easy_low_budget"
    if best_policy == "bm25_top5":
        return "medium_budget"
    if best_policy == "bm25_top10":
        return "hard_high_budget"
    if best_policy == "multi_query_bm25_top5":
        return "query_expansion_helpful"
    if best_coverage >= 1.0 and best_policy in {"dense_top10", "lexical_top10"}:
        return "easy_cheap_sufficient"
    if best_policy in {"dense50_rerank10", "lexical_top50_rerank10"}:
        return "rerank_preferred"
    if "multi_query" in best_policy:
        return "multi_query_preferred"
    if gap_to_second < 0.05:
        return "near_tie"
    return "other"


def main() -> int:
    args = parse_args()
    rows = load_rows(Path(args.input))

    by_case: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        by_case[row["case_id"]].append(row)

    oracle_rows = []
    best_policy_counts = Counter()
    case_type_counts = Counter()

    for case_id, case_rows in by_case.items():
        ranked = sorted(
            case_rows,
            key=lambda r: (
                to_float(r, "reward"),
                to_float(r, "evidence_coverage"),
                -to_float(r, "search_cost"),
            ),
            reverse=True,
        )
        best = ranked[0]
        second = ranked[1] if len(ranked) > 1 else ranked[0]

        best_reward = to_float(best, "reward")
        second_reward = to_float(second, "reward")
        best_policy = best["policy"]
        best_coverage = to_float(best, "evidence_coverage")
        gap_to_second = best_reward - second_reward
        case_type = classify_case(best_policy, best_coverage, gap_to_second)

        best_policy_counts[best_policy] += 1
        case_type_counts[case_type] += 1

        oracle_rows.append(
            {
                "case_id": case_id,
                "question": best.get("question", ""),
                "gold_source_count": best.get("gold_source_count", ""),
                "best_policy": best_policy,
                "best_coverage": f"{best_coverage:.4f}",
                "best_cost": best.get("search_cost", ""),
                "best_reward": f"{best_reward:.4f}",
                "second_policy": second["policy"],
                "second_reward": f"{second_reward:.4f}",
                "gap_to_second": f"{gap_to_second:.4f}",
                "case_type": case_type,
            }
        )

    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(oracle_rows[0].keys()))
        writer.writeheader()
        writer.writerows(oracle_rows)

    total = len(oracle_rows)
    summary = []
    summary.append("# Policy Oracle Best-Action Analysis v0")
    summary.append("")
    summary.append("## 目的")
    summary.append("")
    summary.append("本分析基于 fixed policy reward table，统计每个 HotpotQA case 的 oracle best action。")
    summary.append("")
    summary.append("它用于判断当前 action space 是否有足够多样性，避免后续 controller 训练退化成永远选择同一个 search policy。")
    summary.append("")
    summary.append("## 输入")
    summary.append("")
    summary.append(f"- Reward table: {args.input}")
    summary.append(f"- Case 数量: {total}")
    summary.append("")
    summary.append("## Oracle best policy 分布")
    summary.append("")
    summary.append("| policy | count | share |")
    summary.append("| --- | ---: | ---: |")
    for policy, count in best_policy_counts.most_common():
        summary.append(f"| {policy} | {count} | {count / total:.4f} |")
    summary.append("")
    summary.append("## Case type 分布")
    summary.append("")
    summary.append("| case_type | count | share |")
    summary.append("| --- | ---: | ---: |")
    for case_type, count in case_type_counts.most_common():
        summary.append(f"| {case_type} | {count} | {count / total:.4f} |")
    summary.append("")
    summary.append("## 解释")
    summary.append("")
    summary.append("如果 oracle best policy 高度集中在单一 action，说明当前 reward simulation 或 action space 还不够丰富。")
    summary.append("")
    summary.append("这种情况下，下一步不应该急着训练更复杂的 controller，而应该引入真实 lexical/BM25/dense retrieval reward 或构造更细的 difficulty 分组。")
    summary.append("")
    summary.append(f"详细 per-case 输出见: {args.output}")
    summary.append("")

    Path(args.summary_output).write_text("\n".join(summary), encoding="utf-8")

    print(f"wrote oracle rows: {args.output}")
    print(f"wrote summary: {args.summary_output}")
    print("best policy counts:")
    for policy, count in best_policy_counts.most_common():
        print(f"- {policy}: {count}/{total}")
    print("case type counts:")
    for case_type, count in case_type_counts.most_common():
        print(f"- {case_type}: {count}/{total}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())