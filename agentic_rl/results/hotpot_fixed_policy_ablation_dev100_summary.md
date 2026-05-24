# HotpotQA Fixed Policy Reward Simulation v0

## 目的

本实验用于验证公开 HotpotQA 数据可以接入 Agentic Evidence RAG 的 search-policy evaluation 闭环。

当前版本是 reward simulation，不是真实检索实验。脚本使用 HotpotQA 的 `supporting_facts` 构造 gold evidence titles，并通过模拟 retrieval 行为测试不同 fixed search policies 在 evidence coverage、search cost 和 reward 上的区分度。

## 数据

- 数据集：HotpotQA dev distractor
- 样本数：100
- Policy 数：5
- 输出记录：500 条 policy-case 结果

## Reward

```text
reward = evidence_coverage - 0.1 * search_cost