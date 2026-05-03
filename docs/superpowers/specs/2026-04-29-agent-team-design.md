# 智能体团队协作系统设计

## 目标
在 Trae CN 中创建一个智能体团队，能够：
1. 使用 brainstorming 技能分析需求
2. 使用 writing-plans 技能拆解任务
3. 多角色协作完成功能开发
4. 完整的代码审查和验证流程

## 背景
项目已有完整的 superpowers 技能框架，包括：

### 核心技能
- **brainstorming**：需求分析 → 设计规格，不写代码先想清楚
- **writing-plans**：把规格拆成可执行的实施步骤
- **executing-plans**：按计划逐步实施，每步验证
- **test-driven-development**：严格 TDD：先写测试，再写代码
- **systematic-debugging**：四阶段调试法：定位→分析→假设→修复
- **requesting-code-review**：派遣审查 agent 检查代码质量
- **receiving-code-review**：技术严谨地处理审查反馈，拒绝敷衍
- **verification-before-completion**：证据先行——宣称完成前必须跑验证
- **dispatching-parallel-agents**：多任务并发执行
- **subagent-driven-development**：每个任务一个 agent，两轮审查
- **workflow-runner**：工作流执行

### 角色定义
- **project-manager.md**：项目总协调者
- **frontend-developer.md**：前端开发
- **backend-developer.md**：后端开发
- **database-developer.md**：数据库开发

## 架构设计

### 目录结构
```
workflows/                           # 新建工作流目录
├── project-development.yaml         # 完整项目开发工作流
├── quick-feature.yaml               # 快速功能开发工作流
└── README.md                        # 工作流使用说明
```

### 核心组件

#### 1. YAML 工作流定义
使用 agency-orchestrator 格式定义工作流，包含：
- 输入变量定义
- 执行步骤（DAG 拓扑）
- 角色分配
- 输出变量

#### 2. 角色定义
复用现有的 `.trae/skills/` 下的角色文件：
- project-manager.md：项目总协调者
- frontend-developer.md：前端开发
- backend-developer.md：后端开发
- database-developer.md：数据库开发

#### 3. workflow-runner 技能
使用现有 workflow-runner 技能执行 YAML 工作流

## 工作流设计

### 主工作流：project-development.yaml
```yaml
name: "智能体团队项目开发"
agents_dir: ".trae/skills"
inputs:
  - name: requirement
    required: true
    description: "功能需求描述"
steps:
  - id: brainstorm
    role: "project-manager"
    task: "使用 brainstorming 技能分析需求：{{requirement}}"
    output: spec_design
  - id: plan
    role: "project-manager"
    task: "使用 writing-plans 技能创建实现计划，基于：{{spec_design}}"
    output: implementation_plan
  - id: confirm
    role: "project-manager"
    task: "向用户展示计划并等待确认：{{implementation_plan}}"
    output: user_confirmation
```

### 快捷工作流：quick-feature.yaml
针对小型功能的简化版本，跳过部分评审步骤。

## 触发方式

### 手动触发
用户明确输入：
```
运行工作流 workflows/project-development.yaml
需求：[你的需求描述]
```

### 自动触发（可选）
配置关键词触发，如：
- "开发新功能"
- "实现"
- "创建"

## 输出产物

### 规格文档
保存位置：`docs/superpowers/specs/YYYY-MM-DD-<topic>-design.md`

### 实现计划
保存位置：`docs/superpowers/plans/YYYY-MM-DD-<feature-name>.md`

### 工作流输出
保存位置：`.ao-output/{工作流名称}-{YYYY-MM-DD}/`

## 执行流程

### 完整流程

1. **触发阶段**
   - 用户触发工作流（手动或自动）
   - workflow-runner 解析 YAML
   - 收集输入变量

2. **需求分析阶段**
   - project-manager 扮演角色
   - 调用 brainstorming 技能
   - 探索项目上下文
   - 澄清问题（每次一个）
   - 提出方案
   - 展示设计
   - 编写规格文档
   - 自检
   - 用户审查

3. **计划阶段**
   - project-manager 调用 writing-plans
   - 范围检查
   - 设计文件结构
   - 分解任务（小步骤）
   - 自检
   - 向用户展示计划
   - 等待用户确认

4. **执行阶段（选择一）**
   - **subagent-driven-development（推荐）**
     - 每个任务分派全新子智能体
     - 实现者遵循 TDD（test-driven-development）
     - 先写失败测试 → 写代码 → 验证通过
     - 自审
     - 提交
     - 规格合规性审查（两阶段审查第一阶段）
     - 代码质量审查（两阶段审查第二阶段）
     - 使用 requesting-code-review 审查
     - 使用 receiving-code-review 处理反馈
     - 每个任务用 verification-before-completion 验证
     - 独立任务用 dispatching-parallel-agents 并行
     - 遇到 bug 用 systematic-debugging
     - 循环直到所有任务完成

   - **executing-plans（备选）**
     - 同会话逐任务执行
     - 每批任务后审查
     - 其他同上述

5. **收尾阶段**
   - 调用 finishing-a-development-branch
   - 最终验证
   - 向用户展示成果

## 关键约束

### 必须严格遵循

- **brainstorming 的 HARD-GATE**：展示设计并获批准前，不调用实现技能、不写代码
- **writing-plans 的禁止占位符**：每个步骤必须有实际内容，不写"待定"
- **test-driven-development 的铁律**：没有失败的测试就不写生产代码
- **systematic-debugging 的铁律**：不做根因调查不许提修复方案
- **verification-before-completion 的铁律**：没有新鲜验证证据不许宣称完成
- **subagent-driven-development 的红线**：每个任务一个全新子智能体 + 两轮审查
- **所有工作流执行**：必须有明确的用户确认关卡

### 其他约束

- 严格遵循现有 superpowers 技能的使用规范
- 所有输出产物必须保存到指定目录
- 角色切换必须清晰标注
- 未经用户明确同意，绝不在 main/master 分支上开始实现

## 后续扩展

- 支持更多工作流模板（bug修复、重构、性能优化）
- 增加工作流执行历史记录
- 支持自定义工作流创建向导
