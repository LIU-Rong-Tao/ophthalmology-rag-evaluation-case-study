#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import random
from collections import Counter, defaultdict
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Train a minimal bandit-style search policy controller from a precomputed fixed-policy reward table."
    )
    parser.add_argument(
        "--input",
        default="agentic_rl/results/hotpot_fixed_policy_ablation_dev100.csv",
    )
    parser.add_argument(
        "--curve-output",
        default="agentic_rl/results/policy_controller_reward_curve_smoke.csv",
    )
    parser.add_argument(
        "--action-output",
        default="agentic_rl/results/policy_controller_action_distribution_smoke.csv",
    )
    parser.add_argument("--epochs", type=int, default=80)
    parser.add_argument("--epsilon-start", type=float, default=0.6)
    parser.add_argument("--epsilon-end", type=float, default=0.05)
    parser.add_argument("--seed", type=int, default=42)
    return parser.parse_args()


def load_reward_table(path: Path) -> dict[str, dict[str, float]]:
    rows = list(csv.DictReader(path.open(encoding="utf-8")))
    if not rows:
        raise ValueError(f"No rows found in {path}")

    table: dict[str, dict[str, float]] = defaultdict(dict)
    for row in rows:
        table[row["case_id"]][row["policy"]] = float(row["reward"])
    return dict(table)


def epsilon_for_epoch(epoch: int, epochs: int, start: float, end: float) -> float:
    if epochs <= 1:
        return end
    progress = (epoch - 1) / (epochs - 1)
    return start + progress * (end - start)


def choose_policy(action_value: dict[str, float], epsilon: float, rng: random.Random) -> str:
    policies = list(action_value)
    if rng.random() < epsilon:
        return rng.choice(policies)

    best_value = max(action_value.values())
    best_policies = [p for p, value in action_value.items() if value == best_value]
    return rng.choice(best_policies)


def write_csv(path: Path, rows: list[dict[str, str | int]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def main() -> int:
    args = parse_args()
    rng = random.Random(args.seed)

    reward_table = load_reward_table(Path(args.input))
    case_ids = list(reward_table)
    policies = sorted({policy for rewards in reward_table.values() for policy in rewards})

    action_value = {policy: 0.0 for policy in policies}
    action_count = {policy: 0 for policy in policies}
    curve_rows = []
    action_rows = []

    for epoch in range(1, args.epochs + 1):
        epsilon = epsilon_for_epoch(epoch, args.epochs, args.epsilon_start, args.epsilon_end)
        rng.shuffle(case_ids)

        rewards = []
        selected = Counter()

        for case_id in case_ids:
            policy = choose_policy(action_value, epsilon, rng)
            reward = reward_table[case_id][policy]

            rewards.append(reward)
            selected[policy] += 1

            action_count[policy] += 1
            n = action_count[policy]
            action_value[policy] += (reward - action_value[policy]) / n

        mean_reward = sum(rewards) / len(rewards)
        curve_rows.append(
            {
                "epoch": epoch,
                "epsilon": f"{epsilon:.4f}",
                "mean_reward": f"{mean_reward:.4f}",
                **{f"value_{p}": f"{action_value[p]:.4f}" for p in policies},
            }
        )

        total = sum(selected.values())
        action_rows.append(
            {
                "epoch": epoch,
                **{p: f"{selected[p] / total:.4f}" for p in policies},
            }
        )

    write_csv(Path(args.curve_output), curve_rows)
    write_csv(Path(args.action_output), action_rows)

    print(f"wrote reward curve: {args.curve_output}")
    print(f"wrote action distribution: {args.action_output}")
    print("final action values:")
    for policy in policies:
        print(f"- {policy}: {action_value[policy]:.4f}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
