# Ophthalmology RAG Evaluation Case Study

> 本项目是基于 Modular RAG 框架完成的眼科 AI 文献 RAG 评测型 case study。
> 它不是生产级医学问答系统，也不用于临床诊断或临床决策。
> 项目重点是小规模眼科文献语料下的 source-level 评测设计、检索与生成消融实验、
> hardcase 分析、图表 caption 增强探索，以及工程 badcase 复盘。

主要工作包括：

- 领域化 ingestion 与中文医学文本适配
- source-level golden set 设计
- Dense / Sparse / Hybrid 检索消融
- Vanilla LLM vs RAG generation 对比
- 成功案例、hard case 和工程 bad case 分析
- Vision caption / 图表增强 RAG 探索
- Markdown/TXT 派生知识源入库
- metadata-aware source evaluation
（持续进行）

> 本仓库不包含原始 PDF、向量数据库、API key 或上游完整源码，只保留评测设计、实验结果、脚本、patch 和案例分析。

> MCP server、dashboard 和完整 RAG runtime 来自上游 Modular RAG MCP Server；本仓库只展示眼科场景评测产物、patch、脚本和 case study。

## TL;DR

| Dimension | Result |
| --- | --- |
| Corpus | 10 篇眼科 AI 文献，英文论文 + 中文研究汇报 |
| Text chunks | 801 chunks，recursive splitter，补充中文分隔符 |
| Best retrieval baseline | `dense`：source_hit@5 = 1.0000，source_mrr@5 = 0.7917 |
| Best generation setting | `dense_top10`：source_coverage@k = 0.6833 |
| Hybrid finding | 跨语言医学检索里，简单 Hybrid RRF 不一定优于 Dense |
| Caption pilot | 小规模 hard pilot 中，caption-derived source 召回从 0/5 提升到 5/5 |
| Caption limitation | 关键词覆盖有提升，但不等于 answer-level factual correctness |
| LLM ingestion finding | 长论文全量 chunk-level LLM refine 会触发大量 429，应改为 selective refinement |

## Visual Overview

**Architecture Overview**  
![Architecture Overview](assets/figures/medical_literature_rag_architecture_overview.png)

> 该图用于概览本项目评测过的流程与后续扩展点；具体定量结果以本文表格和 `eval/results/` 记录为准。

## Project Navigation

### Core Story

- [Key Findings](docs/showcase/key_findings.md)
- [Evaluation Methodology](docs/showcase/evaluation_methodology.md)
- [Hardcase Examples](docs/showcase/hardcase_examples.md)
- [Engineering Notes & Badcases](docs/showcase/engineering_notes_badcases.md)
- [Caption-Augmented RAG](docs/showcase/caption_augmented_rag.md)
- [Interview Pitch](docs/records/interview_pitch.md)

### Detailed Case Studies

- [Overall Evaluation Summary](docs/records/ophthalmology_rag_eval_summary.md)
- [Success Case](docs/records/success_case.md)
- [Limitation Case](docs/records/limitation_case.md)
- [Original Error Analysis](docs/records/error_analysis.md)
- [Vision Caption Exploration](docs/records/vision_caption_exploration.md)

### Results

- [Retrieval Ablation](eval/results/retrieval_ablation_summary.md)
- [Generation Top-k Ablation](eval/results/generation_topk_ablation_summary.md)
- [Reti-Pioneer Figure Captions](eval/results/reti_pioneer_figure_captions.md)
- [Vision Caption Retrieval Comparison](eval/results/vision_caption_retrieval_summary.md)
- [Vision Caption Generation Comparison](eval/results/vision_caption_generation_summary.md)
- [Vision Caption Hard Retrieval Comparison](eval/results/vision_caption_hard_retrieval_summary.md)
- [Vision Caption Hard Generation Comparison](eval/results/vision_caption_hard_generation_summary.md)

### Patches

- [Source-level Evaluation](patches/source_level_evaluation.patch)
- [Chinese Recursive Splitter](patches/chinese_recursive_splitter.patch)
- [Logging Noise Suppression](patches/logging_noise_suppression.patch)
- [Vision LLM Base URL Fix](patches/vision_llm_base_url.patch)
- [Markdown/TXT Ingestion](patches/text_loader_markdown_ingestion.patch)

## What I Built

### 1. 眼科文献领域适配

我将通用 Modular RAG MCP Server 适配到眼科 AI 文献场景：

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

当前 generation demo 配置：`dense_top10`。

## Key Findings

1. **在当前跨语言 pilot hard set 上，Dense retrieval 表现最好。**  
   许多问题用中文提出，但目标证据来自英文论文。相比 sparse keyword matching，dense retrieval 更适合这类跨语言语义匹配。

2. **RAG 生成质量受 source coverage 限制。**  
   当检索漏掉关键 evidence sources 时，生成答案仍可能很流畅，但内容会变窄、不完整，甚至偏向已召回的旁支材料。

3. **全量 chunk-level LLM ingestion 不适合作为默认方案。**  
   LLM-based refinement 在小文档上可行，但长论文会触发大量 429 fallback。更实际的设计是 selective refinement，配合 cache、retry/backoff 和异步任务。

4. **Caption augmentation 是小规模 pilot extension，不是完整多模态 benchmark。**  
   Caption-derived chunks 在 5 条图表 hard pilot 问题上提升了目标来源召回，但 keyword coverage 只是轻量信号，仍需要 answer-level human review。

更多细节见：[Key Findings](docs/showcase/key_findings.md)、[Caption-Augmented RAG](docs/showcase/caption_augmented_rag.md)、[Hardcase Examples](docs/showcase/hardcase_examples.md)。

## Evaluation Methodology

本项目采用 source-level evaluation 作为主评测方式，避免固定 chunk-id 随 chunk size、overlap、splitter 和 transform 变化而漂移。

核心指标包括：

- `source_hit@k`：是否召回至少一个期望来源
- `source_mrr@k`：期望来源首次出现的位置
- `source_coverage@k`：多来源问题中覆盖了多少期望来源
- `keyword coverage`：仅用于生成结果的轻量信息覆盖观察，不代表事实正确性

对于 caption-derived knowledge，我进一步加入 metadata-aware source matching，例如 `source_type=figure_caption`、`source_paper=Reti-Pioneer`、`modality=vision_caption`。

更多细节见：[Evaluation Methodology](docs/showcase/evaluation_methodology.md)。

## Hardcase & Engineering Notes

本项目主动保留 hardcase / badcase，而不是只展示成功样例：

- 简单 Hybrid RRF 在跨语言医学问题上可能被 sparse 关键词噪声干扰
- 检索缺失关键 evidence sources 时，RAG 生成会变窄或不完整
- Vision caption 能补充图表检索，但可能误读密集医学统计图
- 全量 LLM refine 会触发 API rate limit，更适合改为 selective / cached / async refinement
- Vision wrapper 的 `base_url` 配置问题通过逐层 debug 定位并修复

更多细节见：[Hardcase Examples](docs/showcase/hardcase_examples.md)、[Engineering Notes & Badcases](docs/showcase/engineering_notes_badcases.md)。

## Exploratory Extension: Caption-Augmented RAG

图表增强部分是一个小规模 exploratory extension，而不是完整多模态 RAG benchmark。

我从 Reti-Pioneer 中筛选 8 张大图生成 caption，并将 caption Markdown 作为派生知识源入库。在 5 条图表 hard pilot 问题上，caption-derived source 召回从 `0/5` 提升到 `5/5`；生成关键词覆盖从 `3.40` 提升到 `5.80`。

这个结果只说明 caption 入库对图表相关 evidence retrieval 有正向信号，不代表回答已经达到医学事实正确。后续需要人工 review、chart-specific labels 和更大的 image/table-only golden set。

更多细节见：[Caption-Augmented RAG](docs/showcase/caption_augmented_rag.md)。

## Repository Boundary

本仓库是一个 portfolio case study，不是 production medical diagnosis system。

刻意排除：

- original PDFs
- extracted paper images
- vector databases
- API keys
- full upstream project source

包含：

- evaluation design
- summaries
- case studies
- scripts
- patches
- charts
- engineering notes

## Next Steps

- 扩展 caption hard set，并加入 answer-level human review
- 添加 qwen3-rerank 作为独立的 rerank ablation
- 为 vision-caption generation 添加更严格的 answer-level correctness labels
- 添加小规模 metadata filtering 实验（按 paper type / modality / language）
- 扩展 hard image/table-only golden set，包含 manually verified chart facts