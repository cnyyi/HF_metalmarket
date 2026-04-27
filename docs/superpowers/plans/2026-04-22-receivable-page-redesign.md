# 应收账款页面重构 实现计划

> **面向 AI 代理的工作者：** 必需子技能：使用 superpowers:subagent-driven-development（推荐）或 superpowers:executing-plans 逐任务实现此计划。步骤使用复选框（`- [ ]`）语法来跟踪进度。

**目标：** 将应收账款页面从单列表视图重构为双选项卡视图（按客户显示+按明细显示），镜像应付页面设计，增加账龄分析列和批量收款功能。

**架构：** Routes → Services → Repository 三层分离，前端使用 Bootstrap 5 选项卡 + jQuery Ajax，账龄通过 SQL CASE WHEN 动态计算。

**技术栈：** Flask + pyodbc (SQL Server) + Bootstrap 5 + jQuery

---

## 文件结构

| 文件 | 操作 | 职责 |
|------|------|------|
| `app/repositories/receivable_repo.py` | 修改 | get_list_by_customer 增加5个账龄分段 SUM 列 |
| `app/services/receivable_service.py` | 修改 | 新增 get_receivables_by_customer 方法 |
| `app/services/finance_service.py` | 修改 | 新增 batch_collect_by_customer 方法 |
| `app/routes/finance.py` | 修改 | 新增2个路由端点 |
| `templates/finance/receivable.html` | 重写 | 双选项卡+账龄+批量收款UI |

---

### 任务 1：修改 receivable_repo.py — 增加账龄分段列

**文件：**
- 修改：`app/repositories/receivable_repo.py:218-295`（`get_list_by_customer` 方法）

- [ ] **步骤 1：修改 get_list_by_customer 方法的 base_query，增加5个账龄分段 SUM 列**

在 `base_query` 的 SELECT 部分增加账龄分段列，修改后的完整方法如下：

```python
def get_list_by_customer(self, page=1, per_page=10, search=None, status=None):
    with DBConnection() as conn:
        cursor = conn.cursor()

        base_query = f"""
            SELECT
                r.CustomerType,
                r.CustomerID,
                {self._CUSTOMER_EXPR} AS CustomerName,
                COUNT(*) AS RecordCount,
                SUM(r.Amount) AS TotalAmount,
                SUM(r.PaidAmount) AS TotalPaid,
                SUM(r.RemainingAmount) AS TotalRemaining,
                SUM(CASE WHEN r.DueDate >= CAST(GETDATE() AS DATE) THEN r.RemainingAmount ELSE 0 END) AS NotDueAmount,
                SUM(CASE WHEN r.DueDate >= DATEADD(DAY, -30, CAST(GETDATE() AS DATE)) AND r.DueDate < CAST(GETDATE() AS DATE) THEN r.RemainingAmount ELSE 0 END) AS Overdue1to30,
                SUM(CASE WHEN r.DueDate >= DATEADD(DAY, -60, CAST(GETDATE() AS DATE)) AND r.DueDate < DATEADD(DAY, -30, CAST(GETDATE() AS DATE)) THEN r.RemainingAmount ELSE 0 END) AS Overdue31to60,
                SUM(CASE WHEN r.DueDate >= DATEADD(DAY, -90, CAST(GETDATE() AS DATE)) AND r.DueDate < DATEADD(DAY, -60, CAST(GETDATE() AS DATE)) THEN r.RemainingAmount ELSE 0 END) AS Overdue61to90,
                SUM(CASE WHEN r.DueDate < DATEADD(DAY, -90, CAST(GETDATE() AS DATE)) THEN r.RemainingAmount ELSE 0 END) AS OverdueOver90,
                MIN(r.DueDate) AS EarliestDueDate
            FROM Receivable r
            {self._BASE_JOINS}
            WHERE r.IsActive = 1
        """
```

- [ ] **步骤 2：修改 sum_query，增加账龄分段汇总**

```python
        sum_query = f"""
            SELECT ISNULL(SUM(sub.TotalAmount), 0), ISNULL(SUM(sub.TotalPaid), 0),
                   ISNULL(SUM(sub.TotalRemaining), 0), ISNULL(SUM(sub.RecordCount), 0),
                   ISNULL(SUM(sub.NotDueAmount), 0), ISNULL(SUM(sub.Overdue1to30), 0),
                   ISNULL(SUM(sub.Overdue31to60), 0), ISNULL(SUM(sub.Overdue61to90), 0),
                   ISNULL(SUM(sub.OverdueOver90), 0)
            FROM (
                SELECT
                    COUNT(*) AS RecordCount,
                    SUM(r.Amount) AS TotalAmount,
                    SUM(r.PaidAmount) AS TotalPaid,
                    SUM(r.RemainingAmount) AS TotalRemaining,
                    SUM(CASE WHEN r.DueDate >= CAST(GETDATE() AS DATE) THEN r.RemainingAmount ELSE 0 END) AS NotDueAmount,
                    SUM(CASE WHEN r.DueDate >= DATEADD(DAY, -30, CAST(GETDATE() AS DATE)) AND r.DueDate < CAST(GETDATE() AS DATE) THEN r.RemainingAmount ELSE 0 END) AS Overdue1to30,
                    SUM(CASE WHEN r.DueDate >= DATEADD(DAY, -60, CAST(GETDATE() AS DATE)) AND r.DueDate < DATEADD(DAY, -30, CAST(GETDATE() AS DATE)) THEN r.RemainingAmount ELSE 0 END) AS Overdue31to60,
                    SUM(CASE WHEN r.DueDate >= DATEADD(DAY, -90, CAST(GETDATE() AS DATE)) AND r.DueDate < DATEADD(DAY, -60, CAST(GETDATE() AS DATE)) THEN r.RemainingAmount ELSE 0 END) AS Overdue61to90,
                    SUM(CASE WHEN r.DueDate < DATEADD(DAY, -90, CAST(GETDATE() AS DATE)) THEN r.RemainingAmount ELSE 0 END) AS OverdueOver90
                FROM Receivable r
                {self._BASE_JOINS}
                WHERE r.IsActive = 1
                {extra_where}
                GROUP BY r.CustomerType, r.CustomerID, {self._CUSTOMER_EXPR}
            ) sub
        """
```

注意：`sum_query` 的定义需要移到 `extra_where` 变量赋值之后，因为它依赖 `extra_where`。当前代码中 `sum_query` 的位置需要调整。

- [ ] **步骤 3：调整代码顺序，确保 sum_query 在 extra_where 之后定义**

将 `sum_query` 的定义从当前位置移到 `extra_where = ""` 和 `if conditions:` 块之后。同时修改 `sum_row` 的返回，现在包含9个值而非4个。

- [ ] **步骤 4：验证修改**

启动 Flask 应用，访问 `http://127.0.0.1:5000/finance/receivable`，确认现有页面仍正常加载。

---

### 任务 2：修改 receivable_service.py — 增加 get_receivables_by_customer 方法

**文件：**
- 修改：`app/services/receivable_service.py`

- [ ] **步骤 1：在 ReceivableService 类中新增 get_receivables_by_customer 方法**

在 `get_receivables` 方法之后添加：

```python
def get_receivables_by_customer(self, page=1, per_page=10, search=None, status=None):
    rows, total_count, sum_row = self.repo.get_list_by_customer(
        page=page, per_page=per_page, search=search, status=status
    )
    total_pages = (total_count + per_page - 1) // per_page if total_count > 0 else 0

    result_list = []
    for row in rows:
        result_list.append({
            'customer_type': row.CustomerType or 'Merchant',
            'customer_id': row.CustomerID,
            'customer_name': row.CustomerName or '',
            'total_amount': float(row.TotalAmount),
            'total_paid': float(row.TotalPaid),
            'total_remaining': float(row.TotalRemaining),
            'not_due_amount': float(row.NotDueAmount),
            'overdue_1to30': float(row.Overdue1to30),
            'overdue_31to60': float(row.Overdue31to60),
            'overdue_61to90': float(row.Overdue61to90),
            'overdue_over90': float(row.OverdueOver90),
            'record_count': row.RecordCount,
            'earliest_due_date': row.EarliestDueDate.strftime('%Y-%m-%d') if row.EarliestDueDate else '',
        })

    summary = {
        'total_amount': float(sum_row[0]),
        'total_paid': float(sum_row[1]),
        'total_remaining': float(sum_row[2]),
        'total_records': int(sum_row[3]),
        'not_due_amount': float(sum_row[4]),
        'overdue_1to30': float(sum_row[5]),
        'overdue_31to60': float(sum_row[6]),
        'overdue_61to90': float(sum_row[7]),
        'overdue_over90': float(sum_row[8]),
    } if sum_row else None

    return {
        'items': result_list,
        'total_count': total_count,
        'total_pages': total_pages,
        'current_page': page,
        'summary': summary,
    }
```

- [ ] **步骤 2：验证**

确认 `receivable_service.py` 语法无误。

---

### 任务 3：修改 finance_service.py — 增加 batch_collect_by_customer 方法

**文件：**
- 修改：`app/services/finance_service.py`

- [ ] **步骤 1：在 FinanceService 类中新增 batch_collect_by_customer 方法**

在 `batch_pay_by_customer` 方法之后添加。该方法参照 `batch_pay_by_customer` 的结构，但执行收款核销的5步联动：

```python
def batch_collect_by_customer(self, customer_type, customer_id, total_amount,
                               payment_method, transaction_date, description,
                               created_by, account_id=None,
                               collect_mode='cash', prepayment_id=None):
    """按客户批量收款核销

    Args:
        customer_type: 客户类型 Merchant/Customer
        customer_id: 客户ID
        total_amount: 本次收款总金额
        payment_method: 付款方式
        transaction_date: 交易日期
        description: 备注
        created_by: 操作人UserID
        account_id: 收款账户ID
        collect_mode: 收款模式 cash/prepayment
        prepayment_id: 预收记录ID（预收冲抵模式时必填）
    """
    if collect_mode == 'prepayment':
        return self._batch_collect_by_prepayment(
            customer_type, customer_id, total_amount,
            prepayment_id, description, created_by
        )

    with DBConnection() as conn:
        cursor = conn.cursor()

        customer_name = self._resolve_customer_name(cursor, customer_type, customer_id)
        if not customer_name:
            return {'success': False, 'message': '客户不存在'}

        receivables = self._get_unpaid_receivables(cursor, customer_type, customer_id)
        if not receivables:
            return {'success': False, 'message': '该客户没有未收回应收'}

        remaining_amount = float(total_amount)
        collected_count = 0

        for r in receivables:
            if remaining_amount <= 0.01:
                break

            receivable_id = r.ReceivableID
            current_remaining = float(r.RemainingAmount)
            collect_for_this = min(remaining_amount, current_remaining)
            new_remaining = current_remaining - collect_for_this

            if new_remaining <= 0.01:
                new_status = N'已付款'
            else:
                new_status = N'部分付款'

            cursor.execute("""
                INSERT INTO CollectionRecord (ReceivableID, MerchantID, Amount, PaymentMethod, TransactionDate, Description, CreatedBy, CustomerType)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, receivable_id, customer_id, collect_for_this, payment_method, transaction_date, description, created_by, customer_type)

            cursor.execute("""
                UPDATE Receivable
                SET PaidAmount = PaidAmount + ?, RemainingAmount = RemainingAmount - ?, UpdateTime = GETDATE()
                WHERE ReceivableID = ?
            """, collect_for_this, collect_for_this, receivable_id)

            cursor.execute("""
                UPDATE Receivable SET Status = ?, UpdateTime = GETDATE() WHERE ReceivableID = ?
            """, new_status, receivable_id)

            default_account = self._get_default_account_id(cursor) if not account_id else account_id
            cursor.execute("""
                INSERT INTO CashFlow (Amount, Direction, ExpenseTypeID, Description, TransactionDate, ReferenceID, ReferenceType, CreatedBy, AccountID)
                VALUES (?, N'收入', NULL, ?, ?, ?, N'collection_record', ?, ?)
            """, collect_for_this, f'批量收款-{customer_name}', transaction_date, receivable_id, created_by, default_account)

            if default_account:
                cursor.execute("""
                    UPDATE Account SET Balance = Balance + ? WHERE AccountID = ?
                """, collect_for_this, default_account)

            remaining_amount -= collect_for_this
            collected_count += 1

        conn.commit()

        return {
            'success': True,
            'message': f'批量收款成功，共核销 {collected_count} 条应收',
            'collected_count': collected_count,
            'actual_amount': float(total_amount) - remaining_amount,
        }
```

- [ ] **步骤 2：新增辅助方法 _resolve_customer_name、_get_unpaid_receivables、_get_default_account_id**

```python
def _resolve_customer_name(self, cursor, customer_type, customer_id):
    if customer_type == 'Customer':
        cursor.execute("SELECT CustomerName FROM Customer WHERE CustomerID = ?", customer_id)
    else:
        cursor.execute("SELECT MerchantName FROM Merchant WHERE MerchantID = ?", customer_id)
    row = cursor.fetchone()
    return row[0] if row else None

def _get_unpaid_receivables(self, cursor, customer_type, customer_id):
    if customer_type == 'Customer':
        cursor.execute("""
            SELECT ReceivableID, RemainingAmount, DueDate
            FROM Receivable
            WHERE CustomerType = ? AND CustomerID = ? AND Status != N'已付款' AND IsActive = 1
            ORDER BY DueDate ASC
        """, customer_type, customer_id)
    else:
        cursor.execute("""
            SELECT ReceivableID, RemainingAmount, DueDate
            FROM Receivable
            WHERE CustomerType = ? AND CustomerID = ? AND Status != N'已付款' AND IsActive = 1
            ORDER BY DueDate ASC
        """, customer_type, customer_id)
    return cursor.fetchall()

def _get_default_account_id(self, cursor):
    cursor.execute("SELECT AccountID FROM Account WHERE IsDefault = 1 AND Status = N'有效'")
    row = cursor.fetchone()
    return row[0] if row else None
```

- [ ] **步骤 3：新增 _batch_collect_by_prepayment 方法（预收冲抵批量收款）**

```python
def _batch_collect_by_prepayment(self, customer_type, customer_id, total_amount,
                                  prepayment_id, description, created_by):
    with DBConnection() as conn:
        cursor = conn.cursor()

        cursor.execute("""
            SELECT PrepaymentID, RemainingAmount, CustomerName
            FROM Prepayment
            WHERE PrepaymentID = ? AND Direction = N'income' AND Status != N'已核销'
        """, prepayment_id)
        prepay_row = cursor.fetchone()
        if not prepay_row:
            return {'success': False, 'message': '预收记录不存在或已核销'}

        prepay_remaining = float(prepay_row.RemainingAmount)
        if float(total_amount) > prepay_remaining:
            return {'success': False, 'message': f'冲抵金额超过预收余额（¥{prepay_remaining:.2f}）'}

        receivables = self._get_unpaid_receivables(cursor, customer_type, customer_id)
        if not receivables:
            return {'success': False, 'message': '该客户没有未收回应收'}

        remaining_amount = float(total_amount)
        collected_count = 0

        for r in receivables:
            if remaining_amount <= 0.01:
                break

            receivable_id = r.ReceivableID
            current_remaining = float(r.RemainingAmount)
            collect_for_this = min(remaining_amount, current_remaining)
            new_remaining = current_remaining - collect_for_this

            if new_remaining <= 0.01:
                new_status = N'已付款'
            else:
                new_status = N'部分付款'

            cursor.execute("""
                INSERT INTO CollectionRecord (ReceivableID, MerchantID, Amount, PaymentMethod, TransactionDate, Description, CreatedBy, CustomerType)
                VALUES (?, ?, ?, N'预收冲抵', GETDATE(), ?, ?, ?)
            """, receivable_id, customer_id, collect_for_this, description, created_by, customer_type)

            cursor.execute("""
                UPDATE Receivable
                SET PaidAmount = PaidAmount + ?, RemainingAmount = RemainingAmount - ?, Status = ?, UpdateTime = GETDATE()
                WHERE ReceivableID = ?
            """, collect_for_this, collect_for_this, new_status, receivable_id)

            remaining_amount -= collect_for_this
            collected_count += 1

        cursor.execute("""
            UPDATE Prepayment
            SET AppliedAmount = AppliedAmount + ?, RemainingAmount = RemainingAmount - ?, UpdateTime = GETDATE()
            WHERE PrepaymentID = ?
        """, float(total_amount) - remaining_amount, float(total_amount) - remaining_amount, prepayment_id)

        new_prepay_remaining = prepay_remaining - (float(total_amount) - remaining_amount)
        if new_prepay_remaining <= 0.01:
            cursor.execute("UPDATE Prepayment SET Status = N'已核销' WHERE PrepaymentID = ?", prepayment_id)
        else:
            cursor.execute("UPDATE Prepayment SET Status = N'部分核销' WHERE PrepaymentID = ?", prepayment_id)

        cursor.execute("""
            INSERT INTO PrepaymentApply (PrepaymentID, ReceivableID, Amount, Description, CreatedBy)
            VALUES (?, NULL, ?, ?, ?)
        """, prepayment_id, float(total_amount) - remaining_amount, description, created_by)

        conn.commit()

        return {
            'success': True,
            'message': f'预收冲抵成功，共核销 {collected_count} 条应收',
            'collected_count': collected_count,
            'actual_amount': float(total_amount) - remaining_amount,
        }
```

- [ ] **步骤 4：验证语法**

确认 `finance_service.py` 无语法错误。

---

### 任务 4：修改 finance.py — 新增路由端点

**文件：**
- 修改：`app/routes/finance.py`

- [ ] **步骤 1：在应收账款路由区域（`receivable_detail` 之后）新增 `/receivable/list_by_customer` 路由**

```python
@finance_bp.route('/receivable/list_by_customer', methods=['GET'])
@login_required
def receivable_list_by_customer():
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 12, type=int)
        search = request.args.get('search', '').strip()
        status = request.args.get('status', '').strip()

        result = receivable_svc.get_receivables_by_customer(
            page=page, per_page=per_page,
            search=search or None, status=status or None
        )

        return success_response(result)
    except Exception as e:
        return error_response(f'获取数据失败：{str(e)}', status=500)
```

- [ ] **步骤 2：新增 `/receivable/batch_collect` 路由**

```python
@finance_bp.route('/receivable/batch_collect', methods=['POST'])
@login_required
def receivable_batch_collect():
    try:
        data = request.json
        result = finance_svc.batch_collect_by_customer(
            customer_type=data.get('customer_type', 'Merchant'),
            customer_id=int(data.get('customer_id', 0)),
            total_amount=float(data.get('amount', 0)),
            payment_method=data.get('payment_method', ''),
            transaction_date=data.get('transaction_date', ''),
            description=data.get('description', ''),
            created_by=current_user.user_id,
            account_id=data.get('account_id'),
            collect_mode=data.get('collect_mode', 'cash'),
            prepayment_id=data.get('prepayment_id')
        )
        if result['success']:
            result_data = {k: v for k, v in result.items() if k not in ('success', 'message')}
            return success_response(result_data or None, message=result.get('message', '批量收款成功'))
        else:
            return error_response(result.get('message', '批量收款失败'), status=400)
    except Exception as e:
        return error_response(f'批量收款失败：{str(e)}', status=500)
```

- [ ] **步骤 3：验证路由注册**

启动 Flask 应用，确认无路由冲突。

---

### 任务 5：重写 receivable.html — 双选项卡+账龄+批量收款

**文件：**
- 重写：`templates/finance/receivable.html`

这是最大的任务。页面完全镜像 `payable.html` 的结构，但包含应收特有的差异：

- [ ] **步骤 1：编写页面 HTML 结构**

页面继承 `admin_base.html`，包含：
1. 面包屑导航
2. 卡片容器（标题+按钮）
3. 筛选栏（搜索+状态+费用类型+搜索按钮）
4. 选项卡导航（按客户显示/按明细显示）
5. 按客户显示表格（含5个账龄列）
6. 按明细显示表格（含品名列）
7. 分页控件
8. 6个弹窗（添加应收、收款核销、客户明细、批量收款、删除确认、详情）

- [ ] **步骤 2：编写 JavaScript — 按客户显示逻辑**

- `loadReceivablesByCustomer(page)` — 调用 `/finance/receivable/list_by_customer`
- `renderCustomerTable(data)` — 渲染客户汇总表格，含5个账龄分段列和合计行
- 账龄列渲染函数 `getAgingClass(amount, type)` 返回对应 CSS 类

- [ ] **步骤 3：编写 JavaScript — 按明细显示逻辑**

- `loadReceivables(page)` — 调用 `/finance/receivable/list`
- `renderTable(data)` — 渲染明细表格，含品名列

- [ ] **步骤 4：编写 JavaScript — 收款核销弹窗（双模式）**

复用现有 `collectModal` 的双模式设计（现金+预收冲抵）：
- `openCollectModal()` — 打开收款弹窗
- `submitCollect()` — 提交收款

- [ ] **步骤 5：编写 JavaScript — 批量收款弹窗（双模式+预览）**

镜像 `batchPayModal` 的设计，增加预收冲抵选项：
- `openBatchCollectModal()` — 打开批量收款弹窗
- `previewBatchCollect()` — 实时预览核销方案
- `submitBatchCollect()` — 提交批量收款

- [ ] **步骤 6：编写 JavaScript — 其他弹窗和事件绑定**

- 添加应收弹窗（含品名/规格/数量/单价/单位）
- 客户明细弹窗
- 删除确认弹窗
- 详情弹窗（含合同/抄表数据）
- 客户名称超链接 → 客户交易历史弹窗
- 选项卡切换、搜索、分页等事件绑定

- [ ] **步骤 7：验证页面功能**

启动 Flask 应用，访问 `http://127.0.0.1:5000/finance/receivable`，逐一验证：
1. 按客户显示 — 数据加载、账龄列显示、合计行
2. 按明细显示 — 数据加载、品名列显示
3. 选项卡切换
4. 搜索和筛选
5. 收款核销（现金+预收冲抵）
6. 批量收款（现金+预收冲抵+预览）
7. 添加应收
8. 删除应收
9. 查看详情
10. 客户名称超链接
11. 导出 Excel
