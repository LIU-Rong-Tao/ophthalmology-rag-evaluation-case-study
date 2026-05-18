# Vision Caption Hard Retrieval 对比结果

## 1. 实验目标

第一版 vision caption golden set 证明 caption-augmented collection 可以召回 Reti-Pioneer caption source。但其中部分问题仍可能被 text-only PDF 正文或图注附近文本回答。

因此，我进一步构造了 5 条 hard vision caption 问题，重点考察图表表达方式，而不是论文总体任务。

hard 的定义是：

- 更依赖图表结构、曲线、图例和 caption 信息
- 不要求精确 OCR 小数字
- 不问论文总体任务
- 包含 caption 自身误读风险的问题

## 2. Hard Set 覆盖点

| case | 重点 |
| --- | --- |
| vision_hard_001 | calibration curve 的横轴、纵轴和校准含义 |
| vision_hard_002 | normalized test benefit 与 threshold probability |
| vision_hard_003 | resource-limited / high-resource settings 的图例或实验设置对比 |
| vision_hard_004 | 分类性能、校准和临床实用性的综合评估 |
| vision_hard_005 | caption 不能直接当论文事实的误读风险 |

## 3. 核心结果

| setting | caption_source_hit@10 |
| --- | ---: |
| text-only hard | 0 / 5 = 0.0000 |
| caption-augmented hard | 5 / 5 = 1.0000 |

## 4. 结论

在更依赖图表表达的 hard set 上，caption-augmented collection 仍然能稳定召回 caption source，而 text-only baseline 不能召回 caption 文档。

这说明把图表 caption 作为派生文本资料入库，确实能增强 RAG 对图表类问题的检索能力。

需要注意的是，这个结果证明的是 retrieval 层的增强。生成层是否更准确，还需要结合人工检查和更严格的图表事实评估。
