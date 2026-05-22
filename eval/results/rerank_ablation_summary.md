# Rerank Ablation 结果总结

## 实验目的

本实验检查 reranker 是否已经接入眼科 RAG 的 query / evaluation pipeline，并评估 LLM rerank 对 hard retrieval set 的排序改善效果。

本阶段不引入新训练，仅比较不同 retrieval + rerank 设置下的 source-level retrieval 指标。

## 实验设置

测试集：`eval/ophthalmology_retrieval_hard.json`

Collection：`ophthalmology_base`

Reranker：`llm`

LLM：`qwen3.5-plus`

最终返回：`top10`

## 结果

| setting | source_hit@10 | source_mrr@10 | source_coverage@10 | avg_query_ms | fallback |
| --- | ---: | ---: | ---: | ---: | ---: |
| dense_top10_none | 1.0000 | 0.7917 | 0.9139 | 432.52 | 0 |
| dense50_llm_top10 | 1.0000 | 0.9583 | 0.9306 | 36257.99 | 0 |
| hybrid30_llm_top10 | 1.0000 | 0.9167 | 0.9306 | 47082.86 | 0 |
| hybrid50_llm_top10_partial | 1.0000 | 0.9583 | 0.8889 | 48795.97 | 2 |

## 主要发现

1. reranker 已经接入 query / evaluation pipeline。  
   代码中 `scripts/query.py`、`src/core/query_engine/reranker.py` 和 `src/observability/evaluation/eval_runner.py` 都已包含 rerank 调用路径。

2. `dense50_llm_top10` 是本轮最干净的提升结果。  
   相比 `dense_top10_none`，source MRR 从 `0.7917` 提升到 `0.9583`，source coverage 从 `0.9139` 提升到 `0.9306`，且没有 fallback。

3. LLM rerank 的主要代价是延迟。  
   `dense50_llm_top10` 平均查询耗时约 `36.26s`，明显高于无 rerank baseline 的 `0.43s`，不适合直接作为低延迟在线默认配置。

4. hybrid rerank 对候选规模更敏感。  
   `hybrid50_llm_top10` 出现 `2/12` timeout fallback，说明 hybrid 候选池扩大到 50 时稳定性不足；缩小到 `hybrid30_llm_top10` 后 fallback 降为 0，但平均耗时仍约 `47.08s`。

## 结论

`dense_top10_none` → `dense50_llm_top10`：MRR 从 `0.7917` 提升到 `0.9583`，source coverage 从 `0.9139` 提升到 `0.9306`，且无 fallback。

但 LLM rerank 带来明显延迟开销，`dense50_llm_top10` 平均查询耗时约 `36.26s`，因此当前更适合作为 evidence utility rerank 的离线评测结果，而不是低延迟线上默认配置。

`hybrid50_llm_top10` 有 `2/12` timeout fallback，不作为 clean 主结果；`hybrid30_llm_top10` 无 fallback，但 MRR 为 `0.9167`，低于 dense50 rerank。

## 后续计划

1. 引入本地 cross-encoder reranker，降低延迟并避免 LLM timeout。
2. 尝试 DashScope / Qwen 专用 rerank API，比较成本与稳定性。
3. 在 generation ablation 中测试 rerank 后 top10 对 citation coverage 和 unsupported claim 控制的影响。