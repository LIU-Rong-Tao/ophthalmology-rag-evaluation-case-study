# BM25 Budget Controller v1

## 目的

本实验训练一个轻量规则式 controller，根据 query 与 BM25 分数特征选择检索预算。

候选 action 为 bm25_top2、bm25_top5、bm25_top10。目标不是提升 BM25 排序本身，而是在 coverage 与 search cost 之间学习预算调度。

## 背景

在 full-context HotpotQA dev subset 100 条样本上，oracle best policy 已经不再塌缩到单一 action：

| oracle policy | count | share |
| --- | ---: | ---: |
| bm25_top5 | 41 | 0.4100 |
| bm25_top2 | 33 | 0.3300 |
| bm25_top10 | 26 | 0.2600 |

这说明当前 action space 存在真实的 retrieval budget tradeoff。

## Controller 设置

该版本使用简单规则搜索，根据以下特征选择预算：

- query_len
- capitalized_count
- quoted_count
- top1_score
- top1_top2_gap
- top2_top5_gap
- top5_entropy

最优规则参数：

| parameter | value |
| --- | ---: |
| top1_top2_gap threshold | 6.9466 |
| top5_entropy threshold | 1.6059 |

## 结果

| method | avg_reward | avg_coverage | avg_cost |
| --- | ---: | ---: | ---: |
| fixed bm25_top2 | 0.5300 | 0.6300 | 1.0000 |
| fixed bm25_top5 | 0.6700 | 0.8700 | 2.0000 |
| fixed bm25_top10 | 0.6000 | 1.0000 | 4.0000 |
| fixed multi_query_bm25_top5 | 0.4200 | 0.8700 | 4.5000 |
| fixed abstain | -0.0500 | 0.0000 | 0.5000 |
| rule controller v1 | 0.6660 | 0.8650 | 1.9900 |

Controller diagnostic metrics:

| metric | value |
| --- | ---: |
| avg_regret_vs_oracle | 0.1150 |
| oracle_action_accuracy | 0.4300 |

## Action distribution

Predicted action distribution:

| policy | count |
| --- | ---: |
| bm25_top5 | 87 |
| bm25_top2 | 9 |
| bm25_top10 | 4 |

Oracle action distribution:

| policy | count |
| --- | ---: |
| bm25_top5 | 41 |
| bm25_top2 | 33 |
| bm25_top10 | 26 |

## 解释

该结果说明 action space 已经具备可学习的 budget tradeoff，但 v1 规则式 controller 还没有超过最强 fixed policy bm25_top5。

因此，这一步不能被解读为 RL/controller 已经提升了 retrieval performance。更准确的结论是：当前实验已经验证了 adaptive retrieval budget learning 的可行性边界，并暴露出简单 query/BM25 score 特征不足以可靠预测 oracle action。

下一步如果继续 controller 路线，应改进 state features 或模型，例如加入 gold-free retrieval uncertainty、top-k score curve、entity overlap、question type、learned classifier，或者扩大样本规模后训练 contextual bandit。
