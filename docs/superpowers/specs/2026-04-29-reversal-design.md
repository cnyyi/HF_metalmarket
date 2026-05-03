# 收款/付款冲销功能设计

## 1. 背景

当前系统中收款核销和付款核销操作一旦执行就不可逆。如果操作人员输入错误（如金额错误、选错客户、选错付款方式等），无法撤销，只能手动补录反向记录，容易造成数据不一致。

本设计为收款核销和付款核销增加**红字冲回**机制，允许7天内撤销操作。

## 2. 需求

- 支持收款核销的冲销（撤销收款）
- 支持付款核销的冲销（撤销付款）
- 冲销时间限制：操作后7天内
- 冲销必须填写原因
- 审计链完整：原记录 + 冲销记录 + 冲销原因均可追溯
- 新增"已收账款管理"和"已付账款管理"独立页面

## 3. 数据库设计

### 3.1 新建 ReversalRecord 表

```sql
CREATE TABLE ReversalRecord (
    ReversalID         INT IDENTITY(1,1) PRIMARY KEY,
    OriginalType       NVARCHAR(50) NOT NULL,        -- 'collection_record' 或 'payment_record'
    OriginalID         INT NOT NULL,                  -- 原 CollectionRecordID 或 PaymentRecordID
    ReversalAmount     DECIMAL(18,2) NOT NULL,        -- 冲销金额（正数）
    Reason             NVARCHAR(500) NOT NULL,        -- 冲销原因
    ReversalCashFlowID INT NULL,                      -- 冲销产生的反向 CashFlowID
    CreatedBy          INT NOT NULL,
    CreateTime         DATETIME DEFAULT GETDATE(),

    CONSTRAINT FK_Reversal_CreatedBy FOREIGN KEY (CreatedBy) REFERENCES [User](UserID)
);
```

### 3.2 CollectionRecord 表增加字段

```sql
ALTER TABLE CollectionRecord ADD IsReversed BIT DEFAULT 0;
ALTER TABLE CollectionRecord ADD ReversalID INT NULL;
```

### 3.3 PaymentRecord 表增加字段

```sql
ALTER TABLE PaymentRecord ADD IsReversed BIT DEFAULT 0;
ALTER TABLE PaymentRecord ADD ReversalID INT NULL;
```

## 4. 冲销业务逻辑

### 4.1 收款冲销（reverse_collection）

**前置校验**：
1. 原 CollectionRecord 存在且 `IsReversed = 0`
2. 原记录创建时间在7天内
3. 冲销金额 ≤ 原收款金额
4. 冲销后 Receivable 的 RemainingAmount 不超过原 Amount（防止超额恢复）

**操作步骤（单事务）**：

| 步骤 | 操作 | 说明 |
|------|------|------|
| 1 | INSERT ReversalRecord | 记录冲销信息（OriginalType='collection_record', OriginalID=原记录ID, ReversalAmount, Reason） |
| 2 | UPDATE CollectionRecord SET IsReversed=1, ReversalID=? | 标记原记录已冲销 |
| 3 | UPDATE Receivable SET PaidAmount -= amount, RemainingAmount += amount | 恢复应收金额 |
| 4 | UPDATE Receivable SET Status = 重新计算 | RemainingAmount >= Amount-0.01 → '未付款'；0.01 < RemainingAmount < Amount → '部分付款' |
| 5 | INSERT CashFlow（反向） | Direction='支出'，Amount=冲销金额，ExpenseTypeID=原Receivable的ExpenseTypeID，ReferenceType='reversal'，ReferenceID=ReversalID |
| 6 | UPDATE ReversalRecord SET ReversalCashFlowID=? | 关联冲销 CashFlow |
| 7 | UPDATE Account SET Balance -= amount | 恢复账户余额 |

### 4.2 付款冲销（reverse_payment）

**前置校验**：
1. 原 PaymentRecord 存在且 `IsReversed = 0`
2. 原记录创建时间在7天内
3. 冲销金额 ≤ 原付款金额
4. 冲销后 Account 余额不会变为负数

**操作步骤（单事务）**：

| 步骤 | 操作 | 说明 |
|------|------|------|
| 1 | INSERT ReversalRecord | 记录冲销信息（OriginalType='payment_record', OriginalID=原记录ID, ReversalAmount, Reason） |
| 2 | UPDATE PaymentRecord SET IsReversed=1, ReversalID=? | 标记原记录已冲销 |
| 3 | UPDATE Payable SET PaidAmount -= amount, RemainingAmount += amount | 恢复应付金额 |
| 4 | UPDATE Payable SET Status = 重新计算 | 同收款冲销的状态恢复逻辑 |
| 5 | INSERT CashFlow（反向） | Direction='收入'，Amount=冲销金额，ExpenseTypeID=原Payable的ExpenseTypeID，ReferenceType='reversal'，ReferenceID=ReversalID |
| 6 | UPDATE ReversalRecord SET ReversalCashFlowID=? | 关联冲销 CashFlow |
| 7 | UPDATE Account SET Balance += amount | 恢复账户余额 |

### 4.3 状态恢复逻辑

```
如果 RemainingAmount >= Amount - 0.01 → Status = '未付款'
如果 0.01 < RemainingAmount < Amount  → Status = '部分付款'
```

## 5. 路由设计

| 路由 | 方法 | 说明 | 权限 |
|------|------|------|------|
| `/finance/collection` | GET | 已收账款页面 | `finance_view` |
| `/finance/collection/list` | GET | 已收账款列表API | `finance_view` |
| `/finance/collection/reverse/<int:record_id>` | POST | 冲销收款记录 | `finance_create` |
| `/finance/payment` | GET | 已付账款页面 | `finance_view` |
| `/finance/payment/list` | GET | 已付账款列表API | `finance_view` |
| `/finance/payment/reverse/<int:record_id>` | POST | 冲销付款记录 | `finance_create` |

## 6. 前端设计

### 6.1 已收账款管理页面（/finance/collection）

**列表字段**：

| 列 | 说明 |
|----|------|
| 收款单号 | CollectionRecordID |
| 客户类型 | CustomerType |
| 客户名称 | 关联查询 |
| 费用类型 | 关联 Receivable → ExpenseTypeID → Sys_Dictionary |
| 收款金额 | Amount |
| 付款方式 | PaymentMethod |
| 收款日期 | TransactionDate |
| 状态 | 正常 / 已冲销 |
| 操作人 | CreatedBy → User.RealName |
| 操作 | 冲销（仅7天内且未冲销的显示） |

**筛选条件**：客户名称搜索、付款方式、日期范围、状态（正常/已冲销）

**冲销操作**：点击"冲销"按钮 → 弹出模态窗口 → 显示原记录详情 → 输入冲销原因 → 确认冲销

### 6.2 已付账款管理页面（/finance/payment）

**列表字段**：

| 列 | 说明 |
|----|------|
| 付款单号 | PaymentRecordID |
| 供应商 | VendorName |
| 客户类型 | CustomerType |
| 客户名称 | 关联查询 |
| 费用类型 | 关联 Payable → ExpenseTypeID → Sys_Dictionary |
| 付款金额 | Amount |
| 付款方式 | PaymentMethod |
| 付款日期 | TransactionDate |
| 状态 | 正常 / 已冲销 |
| 操作人 | CreatedBy → User.RealName |
| 操作 | 冲销（仅7天内且未冲销的显示） |

### 6.3 冲销模态窗口

- 显示原记录详情（金额、客户、日期等）
- 冲销原因（必填，textarea）
- 警告提示：冲销后金额将恢复到原应收/应付记录
- 确认按钮（二次确认）

### 6.4 侧边栏菜单

```
财务管理
├── 应收账款      /finance/receivable
├── 已收账款      /finance/collection     ← 新增
├── 应付账款      /finance/payable
├── 已付账款      /finance/payment        ← 新增
├── 现金流水      /finance/cash_flow
├── 预收/预付     /finance/prepayment
├── 押金管理      /finance/deposit
├── 账户管理      /finance/account
└── 直接记账      /finance/direct_entry
```

## 7. 权限迁移

需要在 CRUD 权限迁移脚本中注册以下菜单和权限：

- 已收账款（collection）：view / create（冲销用create权限）
- 已付账款（payment）：view / create（冲销用create权限）
