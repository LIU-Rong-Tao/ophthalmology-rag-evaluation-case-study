# 眼科 RAG 评测总结

## 1. 评测目标

本评测用于验证眼科 AI 文献知识库在中文问题场景下的检索与生成增强效果。知识库包含英文眼科 AI 论文和中文研究汇报，目标不是医学诊断，而是辅助论文理解、技术方案总结和项目 demo 设计。

## 2. 语料与配置

- 文档数量：10 篇 PDF
- 切分结果：801 个 chunks
- 切分方式：recursive splitter，并补充了中文和英文分隔符
- chunk size / overlap：1000 / 200
- 当前范围：文本 RAG baseline + 小规模图表 caption 探索
- 图像/表格抽取：Reti-Pioneer 论文中抽取 32 个 image objects，筛选 8 张大图生成 caption

## 3. 检索消融实验

| 模式 | source_hit@5 | source_mrr@5 | 平均查询耗时 ms |
| --- | --- | --- | --- |
| dense | 1.0000 | 0.7917 | 371.93 |
| hybrid | 0.9167 | 0.7667 | 703.43 |
| sparse | 0.8333 | 0.6944 | 223.81 |

在当前 hard test set 上，dense retrieval 表现最好。原因是很多问题是中文改写，但目标答案来源往往是英文论文，语义检索比关键词匹配更稳定。Sparse retrieval 速度最快，但更容易受到中文关键词噪声影响。Hybrid RRF 并不总是更优，因为 sparse retrieval 有时会把中文汇报 chunks 排得过高，进而影响融合排序。

## 4. 生成消融实验

| 配置 | source_hit@k | source_coverage@k | citation_coverage | RAG 平均总耗时 ms |
| --- | --- | --- | --- | --- |
| dense_top5 | 0.8333 | 0.4889 | 0.4556 | 6830.34 |
| dense_top8 | 1.0000 | 0.6417 | 0.6417 | 7861.15 |
| dense_top10 | 1.0000 | 0.6833 | 0.6417 | 6737.67 |
| hybrid_top10 | 1.0000 | 0.5861 | 0.5861 | 7332.00 |

最终选择 `dense_top10` 作为生成展示配置。它的来源覆盖率最高，同时耗时仍在可接受范围内。

## 5. 成功案例

Case 5：如果要设计一个眼科 AI demo，应该如何把英文论文原文和中文研究汇报结合起来？

Vanilla LLM 的回答主要是通用建议，例如提取论文方法、做可视化说明、补充风险提示等。RAG 回答则能结合汇报4、汇报5、汇报6中的项目上下文，进一步给出更具体的工程方案，例如报告幻觉控制、临床可信度验证、跨语言适配和 demo 简化设计。

结论：RAG 将回答从通用方法论提升为基于本项目知识库的领域化方案总结。

## 6. 边界案例

Case 6：眼科多模态模型、报告生成模型和真实临床验证之间是什么关系？

该问题的期望来源包括 Shi 多模态基础模型、Chen OCT 报告生成、OBUSight 和 Reti-Pioneer。实际检索只覆盖了部分来源，source_coverage 为 0.5000，citation_expected_coverage 为 0.2500。RAG 回答虽然比 Vanilla 更具体，但由于关键论文缺失，内容会向中文汇报和部分旁支医学影像材料偏移。

结论：RAG 的生成质量受到检索覆盖率限制。即使检索命中了部分相关材料，如果关键来源缺失，最终回答仍可能出现主题偏移。

## 7. 误差分析

RETFound 相关问题说明 hybrid search 并不是天然最优。Dense retrieval 能把 Zhou 2023 RETFound 论文排在较靠前位置，但 hybrid top5 可能漏掉它。原因是 sparse retrieval 会把包含“基础模型”“泛化”“预训练”等通用关键词的中文汇报 chunks 排得过高，RRF 融合后反而把真正相关的英文论文挤出 top5。

后续改进方向：

- metadata filtering：按论文类型、模态、来源语言过滤
- query decomposition：将复杂问题拆成多个子问题检索
- weighted RRF：降低 sparse 在跨语言语义问题中的干扰
- reranker：对 dense / sparse / hybrid 初筛结果重新排序
- vision/table extraction：已完成 Reti-Pioneer 图表 caption 初探，下一步将 caption 入库并设计图表类 golden set

## 8. 图表 Caption 探索

在文本 RAG baseline 之外，我进一步测试了 PDF 图像抽取与 Vision LLM caption。安装 PyMuPDF 后，Reti-Pioneer 论文可抽取 32 个 image objects；其中筛选出 8 张大尺寸图表，并使用 `qwen-vl-plus` 生成中文 caption。

这一步的价值不是直接把 caption 当作论文事实，而是验证图表增强 RAG 的工程可行性：图表可以被抽取、压缩、送入视觉模型，并形成可检索的文本描述。同时，这也暴露了一个边界：密集医学统计图容易出现语义归因偏差，因此 caption 入库前需要人工复核，后续还应设计 image/table-only golden set 来评估它是否真正改善图表相关问题。


## 9. 可视化结果

### 9.1 检索消融实验

![Retrieval Ablation](../eval/results/figures/retrieval_ablation.svg)

该图对比了 dense、hybrid 和 sparse 三种检索模式的来源命中率、MRR 和平均查询耗时。结果显示，在中文问题检索英文眼科论文的场景下，dense retrieval 的检索质量最高，而 sparse retrieval 虽然最快，但更容易受到关键词噪声影响。Hybrid RRF 并没有稳定超过 dense，说明融合策略仍需要进一步调权或 rerank。

### 9.2 生成消融实验

![Generation Ablation](../eval/results/figures/generation_ablation.svg)

该图对比了不同 top-k 和检索模式下的生成增强效果。dense_top10 在 source_coverage 和 citation_coverage 上表现最好，同时总耗时仍可接受，因此被选为当前 demo 的默认生成配置。
