# 眼科 RAG 评测与误差分析案例

本项目是基于 Modular RAG MCP Server 框架完成的一次眼科 AI 文献场景扩展。原框架提供了文档摄取、Hybrid Search、MCP Server、Dashboard、Evaluation 等模块化能力；我的工作重点不是重复介绍原框架，而是围绕眼科文献知识库做领域化适配、评测集设计、检索/生成消融实验和 bad case 分析。

> 说明：本仓库不包含原始 PDF、向量数据库、API key 和上游完整源码，只记录我的评测设计、实验结果、脚本和改造思路。

## 项目产出导航

- 总结文档：`docs/ophthalmology_rag_eval_summary.md`
- 成功案例：`docs/success_case.md`
- 边界案例：`docs/limitation_case.md`
- 错误分析与工程问题：`docs/error_analysis.md`
- Reti-Pioneer 图表 caption 结果：`eval/results/reti_pioneer_figure_captions.md`
- Vision caption 检索对比：`eval/results/vision_caption_retrieval_summary.md`
- Vision caption hard 检索对比：`eval/results/vision_caption_hard_retrieval_summary.md`
- Vision caption 生成对比：`eval/results/vision_caption_generation_summary.md`
- Markdown/TXT ingestion patch：`patches/text_loader_markdown_ingestion.patch`
- 检索与生成消融图：`eval/results/figures/`
- 关键改造 patch：`patches/`

## 我做了什么

- 整理 10 篇眼科 AI 论文和中文研究汇报，构建小型知识库
- 针对中英文混排 PDF，调整 recursive splitter 的中文分隔规则
- 修复 ingest/query 阶段第三方库日志刷屏问题
- 设计 source-level golden set，避免评测完全依赖固定 chunk ID
- 对比 dense、sparse、hybrid RRF 三种检索方式
- 对比 Vanilla LLM 和 RAG-enhanced generation
- 导出成功案例和 bad case，分析 RAG 的能力边界
- 探索 PDF 图表抽取与 Vision LLM caption，为后续图表增强 RAG 做准备
- 扩展 ingestion 支持 Markdown/TXT，让图表 caption 作为派生知识源直接入库
- 对比 text-only RAG 与 caption-augmented RAG 的图表问题检索和生成表现
- 使用 AI coding 辅助代码阅读、脚本实现、bug 定位和评测自动化

## 原框架能力

原始 Modular RAG MCP Server 提供了比较完整的 RAG 工程骨架，包括：

- Ingestion Pipeline：PDF 解析、chunking、embedding、vector upsert
- Hybrid Search：Dense + Sparse + RRF fusion
- MCP Server：通过 MCP 协议暴露知识库查询工具
- Dashboard：可视化管理、摄取追踪、查询追踪和评估面板
- Evaluation：支持 Ragas 和 Custom evaluator
- Observability：记录 ingestion 和 query 的中间状态

我的工作是在这个通用框架上做眼科 AI 文献场景的适配和评测，而不是从零重写整个 RAG 平台。

## 语料与配置

| 项目 | 配置 |
| --- | --- |
| 文档数量 | 10 篇 PDF |
| 切分结果 | 801 个 chunks |
| 语料类型 | 英文眼科 AI 论文 + 中文研究汇报 |
| chunking | recursive splitter |
| chunk size / overlap | 1000 / 200 |
| 当前范围 | text-based RAG baseline + 小规模图表 caption 探索 |
| 图像/表格抽取 | Reti-Pioneer 论文中抽取 32 个 image objects，筛选 8 张大图生成 caption |

## 评测方式

我没有只用固定 chunk ID 做评测。chunk-level 评测很精确，但 chunk ID 会随着 chunk size、overlap 和 splitter 规则变化而变化。

所以当前采用 source-level 为主、chunk-level 为辅的方式：

- source-level：判断是否找对论文或汇报来源，适合比较不同检索策略
- chunk-level：后续用于更精确的证据定位，适合同主题论文较多的场景

## 检索消融实验

![Retrieval Ablation](eval/results/figures/retrieval_ablation.svg)

| 模式 | source_hit@5 | source_mrr@5 | 平均查询耗时 ms |
| --- | --- | --- | --- |
| dense | 1.0000 | 0.7917 | 371.93 |
| hybrid | 0.9167 | 0.7667 | 703.43 |
| sparse | 0.8333 | 0.6944 | 223.81 |

在当前 hard test set 上，dense retrieval 表现最好。很多问题是中文提问，但目标来源是英文论文，语义检索比关键词匹配更稳定。

Sparse retrieval 速度最快，但更容易受到中文关键词噪声影响。Hybrid RRF 并没有稳定超过 dense，说明 hybrid 不是天然最优，还需要 weighted RRF 或 reranker。

## 生成消融实验

![Generation Ablation](eval/results/figures/generation_ablation.svg)

| 配置 | source_hit@k | source_coverage@k | citation_coverage | RAG 平均总耗时 ms |
| --- | --- | --- | --- | --- |
| dense_top5 | 0.8333 | 0.4889 | 0.4556 | 6830.34 |
| dense_top8 | 1.0000 | 0.6417 | 0.6417 | 7861.15 |
| dense_top10 | 1.0000 | 0.6833 | 0.6417 | 6737.67 |
| hybrid_top10 | 1.0000 | 0.5861 | 0.5861 | 7332.00 |

最终选择 `dense_top10` 作为当前 generation demo 的展示配置。它的来源覆盖率最高，同时耗时仍在可接受范围内。

## 成功案例

问题：

> 如果要设计一个眼科 AI demo，应该如何把英文论文原文和中文研究汇报结合起来？

结果：

- `source_hit@k = 1.0000`
- `source_mrr@k = 1.0000`
- `source_coverage@k = 1.0000`
- `citation_expected_coverage = 1.0000`

Vanilla LLM 的回答更像通用建议。RAG 回答能结合汇报4、汇报5、汇报6中的项目上下文，给出更具体的工程方案，例如报告幻觉控制、临床可信度验证、跨语言适配和 demo 简化设计。

## Bad Case 分析

问题：

> 眼科多模态模型、报告生成模型和真实临床验证之间是什么关系？

这个问题需要同时召回多模态基础模型、OCT 报告生成、OBUSight 和 Reti-Pioneer 等来源。但实际检索只覆盖了部分来源：

- `source_coverage = 0.5000`
- `citation_expected_coverage = 0.2500`

RAG 回答虽然比 Vanilla 更具体，但由于关键论文缺失，内容会向中文汇报和部分旁支医学影像材料偏移。

这个案例说明：RAG 的生成质量受检索覆盖率限制。即使回答看起来完整，如果关键来源没召回，最终答案仍可能跑偏。

## 一个发现：Hybrid 不一定更好

RETFound 相关问题里，dense retrieval 能把 Zhou 2023 RETFound 论文排到前面，但 hybrid top5 反而可能漏掉它。

原因是 sparse retrieval 会把包含“基础模型”“泛化”“预训练”等通用关键词的中文汇报 chunks 排得过高。RRF 融合后，真正相关的英文论文反而被挤出 top5。

这个 bad case 说明，在跨语言医学文献场景里，简单 hybrid search 不一定优于 dense。后续更合理的做法是 weighted RRF、query rewrite 或 reranker。

## 图表 Caption 探索

在文本 RAG baseline 之外，我进一步测试了图表增强链路。安装 PyMuPDF 后，Reti-Pioneer 论文可以抽取出 32 个 image objects；我筛选其中 8 张大尺寸图表，用 Vision LLM 生成中文 caption，并将结果保存为 `eval/results/reti_pioneer_figure_captions.md`。

这个实验验证了图表增强 RAG 的工程可行性：论文图片可以被抽取、筛选、压缩、送入视觉模型，并转化为可检索文本。但 caption 也暴露了边界：密集医学统计图可能出现语义归因偏差，因此当前结果只作为 model-assisted annotation 和 bad case 记录，不直接当作论文事实。

同时，我定位并修复了项目内置 `OpenAIVisionLLM` wrapper 没有读取 `vision_llm.base_url` 的问题。修复后，DashScope OpenAI-compatible endpoint 可以被正确使用，tiny image wrapper 调用已验证通过。对应 patch 见 `patches/vision_llm_base_url.patch`。

进一步实验中，我扩展了 ingestion pipeline，使 `.md` / `.txt` 文档可以像 PDF 一样进入 chunking、embedding 和 vector store。这样 Reti-Pioneer 图表 caption 不需要转成 PDF，可以作为派生文本资料直接入库。

在 8 个图表相关问题上，caption-augmented collection 的 `caption_source_hit@10` 从 text-only baseline 的 `0.0000` 提升到 `1.0000`。生成层面，图表关键词平均覆盖从 `9.38` 提升到 `10.12`，说明 caption 入库显著改善了图表来源召回，生成收益则相对温和，仍需要更严格的 image/table-only golden set 继续验证。

## AI Coding 在项目里的作用

这个项目我用了 AI coding 辅助开发，主要用在代码阅读、模块定位、脚本编写和问题修复上。

比如：

- 定位 evaluator 如何从 chunk-level 扩展到 source-level
- 修改 splitter，让它更适合中文医学文本
- 修复日志刷屏问题
- 编写评测汇总、case 导出和可视化脚本

但 AI coding 不是替我决定项目怎么做。真正需要自己判断的是：评测集怎么设计、哪些指标有意义、为什么某个检索策略失败、以及下一步应该怎么优化。

## 后续改进方向

- LLM ingestion 增强：从全量调用改为 selective refinement、cache 和 retry/backoff
- 图表检索增强：已完成 Reti-Pioneer 图表 caption 初探，下一步将 caption 入库并评测是否提升图表相关问题
- Image/table-only golden set：增加必须依赖图表才能回答的问题
- Metadata filtering：按论文类型、模态、语言过滤来源
- Weighted RRF：降低 sparse 在跨语言问题中的噪声影响
- Reranker：对初筛结果重新排序
- Chunk ablation：系统比较不同 chunk size / overlap
- LLM ablation：比较不同 LLM 的引用遵循、中文表达和延迟

## 项目边界

这个项目不是生产级医疗系统，也不用于真实诊断。它更像是一个学生项目里的工程评测案例：展示我如何把通用 RAG 框架迁移到具体领域，如何设计评测，如何做消融实验，如何发现 bad case，并给出下一步优化方向。
