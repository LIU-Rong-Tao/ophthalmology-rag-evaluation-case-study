# HotpotQA Fixed Policy Reward Simulation v0

## 目的

本实验用于验证公开 HotpotQA 数据可以接入 Agentic Evidence RAG 的 search-policy evaluation 闭环。

当前版本是 reward simulation，不是真实检索实验。脚本使用 HotpotQA 的 `supporting_facts` 构造 gold evidence titles，并通过模拟 retrieval 行为测试不同 fixed search policies 在 evidence coverage、search cost 和 reward 上的区分度。

## 数据

- 数据集：HotpotQA dev distractor
- 样本数：100
- Policy 数：5
- 输出记录：500 条 policy-case 结果

## Reward

Reward: `reward = evidence_coverage - 0.1 * search_cost`

## 结果

| policy | avg_coverage | avg_cost | avg_reward |
| --- | ---: | ---: | ---: |
| dense_top10 | 0.5000 | 1.00 | 0.4000 |
| dense50_rerank10 | 1.0000 | 3.00 | 0.7000 |
| multi_query_dense_top10 | 0.5000 | 4.00 | 0.1000 |
| multi_query_rerank10 | 1.0000 | 5.00 | 0.5000 |
| abstain | 0.0000 | 0.50 | -0.0500 |

## 解读

该结果说明 fixed policy / cost / reward 的最小闭环已经跑通。当前最优 reward 来自 `dense50_rerank10`，因为它在模拟设定中达到完整 evidence coverage，同时成本低于 `multi_query_rerank10`。

该实验不代表真实 retrieval 性能。下一步需要将模拟 retrieval 替换为基于 HotpotQA context 的 lexical/BM25 retrieval baseline，再进入 RL Search Policy Controller 训练。
