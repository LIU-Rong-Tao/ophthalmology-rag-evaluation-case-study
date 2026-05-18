# Vision Caption Hard Generation 对比结果

## 1. 实验目标

在 hard retrieval set 已经证明 caption-augmented collection 能稳定召回 caption source 后，本实验进一步比较 text-only RAG 与 caption-augmented RAG 在图表类 hard 问题上的生成回答差异。

hard set 的问题更关注图表表达方式，例如 calibration curve 坐标轴、normalized test benefit curve、resource-limited / high-resource 图例设置，以及 caption 自身误读风险。

## 2. 实验设置

| setting | collection | retrieval |
| --- | --- | --- |
| text-only hard | `ophthalmology_base` | dense top10 |
| caption-augmented hard | `ophthalmology_caption_augmented` | dense top10 |

LLM ingestion refine、metadata enrichment 和自动 vision caption 均关闭，确保主要变量是是否加入 Reti-Pioneer 图表 caption Markdown。

## 3. Retrieval 层结果

| setting | caption_source_hit@10 |
| --- | ---: |
| text-only hard | 0 / 5 = 0.0000 |
| caption-augmented hard | 5 / 5 = 1.0000 |

## 4. Generation 层关键词覆盖

关键词覆盖统计关注图表相关术语，包括 calibration curve、predicted probability、observed proportion、Brier、normalized test benefit、threshold probability、resource-limited / high-resource setting、AUC、clinical utility，以及 caption 可靠性相关表述。

| setting | avg_keyword_hits_per_answer |
| --- | ---: |
| text-only hard | 3.40 |
| caption-augmented hard | 5.80 |

## 5. 代表性观察

第 5 个 hard case 询问 caption 中哪些内容提示不能把视觉模型生成的 caption 直接当成论文事实。text-only RAG 没有覆盖相关关键词，而 caption-augmented RAG 命中了：

- `不能直接视为论文事实`
- `人工复核`
- `语义归因偏差`

这说明 caption 文档不仅能补充图表信息，也能把 caption 自身的质量边界纳入检索和生成。

## 6. 结论

在更依赖图表表达的 hard set 上，caption-augmented RAG 不仅显著提升 caption source 的召回，也让生成回答覆盖更多图表相关概念。

但这个结果仍应谨慎解释：关键词覆盖提升不等于医学事实完全正确。下一步如果继续深化，需要人工标注 answer-level correctness，检查回答是否正确使用图表信息，而不是只统计术语命中。
