# MedRAG-Align v0 数据流水线报告

## 目标

本阶段目标是在训练前先建立可信的 evidence-grounded 数据结构。

当前项目不声称已经完成医生验证标注，也不声称已经完成医学模型训练。PubMedQA 被转换为弱监督的 evidence-grounded SFT seed 数据；本地眼科 RAG 样例只作为小规模垂直领域 smoke test。

## 已完成产物

| 产物 | 路径 | 数量 |
| --- | --- | ---: |
| PubMedQA SFT seed | `eval/align/pubmedqa_sft_seed.sample.jsonl` | 500 |
| Preference pair seed | `eval/align/preference_pairs_seed.sample.jsonl` | 30 |
| 眼科 smoke eval | `eval/golden_v2/oph_smoke_eval_seed.json` | 1 |
| Golden v2 schema | `eval/golden_v2/schema.json` | - |
| 数据结构说明 | `docs/data_schema.md` | - |

## PubMedQA 转换方式

PubMedQA 字段被映射到 Golden v2 schema：

- `QUESTION` -> `question`
- `CONTEXTS` -> `evidence_spans`
- `LABELS` -> 证据片段 section 标签
- `LONG_ANSWER` -> `answer` / `reference_answer`
- `final_decision` -> `metadata.final_decision`

其中 claim-to-evidence 关系统一标记为 `weak_supervision`。

## Alignment Metrics v0

| 输入 | 数量 | Citation Coverage | Unsupported Claim Rate | Abstain Accuracy |
| --- | ---: | ---: | ---: | ---: |
| PubMedQA SFT seed | 500 | 1.0000 | 0.0000 | N/A |
| 眼科 smoke eval | 1 | 1.0000 | 0.0000 | 1.0000 |

这些指标只是数据结构层面的 sanity check，不是模型性能结果。

## Preference Pair Seed

第一版 preference seed 包含三类 rejected answer：

- `citation_grounding`：rejected answer 缺少证据引用。
- `unsupported_claim`：rejected answer 加入了无证据支持的临床泛化。
- `medical_abstain`：rejected answer 违反医学安全边界，过度诊断或过度建议。

这些 preference pairs 是弱监督偏好种子，不是医生验证的偏好标注。

## 下一步

1. 将眼科 smoke eval 从 1 条扩展到 10-20 条。
2. 添加 MedQA / MedMCQA instruction-format adapter。
3. 回到原眼科 RAG pipeline，继续 rerank ablation。
4. 在数据版本和 baseline evaluation 记录清楚后，再启动 QLoRA SFT。