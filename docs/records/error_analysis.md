# Bad Case 与工程问题记录

## 1. LLM Ingestion 增强的限流问题

我尝试开启 LLM-based chunk refinement，希望在 ingestion 阶段提升 chunk 质量。实验发现，小文档可以正常完成，但长论文会快速触发 API 429 rate limit，导致大量 chunk fallback 到规则增强。

| 文档 | chunks | LLM refined | fallback | 现象 |
| --- | ---: | ---: | ---: | --- |
| 汇报6.pdf | 6 | 6 | 0 | 小文档可正常完成 LLM refine |
| Reti-Pioneer 长论文 | 126 | 10 | 116 | 长论文触发大量 HTTP 429 |

这说明 LLM ingestion enhancement 不能简单全量开启。即使加入 sleep 和 retry backoff，也会带来明显的线性耗时：如果每个 chunk 间隔 1.5 秒，126 个 chunk 仅等待时间就超过 3 分钟，801 个 chunk 则会更长。

因此，更合理的方向不是“所有 chunk 都调用 LLM”，而是 selective refinement：

- 先用 rule-based pipeline 保证稳定 ingestion baseline
- 只对高价值 chunk 做 LLM refine，例如摘要、结论、图表附近、指标密集段落、bad case 中经常漏掉的证据段
- 对 LLM 调用结果做缓存，避免重复请求
- 对 429 做 retry with exponential backoff
- 根据 golden set 和 bad case 持续维护 selector 规则

这不是一次性写死的规则，而是一个需要随着文档类型、查询分布和失败案例持续迭代的工程模块。

## Vision Caption 调用封装问题

在图表增强实验中，我先安装 PyMuPDF，使 PDF loader 能从 Reti-Pioneer 论文中抽取 32 个 image objects。随后筛选出 8 张大尺寸图表候选图用于 caption。

初始尝试复用项目内置 `OpenAIVisionLLM` wrapper 时，即使对 128x128 的 tiny 测试图也出现 60 秒 timeout。为了定位问题，我做了三个最小验证：

- `GET /models` 能在 0.14 秒返回 401，说明服务器到 DashScope 网络可达；
- text-only `POST /chat/completions` 能在 0.37 秒返回 200，说明 base_url、api_key 和 qwen-vl-plus 模型可用；
- raw OpenAI-compatible vision payload 加 tiny image 能在 0.46 秒返回 200，说明 DashScope Vision 接口和 base64 image_url 格式可用。

因此，问题不在网络、key 或模型，而更可能在项目内置 Vision wrapper 的请求封装或图像预处理路径。为了先完成图表增强实验，我临时写了独立脚本 `scripts/caption_selected_images.py`，绕过 wrapper，直接使用验证通过的 raw POST payload 对筛选后的图表生成 caption。

这个 bad case 说明，多模态链路调试时不能只看“接口是否可用”，还要把网络连通、文本请求、图像请求、项目封装层逐层拆开验证。

### 后续定位与修复

进一步排查后确认，`llm_factory.py` 会完整传入 `settings`，`src/core/settings.py` 也已经支持 `vision_llm.base_url`。真正问题在 `OpenAIVisionLLM.__init__`：原实现没有读取 `settings.vision_llm.base_url`，因此配置中的 DashScope endpoint 被忽略，wrapper 回退到默认 `https://api.openai.com/v1`，最终表现为请求 timeout。

修复后，`OpenAIVisionLLM` 会优先读取 `vision_llm.base_url`。wrapper 级 tiny image 调用已验证通过，返回结果为：`The image shows a red square with the letters "AI" centered inside it.`

这个案例说明，OpenAI-compatible 多模态接口接入时，除了验证 raw payload 成功，还需要确认项目封装层是否完整传递 provider-specific 配置。


## 3. Caption-Augmented Retrieval 评测中的工程问题

在做 text-only RAG 与 caption-augmented RAG 对比时，我遇到了几个评测层面的 bad case。

### 3.1 `expected_sources` 名称不匹配

我最开始在 vision caption golden set 中写的是：

`Reti-Pioneer figure captions`

但 evaluator 实际根据 chunk metadata 里的 `source_path` 进行 source-level 判断。caption 文档真实来源是：

`data/ophthalmology_caption_docs/reti_pioneer_figure_captions.md`

因此增强 collection 实际已经召回了 caption 内容，但 `source_hit_rate` 仍然显示为 0。

这个问题说明，source-level evaluator 的 `expected_sources` 必须和真实 metadata 对齐，否则会把正确召回误判成失败。

### 3.2 精确 chunk id 匹配失败

为了确认 caption 是否被召回，我尝试根据 caption Markdown 重新切分并计算 chunk id，再和 `retrieved_chunk_ids` 做精确匹配。结果发现前缀一致，但最后的 content hash 不一致：

- 实际召回示例：`0d6b1c83_0000_45e47829`
- 重新计算示例：`0d6b1c83_0000_576f84cb`

原因是 ingestion pipeline 中 rule-based transform 可能会轻微改写 chunk 文本，导致 content hash 变化。因此，精确 chunk id 不适合用于这类派生文档的评测判断。

更稳妥的做法是使用 source-level prefix 或 metadata 字段，例如 `source_type: figure_caption`、`source_paper: Reti-Pioneer`、`modality: vision_caption`。

### 3.3 相对路径 hash 与绝对路径 hash 不一致

我又尝试用 caption 文档路径计算 source prefix，但第一次使用的是相对路径：

`data/ophthalmology_caption_docs/reti_pioneer_figure_captions.md`

得到的 prefix 是：

`6c378b7c_`

而实际入库时 `TextLoader` 会把 `source_path` 解析成绝对路径：

`<PROJECT_ROOT>/data/ophthalmology_caption_docs/reti_pioneer_figure_captions.md`

真实 prefix 是：

`0d6b1c83_`

因此第一次统计 `caption_source_hit@10` 仍然是 0。改成读取 `TextLoader().load(...).metadata["source_path"]` 后，统计结果正常。

最终结果：

| collection | caption_source_hit@10 |
| --- | ---: |
| text-only baseline | 0 / 8 = 0.0000 |
| caption-augmented | 8 / 8 = 1.0000 |

这个结果说明，caption-augmented collection 能稳定召回 caption source；同时也说明评测脚本要尽量使用 loader / pipeline 真实 metadata，而不是手写路径或手算 chunk id。
