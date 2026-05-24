# Agentic Evidence RAG 实验模块

本目录用于承接后续 RL Search Policy Controller 实验。

当前项目已经完成眼科 RAG 的 source-level evaluation、retrieval/generation ablation、rerank ablation 和 reranker 接入 evaluation pipeline。下一步不直接训练医学大模型，而是先把 RAG 检索过程抽象成一个可控的 search-policy environment。

## 第一阶段目标

第一阶段先使用 HotpotQA subset 构建公开 multi-hop QA search environment，并运行 fixed policy ablation。目是验证不同 search policies 在 evidence coverage、search cost 和 latency 上是否有稳定差异。

计划比较的 fixed policies 包括：

- `dense_top10`
- `dense50_rerank10`
- `multi_query_dense_top10`
- `multi_query_rerank10`
- `abstain`

第一版 reward 只使用：

```text
reward = evidence_coverage - search_cost