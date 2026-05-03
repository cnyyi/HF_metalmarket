# 收款/付款冲销功能 实现计划

> **面向 AI 代理的工作者：** 必需子技能：使用 superpowers:subagent-driven-development（推荐）或 superpowers:executing-plans 逐任务实现此计划。步骤使用复选框（`- [ ]`）语法来跟踪进度。

**目标：** 为收款核销和付款核销增加红字冲回机制，允许7天内撤销操作，并新增"已收账款管理"和"已付账款管理"独立页面。

**架构：** 新建 ReversalRecord 表记录冲销操作，在 CollectionRecord/PaymentRecord 上增加 IsReversed/ReversalID 字段。冲销时生成反向 CashFlow，恢复 Receivable/Payable 金额和状态，恢复 Account 余额。新增两个独立页面展示已收/已付记录并提供冲销操作。

**技术栈：** Flask + SQL Server + Bootstrap 5 + jQuery

---

## 文件结构

| 文件 | 操作 | 职责 |
|------|------|------|
| `scripts/add_reversal_tables.sql` | 创建 | 数据库迁移脚本 |
| `app/services/finance_service.py` | 修改 | 新增 reverse_collection / reverse_payment / get_collection_records / get_payment_records 方法 |
| `app/routes/finance.py` | 修改 | 新增4个路由（collection/payment 页面+列表+冲销） |
| `templates/finance/collection.html` | 创建 | 已收账款管理页面 |
| `templates/finance/payment.html` | 创建 | 已付账款管理页面 |
| `templates/admin_base.html` | 修改 | 侧边栏新增两个菜单项 |
| `utils/migrate_crud_permissions.py` | 修改 | 注册新菜单权限 |

---

### 任务 1：数据库迁移

**文件：**
- 创建：`scripts/add_reversal_tables.sql`

- [ ] **步骤 1：编写迁移 SQL**

```sql
-- 新建冲销记录表
CREATE TABLE ReversalRecord (
    ReversalID         INT IDENTITY(1,1) PRIMARY KEY,
    OriginalType       NVARCHAR(50) NOT NULL,
    OriginalID         INT NOT NULL,
    ReversalAmount     DECIMAL(18,2) NOT NULL,
    Reason             NVARCHAR(500) NOT NULL,
    ReversalCashFlowID INT NULL,
    CreatedBy          INT NOT NULL,
    CreateTime         DATETIME DEFAULT GETDATE(),
    CONSTRAINT FK_Reversal_CreatedBy FOREIGN KEY (CreatedBy) REFERENCES [User](UserID)
);

-- CollectionRecord 增加冲销标记
ALTER TABLE CollectionRecord ADD IsReversed BIT DEFAULT 0;
ALTER TABLE CollectionRecord ADD ReversalID INT NULL;

-- PaymentRecord 增加冲销标记
ALTER TABLE PaymentRecord ADD IsReversed BIT DEFAULT 0;
ALTER TABLE PaymentRecord ADD ReversalID INT NULL;
```

- [ ] **步骤 2：执行迁移脚本**

运行：`python -c "from utils.database import DBConnection; import pyodbc; conn = DBConnection(); cursor = conn.cursor(); cursor.execute(open('scripts/add_reversal_tables.sql').read()); conn.commit(); print('OK')"` 或在 SSMS 中手动执行。

- [ ] **步骤 3：Commit**

```bash
git add scripts/add_reversal_tables.sql
git commit -m "feat: 新增 ReversalRecord 表及冲销字段"
```

---

### 任务 2：后端 — 冲销业务逻辑

**文件：**
- 修改：`app/services/finance_service.py`

- [ ] **步骤 1：在 FinanceService 类中新增 reverse_collection 方法**

在 `batch_collect_by_customer` 方法之前插入：

```python
    def reverse_collection(self, collection_record_id, reason, created_by):
        with DBConnection() as conn:
            cursor = conn.cursor()

            cursor.execute("""
                SELECT cr.CollectionRecordID, cr.Amount, cr.ReceivableID,
                       cr.IsReversed, cr.CreateTime,
                       r.PaidAmount, r.RemainingAmount, r.Amount AS ReceivableAmount,
                       r.ExpenseTypeID, r.Status
                FROM CollectionRecord cr
                INNER JOIN Receivable r ON cr.ReceivableID = r.ReceivableID
                WHERE cr.CollectionRecordID = ?
            """, collection_record_id)
            row = cursor.fetchone()
            if not row:
                return {'success': False, 'message': '收款记录不存在'}
            if row.IsReversed:
                return {'success': False, 'message': '该记录已被冲销，不可重复操作'}

            days_diff = (datetime.now() - row.CreateTime).days
            if days_diff > 7:
                return {'success': False, 'message': '超过7天，不可冲销'}

            amount = float(row.Amount)
            receivable_id = row.ReceivableID
            expense_type_id = row.ExpenseTypeID

            cursor.execute("""
                INSERT INTO ReversalRecord (OriginalType, OriginalID, ReversalAmount, Reason, CreatedBy)
                VALUES (N'collection_record', ?, ?, ?, ?)
            """, collection_record_id, amount, reason, created_by)

            cursor.execute("SELECT @@IDENTITY")
            reversal_id = cursor.fetchone()[0]

            cursor.execute("""
                UPDATE CollectionRecord SET IsReversed = 1, ReversalID = ?
                WHERE CollectionRecordID = ?
            """, reversal_id, collection_record_id)

            new_paid = float(row.PaidAmount) - amount
            new_remaining = float(row.RemainingAmount) + amount
            if new_remaining >= float(row.ReceivableAmount) - 0.01:
                new_status = '未付款'
            elif new_remaining > 0.01:
                new_status = '部分付款'
            else:
                new_status = '已付款'

            cursor.execute("""
                UPDATE Receivable
                SET PaidAmount = PaidAmount - ?, RemainingAmount = RemainingAmount + ?,
                    Status = ?, UpdateTime = GETDATE()
                WHERE ReceivableID = ?
            """, amount, amount, new_status, receivable_id)

            default_account = self._get_default_account_id(cursor)
            transaction_no = generate_serial_no(cursor, 'CF', 'CashFlow', 'TransactionNo')
            cursor.execute("""
                INSERT INTO CashFlow (Amount, Direction, ExpenseTypeID, Description,
                    TransactionDate, ReferenceID, ReferenceType, CreatedBy, AccountID, TransactionNo)
                VALUES (?, N'支出', ?, ?, GETDATE(), ?, N'reversal', ?, ?, ?)
            """, amount, expense_type_id,
                f'冲销收款-记录#{collection_record_id}',
                reversal_id, created_by, default_account, transaction_no)

            cursor.execute("SELECT @@IDENTITY")
            cash_flow_id = cursor.fetchone()[0]

            cursor.execute("""
                UPDATE ReversalRecord SET ReversalCashFlowID = ? WHERE ReversalID = ?
            """, cash_flow_id, reversal_id)

            if default_account:
                cursor.execute("""
                    UPDATE Account SET Balance = Balance - ? WHERE AccountID = ?
                """, amount, default_account)

            conn.commit()

        return {
            'success': True,
            'message': f'冲销成功，已恢复应收金额 ¥{amount:.2f}',
            'reversal_id': reversal_id,
            'new_status': new_status
        }
```

- [ ] **步骤 2：在 FinanceService 类中新增 reverse_payment 方法**

紧接 `reverse_collection` 之后插入：

```python
    def reverse_payment(self, payment_record_id, reason, created_by):
        with DBConnection() as conn:
            cursor = conn.cursor()

            cursor.execute("""
                SELECT pr.PaymentRecordID, pr.Amount, pr.PayableID,
                       pr.IsReversed, pr.CreateTime,
                       p.PaidAmount, p.RemainingAmount, p.Amount AS PayableAmount,
                       p.ExpenseTypeID, p.Status
                FROM PaymentRecord pr
                INNER JOIN Payable p ON pr.PayableID = p.PayableID
                WHERE pr.PaymentRecordID = ?
            """, payment_record_id)
            row = cursor.fetchone()
            if not row:
                return {'success': False, 'message': '付款记录不存在'}
            if row.IsReversed:
                return {'success': False, 'message': '该记录已被冲销，不可重复操作'}

            days_diff = (datetime.now() - row.CreateTime).days
            if days_diff > 7:
                return {'success': False, 'message': '超过7天，不可冲销'}

            amount = float(row.Amount)
            payable_id = row.PayableID
            expense_type_id = row.ExpenseTypeID

            default_account = self._get_default_account_id(cursor)
            if default_account:
                cursor.execute("SELECT Balance FROM Account WHERE AccountID = ?", default_account)
                acc_row = cursor.fetchone()
                if acc_row and float(acc_row.Balance) < amount:
                    return {'success': False, 'message': f'账户余额不足（当前余额: ¥{float(acc_row.Balance):.2f}），无法冲销'}

            cursor.execute("""
                INSERT INTO ReversalRecord (OriginalType, OriginalID, ReversalAmount, Reason, CreatedBy)
                VALUES (N'payment_record', ?, ?, ?, ?)
            """, payment_record_id, amount, reason, created_by)

            cursor.execute("SELECT @@IDENTITY")
            reversal_id = cursor.fetchone()[0]

            cursor.execute("""
                UPDATE PaymentRecord SET IsReversed = 1, ReversalID = ?
                WHERE PaymentRecordID = ?
            """, reversal_id, payment_record_id)

            new_paid = float(row.PaidAmount) - amount
            new_remaining = float(row.RemainingAmount) + amount
            if new_remaining >= float(row.PayableAmount) - 0.01:
                new_status = '未付款'
            elif new_remaining > 0.01:
                new_status = '部分付款'
            else:
                new_status = '已付款'

            cursor.execute("""
                UPDATE Payable
                SET PaidAmount = PaidAmount - ?, RemainingAmount = RemainingAmount + ?,
                    Status = ?, UpdateTime = GETDATE()
                WHERE PayableID = ?
            """, amount, amount, new_status, payable_id)

            transaction_no = generate_serial_no(cursor, 'CF', 'CashFlow', 'TransactionNo')
            cursor.execute("""
                INSERT INTO CashFlow (Amount, Direction, ExpenseTypeID, Description,
                    TransactionDate, ReferenceID, ReferenceType, CreatedBy, AccountID, TransactionNo)
                VALUES (?, N'收入', ?, ?, GETDATE(), ?, N'reversal', ?, ?, ?)
            """, amount, expense_type_id,
                f'冲销付款-记录#{payment_record_id}',
                reversal_id, created_by, default_account, transaction_no)

            cursor.execute("SELECT @@IDENTITY")
            cash_flow_id = cursor.fetchone()[0]

            cursor.execute("""
                UPDATE ReversalRecord SET ReversalCashFlowID = ? WHERE ReversalID = ?
            """, cash_flow_id, reversal_id)

            if default_account:
                cursor.execute("""
                    UPDATE Account SET Balance = Balance + ? WHERE AccountID = ?
                """, amount, default_account)

            conn.commit()

        return {
            'success': True,
            'message': f'冲销成功，已恢复应付金额 ¥{amount:.2f}',
            'reversal_id': reversal_id,
            'new_status': new_status
        }
```

- [ ] **步骤 3：在 FinanceService 类中新增 get_collection_records 方法**

```python
    def get_collection_records(self, page=1, per_page=10, search=None,
                                payment_method=None, start_date=None,
                                end_date=None, is_reversed=None):
        with DBConnection() as conn:
            cursor = conn.cursor()
            conditions = ['1=1']
            params = []

            if search:
                conditions.append("""(
                    EXISTS (SELECT 1 FROM Merchant m WHERE m.MerchantID = cr.MerchantID AND m.MerchantName LIKE ?)
                    OR EXISTS (SELECT 1 FROM Customer c WHERE c.CustomerID = cr.CustomerID AND c.CustomerName LIKE ?)
                )""")
                params.extend([f'%{search}%', f'%{search}%'])

            if payment_method:
                conditions.append("cr.PaymentMethod = ?")
                params.append(payment_method)

            if start_date:
                conditions.append("cr.TransactionDate >= ?")
                params.append(start_date)

            if end_date:
                conditions.append("cr.TransactionDate <= ?")
                params.append(end_date)

            if is_reversed is not None:
                conditions.append("cr.IsReversed = ?")
                params.append(1 if is_reversed else 0)

            where_clause = ' AND '.join(conditions)

            cursor.execute(f"""
                SELECT COUNT(*) FROM CollectionRecord cr WHERE {where_clause}
            """, *params)
            total_count = cursor.fetchone()[0]

            cursor.execute(f"""
                SELECT cr.CollectionRecordID, cr.ReceivableID, cr.MerchantID,
                       cr.Amount, cr.PaymentMethod, cr.TransactionDate,
                       cr.Description, cr.IsReversed, cr.ReversalID,
                       cr.CustomerType, cr.CreateTime,
                       ISNULL(sd.DictName, N'') AS ExpenseTypeName,
                       CASE
                           WHEN cr.CustomerType = N'Customer' THEN ISNULL(c.CustomerName, N'')
                           ELSE ISNULL(m.MerchantName, N'')
                       END AS CustomerName,
                       u.RealName AS OperatorName,
                       rv.ReversalAmount, rv.Reason AS ReversalReason, rv.CreateTime AS ReversalTime
                FROM CollectionRecord cr
                LEFT JOIN Receivable r ON cr.ReceivableID = r.ReceivableID
                LEFT JOIN Sys_Dictionary sd ON r.ExpenseTypeID = sd.DictID
                LEFT JOIN Merchant m ON cr.CustomerType != N'Customer' AND cr.MerchantID = m.MerchantID
                LEFT JOIN Customer c ON cr.CustomerType = N'Customer' AND cr.CustomerID = c.CustomerID
                LEFT JOIN [User] u ON cr.CreatedBy = u.UserID
                LEFT JOIN ReversalRecord rv ON cr.ReversalID = rv.ReversalID
                WHERE {where_clause}
                ORDER BY cr.CreateTime DESC
                OFFSET ? ROWS FETCH NEXT ? ROWS ONLY
            """, *params, (page - 1) * per_page, per_page)

            rows = cursor.fetchall()
            items = []
            for row in rows:
                item = {
                    'collection_record_id': row.CollectionRecordID,
                    'receivable_id': row.ReceivableID,
                    'merchant_id': row.MerchantID,
                    'amount': safe_float(row.Amount),
                    'payment_method': row.PaymentMethod or '',
                    'transaction_date': format_date(row.TransactionDate),
                    'description': row.Description or '',
                    'is_reversed': bool(row.IsReversed),
                    'reversal_id': row.ReversalID,
                    'customer_type': row.CustomerType or 'Merchant',
                    'customer_name': row.CustomerName,
                    'expense_type_name': row.ExpenseTypeName,
                    'operator_name': row.OperatorName or '',
                    'create_time': format_datetime(row.CreateTime),
                    'can_reverse': (not bool(row.IsReversed)) and (datetime.now() - row.CreateTime).days <= 7,
                }
                if row.IsReversed and row.ReversalID:
                    item['reversal_amount'] = safe_float(row.ReversalAmount)
                    item['reversal_reason'] = row.ReversalReason or ''
                    item['reversal_time'] = format_datetime(row.ReversalTime)
                items.append(item)

            total_pages = (total_count + per_page - 1) // per_page if total_count > 0 else 0
            return {
                'items': items,
                'total_count': total_count,
                'total_pages': total_pages,
                'current_page': page
            }
```

- [ ] **步骤 4：在 FinanceService 类中新增 get_payment_records_list 方法**

```python
    def get_payment_records_list(self, page=1, per_page=10, search=None,
                                  payment_method=None, start_date=None,
                                  end_date=None, is_reversed=None):
        with DBConnection() as conn:
            cursor = conn.cursor()
            conditions = ['1=1']
            params = []

            if search:
                conditions.append("(pr.VendorName LIKE ? OR ISNULL(c.CustomerName, N'') LIKE ?)")
                params.extend([f'%{search}%', f'%{search}%'])

            if payment_method:
                conditions.append("pr.PaymentMethod = ?")
                params.append(payment_method)

            if start_date:
                conditions.append("pr.TransactionDate >= ?")
                params.append(start_date)

            if end_date:
                conditions.append("pr.TransactionDate <= ?")
                params.append(end_date)

            if is_reversed is not None:
                conditions.append("pr.IsReversed = ?")
                params.append(1 if is_reversed else 0)

            where_clause = ' AND '.join(conditions)

            cursor.execute(f"""
                SELECT COUNT(*) FROM PaymentRecord pr WHERE {where_clause}
            """, *params)
            total_count = cursor.fetchone()[0]

            cursor.execute(f"""
                SELECT pr.PaymentRecordID, pr.PayableID, pr.VendorName,
                       pr.Amount, pr.PaymentMethod, pr.TransactionDate,
                       pr.Description, pr.IsReversed, pr.ReversalID,
                       pr.CustomerType, pr.CustomerID, pr.CreateTime,
                       ISNULL(sd.DictName, N'') AS ExpenseTypeName,
                       ISNULL(c.CustomerName, pr.VendorName) AS CustomerName,
                       u.RealName AS OperatorName,
                       rv.ReversalAmount, rv.Reason AS ReversalReason, rv.CreateTime AS ReversalTime
                FROM PaymentRecord pr
                LEFT JOIN Payable p ON pr.PayableID = p.PayableID
                LEFT JOIN Sys_Dictionary sd ON p.ExpenseTypeID = sd.DictID
                LEFT JOIN Customer c ON pr.CustomerID = c.CustomerID AND pr.CustomerType = N'Customer'
                LEFT JOIN [User] u ON pr.CreatedBy = u.UserID
                LEFT JOIN ReversalRecord rv ON pr.ReversalID = rv.ReversalID
                WHERE {where_clause}
                ORDER BY pr.CreateTime DESC
                OFFSET ? ROWS FETCH NEXT ? ROWS ONLY
            """, *params, (page - 1) * per_page, per_page)

            rows = cursor.fetchall()
            items = []
            for row in rows:
                item = {
                    'payment_record_id': row.PaymentRecordID,
                    'payable_id': row.PayableID,
                    'vendor_name': row.VendorName or '',
                    'amount': safe_float(row.Amount),
                    'payment_method': row.PaymentMethod or '',
                    'transaction_date': format_date(row.TransactionDate),
                    'description': row.Description or '',
                    'is_reversed': bool(row.IsReversed),
                    'reversal_id': row.ReversalID,
                    'customer_type': row.CustomerType or 'Merchant',
                    'customer_id': row.CustomerID,
                    'customer_name': row.CustomerName,
                    'expense_type_name': row.ExpenseTypeName,
                    'operator_name': row.OperatorName or '',
                    'create_time': format_datetime(row.CreateTime),
                    'can_reverse': (not bool(row.IsReversed)) and (datetime.now() - row.CreateTime).days <= 7,
                }
                if row.IsReversed and row.ReversalID:
                    item['reversal_amount'] = safe_float(row.ReversalAmount)
                    item['reversal_reason'] = row.ReversalReason or ''
                    item['reversal_time'] = format_datetime(row.ReversalTime)
                items.append(item)

            total_pages = (total_count + per_page - 1) // per_page if total_count > 0 else 0
            return {
                'items': items,
                'total_count': total_count,
                'total_pages': total_pages,
                'current_page': page
            }
```

- [ ] **步骤 5：验证编译**

运行：`python -c "import py_compile; py_compile.compile('app/services/finance_service.py', doraise=True); print('OK')"`

- [ ] **步骤 6：Commit**

```bash
git add app/services/finance_service.py
git commit -m "feat: 新增收款/付款冲销业务逻辑"
```

---

### 任务 3：后端 — 路由层

**文件：**
- 修改：`app/routes/finance.py`

- [ ] **步骤 1：在 finance.py 中新增4个路由**

在 `receivable_batch_collect` 路由之后、`payable` 路由之前插入：

```python
@finance_bp.route('/collection')
@login_required
@check_permission('finance_view')
def collection():
    return render_template('finance/collection.html')


@finance_bp.route('/collection/list', methods=['GET'])
@login_required
@check_permission('finance_view')
def collection_list():
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        search = request.args.get('search', '').strip()
        payment_method = request.args.get('payment_method', '').strip()
        start_date = request.args.get('start_date', '').strip()
        end_date = request.args.get('end_date', '').strip()
        is_reversed = request.args.get('is_reversed', '').strip()

        is_reversed_filter = None
        if is_reversed == '1':
            is_reversed_filter = True
        elif is_reversed == '0':
            is_reversed_filter = False

        result = finance_svc.get_collection_records(
            page=page, per_page=per_page,
            search=search or None,
            payment_method=payment_method or None,
            start_date=start_date or None,
            end_date=end_date or None,
            is_reversed=is_reversed_filter
        )
        return success_response(result)
    except Exception as e:
        return handle_exception(e)


@finance_bp.route('/collection/reverse/<int:record_id>', methods=['POST'])
@login_required
@check_permission('finance_create')
def collection_reverse(record_id):
    try:
        data = request.json
        reason = data.get('reason', '').strip()
        if not reason:
            return error_response('请填写冲销原因')
        result = finance_svc.reverse_collection(
            collection_record_id=record_id,
            reason=reason,
            created_by=current_user.user_id
        )
        if result['success']:
            result_data = {k: v for k, v in result.items() if k not in ('success', 'message')}
            return success_response(result_data or None, message=result.get('message', '冲销成功'))
        else:
            return error_response(result.get('message', '冲销失败'), status=400)
    except Exception as e:
        return handle_exception(e)


@finance_bp.route('/payment')
@login_required
@check_permission('finance_view')
def payment():
    return render_template('finance/payment.html')


@finance_bp.route('/payment/list', methods=['GET'])
@login_required
@check_permission('finance_view')
def payment_list():
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        search = request.args.get('search', '').strip()
        payment_method = request.args.get('payment_method', '').strip()
        start_date = request.args.get('start_date', '').strip()
        end_date = request.args.get('end_date', '').strip()
        is_reversed = request.args.get('is_reversed', '').strip()

        is_reversed_filter = None
        if is_reversed == '1':
            is_reversed_filter = True
        elif is_reversed == '0':
            is_reversed_filter = False

        result = finance_svc.get_payment_records_list(
            page=page, per_page=per_page,
            search=search or None,
            payment_method=payment_method or None,
            start_date=start_date or None,
            end_date=end_date or None,
            is_reversed=is_reversed_filter
        )
        return success_response(result)
    except Exception as e:
        return handle_exception(e)


@finance_bp.route('/payment/reverse/<int:record_id>', methods=['POST'])
@login_required
@check_permission('finance_create')
def payment_reverse(record_id):
    try:
        data = request.json
        reason = data.get('reason', '').strip()
        if not reason:
            return error_response('请填写冲销原因')
        result = finance_svc.reverse_payment(
            payment_record_id=record_id,
            reason=reason,
            created_by=current_user.user_id
        )
        if result['success']:
            result_data = {k: v for k, v in result.items() if k not in ('success', 'message')}
            return success_response(result_data or None, message=result.get('message', '冲销成功'))
        else:
            return error_response(result.get('message', '冲销失败'), status=400)
    except Exception as e:
        return handle_exception(e)
```

- [ ] **步骤 2：验证编译**

运行：`python -c "import py_compile; py_compile.compile('app/routes/finance.py', doraise=True); print('OK')"`

- [ ] **步骤 3：Commit**

```bash
git add app/routes/finance.py
git commit -m "feat: 新增已收/已付账款管理路由及冲销接口"
```

---

### 任务 4：前端 — 已收账款管理页面

**文件：**
- 创建：`templates/finance/collection.html`

- [ ] **步骤 1：创建 collection.html**

页面包含：
- 面包屑导航
- 筛选条件（搜索、付款方式、日期范围、状态）
- 数据表格（收款单号、客户类型、客户名称、费用类型、收款金额、付款方式、收款日期、状态、操作人、操作）
- 分页
- 冲销模态窗口（显示原记录详情、冲销原因输入、确认按钮）

关键 JS 逻辑：
- `loadCollectionRecords(page)` — 加载列表
- `renderTable(data)` — 渲染表格
- `openReverseModal(id, amount, customer, date)` — 打开冲销弹窗
- `submitReverse(id)` — 提交冲销（Ajax POST `/finance/collection/reverse/<id>`）
- 状态列：正常显示绿色 badge，已冲销显示红色 badge + 冲销原因 tooltip
- 操作列：仅 `can_reverse=true` 时显示冲销按钮

- [ ] **步骤 2：验证页面可访问**

启动应用，访问 `/finance/collection`，确认页面正常渲染。

- [ ] **步骤 3：Commit**

```bash
git add templates/finance/collection.html
git commit -m "feat: 新增已收账款管理页面"
```

---

### 任务 5：前端 — 已付账款管理页面

**文件：**
- 创建：`templates/finance/payment.html`

- [ ] **步骤 1：创建 payment.html**

与 collection.html 结构对称，区别：
- 调用 `/finance/payment/list` API
- 冲销调用 `/finance/payment/reverse/<id>` API
- 列字段：付款单号、供应商、客户类型、客户名称、费用类型、付款金额、付款方式、付款日期、状态、操作人、操作
- 面包屑：财务管理 → 已付账款

- [ ] **步骤 2：验证页面可访问**

启动应用，访问 `/finance/payment`，确认页面正常渲染。

- [ ] **步骤 3：Commit**

```bash
git add templates/finance/payment.html
git commit -m "feat: 新增已付账款管理页面"
```

---

### 任务 6：侧边栏菜单

**文件：**
- 修改：`templates/admin_base.html`

- [ ] **步骤 1：在财务管理分区中新增两个菜单项**

在"应收账款"菜单项之后插入"已收账款"，在"应付账款"菜单项之后插入"已付账款"：

```html
{% if current_user.has_permission('finance_view') %}
<a class="sidebar-item {% if request.endpoint == 'finance.collection' %}active{% endif %}"
   href="{{ url_for('finance.collection') }}">
    <i class="fa fa-check-circle"></i>
    <span class="sidebar-item-text">已收账款</span>
</a>
{% endif %}
```

```html
{% if current_user.has_permission('finance_view') %}
<a class="sidebar-item {% if request.endpoint == 'finance.payment' %}active{% endif %}"
   href="{{ url_for('finance.payment') }}">
    <i class="fa fa-check-circle-o"></i>
    <span class="sidebar-item-text">已付账款</span>
</a>
{% endif %}
```

- [ ] **步骤 2：验证菜单显示**

刷新页面，确认侧边栏出现新菜单项。

- [ ] **步骤 3：Commit**

```bash
git add templates/admin_base.html
git commit -m "feat: 侧边栏新增已收/已付账款菜单"
```

---

### 任务 7：权限注册

**文件：**
- 修改：`utils/migrate_crud_permissions.py`

- [ ] **步骤 1：在 PERMISSIONS_DATA 中新增权限项**

在财务管理权限组中添加：

```python
('collection_view',   '已收账款查看', '财务管理', 'view',   1051),
('collection_create', '已收账款操作', '财务管理', 'create', 1052),
('payment_view',      '已付账款查看', '财务管理', 'view',   1061),
('payment_create',    '已付账款操作', '财务管理', 'create', 1062),
```

- [ ] **步骤 2：在 MANAGE_TO_CRUD 映射中添加**

```python
'finance_manage': ['finance_view', 'finance_create', 'finance_edit', 'finance_delete', 'collection_view', 'collection_create', 'payment_view', 'payment_create'],
```

- [ ] **步骤 3：运行迁移脚本**

运行：`python utils/migrate_crud_permissions.py`

- [ ] **步骤 4：验证权限生效**

登录系统，确认拥有 finance_manage 权限的角色可以看到新菜单。

- [ ] **步骤 5：Commit**

```bash
git add utils/migrate_crud_permissions.py
git commit -m "feat: 注册已收/已付账款权限"
```

---

### 任务 8：端到端验证

- [ ] **步骤 1：测试收款冲销完整流程**

1. 在应收账款页面，对某条应收执行收款核销
2. 进入已收账款页面，确认新记录出现
3. 点击冲销按钮，输入原因，确认
4. 验证：原收款记录状态变为"已冲销"，应收记录金额恢复，账户余额恢复，现金流水出现反向记录

- [ ] **步骤 2：测试付款冲销完整流程**

1. 在应付账款页面，对某条应付执行付款核销
2. 进入已付账款页面，确认新记录出现
3. 点击冲销按钮，输入原因，确认
4. 验证：原付款记录状态变为"已冲销"，应付记录金额恢复，账户余额恢复

- [ ] **步骤 3：测试边界条件**

1. 尝试冲销7天前的记录 → 应提示"超过7天"
2. 尝试重复冲销同一条记录 → 应提示"已被冲销"
3. 不填冲销原因直接提交 → 应提示"请填写冲销原因"

- [ ] **步骤 4：Commit**

```bash
git commit --allow-empty -m "test: 收款/付款冲销功能端到端验证通过"
```
