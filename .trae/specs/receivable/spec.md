# 应收账款模块 — 规格说明书（Spec）

## 文档信息

| 项目名称 | 宏发金属交易市场管理系统 |
| ---- | ---- |
| 模块名称 | 应收账款 |
| 文档版本 | V1.0 |
| 编写日期 | 2026-04-15 |
| 文档状态 | 工程版 |

---

## 1. 模块概述

### 1.1 业务定义

应收账款模块是财务管理子系统的核心组件，负责管理市场运营中所有应收款项的全生命周期，包括应收创建、收款核销、逾期跟踪、数据查询与导出。应收账款数据来源包括：

- **手动创建**：财务人员直接录入
- **合同自动生成**：合同创建时自动插入租金应收
- **水电费自动生成**：批量抄表保存时按商户合并生成水电费应收

### 1.2 目标用户

| 角色 | 权限代码 | 操作范围 |
|------|---------|---------|
| 管理员 | `finance_manage` | 全部操作 |
| 工作人员 | `finance_manage` | 全部操作 |
| 商户 | `contract_manage` | 仅查看自己的应收 |

### 1.3 当前完成度

| 功能 | 完成度 | 说明 |
|------|--------|------|
| 应收列表 | 90% | 分页+搜索+状态筛选，缺少费用类型筛选和日期范围筛选 |
| 新增应收 | 85% | 支持商户/客户双模式，费用类型已迁移字典表 |
| 收款核销 | 90% | 事务内四步联动（CollectionRecord+Receivable+Status+CashFlow） |
| 应收详情 | 80% | 基本信息展示+收款历史，路由层绕过Service层 |
| 删除应收 | 0% | 未实现 |
| 编辑应收 | 0% | 未实现 |
| 导出Excel | 0% | 按钮存在但功能未实现 |
| 逾期自动标记 | 0% | check_overdue()方法存在但无定时调度 |
| 逾期提醒 | 0% | 未实现 |

---

## 2. 数据模型

### 2.1 Receivable 表（应收账款主表）

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| ReceivableID | INT | PK IDENTITY(1,1) | 主键 |
| MerchantID | INT | NOT NULL FK→Merchant | 商户ID（兼容旧逻辑，CustomerType=Customer时等于CustomerID） |
| ExpenseTypeID | INT | NOT NULL | 费用类型ID（关联Sys_Dictionary.DictID或ExpenseType.ExpenseTypeID） |
| Amount | DECIMAL(12,2) | NOT NULL | 应收金额 |
| Description | NVARCHAR(500) | NULL | 备注 |
| DueDate | DATETIME | NOT NULL | 到期日期 |
| Status | NVARCHAR(50) | DEFAULT N'未付款' | 状态：未付款/部分付款/已付款/逾期 |
| PaidAmount | DECIMAL(12,2) | DEFAULT 0 | 已付金额 |
| RemainingAmount | DECIMAL(12,2) | NOT NULL | 剩余金额 |
| ReferenceID | INT | NULL | 关联业务ID（合同ID或抄表记录ID） |
| ReferenceType | NVARCHAR(50) | NULL | 关联类型：contract / utility_reading |
| CreateTime | DATETIME | DEFAULT GETDATE() | 创建时间 |
| UpdateTime | DATETIME | NULL | 更新时间 |
| CustomerType | NVARCHAR(20) | NULL | 客户类型：Merchant / Customer |
| CustomerID | INT | NULL | 客户ID（CustomerType=Customer时有效） |

### 2.2 CollectionRecord 表（收款记录表）

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| CollectionRecordID | INT | PK IDENTITY(1,1) | 主键 |
| ReceivableID | INT | NOT NULL FK→Receivable | 应收ID |
| MerchantID | INT | NOT NULL FK→Merchant | 商户ID |
| Amount | DECIMAL(12,2) | NOT NULL | 收款金额 |
| PaymentMethod | NVARCHAR(50) | NOT NULL | 付款方式 |
| TransactionDate | DATETIME | DEFAULT GETDATE() | 交易日期 |
| Description | NVARCHAR(500) | NULL | 备注 |
| CreatedBy | INT | NOT NULL FK→User | 操作人 |
| CreateTime | DATETIME | DEFAULT GETDATE() | 创建时间 |
| CustomerType | NVARCHAR(20) | NULL | 客户类型 |

### 2.3 ReceivableDetail 表（应收明细关联表）

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| DetailID | INT | PK IDENTITY(1,1) | 主键 |
| ReceivableID | INT | NOT NULL FK→Receivable | 应收ID |
| ReadingID | INT | NOT NULL FK→UtilityReading | 抄表记录ID |
| CreateTime | DATETIME | DEFAULT GETDATE() | 创建时间 |

约束：`UQ_ReceivableDetail_Unique (ReceivableID, ReadingID)`

### 2.4 CashFlow 表（现金流水表）

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| CashFlowID | INT | PK IDENTITY(1,1) | 主键 |
| Direction | NVARCHAR(20) | NOT NULL | 方向：收入/支出 |
| Amount | DECIMAL(12,2) | NOT NULL | 金额 |
| TransactionDate | DATETIME | NOT NULL | 交易日期 |
| PaymentMethod | NVARCHAR(50) | NULL | 付款方式 |
| ReferenceID | INT | NULL | 关联ID |
| ReferenceType | NVARCHAR(50) | NULL | 关联类型 |
| Description | NVARCHAR(500) | NULL | 描述 |
| CreatedBy | INT | NOT NULL FK→User | 操作人 |
| CreateTime | DATETIME | DEFAULT GETDATE() | 创建时间 |

### 2.5 状态流转

```
未付款 ──收款(部分)──→ 部分付款 ──收款(全额)──→ 已付款
  │                                              ↑
  └──到期日<今天且未付──→ 逾期 ──收款(全额)──→ 已付款
```

---

## 3. API 接口规格

### 3.1 现有接口

| URL | 方法 | 功能 | 状态 |
|-----|------|------|------|
| `/finance/receivable` | GET | 渲染页面 | ✅ |
| `/finance/receivable/list` | GET | 分页列表 | ✅ |
| `/finance/receivable/create` | POST | 新增应收 | ✅ |
| `/finance/receivable/expense_types` | GET | 获取费用类型 | ✅ |
| `/finance/receivable/search_merchants` | GET | 搜索商户 | ✅ |
| `/finance/receivable/search_customers` | GET | 搜索客户 | ✅ |
| `/finance/receivable/collect/<id>` | POST | 收款核销 | ✅ |
| `/finance/receivable/detail/<id>` | GET | 应收详情 | ✅ |

### 3.2 待实现接口

| URL | 方法 | 功能 | 优先级 |
|-----|------|------|--------|
| `/finance/receivable/update/<id>` | POST | 编辑应收 | P1 |
| `/finance/receivable/delete/<id>` | POST | 删除应收 | P1 |
| `/finance/receivable/export` | GET | 导出Excel | P2 |
| `/finance/receivable/overdue_check` | POST | 手动触发逾期检查 | P2 |

### 3.3 接口详细规格

#### GET `/finance/receivable/list`

请求参数：

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| page | int | 否 | 页码，默认1 |
| per_page | int | 否 | 每页条数，默认10 |
| search | string | 否 | 搜索关键词（商户名/客户名） |
| status | string | 否 | 状态筛选：未付款/部分付款/已付款/逾期 |
| expense_type_id | int | 否 | 费用类型ID筛选（新增） |
| date_from | string | 否 | 到期日期起始（新增） |
| date_to | string | 否 | 到期日期结束（新增） |

响应格式：

```json
{
  "success": true,
  "data": {
    "items": [
      {
        "receivable_id": 1,
        "customer_name": "张三",
        "customer_type": "Merchant",
        "expense_type_name": "租金",
        "amount": 50000.00,
        "paid_amount": 0,
        "remaining_amount": 50000.00,
        "due_date": "2026-05-01",
        "status": "未付款",
        "description": "第1期第1年租金",
        "reference_type": "contract",
        "create_time": "2026-04-15 10:00:00"
      }
    ],
    "total": 100,
    "page": 1,
    "per_page": 10,
    "total_pages": 10
  }
}
```

#### POST `/finance/receivable/update/<id>`

请求体：

```json
{
  "amount": 50000.00,
  "due_date": "2026-05-01",
  "description": "备注",
  "expense_type_id": 1
}
```

业务规则：
- 仅允许编辑 `未付款` 状态的应收
- `部分付款` 和 `已付款` 状态不允许编辑金额
- 已由系统自动生成的应收（ReferenceType=contract/utility_reading）编辑时需提示确认

#### POST `/finance/receivable/delete/<id>`

业务规则：
- 仅允许删除 `未付款` 状态的应收
- `部分付款` 状态需先撤销收款才能删除
- `已付款` 状态不允许删除
- 删除时需二次确认
- 系统自动生成的应收删除时需提示"该应收由系统自动生成，删除后不影响原始业务数据"

#### GET `/finance/receivable/export`

请求参数：同 list 接口的筛选参数

响应：Excel 文件下载

---

## 4. 业务规则

### 4.1 应收创建规则

| 规则编号 | 规则描述 |
|---------|---------|
| R-01 | 手动创建应收时，CustomerType 默认为 Merchant |
| R-02 | CustomerType=Merchant 时，MerchantID 和 CustomerID 均设为商户ID |
| R-03 | CustomerType=Customer 时，MerchantID 设为 CustomerID（兼容外键约束） |
| R-04 | Amount 必须 > 0 |
| R-05 | DueDate 必须是有效日期 |
| R-06 | ExpenseTypeID 必须是有效的费用类型 |
| R-07 | 创建时 RemainingAmount = Amount, PaidAmount = 0, Status = '未付款' |

### 4.2 收款核销规则

| 规则编号 | 规则描述 |
|---------|---------|
| R-08 | 收款金额 ≤ RemainingAmount |
| R-09 | 收款金额必须 > 0 |
| R-10 | 收款必须在事务内完成四步联动：CollectionRecord + Receivable更新 + Status更新 + CashFlow |
| R-11 | 收款后 RemainingAmount=0 时 Status 自动变为 '已付款' |
| R-12 | 收款后 RemainingAmount>0 时 Status 自动变为 '部分付款' |
| R-13 | PaymentMethod 必填 |

### 4.3 逾期规则

| 规则编号 | 规则描述 |
|---------|---------|
| R-14 | DueDate < 当前日期 且 Status='未付款' 时标记为 '逾期' |
| R-15 | 部分付款的应收不自动标记逾期 |
| R-16 | 逾期检查可手动触发或定时执行 |

### 4.4 删除规则

| 规则编号 | 规则描述 |
|---------|---------|
| R-17 | 仅 Status='未付款' 的应收可删除 |
| R-18 | 已有收款记录的应收不允许删除 |
| R-19 | 系统自动生成的应收删除时需额外确认 |

---

## 5. 已知问题与技术债

| 编号 | 问题 | 影响 | 优先级 |
|------|------|------|--------|
| T-01 | `ReceivableService.pay()` 方法已废弃但仍保留 | 代码混乱，可能被误调用 | P1 |
| T-02 | `ReceivableService.get_expense_types()` 已废弃但仍保留 | 查询旧表，数据不准确 | P1 |
| T-03 | 详情路由直接访问 repo 层 | 违反分层架构 | P2 |
| T-04 | MerchantID NOT NULL 外键约束与 CustomerType=Customer 冲突 | 插入Customer类型应收时需hack | P2 |
| T-05 | CollectionRecord.MerchantID NOT NULL 外键约束 | Customer类型收款时可能失败 | P2 |
| T-06 | ReceivableDetail 表不在主初始化流程中 | 新环境部署可能遗漏 | P3 |
| T-07 | 导出Excel功能未实现 | 用户体验缺失 | P2 |
| T-08 | 逾期状态无自动更新机制 | 数据不准确 | P2 |

---

## 6. 非功能需求

| 需求 | 说明 |
|------|------|
| 事务完整性 | 收款核销必须在同一数据库事务内完成 |
| 数据一致性 | 应收金额 = 已付金额 + 剩余金额 |
| 权限控制 | 所有写操作需 `finance_manage` 权限 |
| 操作审计 | 收款记录需记录操作人（CreatedBy） |
| 性能要求 | 列表查询响应时间 < 2秒（1000条数据内） |
| 并发安全 | 同一应收不允许同时收款（乐观锁或行锁） |
