# &#x20;

# HF_metalmarket V3 Agent 实现方案（供 Trae_CN 自动开发）

## 一、目标说明

本方案用于指导将当前系统升级为 **V3智能分析Agent系统**，实现以下能力：

* 多步骤推理（Multi-step reasoning）
* 自动生成分析报告
* 自动生成图表数据
* 风险识别与预警
* 可扩展的业务分析架构

---

## 二、总体架构

```
用户输入
   ↓
Planner（任务拆解）
   ↓
Executor（逐步执行）
   ↓
Memory（存储中间结果）
   ↓
Chart Builder（图表生成）
   ↓
Risk Engine（风险识别）
   ↓
Report Builder（报告生成）
   ↓
返回结果（JSON）

```

---

## 三、目录结构

```
HF_metalmarket/
├── app.py
├── services/
│   └── db.py
├── agent/
│   ├── agent_service.py
│   ├── planner.py
│   ├── executor.py
│   ├── memory.py
│   ├── tools.py
│   ├── chart_builder.py
│   ├── risk_engine.py
│   ├── report_builder.py
│   └── prompts.py
└── routes/
    └── agent_route.py

```

---

## 四、核心模块说明

---

### 1️⃣ Planner（任务拆解）

#### 作用

将用户自然语言转为执行计划（Plan JSON）

#### 输出格式

```
{
  "steps": [
    {
      "id": "step1",
      "tool": "get_payable_this_month",
      "args": {}
    },
    {
      "id": "step2",
      "tool": "get_fee_breakdown",
      "args": {}
    },
    {
      "id": "step3",
      "tool": "analyze_abnormal",
      "args": {
        "total": "$step1.amount",
        "breakdown": "$step2"
      }
    }
  ]
}

```

#### 实现方式

优先使用规则（稳定）：

* 包含“应付” → 调用账款分析流程
* 包含“合同” → 调用合同查询流程

后期可替换为 LLM Planner

---

### 2️⃣ Executor（执行器）

#### 作用

逐步执行 Plan

#### 核心能力

* 工具调用（Tool Map）
* 参数解析（支持 `$step1.amount`）
* 自动注入权限（merchant_id）
* 结果写入 Memory

---

### 3️⃣ Memory（上下文存储）

#### 功能

* 存储每一步执行结果
* 支持变量引用

#### 示例

```
memory = {
  "step1": {"amount": 120000},
  "step2": {"rent": 80000}
}

```

---

### 4️⃣ Tools（业务函数层）

#### 原则

* 不允许 LLM 直接写 SQL
* 所有数据库访问必须封装为函数

#### 示例

```
def get_payable_this_month(merchant_id):
    # 查询应付账款
    return {"amount": 120000}

```

#### 必备工具

* get_payable_this_month
* get_fee_breakdown
* get_expiring_contracts
* analyze_abnormal

---

### 5️⃣ Chart Builder（图表构建）

#### 作用

自动生成前端可用图表数据

#### 输出格式

```
{
  "type": "pie",
  "title": "费用构成",
  "data": [
    {"name": "租金", "value": 80000}
  ]
}

```

#### 规则

* 存在费用结构 → 饼图
* 存在时间序列 → 折线图（后续扩展）

---

### 6️⃣ Risk Engine（风险引擎）

#### 作用

自动识别业务风险

#### 示例规则

| 类型条件等级 |           |       |
| ------ | --------- | ----- |
| 合同风险   | 合同即将到期    | 高     |
| 成本风险   | 单项占比 >70% | 中     |
| 资金风险   | 应收过高      | 高（后续） |

#### 输出

```
[
  {
    "level": "high",
    "message": "3个合同即将到期"
  }
]

```

---

### 7️⃣ Report Builder（报告生成）

#### 输出结构

```
【总体情况】
【费用结构】
【风险提示】
【建议措施】

```

#### 示例

```
【总体情况】本月应付 120000 元
【费用结构】
- 租金：80000
- 电费：20000

【风险提示】
- 租金占比过高

【建议措施】
- 优化成本结构

```

---

## 五、接口设计

---

### POST /agent/query

#### 请求

```
{
  "query": "本月应付账款情况如何？"
}

```

#### 返回

```
{
  "report": "...",
  "chart": {...},
  "risks": [...],
  "steps": [...]
}

```

---

## 六、前端对接规范

---

### 1️⃣ 报告展示

直接文本展示：

```
report

```

---

### 2️⃣ 图表展示（ECharts）

```
option = {
  series: [{
    type: chart.type,
    data: chart.data
  }]
}

```

---

### 3️⃣ 风险提示

```
risks.map(r => showAlert(r.message))

```

---

## 七、开发步骤（给 Trae_CN）

---

### 第一步：创建 agent 模块

* 创建所有 agent/*.py 文件
* 建立基础结构

---

### 第二步：实现 Tools

* 替换为真实 SQL
* 接入现有数据库

---

### 第三步：实现 Executor + Memory

* 支持变量引用
* 支持权限注入

---

### 第四步：实现 Chart + Risk + Report

* 按规则生成结构化数据

---

### 第五步：接入 Flask

* 新增 `/agent/query` 接口

---

### 第六步：联调测试

测试以下问题：

* 本月应付是多少？
* 合同是否到期？
* 费用结构如何？

---

## 八、扩展方向（后续）

---

### V3.5

* 趋势分析（同比/环比）
* 多商户对比

---

### V4

* 自动生成 PDF 报告
* 定时推送（微信/短信）
* AI预测（收入预测）

---

## 九、关键设计原则

---

### ❗ 1. LLM 不直接访问数据库

### ❗ 2. 所有数据必须可解释

### ❗ 3. Agent 必须可控（非黑盒）

### ❗ 4. 先规则，后AI（逐步升级）

---

## 十、最终效果

系统将从：

👉 管理系统

升级为：

👉 **AI经营分析系统**

具备：

* 自动分析能力
* 决策辅助能力
* 风险预警能力

---

## 完成标准（验收）

* 能返回报告 + 图表 + 风险
* 支持多步骤查询
* 无SQL直接暴露
* 响应稳定

---

（文档结束）

  （供 Trae_CN 自动开发）

## 一、目标说明

本方案用于指导将当前系统升级为 **V3智能分析Agent系统**，实现以下能力：

* 多步骤推理（Multi-step reasoning）
* 自动生成分析报告
* 自动生成图表数据
* 风险识别与预警
* 可扩展的业务分析架构

---

## 二、总体架构

```
用户输入
   ↓
Planner（任务拆解）
   ↓
Executor（逐步执行）
   ↓
Memory（存储中间结果）
   ↓
Chart Builder（图表生成）
   ↓
Risk Engine（风险识别）
   ↓
Report Builder（报告生成）
   ↓
返回结果（JSON）
```

---

## 三、目录结构

```
HF_metalmarket/
├── app.py
├── services/
│   └── db.py
├── agent/
│   ├── agent_service.py
│   ├── planner.py
│   ├── executor.py
│   ├── memory.py
│   ├── tools.py
│   ├── chart_builder.py
│   ├── risk_engine.py
│   ├── report_builder.py
│   └── prompts.py
└── routes/
    └── agent_route.py
```

---

## 四、核心模块说明

---

### 1️⃣ Planner（任务拆解）

#### 作用

将用户自然语言转为执行计划（Plan JSON）

#### 输出格式

```json
{
  "steps": [
    {
      "id": "step1",
      "tool": "get_payable_this_month",
      "args": {}
    },
    {
      "id": "step2",
      "tool": "get_fee_breakdown",
      "args": {}
    },
    {
      "id": "step3",
      "tool": "analyze_abnormal",
      "args": {
        "total": "$step1.amount",
        "breakdown": "$step2"
      }
    }
  ]
}
```

#### 实现方式

优先使用规则（稳定）：

* 包含“应付” → 调用账款分析流程
* 包含“合同” → 调用合同查询流程

后期可替换为 LLM Planner

---

### 2️⃣ Executor（执行器）

#### 作用

逐步执行 Plan

#### 核心能力

* 工具调用（Tool Map）
* 参数解析（支持 `$step1.amount`）
* 自动注入权限（merchant_id）
* 结果写入 Memory

---

### 3️⃣ Memory（上下文存储）

#### 功能

* 存储每一步执行结果
* 支持变量引用

#### 示例

```python
memory = {
  "step1": {"amount": 120000},
  "step2": {"rent": 80000}
}
```

---

### 4️⃣ Tools（业务函数层）

#### 原则

* 不允许 LLM 直接写 SQL
* 所有数据库访问必须封装为函数

#### 示例

```python
def get_payable_this_month(merchant_id):
    # 查询应付账款
    return {"amount": 120000}
```

#### 必备工具

* get_payable_this_month
* get_fee_breakdown
* get_expiring_contracts
* analyze_abnormal

---

### 5️⃣ Chart Builder（图表构建）

#### 作用

自动生成前端可用图表数据

#### 输出格式

```json
{
  "type": "pie",
  "title": "费用构成",
  "data": [
    {"name": "租金", "value": 80000}
  ]
}
```

#### 规则

* 存在费用结构 → 饼图
* 存在时间序列 → 折线图（后续扩展）

---

### 6️⃣ Risk Engine（风险引擎）

#### 作用

自动识别业务风险

#### 示例规则

| 类型   | 条件        | 等级    |
| ---- | --------- | ----- |
| 合同风险 | 合同即将到期    | 高     |
| 成本风险 | 单项占比 >70% | 中     |
| 资金风险 | 应收过高      | 高（后续） |

#### 输出

```json
[
  {
    "level": "high",
    "message": "3个合同即将到期"
  }
]
```

---

### 7️⃣ Report Builder（报告生成）

#### 输出结构

```
【总体情况】
【费用结构】
【风险提示】
【建议措施】
```

#### 示例

```
【总体情况】本月应付 120000 元
【费用结构】
- 租金：80000
- 电费：20000

【风险提示】
- 租金占比过高

【建议措施】
- 优化成本结构
```

---

## 五、接口设计

---

### POST /agent/query

#### 请求

```json
{
  "query": "本月应付账款情况如何？"
}
```

#### 返回

```json
{
  "report": "...",
  "chart": {...},
  "risks": [...],
  "steps": [...]
}
```

---

## 六、前端对接规范

---

### 1️⃣ 报告展示

直接文本展示：

```
report
```

---

### 2️⃣ 图表展示（ECharts）

```js
option = {
  series: [{
    type: chart.type,
    data: chart.data
  }]
}
```

---

### 3️⃣ 风险提示

```js
risks.map(r => showAlert(r.message))
```

---

## 七、开发步骤（给 Trae_CN）

---

### 第一步：创建 agent 模块

* 创建所有 agent/*.py 文件
* 建立基础结构

---

### 第二步：实现 Tools

* 替换为真实 SQL
* 接入现有数据库

---

### 第三步：实现 Executor + Memory

* 支持变量引用
* 支持权限注入

---

### 第四步：实现 Chart + Risk + Report

* 按规则生成结构化数据

---

### 第五步：接入 Flask

* 新增 `/agent/query` 接口

---

### 第六步：联调测试

测试以下问题：

* 本月应付是多少？
* 合同是否到期？
* 费用结构如何？

---

## 八、扩展方向（后续）

---

### V3.5

* 趋势分析（同比/环比）
* 多商户对比

---

### V4

* 自动生成 PDF 报告
* 定时推送（微信/短信）
* AI预测（收入预测）

---

## 九、关键设计原则

---

### ❗ 1. LLM 不直接访问数据库

### ❗ 2. 所有数据必须可解释

### ❗ 3. Agent 必须可控（非黑盒）

### ❗ 4. 先规则，后AI（逐步升级）

---

## 十、最终效果

系统将从：

👉 管理系统

升级为：

👉 **AI经营分析系统**

具备：

* 自动分析能力
* 决策辅助能力
* 风险预警能力

---

## 完成标准（验收）

* 能返回报告 + 图表 + 风险
* 支持多步骤查询
* 无SQL直接暴露
* 响应稳定

---

（文档结束）
