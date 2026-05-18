# Vision Caption Generation 对比结果

## 1. 实验目标

本实验用于验证：在图表 caption 已经能被检索召回的前提下，caption-augmented RAG 是否能进一步改善图表相关问题的生成回答。

对比对象：

| setting | collection | 内容 |
| --- | --- | --- |
| text-only | `ophthalmology_base` | 原 10 篇 PDF 文本 |
| caption-augmented | `ophthalmology_caption_augmented` | 原 10 篇 PDF 文本 + Reti-Pioneer 图表 caption Markdown |

实验设置：

- retrieval mode：dense
- top-k：10
- answer mode：both
- LLM ingestion refine：关闭
- metadata enrichment：关闭
- 自动 vision caption：关闭

## 2. Retrieval 层结果

| setting | caption_source_hit@10 |
| --- | ---: |
| text-only | 0 / 8 = 0.0000 |
| caption-augmented | 8 / 8 = 1.0000 |

caption-augmented collection 可以稳定召回 Reti-Pioneer caption source，而 text-only baseline 不会召回 caption 文档。

## 3. Generation 层关键词覆盖

我用图表相关关键词对 RAG 回答进行轻量统计，包括 calibration、Brier score、normalized test benefit、threshold probability、resource-limited / high-resource setting，以及多个疾病任务名称。

| setting | avg_keyword_hits_per_answer |
| --- | ---: |
| text-only | 9.38 |
| caption-augmented | 10.12 |

结果显示，caption-augmented 的生成回答在关键词覆盖上有小幅提升。

## 4. 结果解释

生成层面的提升没有 retrieval 层那么明显。原因是 text-only PDF 解析结果中可能已经包含部分图注、图表附近文字或论文正文里的指标描述，因此 text-only RAG 也能回答一部分图表相关问题。

因此，这组实验的结论不是“caption 让所有回答大幅变好”，而是：

- caption 入库显著提高了图表派生文本的可召回性；
- 生成回答的关键词覆盖略有提升；
- 如果要进一步证明生成质量提升，需要设计更严格的 image/table-only 问题，并人工评估回答是否正确使用图表信息；
- caption 本身仍可能包含视觉模型误读，因此不能直接当作论文事实来源。

## 5. 下一步

下一步应该把 golden set 进一步收紧，增加必须依赖图表细节的问题，例如特定图表面板、曲线类型、图例设置和图表中的比较维度。同时，可以为 caption chunk 增加更稳定的 metadata 字段，让 evaluator 直接统计 `source_type=figure_caption`，避免依赖路径 hash。
