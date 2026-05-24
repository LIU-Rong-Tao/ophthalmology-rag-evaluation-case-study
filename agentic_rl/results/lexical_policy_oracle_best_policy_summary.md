# Policy Oracle Best-Action Analysis v0

## 目的

本分析基于 fixed policy reward table，统计每个 HotpotQA case 的 oracle best action。

它用于判断当前 action space 是否有足够多样性，避免后续 controller 训练退化成永远选择同一个 search policy。

## 输入

- Reward table: agentic_rl/results/hotpot_lexical_policy_ablation_dev100.csv
- Case 数量: 100

## Oracle best policy 分布

| policy | count | share |
| --- | ---: | ---: |
| lexical_top10 | 93 | 0.9300 |
| abstain | 7 | 0.0700 |

## Case type 分布

| case_type | count | share |
| --- | ---: | ---: |
| easy_cheap_sufficient | 47 | 0.4700 |
| other | 46 | 0.4600 |
| abstain_best | 7 | 0.0700 |

## 解释

如果 oracle best policy 高度集中在单一 action，说明当前 reward simulation 或 action space 还不够丰富。

这种情况下，下一步不应该急着训练更复杂的 controller，而应该引入真实 lexical/BM25/dense retrieval reward 或构造更细的 difficulty 分组。

详细 per-case 输出见: agentic_rl/results/lexical_policy_oracle_best_policy_dev100.csv
