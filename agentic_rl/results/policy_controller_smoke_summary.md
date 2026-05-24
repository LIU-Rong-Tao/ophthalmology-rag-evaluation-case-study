# RL Search Policy Controller Smoke Test v0

## 目的

本实验验证 Agentic Evidence RAG 项目已经可以在 fixed policy reward table 之上运行一个最小 controller training loop。

该结果不是最终 retrieval/RL 结果，而是训练闭环冒烟测试。

## 输入

- Reward table: agentic_rl/results/hotpot_fixed_policy_ablation_dev100.csv
- 样本数: 100 HotpotQA dev examples
- Actions: 5 fixed search policies
- Epochs: 80
- Epsilon: 0.60 -> 0.05

## 输出

- agentic_rl/results/policy_controller_reward_curve_smoke.csv
- agentic_rl/results/policy_controller_action_distribution_smoke.csv

## 结果

| metric | epoch 1 | epoch 80 |
| --- | ---: | ---: |
| mean_reward | 0.4640 | 0.6835 |
| epsilon | 0.6000 | 0.0500 |
| dense50_rerank10 action share | 0.4500 | 0.9600 |

最终 action value:

| policy | value |
| --- | ---: |
| abstain | -0.0500 |
| dense50_rerank10 | 0.7000 |
| dense_top10 | 0.4000 |
| multi_query_dense_top10 | 0.1000 |
| multi_query_rerank10 | 0.5000 |

## 解释

该实验证明如下训练闭环已经跑通：

fixed policy reward table -> controller update -> reward curve -> action distribution

当前版本的 reward 来自 simulation，而且最优动作基本固定为 dense50_rerank10。因此该结果只能说明训练管线可运行，不能说明 controller 已经学会针对不同问题选择不同 search action。

下一步应做 per-case oracle / difficulty analysis，检查不同 case 的最优 action 是否有足够差异，再进入 contextual controller 或真实 retrieval reward。
