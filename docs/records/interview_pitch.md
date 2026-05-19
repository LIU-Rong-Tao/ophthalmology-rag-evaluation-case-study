# 面试讲解稿：眼科 RAG 评测与误差分析案例

## 1. 项目一句话

我基于 Modular RAG MCP Server 做了一个眼科 AI 文献 RAG 项目。重点不是简单跑通 RAG，而是围绕真实论文做领域化切分、评测集设计、检索/生成对比和 bad case 分析。

## 2. 我做了什么

- 整理 10 篇眼科 AI 论文和中文研究汇报，构建 801 个 chunks 的知识库
- 针对中英文混排 PDF，调整 recursive splitter 的中文分隔符
- 修复 ingestion/query 阶段第三方库 DEBUG 日志刷屏问题
- 设计 source-level golden set，避免评测过度依赖不稳定 chunk ID
- 对比 dense、sparse、hybrid RRF 三种检索方式
- 对比 Vanilla LLM 和 RAG-enhanced generation
- 导出成功案例、边界案例和 hybrid 检索失败案例
- 探索 PyMuPDF 图像抽取和 Vision LLM caption
- 定位并修复 Vision wrapper 没读取 `vision_llm.base_url` 的问题

## 3. 关键结果

检索实验中，dense retrieval 在当前 hard set 上表现最好：

| mode | source_hit@5 | source_mrr@5 | avg_query_ms |
| --- | ---: | ---: | ---: |
| dense | 1.0000 | 0.7917 | 371.93 |
| hybrid | 0.9167 | 0.7667 | 703.43 |
| sparse | 0.8333 | 0.6944 | 223.81 |

生成实验中，`dense_top10` 是当前展示配置：

| setting | source_hit@k | source_coverage@k | citation_coverage | rag_total_avg_ms |
| --- | ---: | ---: | ---: | ---: |
| dense_top5 | 0.8333 | 0.4889 | 0.4556 | 6830.34 |
| dense_top8 | 1.0000 | 0.6417 | 0.6417 | 7861.15 |
| dense_top10 | 1.0000 | 0.6833 | 0.6417 | 6737.67 |
| hybrid_top10 | 1.0000 | 0.5861 | 0.5861 | 7332.00 |

## 4. 真实遇到的问题

第一个问题是 hybrid search 不一定更好。RETFound 相关问题里，dense 能找到 Zhou 2023 RETFound 论文，但 hybrid top5 有时会漏掉。原因是 sparse 会把中文汇报里“基础模型、泛化、预训练”等通用词排得太高，RRF 融合后反而把正确英文论文挤下去。

第二个问题是检索覆盖不完整会影响回答重点。比如问“眼科多模态模型、报告生成模型和真实临床验证之间是什么关系”，理想情况要同时召回多模态模型、OCT 报告生成、眼科超声诊断和真实世界验证相关论文。但实际只召回了一部分材料时，RAG 会围绕已召回内容回答。它不一定是捏造，因为有些论文确实研究多个疾病；问题是回答没有完整覆盖我想要的关系链条。

第三个问题是 LLM ingestion 增强不能直接全量开。小文档可以 refine 成功，但长论文 126 个 chunks 里只有 10 个成功，116 个 fallback，主要是 API 429 限流。后续应该做 selective refinement、cache 和 retry/backoff，而不是每个 chunk 都调 LLM。

## 5. 图表增强探索

安装 PyMuPDF 后，Reti-Pioneer 论文从 `Images processed: 0` 变成可以抽取 32 个 image objects。我筛选 8 张大图，用 `qwen-vl-plus` 生成中文 caption，保存到 `eval/results/reti_pioneer_figure_captions.md`。

这个实验说明论文图表可以转成文本，用于后续图表增强 RAG。但 caption 不能直接当事实，因为密集医学图表可能会被模型解释偏，所以还需要人工复核和专门的图表类评测集。

## 6. Vision wrapper 修复

图表 caption 调试时，raw DashScope vision payload 可以成功，但项目自带 `OpenAIVisionLLM` wrapper 会 timeout。最后定位到原因是 wrapper 没读取 `vision_llm.base_url`，导致配置里的 DashScope endpoint 被忽略，回退到了 OpenAI 默认地址。

修复后，wrapper 能正确使用 DashScope endpoint，tiny image 测试通过。对应 patch 在 `patches/vision_llm_base_url.patch`。

## 7. 下一步

- 构造 image/table-only golden set
- 对比 text-only RAG 和 caption-augmented RAG
- 把图表 caption 入库，测试图表相关问题是否能召回 caption chunk
- 对 caption 成功和失败案例做误差分析
- 尝试 reranker 或 weighted RRF，降低跨语言 hybrid 检索噪声
