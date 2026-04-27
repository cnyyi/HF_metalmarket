# 应收账款页面重构设计

## 概述

将应收账款页面（`/finance/receivable`）从单列表视图重构为双选项卡视图，镜像应付账款页面的设计风格和交互模式，同时增加账龄分析功能。

## 现状

- 当前应收页面为单列表视图，无选项卡
- 应付页面已有完整的双选项卡设计（按客户显示/按明细显示）
- 后端 `receivable_repo.py` 已有 `get_list_by_customer()` 方法，但缺少路由端点
- 应收比应付多了品名/规格/数量/单价等字段，以及预收冲抵收款方式

## 目标

1. 页面布局与应付页面保持一致的双选项卡结构
2. 按客户显示增加账龄分段列（未到期/1-30天/31-60天/61-90天/90天以上）
3. 支持批量收款核销（现金+预收冲抵双模式）
4. 保留应收特有的品名/规格/数量/单价字段
5. 保留预收冲抵收款方式

## 页面结构

### 选项卡布局

```
┌─────────────────────────────────────────────────────┐
│ 应收账款                          [添加] [导出Excel] │
├─────────────────────────────────────────────────────┤
│ [搜索框] [状态筛选] [费用类型筛选] [搜索按钮]         │
├──────────────┬──────────────────────────────────────┤
│ 按客户显示    │ 按明细显示                            │
├──────────────┴──────────────────────────────────────┤
│ 表格内容区                                           │
│ 分页控件                                             │
└─────────────────────────────────────────────────────┘
```

### 按客户显示表格列

| 列名 | 宽度 | 说明 |
|------|------|------|
| 序号 | 50px | 行号 |
| 客户类型 | - | 徽章：内部商户/往来客户 |
| 客户名称 | - | 超链接→客户交易历史弹窗 |
| 应收合计 | 右对齐 | SUM(Amount) |
| 已收合计 | 右对齐 | SUM(PaidAmount) |
| 未收合计 | 右对齐 | SUM(RemainingAmount) |
| 未到期 | 右对齐 | DueDate >= 今天的 RemainingAmount 合计 |
| 1-30天 | 右对齐 | DueDate 在今天前1~30天的 RemainingAmount 合计 |
| 31-60天 | 右对齐 | DueDate 在今天前31~60天的 RemainingAmount 合计 |
| 61-90天 | 右对齐 | DueDate 在今天前61~90天的 RemainingAmount 合计 |
| 90天以上 | 右对齐 | DueDate 在今天前超过90天的 RemainingAmount 合计 |
| 记录数 | 居中 | COUNT(*) |
| 最早到期 | - | MIN(DueDate) |
| 操作 | 120px | [收款] [明细] |

账龄列样式：
- 未到期：绿色文字（`amount-paid` 类）
- 1-30天：黄色/默认文字
- 31-60天：橙色文字
- 61-90天：红色文字（`amount-unpaid` 类）
- 90天以上：深红色加粗

### 按明细显示表格列

| 列名 | 说明 |
|------|------|
| 序号 | 行号 |
| 客户类型 | 徽章 |
| 名称 | 超链接→客户交易历史弹窗 |
| 费用类型 | 字典表名称 |
| 品名 | ProductName（应收特有） |
| 应收金额 | Amount |
| 已收金额 | PaidAmount |
| 未收金额 | RemainingAmount |
| 到期日期 | DueDate |
| 状态 | 状态徽章 |
| 操作 | [收款] [删除] [详情] |

### 弹窗清单

| 弹窗 | 功能 | 与应付差异 |
|------|------|-----------|
| 添加应收 | 含品名/规格/数量/单价/单位 | 应付无品名字段 |
| 收款核销 | 现金收款 + 预收冲抵双模式 | 应付仅现金付款 |
| 客户明细 | 查看该客户所有应收明细 | 相同 |
| 批量收款 | 按客户批量收款（现金+预收冲抵） | 应付仅现金批量付款 |
| 删除确认 | 需填写删除原因 | 相同 |
| 详情 | 含品名/规格/数量/单价 + 关联合同/抄表 | 应付仅付款历史 |

## 后端变更

### 1. 新增路由

| URL | 方法 | 功能 |
|-----|------|------|
| `/finance/receivable/list_by_customer` | GET | 按客户汇总+账龄分段 |
| `/finance/receivable/batch_collect` | POST | 批量收款核销 |

### 2. 修改 receivable_repo.py — get_list_by_customer()

在现有 GROUP BY 查询中增加5个账龄分段 SUM 列：

```sql
SUM(CASE WHEN r.DueDate >= CAST(GETDATE() AS DATE) THEN r.RemainingAmount ELSE 0 END) AS NotDueAmount,
SUM(CASE WHEN r.DueDate >= DATEADD(DAY, -30, CAST(GETDATE() AS DATE)) AND r.DueDate < CAST(GETDATE() AS DATE) THEN r.RemainingAmount ELSE 0 END) AS Overdue1to30,
SUM(CASE WHEN r.DueDate >= DATEADD(DAY, -60, CAST(GETDATE() AS DATE)) AND r.DueDate < DATEADD(DAY, -30, CAST(GETDATE() AS DATE)) THEN r.RemainingAmount ELSE 0 END) AS Overdue31to60,
SUM(CASE WHEN r.DueDate >= DATEADD(DAY, -90, CAST(GETDATE() AS DATE)) AND r.DueDate < DATEADD(DAY, -60, CAST(GETDATE() AS DATE)) THEN r.RemainingAmount ELSE 0 END) AS Overdue61to90,
SUM(CASE WHEN r.DueDate < DATEADD(DAY, -90, CAST(GETDATE() AS DATE)) THEN r.RemainingAmount ELSE 0 END) AS OverdueOver90
```

汇总行也需要增加对应的 SUM 聚合。

### 3. 修改 receivable_service.py

新增方法：
- `get_receivables_by_customer(page, per_page, search, status)` — 调用 repo 的 `get_list_by_customer()`，格式化返回数据（含账龄分段）

### 4. 修改 finance_service.py

新增方法：
- `batch_collect_by_customer(customer_type, customer_id, total_amount, payment_method, transaction_date, description, created_by, account_id, collect_mode, prepayment_id)` — 批量收款核销事务

批量收款事务流程（现金模式）：
1. 查询该客户所有未收回应收，按到期日升序排列
2. 逐条执行与单条收款相同的5步联动：
   - INSERT CollectionRecord
   - UPDATE Receivable SET PaidAmount/RemainingAmount
   - UPDATE Receivable SET Status
   - INSERT CashFlow (Direction=N'收入')
   - UPDATE Account Balance

批量收款事务流程（预收冲抵模式）：
1. 查询该客户所有未收回应收，按到期日升序排列
2. 验证预收记录存在且余额充足
3. 逐条核销：
   - INSERT CollectionRecord
   - UPDATE Receivable SET PaidAmount/RemainingAmount/Status
4. 更新预收记录 AppliedAmount/RemainingAmount/Status
5. INSERT PrepaymentApply 记录

### 5. 修改 finance.py 路由

新增两个路由端点，参照 payable 的 `payable_list_by_customer` 和 `payable_batch_pay` 实现。

## 前端变更

### 重写 receivable.html

完全镜像 payable.html 的结构，主要差异：

1. **筛选栏**：保留费用类型筛选（应付没有）
2. **按客户表格**：增加5个账龄分段列
3. **按明细表格**：增加品名列
4. **收款弹窗**：双模式（现金+预收冲抵），复用现有 `collectModal` 的设计
5. **批量收款弹窗**：双模式+核销预览，复用现有 `batchPayModal` 的设计并增加预收冲抵选项
6. **添加弹窗**：保留品名/规格/数量/单价/单位字段
7. **详情弹窗**：保留关联合同/抄表数据展示

### JavaScript 函数映射

| 应付函数 | 应收函数 | 差异 |
|---------|---------|------|
| `loadPayablesByCustomer()` | `loadReceivablesByCustomer()` | 调用 `/receivable/list_by_customer` |
| `renderCustomerTable()` | `renderCustomerTable()` | 增加账龄列渲染 |
| `loadPayables()` | `loadReceivables()` | 调用 `/receivable/list` |
| `renderTable()` | `renderTable()` | 增加品名列 |
| `openPayModal()` | `openCollectModal()` | 双模式 |
| `openBatchPayModal()` | `openBatchCollectModal()` | 双模式 |
| `submitPay()` | `submitCollect()` | 双模式提交 |
| `submitBatchPay()` | `submitBatchCollect()` | 双模式提交 |
| `openDetailModal()` | `openDetailModal()` | 含合同/抄表数据 |

## 不做的事

- 不修改应付页面
- 不修改数据库表结构（账龄通过 SQL 动态计算）
- 不修改已有的收款/删除/详情等 API
- 不修改客户交易历史弹窗组件

## 文件变更清单

| 文件 | 操作 | 说明 |
|------|------|------|
| `templates/finance/receivable.html` | 重写 | 双选项卡+账龄+批量收款 |
| `app/routes/finance.py` | 修改 | 新增2个路由端点 |
| `app/repositories/receivable_repo.py` | 修改 | get_list_by_customer 增加账龄列 |
| `app/services/receivable_service.py` | 修改 | 新增 get_receivables_by_customer 方法 |
| `app/services/finance_service.py` | 修改 | 新增 batch_collect_by_customer 方法 |
