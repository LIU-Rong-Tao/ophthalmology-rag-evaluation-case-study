# Generation Case Studies

Source report: `eval/results/generation_dense_top10_both.json`

## Case 5

**Query:** 如果要设计一个眼科 AI demo，应该如何把英文论文原文和中文研究汇报结合起来？

**Expected Sources:**
- 汇报4.pdf
- 汇报5.pdf
- 汇报6.pdf

**Retrieved Sources:**
- 汇报5.pdf
- 汇报4.pdf
- 汇报6.pdf
- Liu 等 - 2026 - OBUSight Clinically Aligned Generative AI for Ophthalmic Ultrasound Interpretation and Diagnosis.pdf
- Chen 等 - 2026 - Boosting foundation models for rare eye disease diagnosis via a multimodal text-to-image generative.pdf

**Citation Map:**
- [1] 汇报5.pdf
- [2] 汇报4.pdf
- [3] 汇报4.pdf
- [4] 汇报4.pdf
- [5] 汇报5.pdf
- [6] 汇报4.pdf
- [7] 汇报6.pdf
- [8] 汇报5.pdf
- [9] Liu 等 - 2026 - OBUSight Clinically Aligned Generative AI for Ophthalmic Ultrasound Interpretation and Diagnosis.pdf
- [10] Chen 等 - 2026 - Boosting foundation models for rare eye disease diagnosis via a multimodal text-to-image generative.pdf

**Retrieval Metrics:**
- source_hit@k: 1.0000
- source_mrr@k: 1.0000
- source_coverage@k: 1.0000

**Vanilla Answer:**

设计眼科 AI demo 时，将英文论文原文与中文研究汇报结合，可按以下结构进行：

1. **核心内容对齐**  
   - 提取英文论文中的关键技术点（如模型架构、数据集、评估指标），用中文简洁概括，确保技术逻辑清晰。
   - 中文汇报中对应标注英文原文出处（如“参考文献[1]”），便于溯源。

2. **可视化辅助说明**  
   - 将论文中的图表（如性能对比图、网络结构图）翻译为中文标签，并补充简要解释。
   - 若原图无中文标注，可用文字框添加说明，保持专业性与可读性。

3. **应用场景映射**  
   - 英文论文中描述的实验场景（如糖尿病视网膜病变检测）转化为中文汇报中的实际应用案例（如“用于基层医院筛查”）。
   - 强调该技术在本地化落地的可行性（如适配中文医疗数据、符合中国临床指南）。

4. **风险提示与局限**  
   - 指出论文未覆盖的问题（如跨设备泛化能力），在中文汇报中明确说明当前demo的适用边界。
   - 若涉及伦理或合规问题（如患者隐私保护），需单独列出中文备注。

5. **工具建议**  
   - 使用 LaTeX 或 Markdown 编写中文汇报，嵌入英文论文摘要/公式，避免直接复制。
   - demo界面中提供“点击查看原文”按钮，链接至论文PDF或DOI，实现双语对照。

若具体论文来源不明确，需查阅文献确认其方法细节后再整合。

**RAG Answer:**

要设计一个眼科 AI demo，并将英文论文原文与中文研究汇报结合，可以按照以下步骤进行：

1. **技术方案提炼**：从英文论文中提取核心技术点（如MORG的双图像输入策略、VLS的接地报告机制、Merlin的多任务协同训练等），并将其映射到中文汇报中的“对项目的启示”部分[1][3][5]。这些启示直接指导你的demo架构设计，例如使用MSFF模块处理OCT多B-scan数据或引入CLIP辅助增强视觉编码器[8]。

2. **临床可信度提升**：借鉴Reti-Pioneer的五层评估体系（技术性能→外部泛化→生物学解释→前瞻性验证→临床接受度），在中文汇报中明确指出当前工作不足（如缺乏真实医生参与评估、仅依赖自动指标）[7]。这提示你应在demo中加入专家盲评和人机协作实验设计，以满足临床落地要求。

3. **幻觉控制与数据增强**：针对论文中反复提到的“报告幻觉”问题（如MORG、Glio-LLaMA-Vision均存在虚假描述）[1][4]，可采用VLS提出的“接地报告”机制（即通过SAM分割结果约束文本生成）来抑制错误输出[8]；同时参考EyeDiff等方法为罕见病设计专门的数据增强策略，解决样本不平衡导致的F1=0问题[2][9]。

4. **跨语言与跨设备适配**：若目标是面向中文用户，需考虑将英文论文中的模型适配至中文环境，例如利用OBUSight的研究建议——通过机器翻译+原生报告混合训练，提升多语言兼容性[9]；同时应纳入多中心、多设备数据以提高泛化能力，避免单中心局限[2][4]。

5. **工程化简化与模块集成**：避免过度工程化（如VLS中VLM+SAM+LoRA组合复杂），优先复现核心模块（如MSFF、CLIP辅助）并构建统一框架，便于后续扩展[5][6]。可通过阅读Merlin开源代码学习工程化设计思想，逐步提升项目集成能力[5]。

综上所述，英文论文提供前沿技术思路，中文汇报则揭示其实际应用限制与改进方向，两者结合能帮助你构建既先进又可靠的AI眼科demo。

主要依据来源：汇报5.pdf, 汇报4.pdf, 汇报6.pdf, Liu 等 - 2026 - OBUSight Clinically Aligned Generative AI for Ophthalmic Ultrasound Interpretation and Diagnosis.pdf, Chen 等 - 2026 - Boosting foundation models for rare eye disease diagnosis via a multimodal text-to-image generative.pdf

**Citation Metrics:**
- citation_expected_coverage: 1.0000
- citation_count: 9.0000

