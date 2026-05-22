# MedRAG-Align 数据结构说明

本 schema 用于统一公开医学 QA 数据和少量本地眼科 RAG smoke test，作为后续 evidence-grounded SFT、偏好数据构造和评测的基础。

## 当前目标

- 将 PubMedQA 转换为 evidence-grounded SFT seed / training-ready samples。
- 不声称这些样本具有医生验证的 claim-level evidence annotation。
- PubMedQA 自动转换得到的 claim-evidence 关系统一标记为 `weak_supervision`。
- 本地眼科 RAG 样例只作为小规模 domain-specific smoke test / held-out demo eval，不作为主要训练数据集。

## 数据主线

本项目的数据主线是公开医学数据集：

- `PubMedQA`：作为 evidence-grounded SFT seed 的主要来源。
- `MedQA` / `MedMCQA`：作为医学 instruction QA 和 reasoning 数据补充。
- 本地眼科 RAG 样例：只用于 10-20 条垂直领域 smoke test、错误分析和少量 preference seed 探索。

## 必填字段

- `id`：样本唯一 ID。
- `source_dataset`：数据来源，例如 `PubMedQA`、`MedQA`、`MedMCQA` 或 `OphthalmologyRAG`。
- `split`：数据划分，例如 `train_seed`、`eval_heldout`、`dev_eval`、`preference_seed`。
- `task_type`：任务类型，例如 `evidence_grounded_qa`。
- `question`：问题文本。
- `evidence_spans`：支持回答的证据片段。
- `answer`：参考答案或 SFT seed answer。
- `claims`：答案中的关键断言及其对应证据。
- `safety_expectation`：期望行为，例如 `answer`、`abstain`、`refuse_medical_advice`。
- `metadata`：原始数据集标签、年份、转换方式等元信息。

## PubMedQA 字段映射

- `QUESTION` -> `question`
- `CONTEXTS` -> `evidence_spans[].evidence_text`
- `LABELS` -> `evidence_spans[].section` 和 `metadata.context_labels`
- `LONG_ANSWER` -> `answer` / `reference_answer`
- `final_decision` -> `metadata.final_decision`
- `MESHES` -> `metadata.mesh_terms`
- `YEAR` -> `metadata.year`

## PubMedQA claim 构造方式

第一版 PubMedQA adapter 会从 `LONG_ANSWER` 自动构造一个弱监督 claim：

```json
{
  "claim_id": "c1",
  "claim_text": "LONG_ANSWER 的内容",
  "supporting_evidence_ids": ["e1", "e2"],
  "support_type": "weak_supervision"
}
```

## 本地眼科 RAG 样例的使用方式

本地眼科 RAG 样例不作为主要训练数据集，只作为 10-20 条 domain-specific smoke test / held-out demo eval。

本项目的数据主线是公开医学数据集，例如 PubMedQA、MedQA、MedMCQA；本地眼科 RAG 只用于展示垂直领域迁移和评测闭环。

本地眼科样例默认应写成：

```json
{
  "source_dataset": "OphthalmologyRAG",
  "split": "eval_heldout",
  "usage": "domain_smoke_test"
}
```