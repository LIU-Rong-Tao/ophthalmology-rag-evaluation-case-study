# Evaluation Reranker 接入冒烟测试

## 测试目的

本测试用于确认 `scripts/evaluate.py` 已经能够初始化 `CoreReranker`，并将 reranker 传入 `EvalRunner`。

这意味着 rerank 不再只是在 query 或单独 ablation 脚本中验证，而是可以进入标准 evaluation CLI，作为一种正式可评测的 retrieval policy。

## 测试设置

- 测试集：`tests/fixtures/ophthalmology_golden_test_set.json`
- Collection：`ophthalmology_base`
- 检索模式：`dense`
- CLI top-k：`10`
- 实际候选池：`dense20 -> rerank10`
- Reranker：`llm`
- Query 数量：`10`

说明：当前 `EvalRunner` 在 reranker 启用时会先取 `top_k * 2` 个候选，因此本次设置对应 `dense20 -> rerank10`，不是正式 rerank ablation 中的 `dense50 -> rerank10`。

## 测试结果

| metric | value |
| --- | ---: |
| total_time_ms | 346061 |
| avg_time_per_query_s | 34.61 |
| source_hit_rate | 0.6000 |
| source_mrr | 0.4450 |

## 结果解读

本次结果证明 evaluation pipeline 的 reranker 接线已经跑通：`evaluate.py` 可以初始化 `CoreReranker`，并通过 `EvalRunner` 在 retrieval 后执行 rerank。

但这不是正式的 clean rerank ablation 结果。原因是本次候选池为 `dense20 -> rerank10`，而之前主要 rerank 消融关注的是 `dense50 -> rerank10`。

本次测试也再次说明 LLM rerank 的延迟成本很高：10 条 query 总耗时约 346.1 秒，平均每条约 34.6 秒。因此后续 Agentic Evidence RAG / RL Search Policy Controller 中，rerank 更适合作为高成本可选 search action，而不是默认在线检索策略。
