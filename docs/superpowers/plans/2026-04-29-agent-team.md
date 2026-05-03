# 智能体团队协作系统 实现计划

> **面向 AI 代理的工作者：** 必需子技能：使用 superpowers:subagent-driven-development（推荐）或 superpowers:executing-plans 逐任务实现此计划。步骤使用复选框（`- [ ]`）语法来跟踪进度。

**目标：** 创建 YAML 工作流文件，集成所有 superpowers 技能，实现多角色智能体团队协作

**架构：** 创建 3 个文件（2 个 YAML 工作流 + 1 个 README），工作流使用 agency-orchestrator 格式，集成 brainstorming、writing-plans、subagent-driven-development 等技能

**技术栈：** YAML（agency-orchestrator 格式）、Markdown

---

## 任务 1：创建 workflows 目录和 project-development.yaml 主工作流

**文件：**
- 创建：`workflows/project-development.yaml`

- [ ] **步骤 1：编写 YAML 头部**

```yaml
name: "智能体团队项目开发"
agents_dir: ".trae/skills"
inputs:
  - name: requirement
    required: true
    description: "功能需求描述"
```

- [ ] **步骤 2：运行验证（检查 YAML 语法）**

运行：`python -c "import yaml; yaml.safe_load(open('workflows/project-development.yaml'))"`
预期：无报错

- [ ] **步骤 3：添加 brainstorming 步骤**

```yaml
steps:
  - id: brainstorm
    role: "project-manager"
    task: |
      使用 brainstorming 技能分析需求：{{requirement}}
      流程：探索上下文 → 澄清问题 → 提出方案 → 展示设计 → 自检 → 用户审查
      输出：完整的规格文档
    output: spec_design
```

- [ ] **步骤 4：验证 YAML 语法**

运行：`python -c "import yaml; yaml.safe_load(open('workflows/project-development.yaml'))"`
预期：无报错

- [ ] **步骤 5：添加 writing-plans 步骤**

```yaml
  - id: plan
    role: "project-manager"
    task: |
      使用 writing-plans 技能创建实现计划，基于：{{spec_design}}
      流程：范围检查 → 文件结构 → 任务分解 → 自检
      输出：详细的实现计划
    output: implementation_plan
```

- [ ] **步骤 6：验证 YAML 语法**

运行：`python -c "import yaml; yaml.safe_load(open('workflows/project-development.yaml'))"`
预期：无报错

- [ ] **步骤 7：添加确认步骤**

```yaml
  - id: confirm_plan
    role: "project-manager"
    task: |
      向用户展示计划并等待确认：{{implementation_plan}}
      等待用户批准后继续
    output: user_confirmation
```

- [ ] **步骤 8：验证 YAML 语法**

运行：`python -c "import yaml; yaml.safe_load(open('workflows/project-development.yaml'))"`
预期：无报错

- [ ] **步骤 9：添加执行步骤**

```yaml
  - id: execute
    role: "project-manager"
    task: |
      使用 subagent-driven-development 技能执行计划
      流程：
        1. 每个任务分派实现子智能体
        2. 实现子智能体遵循 TDD（test-driven-development）
        3. 两阶段审查：先规格合规性，再代码质量
        4. 使用 requesting-code-review 进行代码审查
        5. 使用 verification-before-completion 验证每个任务
        6. 如果有独立任务，使用 dispatching-parallel-agents 并行执行
        7. 如果遇到 bug，使用 systematic-debugging 调试
      输出：完整的实现
    output: implementation_result
```

- [ ] **步骤 10：验证 YAML 语法**

运行：`python -c "import yaml; yaml.safe_load(open('workflows/project-development.yaml'))"`
预期：无报错

- [ ] **步骤 11：添加最终审查步骤**

```yaml
  - id: final_review
    role: "project-manager"
    task: |
      使用 finishing-a-development-branch 技能收尾
      最终验证所有功能
      向用户展示最终成果
    output: final_result
```

- [ ] **步骤 12：验证 YAML 语法**

运行：`python -c "import yaml; yaml.safe_load(open('workflows/project-development.yaml'))"`
预期：无报错

- [ ] **步骤 13：Commit**

```bash
git add workflows/project-development.yaml
git commit -m "feat: add project-development workflow"
```

---

## 任务 2：创建 quick-feature.yaml 快捷工作流

**文件：**
- 创建：`workflows/quick-feature.yaml`

- [ ] **步骤 1：编写 YAML 头部**

```yaml
name: "快捷功能开发"
agents_dir: ".trae/skills"
inputs:
  - name: requirement
    required: true
    description: "小型功能需求描述"
```

- [ ] **步骤 2：验证 YAML 语法**

运行：`python -c "import yaml; yaml.safe_load(open('workflows/quick-feature.yaml'))"`
预期：无报错

- [ ] **步骤 3：添加简化版步骤**

```yaml
steps:
  - id: brainstorm
    role: "project-manager"
    task: |
      使用 brainstorming 技能分析需求：{{requirement}}
      （针对小型功能，简化流程）
    output: spec_design

  - id: plan
    role: "project-manager"
    task: |
      使用 writing-plans 技能创建实现计划，基于：{{spec_design}}
    output: implementation_plan

  - id: confirm_plan
    role: "project-manager"
    task: |
      向用户展示计划并等待确认：{{implementation_plan}}
    output: user_confirmation

  - id: execute
    role: "project-manager"
    task: |
      使用 executing-plans 技能执行计划
      （简化版，同会话执行）
    output: implementation_result

  - id: final_review
    role: "project-manager"
    task: |
      使用 finishing-a-development-branch 技能收尾
    output: final_result
```

- [ ] **步骤 4：验证 YAML 语法**

运行：`python -c "import yaml; yaml.safe_load(open('workflows/quick-feature.yaml'))"`
预期：无报错

- [ ] **步骤 5：Commit**

```bash
git add workflows/quick-feature.yaml
git commit -m "feat: add quick-feature workflow"
```

---

## 任务 3：创建 README.md 使用说明

**文件：**
- 创建：`workflows/README.md`

- [ ] **步骤 1：编写标题和简介**

```markdown
# 智能体团队工作流

本目录包含用于 Trae CN 的 YAML 工作流，用于协调多智能体团队完成功能开发。

## 工作流列表

- `project-development.yaml` - 完整项目开发流程（推荐）
- `quick-feature.yaml` - 快捷功能开发（小型功能）
```

- [ ] **步骤 2：添加使用说明**

```markdown
## 使用方法

### 手动触发

```
运行工作流 workflows/project-development.yaml
需求：[你的需求描述]
```

### 工作流说明

#### project-development.yaml

完整的项目开发流程，包含：
1. brainstorming - 需求分析
2. writing-plans - 编写计划
3. 用户确认
4. subagent-driven-development - 子智能体驱动开发
5. finishing-a-development-branch - 收尾

#### quick-feature.yaml

简化版，针对小型功能，使用 executing-plans 而非 subagent-driven-development。
```

- [ ] **步骤 3：添加技能说明**

```markdown
## 集成的技能

- brainstorming - 需求分析
- writing-plans - 计划编写
- executing-plans - 执行计划
- subagent-driven-development - 子智能体驱动开发
- test-driven-development - 测试驱动开发
- systematic-debugging - 系统化调试
- requesting-code-review - 请求代码审查
- receiving-code-review - 接收代码审查
- verification-before-completion - 完成前验证
- dispatching-parallel-agents - 并行分派智能体
- finishing-a-development-branch - 收尾开发
```

- [ ] **步骤 4：验证 Markdown 语法（可选）**

运行：`python -c "import markdown; markdown.markdown(open('workflows/README.md').read())"`
预期：无报错

- [ ] **步骤 5：Commit**

```bash
git add workflows/README.md
git commit -m "docs: add workflows README"
```

---

## 自检

**1. 规格覆盖度：**
- ✅ 目标：创建智能体团队
- ✅ 背景：集成所有 superpowers 技能
- ✅ 架构：YAML 工作流
- ✅ 工作流设计：project-development.yaml 和 quick-feature.yaml
- ✅ 触发方式：README 中有说明
- ✅ 输出产物：docs/superpowers/specs/ 和 plans/
- ✅ 执行流程：工作流步骤覆盖
- ✅ 关键约束：工作流中包含确认关卡

**2. 占位符扫描：**
- ✅ 无"待定"、"TODO"
- ✅ 所有步骤有实际代码
- ✅ 所有命令具体

**3. 类型一致性：**
- ✅ YAML 结构一致
- ✅ 文件路径一致
