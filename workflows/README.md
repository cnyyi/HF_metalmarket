# 智能体团队工作流

本目录包含用于 Trae CN 的 YAML 工作流，用于协调多智能体团队完成功能开发。

## 工作流列表

- `project-development.yaml` - 完整项目开发流程（推荐）
- `quick-feature.yaml` - 快捷功能开发（小型功能）

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
