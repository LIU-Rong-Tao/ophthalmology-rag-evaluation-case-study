# Vision Caption Retrieval 对比结果

## 1. 实验目标

本实验用于验证：将 Reti-Pioneer 图表 caption 作为派生文本资料入库后，是否能提升图表相关问题的检索能力。

对比对象：

| collection | 内容 |
| --- | --- |
| `ophthalmology_base` | 原 10 篇 PDF 文本知识库 |
| `ophthalmology_caption_augmented` | 原 10 篇 PDF 文本 + Reti-Pioneer 图表 caption Markdown |

本实验关闭了 chunk-level LLM refine、metadata enrichment 和自动 vision caption，只保留稳定的 rule-based ingestion + embedding。这样可以确保变量只来自“是否加入 caption 文本”。

## 2. Golden Set

测试集：`eval/ophthalmology_vision_caption_golden.json`

共 8 个问题，主要考察：

- calibration curves
- Brier score
- normalized test benefit curves
- threshold probability
- resource-limited / high-resource setting
- 多疾病检测任务的外部验证
- caption 可能带来的语义误读风险

这些问题故意设计为图表相关问题，text-only RAG 可能只能召回论文正文或一般任务描述，而 caption-augmented RAG 应该能召回图表 caption chunk。

## 3. 核心结果

| collection | caption_source_hit@10 |
| --- | ---: |
| text-only baseline | 0 / 8 = 0.0000 |
| caption-augmented | 8 / 8 = 1.0000 |

结果说明：加入 caption Markdown 后，8 个图表相关问题全部能在 top10 中召回 Reti-Pioneer caption source；而 text-only baseline 没有召回 caption source。

## 4. 评测过程中的注意点

原始 source-level evaluator 不能直接使用 `expected_sources: ["Reti-Pioneer figure captions"]`，因为真实 metadata 中的来源是 caption Markdown 的 `source_path`。因此初始 `source_hit_rate` 显示为 0，但并不代表 caption 没有被召回。

后续我改用 caption 文档真实 `source_path` 对应的 source prefix 来统计 `caption_source_hit@10`。这个指标更适合判断 caption source 是否进入检索结果。

## 5. 结论

Vision caption 作为派生文本入库后，能够显著提升图表相关问题对 caption source 的召回。

但这还不是最终证明“回答质量一定提升”。下一步还需要做 generation 对比，观察回答是否更准确地使用 calibration curve、Brier score、normalized test benefit 等图表信息，同时避免把 caption 中可能存在的语义误读直接当作论文事实。
