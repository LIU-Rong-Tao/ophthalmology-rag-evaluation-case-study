# Ophthalmology RAG Evaluation Case Study

> 本项目是我围绕眼科 AI 文献场景搭建的垂类 RAG 评测型 case study。
> 项目将医学文献摄取、领域化切分、Dense/BM25/Hybrid/Rerank 检索、RAG 生成、
> source-level evaluation、hardcase 分析和图表 caption 增强串成一个可复现的 RAG 评测闭环。
> 它不是生产级医学问答系统，也不用于临床诊断或临床决策。

主要工作包括：

- 领域化 ingestion 与中文医学文本适配
- source-level golden set 设计
- Dense / Sparse / Hybrid / Rerank 检索消融
- Vanilla LLM vs RAG generation 对比
- hardcase / badcase 与工程复盘
- Vision caption / 图表增强 RAG 探索
- Markdown/TXT 派生知识源入库
- metadata-aware source evaluation

> 本仓库不包含原始 PDF、向量数据库、API key 或完整上游 runtime，只保留评测设计、实验结果、脚本、patch 和案例分析。
> 说明：本仓库是面试展示用的 portfolio 版本，只保留眼科场景评测产物、patch、脚本、图表和 case study。
> 完整 MCP server、dashboard 和基础 RAG runtime 已在本地项目中运行验证，但不在这个 portfolio 仓库中重复上传。

## TL;DR

| Dimension | Result |
| --- | --- |
| Corpus | 10 篇眼科 AI 文献，英文论文 + 中文研究汇报 |
| Text chunks | 801 chunks，recursive splitter，补充中文分隔符 |
| Best retrieval baseline | `dense`：source_hit@5 = 1.0000，source_mrr@5 = 0.7917 |
| Best generation setting | `dense_top10`：source_coverage@k = 0.6833 |
| Hybrid finding | 跨语言医学检索里，简单 Hybrid RRF 不一定优于 Dense |
| Rerank finding | `dense50_llm_top10` 提升 source_mrr@10，但平均延迟约 36.26s，更适合作为离线 evidence utility rerank |
| Caption pilot | 小规模 hard pilot 中，caption-derived source 召回从 0/5 提升到 5/5 |
| Caption limitation | 关键词覆盖有提升，但不等于 answer-level factual correctness |
| LLM ingestion finding | 长论文全量 chunk-level LLM refine 会触发大量 429，应改为 selective refinement |

## Visual Overview

**Architecture Overview**
![Architecture Overview](assets/figures/medical_literature_rag_architecture_overview.png)

> 该图用于概览本项目评测过的流程与后续扩展点；具体定量结果以本文表格和 `eval/results/` 记录为准。

## Project Navigation

- [Key Findings](docs/showcase/key_findings.md)
- [Evaluation Methodology](docs/showcase/evaluation_methodology.md)
- [Hardcase & Badcase Analysis](docs/showcase/hardcase_examples.md)
- [Caption-Augmented RAG Pilot](docs/showcase/caption_augmented_rag.md)
- [Engineering Notes](docs/showcase/engineering_notes_badcases.md)
- [Rerank Ablation](eval/results/rerank_ablation_summary.md)
- [Evaluation Reranker 接入测试](eval/results/evaluation_reranker_smoke_test.md)
- [Evidence Alignment Metrics v0 Appendix](eval/results/medrag_align_v0_data_pipeline.md)

完整结果文件、评测集和 patch 见：[Documentation Index](docs/README.md)。

## What I Built

### 1. 眼科文献领域适配

我围绕眼科 AI 文献场景，搭建并扩展了一套垂类 RAG 评测工作流，把文档摄取、领域化切分、Dense/BM25/Hybrid 检索、RAG 生成、source-level evaluation、hardcase 分析和图表 caption 增强串成了一个可展示的实验闭环：

- 10 篇 PDF 文档
- 英文眼科 AI 论文 + 中文研究汇报
- 801 个 text chunks
- recursive splitter with Chinese punctuation separators
- source-level evaluation labels，不受 chunking 变化影响

### 2. 检索与生成评估

围绕真实项目问题构建了 hard retrieval 和 generation test sets。

检索消融：

![Retrieval Ablation](eval/results/figures/retrieval_ablation.svg)

| mode | source_hit@5 | source_mrr@5 | avg_query_ms |
| --- | ---: | ---: | ---: |
| dense | 1.0000 | 0.7917 | 371.93 |
| hybrid | 0.9167 | 0.7667 | 703.43 |
| sparse | 0.8333 | 0.6944 | 223.81 |

生成消融：

![Generation Ablation](eval/results/figures/generation_ablation.svg)

| setting | source_hit@k | source_coverage@k | citation_coverage | rag_total_avg_ms |
| --- | ---: | ---: | ---: | ---: |
| dense_top5 | 0.8333 | 0.4889 | 0.4556 | 6830.34 |
| dense_top8 | 1.0000 | 0.6417 | 0.6417 | 7861.15 |
| dense_top10 | 1.0000 | 0.6833 | 0.6417 | 6737.67 |
| hybrid_top10 | 1.0000 | 0.5861 | 0.5861 | 7332.00 |

Current evaluated generation setting: `dense_top10`.

## Key Findings

1. **在当前跨语言 pilot hard set 上，Dense retrieval 表现最好。**
   许多问题用中文提出，但目标证据来自英文论文。相比 sparse keyword matching，dense retrieval 更适合这类跨语言语义匹配。

2. **RAG 生成质量受 source coverage 限制。**
   当检索漏掉关键 evidence sources 时，生成答案仍可能很流畅，但内容会变窄、不完整，甚至偏向已召回的旁支材料。

3. **LLM rerank 能改善排序，但延迟成本较高。**
   `dense50_llm_top10` 将 source_mrr@10 从 `0.7917` 提升到 `0.9583`，但平均查询耗时约 `36.26s`，更适合作为离线 evidence utility rerank 实验。

4. **全量 chunk-level LLM ingestion 不适合作为默认方案。**
   LLM-based refinement 在小文档上可行，但长论文会触发大量 429 fallback。更实际的设计是 selective refinement，配合 cache、retry/backoff 和异步任务。

5. **Caption augmentation 是小规模 pilot extension，不是完整多模态 benchmark。**
   Caption-derived chunks 在 5 条图表 hard pilot 问题上提升了目标来源召回，但 keyword coverage 只是轻量信号，仍需要 answer-level human review。

## Evaluation Methodology

本项目采用 source-level evaluation 作为主评测方式，避免固定 chunk-id 随 chunk size、overlap、splitter 和 transform 变化而漂移。

核心指标包括 `source_hit@k`、`source_mrr@k`、`source_coverage@k` 和轻量 `keyword coverage`。对于 caption-derived knowledge，评测中进一步加入 metadata-aware source matching。

更多细节见：[Evaluation Methodology](docs/showcase/evaluation_methodology.md)。

## Hardcase & Engineering Notes

本项目主动保留 hardcase / badcase，而不是只展示成功样例，包括 Hybrid RRF 噪声、检索缺失、LLM rerank timeout、Vision caption 误读和 LLM refine rate limit 等问题。

更多细节见：[Hardcase Examples](docs/showcase/hardcase_examples.md)、[Engineering Notes & Badcases](docs/showcase/engineering_notes_badcases.md)、[Rerank Ablation](eval/results/rerank_ablation_summary.md)。

## Exploratory Extension: Caption-Augmented RAG

图表增强部分是一个小规模 exploratory extension，而不是完整多模态 RAG benchmark。

我从 Reti-Pioneer 中筛选 8 张大图生成 caption，并将 caption Markdown 作为派生知识源入库。在 5 条图表 hard pilot 问题上，caption-derived source 召回从 `0/5` 提升到 `5/5`；生成关键词覆盖从 `3.40` 提升到 `5.80`。

这个结果只说明 caption 入库对图表相关 evidence retrieval 有正向信号，不代表回答已经达到医学事实正确。后续需要人工 review、chart-specific labels 和更大的 image/table-only golden set。

更多细节见：[Caption-Augmented RAG](docs/showcase/caption_augmented_rag.md)。

## Appendix: Evidence Alignment Metrics v0

该部分记录 evidence grounding / citation / abstain 指标的早期探索，用于后续 Agentic Evidence RAG 的 reward 与 evaluation 设计参考。

当前已完成 Golden v2 schema、PubMedQA evidence-grounded SFT seed 转换、30 对弱监督 preference pair seed，以及 citation / unsupported claim / abstain 等 alignment metrics v0。

该部分不代表已经完成医学模型训练，也不代表医生验证的 claim-level evidence annotation。后续它将作为 reward / evaluation appendix，而不是单独的 MedRAG-Align 训练主线。

更多细节见：[Evidence Alignment Metrics v0](eval/results/medrag_align_v0_data_pipeline.md)。

## Repository Boundary

本仓库是一个 portfolio case study，不是 production medical diagnosis system。

刻意排除：

- original PDFs
- extracted paper images
- vector databases
- API keys
- full upstream runtime

包含：

- evaluation design
- summaries
- case studies
- scripts
- patches
- charts
- engineering notes

## Next Steps

后续工作会沿着 Agentic Evidence RAG 方向推进：先把 rerank、multi-query 和 abstain 抽象成可选择的 search policies，再在公开 multi-hop QA benchmark 上训练轻量级 RL Search Policy Controller。

主实验将关注 reward、evidence coverage、search cost 和 action distribution 等训练曲线；现有眼科 hard cases 将作为医学证据检索的 domain transfer showcase，用来观察公开 QA 上学到的 search-cost tradeoff 是否能迁移到垂直医学场景。

PubMedQA / BioASQ 暂时只作为 biomedical sanity check，不作为第一阶段主训练集。
