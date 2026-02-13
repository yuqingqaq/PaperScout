

# Agent Memory 领域知识库

## 一、 核心综述框架
### 1. 基础模型智能体记忆 (Foundation Agent Memory)
该领域的研究重点已从单纯提升 Benchmark 分数转向解决现实世界中长周期、动态、用户依赖环境下的 **“上下文爆炸 (Context Explosion)”** 问题。

### 2. 三维统一分类法 (Taxonomy)
*   **存储介质 (Memory Substrate - "形式")**：
    *   **外部记忆 (External)**：存储在模型参数之外，如向量索引、文本记录、结构化存储（SQL/图）或分层存储。
    *   **内部记忆 (Internal)**：直接存储在架构内，包括 **参数权重 (Weights)** 和推理时的 **潜在状态 (Latent-state/KV Cache)**。
*   **认知机制 (Cognitive Mechanism - "功能")**：
    *   **感官记忆 (Sensory)**：临时缓冲原始感知输入（如多模态流）。
    *   **工作记忆 (Working)**：维持和处理当前任务相关的推理状态（如 CoT、中间规划）。
    *   **情景记忆 (Episodic)**：持久记录特定的互动经历（时间、地点、因果关系）。
    *   **语义记忆 (Semantic)**：存储稳定的抽象知识、事实和概念（如百科全书、用户特质）。
    *   **程序记忆 (Procedural)**：编码执行任务的技能、策略和自动化流程（如工具使用习惯、SOP）。
*   **记忆主体 (Memory Subject - "服务对象")**：
    *   **以用户为中心 (User-Centric)**：关注个性化偏好、身份一致性和隐私保护。
    *   **以智能体为中心 (Agent-Centric)**：侧重于任务执行经验积累、跨任务知识迁移和技能习得。

---

## 二、 核心操作机制 (Memory Operation Mechanism)
智能体通过一系列序列化操作主动管理记忆，而非将其视为静态仓库：

1.  **存储与索引 (Storage & Index)**：将信息关联语义嵌入、时间戳、实体等元数据，使用向量或结构化图进行组织。
2.  **加载与检索 (Loading & Retrieval)**：基于相关性、多样性和上下文配额进行筛选，避免上下文过载或干扰噪声。
3.  **更新与刷新 (Update & Refresh)**：根据新观察、反馈或自反思修改旧记忆，通过合并、覆盖或调整权重防止过期。
4.  **压缩与总结 (Compression & Summarization)**：将细粒度的情景记录提炼为抽象摘要或多级树状结构，缓解 Token 饱和。
5.  **遗忘与保留 (Forgetting & Retention)**：显式移除低价值或过时数据，通过衰减机制或学习策略保护高价值知识。
*   **[更新]** 对比性经验蒸馏：从成功/失败经验中提取泛化推理策略 (2509.25140v1)

---

## 三、 记忆学习策略 (Learning Policy)
智能体如何学会高效管理记忆？综述将其归纳为三条路径：

*   **基于提示 (Prompt-based)**：
    *   **静态控制**：通过固定的 Prompt 模板或 OS 级架构（如 **MemGPT**, **EverMemOS**）强制执行记忆规范。
    *   **动态优化**：智能体通过**自反思 (Reflexion)** 自动修正其记忆指令或重组存储结构。
*   **微调强化 (Fine-tuning)**：通过监督信号将记忆内容或检索行为**参数化**，内化为模型的稳定行为。
*   **强化学习 (Reinforcement Learning)**：
    *   **步骤级决策**：学习在每一步执行 ADD/UPDATE/DELETE/NOOP 操作（如 **Memory-R1**）。
    *   **轨迹级表征**：将记忆质量与长周期任务的最终奖励挂钩，驱动模型学习高效的压缩与保留策略。

---

## 四、 评估体系与挑战
### 1. 核心能力指标 (Key Abilities)
*   **Fact Extraction (FE)**：事实提取能力。
*   **Multi-Session Reasoning (MR)**：跨会话推理。
*   **Temporal Reasoning (TR)**：时序/时效性推理（EverMemOS 的核心优势之一）。
*   **Abstain & Boundary (AB)**：边界处理，在缺失证据时学会拒绝回答。
*   **Memory Integrity (MI)** & **False Memory Rate (FMR)**：记忆完整性与虚假记忆率（衡量幻觉）。

### 2. 重要 Benchmark
*   **个性化类**：PersonaMem-v2 (隐式偏好推理), MSC, DuLeMon。
*   **任务/工具类**：OSWorld, WebArena (GUI/Web 操作记忆), SWE-bench (软件工程)。
*   **综合推理类**：LoCoMo (长上下文记忆), HotpotQA。

---

## 五、 应用场景与垂直领域
1.  **教育 (Education)**：模拟遗忘曲线进行个性化辅导（如 **LOOM**, **Agent4Edu**）。
2.  **科学研究 (Scientific Research)**：跨实验的知识合成与验证（如 **GAM**, **IterResearch**）。
3.  **医疗健康 (Healthcare)**：追踪用户的情绪轨迹与生理指标相关性（如 **TheraMind**, **Mem-PAL**）。
4.  **游戏与仿真 (Gaming)**：Believable 的社交历史与技能进化（如 **Generative Agents**, **Voyager**）。
5.  **软件工程 (SWE)**：大规模代码仓库的导航与历史 Fail-Fix 经验复用（如 **MetaGPT**）。

---

## 六、 研究趋势与前沿论文
*   **EverMemOS (2026)**：提出了操作系统级的持久化记忆管理，通过“叙事重写”和“场景聚类”解决碎片化问题。
*   **PersonaMem-v2 (2025)**：首次引入隐式偏好推理，结合 **GRPO 强化学习** 训练智能体自主提取并蒸馏用户档案。
*   **Zep (Graphiti)**：典型的**时间感知知识图谱**架构，支持实体解析和边失效机制。
*   **Memory-R1**：将记忆编辑（增删改）建模为显式行动空间的强化学习系统。

---

## 七、 未来方向 (Future Directions)
*   **多模态与世界模型记忆**：将视觉、触觉流融入具有预测性的“世界模型记忆”中。
*   **记忆基础设施效率**：解决线性 Token 增长问题，转向常数级大小的 latent memory 或参数化记忆。
*   **可信记忆与隐私防御**：对抗记忆注入攻击（Memory Injection Attacks），支持用户审计和撤销存储。
*   **人类-智能体协同记忆**：在多主体环境下管理角色分工、路由权限和冲突解决。

*   **多智能体协作记忆：追踪智能体间交互轨迹与协作经验的记忆机制** (2506.07398v2)
