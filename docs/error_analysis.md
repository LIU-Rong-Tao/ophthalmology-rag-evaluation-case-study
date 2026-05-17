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

