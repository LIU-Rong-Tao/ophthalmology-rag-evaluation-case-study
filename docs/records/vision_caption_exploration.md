# Vision Caption 探索记录

## 1. 为什么做这一步

文本 RAG baseline 已经能回答论文方法、项目方案和部分对比问题，但论文中的图表信息还没有进入知识库。所以我进一步测试：能不能把 PDF 里的 figure 抽取出来，用 Vision LLM 生成 caption，再作为后续图表增强 RAG 的文本来源。

## 2. 图像抽取结果

最开始 PDF ingestion 日志里是 `Images processed: 0`。

安装 PyMuPDF 后，重新 ingest Reti-Pioneer 论文到测试 collection，结果变成：

- `Total chunks generated: 127`
- `Total images processed: 32`

随后我从抽取结果中筛选出 8 张大尺寸图表，并压缩到 1536 宽，用于 Vision LLM caption。

## 3. 调试过程

项目自带的 `OpenAIVisionLLM` wrapper 最开始调用 tiny image 也会 timeout。为了定位问题，我拆成三步验证：

- `GET /models` 能快速返回 401，说明网络可达
- text-only `POST /chat/completions` 能返回 200，说明 base_url、api_key 和 model 可用
- raw OpenAI-compatible vision payload 能返回 200，说明 DashScope vision 接口和 base64 image_url 格式可用

所以问题不在网络、key 或模型，而在项目封装层。

进一步检查后发现：

- `llm_factory.py` 会完整传入 `settings`
- `settings.py` 已经支持 `vision_llm.base_url`
- 但 `OpenAIVisionLLM.__init__` 没读取 `settings.vision_llm.base_url`

因此 wrapper 会忽略 DashScope endpoint，回退到默认 `https://api.openai.com/v1`。

修复后，wrapper 能正确读取 `vision_llm.base_url`，tiny image 测试通过。

## 4. 当前结果

8 张 Reti-Pioneer 大图 caption 已保存到：

`eval/results/reti_pioneer_figure_captions.md`

portfolio 中只保存 caption 文本，不保存原始论文图片，避免版权风险。

## 5. 主要结论

这一步验证了图表增强 RAG 的工程可行性：论文图片可以被抽取、筛选、压缩、送入视觉模型，并转成可检索文本。

但 caption 不能直接当论文事实。密集医学图表可能被模型解释偏，所以后续如果要入库，需要人工复核，并设计 image/table-only golden set 来评估 caption 是否真的改善图表相关问题。
