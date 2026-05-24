# Policy Oracle Best-Action Analysis v0

## 目的

本分析基于 fixed policy reward table，统计每个 HotpotQA case 的 oracle best action。

它用于判断当前 action space 是否有足够多样性，避免后续 controller 训练退化成永远选择同一个 search policy。

## 输入

- Reward table: agentic_rl/results/hotpot_fixed_policy_ablation_dev100.csv
- Case 数量: 100

## Oracle best policy 分布

| policy | count | share |
| --- | ---: | ---: |
| dense50_rerank10 | 100 | 1.0000 |

## Case type 分布

| case_type | count | share |
| --- | ---: | ---: |
| rerank_preferred | 100 | 1.0000 |

## 解释

如果 oracle best policy 高度集中在单一 action，说明当前 reward simulation 或 action space 还不够丰富。

这种情况下，下一步不应该急着训练更复杂的 controller，而应该引入真实 lexical/BM25/dense retrieval reward 或构造更细的 difficulty 分组。

详细 per-case 输出见: agentic_rl/results/policy_oracle_best_policy_dev100.csv
