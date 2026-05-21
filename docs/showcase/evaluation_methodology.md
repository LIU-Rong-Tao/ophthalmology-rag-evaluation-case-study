# Evaluation Methodology

本项目以 evaluation 作为 RAG workflow 的中心。目标不仅是生成答案，而是理解 retrieval 和 generation 何时成功、何时失败。

## 1. Why Source-Level Evaluation

Chunk IDs 是不稳定的。它们会在以下情况发生变化：

- chunk size 改变
- chunk overlap 改变
- splitter rules 改变
- 添加中文标点规则
- 引入 Markdown/TXT derived documents

因此，我使用 source-level evaluation 作为主要的 retrieval metric。

**Source-Level vs Chunk-Level Evaluation**  
![Source-level Evaluation](../../assets/figures/source_level_vs_chunk_id_evaluation_methods.png)

## 2. Retrieval Metrics

核心 retrieval metrics：

- `source_hit@k`
- `source_mrr@k`
- `source_coverage@k`
- query latency

对于 caption-derived documents，我增加了 metadata-aware source matching。

## 3. Metadata-Aware Source Matching

对于普通 paper sources，source 可以用文件名表示。对于 figure captions 等 derived sources，metadata 更加稳定：

```json
{
  "source_type": "figure_caption",
  "source_paper": "Reti-Pioneer",
  "modality": "vision_caption"
}
```

evaluator 可以将 retrieved chunk metadata 与 expected_metadata 进行匹配，避免脆弱的绝对路径。

## 4. Generation Metrics

Generation evaluation 包括：

Vanilla LLM vs RAG answer 对比

source coverage

citation expected coverage

vision-caption hard questions 的 keyword coverage

qualitative hardcase analysis

## 5. Hard Set Design

Hard vision-caption questions 的设计原则：

- 需要 chart structure 或 curve 的解读
- 避免要求精确的 OCR-level 小数字
- 避免通用的 paper-summary 问题
- 包含 caption reliability 和 misreading 风险

**Evaluation Pipeline**  
![Retrieval Pipeline](../../assets/figures/retrieval_pipeline_system_diagram.png)