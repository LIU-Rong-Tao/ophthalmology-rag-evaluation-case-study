# HotpotQA Lexical Fixed Policy Baseline v0

## 目的

本实验将前一版 oracle simulation 推进到真实 HotpotQA dev subset 上的轻量 lexical retrieval baseline。

当前版本不训练 RL controller，而是先运行 fixed policy ablation，验证不同 search policies 在 evidence coverage、search cost 和 reward 上是否具有可区分性。

## 数据

- 数据集：HotpotQA dev distractor
- 样本数：100
- Policy 数：5
- 输出记录：500 条 policy-case 结果
- 检索空间：每条 HotpotQA 样本自带的 `context_titles`

## Policy 设置

- `lexical_top10`：基于 question 与 context title 的词面重叠打分，取 top10。
- `lexical_top50_rerank10`：先取 top50，再用同一 lexical score 近似 rerank，保留 top10。
- `multi_query_lexical_top10`：使用原始 question 和简单扩展 query 检索。
- `multi_query_rerank10`：multi-query + top50->top10 的轻量近似。
- `abstain`：不检索。

## Reward

Reward: `reward = evidence_coverage - 0.1 * search_cost`

## 结果

| policy | avg_coverage | avg_retrieved | avg_cost | avg_reward |
| --- | ---: | ---: | ---: | ---: |
| lexical_top10 | 0.7000 | 4.91 | 1.00 | 0.6000 |
| lexical_top50_rerank10 | 0.7000 | 4.91 | 3.00 | 0.4000 |
| multi_query_lexical_top10 | 0.7000 | 4.91 | 4.00 | 0.3000 |
| multi_query_rerank10 | 0.7000 | 4.91 | 5.00 | 0.2000 |
| abstain | 0.0000 | 0.00 | 0.50 | -0.0500 |

## 解读

该实验说明 HotpotQA dev subset 已经可以进入 fixed search policy evaluation 闭环。

在当前 lexical title retrieval v0 中，贵策略没有带来额外 evidence coverage，因此最高 reward 来自成本最低的 `lexical_top10`。这说明当前 action space 的区分度还不够，不能直接进入 RL controller 训练。

下一步需要引入更强的 retrieval 或 query expansion，使不同 search actions 在 coverage / cost 上产生真实差异。可选方向包括 BM25 over HotpotQA context sentences、dense retrieval、multi-query expansion，以及 difficulty / failure case 分析。
