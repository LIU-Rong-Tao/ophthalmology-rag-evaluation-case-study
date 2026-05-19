# Engineering Notes & Badcases

本文档汇总项目中发现的工程问题。

## 1. Logging Noise Suppression

在 ingestion 过程中，PDF 解析器和 tokenizer 等第三方库产生了大量 DEBUG 日志。我修改了 verbose logging 配置，使项目日志聚焦于自身输出，而不是将所有依赖都设为 DEBUG 模式。

Patch：

- `patches/logging_noise_suppression.patch`

## 2. Chinese Recursive Splitter

原始 recursive splitter 对中文医学文本的分割效果不理想。我补充了中文标点分隔符，使中文研究汇报的分块更自然。

Patch：

- `patches/chinese_recursive_splitter.patch`

## 3. Vision LLM Base URL Bug

项目自带的 `OpenAIVisionLLM` wrapper 接收了 `settings`，但没有读取 `settings.vision_llm.base_url`。这导致 DashScope-compatible vision calls 回退到 OpenAI 默认 endpoint。

修复：

- 读取 `vision_llm.base_url`
- 保持显式 `base_url` override 为最高优先级
- 保留 Azure endpoint 原有行为

Patch：

- `patches/vision_llm_base_url.patch`

## 4. Markdown/TXT Ingestion

Caption 文本不是 PDF。将 Markdown caption 结果转回 PDF 会引入噪声。

我添加了 `TextLoader` 以支持：

- `.md`
- `.markdown`
- `.txt`

这使得 figure captions、手动笔记和轻量级派生文档可以进入相同的 chunking 和 embedding pipeline。

Patch：

- `patches/text_loader_markdown_ingestion.patch`

## 5. Metadata-Aware Evaluation

Caption 文档不应通过绝对路径来评估。我扩展了 evaluator 以支持 metadata 约束，如：

- `source_type`
- `source_paper`
- `modality`

这使得 source-level evaluation 对 derived knowledge sources 更加健壮。

## 6. API Rate Limit Badcase

全量 chunk-level LLM refinement 成本高且不稳定：

| document | chunks | LLM refined | fallback |
| --- | ---: | ---: | ---: |
| 汇报6.pdf | 6 | 6 | 0 |
| Reti-Pioneer paper | 126 | 10 | 116 |

工程结论：保持主 ingestion pipeline 稳定，然后选择性、异步地运行 LLM enrichment。

> **PLACEHOLDER: Engineering Badcases Timeline**  
> 预留路径：`docs/assets/engineering_badcases_timeline.png`