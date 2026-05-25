# Generation Ablation Summary

## 目的

本文件记录 README 中引用的 generation-side RAG ablation 结果。

该实验用于比较不同 retrieval depth 和 retrieval mode 对 RAG 生成阶段 source coverage 与 citation coverage 的影响。

## 结果

| setting | source_hit@k | source_coverage@k | citation_coverage | rag_total_avg_ms |
| --- | ---: | ---: | ---: | ---: |
| dense_top5 | 0.8333 | 0.4889 | 0.4556 | 6830.34 |
| dense_top8 | 1.0000 | 0.6417 | 0.6417 | 7861.15 |
| dense_top10 | 1.0000 | 0.6833 | 0.6417 | 6737.67 |
| hybrid_top10 | 1.0000 | 0.5861 | 0.5861 | 7332.00 |

## 结果解读

当前评测中表现最好的生成设置是 dense_top10，source_coverage@k = 0.6833。

该结果说明，RAG 生成质量不仅取决于是否至少召回一个相关 source，也取决于是否覆盖了足够完整的 evidence set。即使 source_hit@k 达到 1.0000，source_coverage@k 仍然低于 0.70，说明答案生成仍可能漏用关键证据。

后续应继续加强 evidence-aware generation、citation coverage 和 unsupported claim analysis。
