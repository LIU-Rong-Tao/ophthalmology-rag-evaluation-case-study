# Hardcase Examples

本文档收集项目中的代表性 hard cases。

## 1. Hybrid Search 并不总是优于 Dense

RETFound 相关查询暴露了简单 Hybrid RRF 的一个 failure mode。

Dense retrieval 可以将 Zhou 2023 RETFound 论文排到 top 位置，但 Hybrid top-5 可能会漏掉它。Sparse retrieval 将包含“基础模型”、“泛化”、“预训练”等通用词的中文汇报 chunks 排得过高。经过 RRF fusion 后，这些 noisy sparse 结果会把正确的英文论文挤下去。

> **PLACEHOLDER: RETFound Ranking Badcase**  
![Hybrid Retrieval Badcase](../../assets/figures/hybrid_retrieval_badcase_analysis_dashboard.png)

## 2. Source Coverage 限制 RAG Generation

问题：

> 眼科多模态模型、报告生成模型和真实临床验证之间是什么关系？

这个问题需要多个 evidence sources：

- 眼科多模态 foundation models
- OCT 报告生成
- 眼科超声诊断
- 真实世界多疾病验证

当 retrieval 只覆盖了部分 evidence chain 时，RAG 答案可能看起来很完整，但它并不能完整解释 intended relationship。

> **PLACEHOLDER: Missing Evidence Chain**  
![Source Coverage Limitation](../../assets/figures/source_coverage_limitation_in_text_only_retrieval.png)

## 3. Vision Caption 可能误读密集医学图表

Vision caption 可以帮助检索图表信息，但 captions 不是自动可靠的 factual labels。

一个密集的统计图可能被过度解读为特定的疾病机制或基因表达结论。因此，generated captions 应被视为 model-assisted annotations，在使用前需要人工复核。

> **PLACEHOLDER: Caption Misread Example**  
![Hard Generation Keyword Coverage](../../assets/figures/hard_generation_keyword_coverage_analysis.png)

## 4. 全量 LLM Refinement 触发限流

全量 chunk-level LLM refinement 在小文档上工作正常，但因 API rate limit 无法扩展到长论文。

这改变了设计方向：从“LLM-refine every chunk”转向：

- selective refinement
- async jobs
- caching
- retry/backoff
- rule-based fallback