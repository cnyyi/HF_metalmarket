# 财务通用工具类封装 实现计划

> **面向 AI 代理的工作者：** 必需子技能：使用 superpowers:subagent-driven-development（推荐）或 superpowers:executing-plans 逐任务实现此计划。步骤使用复选框（`- [ ]`）语法来跟踪进度。

**目标：** 提取项目中 15+ 处重复的分页查询、50+ 处重复的日期格式化、3 处重复的单号生成为通用工具类，并创建 PayableRepository 对齐 Receivable 架构，使应收/应付款项在多处使用时不再重复编写。

**架构：** 在 `utils/` 下新建 `format_utils.py`（日期格式化）、`query_helper.py`（分页+条件构建）、`sequence.py`（单号生成）三个工具模块，在 `app/repositories/` 下新建 `payable_repo.py` 对齐已有 `receivable_repo.py` 的架构模式。所有工具函数均为纯函数，无 Flask 依赖，可直接在 Service 层调用。

**技术栈：** Python 3 / pyodbc / Flask / SQL Server

---

## 文件结构

| 操作 | 文件路径 | 职责 |
|------|----------|------|
| 创建 | `utils/format_utils.py` | 日期/时间格式化工具函数 |
| 创建 | `utils/query_helper.py` | 分页查询 + 动态条件构建工具 |
| 创建 | `utils/sequence.py` | 单号/流水号生成工具 |
| 创建 | `app/repositories/payable_repo.py` | 应付账款数据访问层（对齐 receivable_repo.py） |
| 修改 | `app/services/receivable_service.py` | 删除内部 `_format_date`/`_format_datetime`，改用 `format_utils` |
| 修改 | `app/services/finance_service.py` | 删除内部 `_generate_transaction_no`，改用 `sequence`；应付查询迁移到 `payable_repo`；日期格式化改用 `format_utils` |
| 修改 | `app/services/prepayment_service.py` | 分页+日期格式化改用通用工具 |
| 修改 | `app/services/deposit_service.py` | 分页+日期格式化改用通用工具 |
| 修改 | `app/services/account_service.py` | 日期格式化改用 `format_utils` |
| 修改 | `app/services/expense_service.py` | 删除内部 `_generate_order_no`，改用 `sequence`；日期格式化改用 `format_utils` |

---

### 任务 1：创建 `utils/format_utils.py` — 日期格式化工具

**文件：**
- 创建：`utils/format_utils.py`

- [ ] **步骤 1：编写 `utils/format_utils.py`**

```python
# -*- coding: utf-8 -*-
import datetime


def format_date(val, fmt='%Y-%m-%d'):
    if not val:
        return ''
    if isinstance(val, str):
        return val[:10] if len(val) >= 10 else val
    if isinstance(val, (datetime.datetime, datetime.date)):
        return val.strftime(fmt)
    return str(val)


def format_datetime(val, fmt='%Y-%m-%d %H:%M'):
    if not val:
        return ''
    if isinstance(val, str):
        return val[:16] if len(val) >= 16 else val
    if isinstance(val, datetime.datetime):
        return val.strftime(fmt)
    return str(val)


def safe_float(val, default=0.0):
    if val is None:
        return default
    try:
        return float(val)
    except (ValueError, TypeError):
        return default


def safe_int(val, default=0):
    if val is None:
        return default
    try:
        return int(val)
    except (ValueError, TypeError):
        return default
```

- [ ] **步骤 2：验证模块可导入**

运行：`cd d:\BaiduSyncdisk\HF_metalmarket && python -c "from utils.format_utils import format_date, format_datetime, safe_float, safe_int; print('OK')"`
预期：输出 `OK`

- [ ] **步骤 3：Commit**

```bash
git add utils/format_utils.py
git commit -m "feat: 添加日期格式化和安全类型转换工具模块"
```

---

### 任务 2：创建 `utils/query_helper.py` — 分页查询 + 条件构建工具

**文件：**
- 创建：`utils/query_helper.py`

- [ ] **步骤 1：编写 `utils/query_helper.py`**

```python
# -*- coding: utf-8 -*-


def build_where(conditions, prefix=' WHERE '):
    if not conditions:
        return '', []
    clause = prefix + ' AND '.join(conditions)
    return clause, []


def paginate(cursor, base_query, count_query, params, page, per_page,
             order_by=None, sum_query=None):
    """
    通用分页查询

    Args:
        cursor: 数据库游标（已有连接）
        base_query: 基础 SELECT 语句（不含 WHERE/OFFSET）
        count_query: 基础 COUNT 语句（不含 WHERE）
        params: WHERE 条件参数列表
        page: 当前页码（从1开始）
        per_page: 每页条数
        order_by: 排序子句，如 "r.ReceivableID DESC"
        sum_query: 可选的汇总 SELECT 语句（不含 WHERE）

    Returns:
        dict: {
            'rows': list,          # fetchall 结果
            'total_count': int,    # 总记录数
            'total_pages': int,    # 总页数
            'current_page': int,   # 当前页码
            'sum_row': Row|None    # 汇总行（仅 sum_query 非空时）
        }
    """
    offset = (page - 1) * per_page

    if order_by:
        base_query += f" ORDER BY {order_by}"

    base_query += " OFFSET ? ROWS FETCH NEXT ? ROWS ONLY"

    query_params = list(params)
    query_params.extend([offset, per_page])

    cursor.execute(base_query, query_params)
    rows = cursor.fetchall()

    count_params = list(params)
    cursor.execute(count_query, count_params)
    total_count = cursor.fetchone()[0]

    total_pages = (total_count + per_page - 1) // per_page if total_count > 0 else 0

    sum_row = None
    if sum_query:
        cursor.execute(sum_query, count_params)
        sum_row = cursor.fetchone()

    return {
        'rows': rows,
        'total_count': total_count,
        'total_pages': total_pages,
        'current_page': page,
        'sum_row': sum_row,
    }


def paginate_result(items, total_count, page, per_page, **extra):
    """
    构建统一的分页返回结构

    Args:
        items: 当前页数据列表
        total_count: 总记录数
        page: 当前页码
        per_page: 每页条数
        **extra: 额外字段（如 summary）

    Returns:
        dict: {
            'items': list,
            'total_count': int,
            'total_pages': int,
            'current_page': int,
            **extra
        }
    """
    total_pages = (total_count + per_page - 1) // per_page if total_count > 0 else 0
    result = {
        'items': items,
        'total_count': total_count,
        'total_pages': total_pages,
        'current_page': page,
    }
    result.update(extra)
    return result
```

- [ ] **步骤 2：验证模块可导入**

运行：`cd d:\BaiduSyncdisk\HF_metalmarket && python -c "from utils.query_helper import build_where, paginate, paginate_result; print('OK')"`
预期：输出 `OK`

- [ ] **步骤 3：Commit**

```bash
git add utils/query_helper.py
git commit -m "feat: 添加通用分页查询和条件构建工具模块"
```

---

### 任务 3：创建 `utils/sequence.py` — 单号生成工具

**文件：**
- 创建：`utils/sequence.py`

- [ ] **步骤 1：编写 `utils/sequence.py`**

```python
# -*- coding: utf-8 -*-
from datetime import datetime, date


def generate_serial_no(cursor, prefix, table_name, column_name, date_format='%Y%m%d', seq_length=3):
    """
    生成流水号（格式：前缀+日期+序号）

    示例：
        generate_serial_no(cursor, 'CF', 'CashFlow', 'TransactionNo')
        → 'CF20260420001'

        generate_serial_no(cursor, 'EO', 'ExpenseOrder', 'OrderNo')
        → 'EO20260420001'

    Args:
        cursor: 数据库游标（在事务内）
        prefix: 前缀，如 'CF', 'EO'
        table_name: 查询序号的表名
        column_name: 查询序号的列名
        date_format: 日期格式，默认 '%Y%m%d'
        seq_length: 序号位数，默认3

    Returns:
        str: 生成的流水号
    """
    today = datetime.now().strftime(date_format)
    like_pattern = f'{prefix}{today}%'

    cursor.execute(f"""
        SELECT {column_name} FROM {table_name}
        WHERE {column_name} LIKE ?
        ORDER BY {column_name} DESC
    """, (like_pattern,))
    row = cursor.fetchone()

    if row:
        last_val = row[0] if isinstance(row[0], str) else getattr(row, column_name, '')
        prefix_len = len(prefix) + len(today)
        try:
            last_seq = int(last_val[prefix_len:])
            new_seq = last_seq + 1
        except (ValueError, IndexError):
            new_seq = 1
    else:
        new_seq = 1

    return f'{prefix}{today}{new_seq:0{seq_length}d}'
```

- [ ] **步骤 2：验证模块可导入**

运行：`cd d:\BaiduSyncdisk\HF_metalmarket && python -c "from utils.sequence import generate_serial_no; print('OK')"`
预期：输出 `OK`

- [ ] **步骤 3：Commit**

```bash
git add utils/sequence.py
git commit -m "feat: 添加通用单号/流水号生成工具模块"
```

---

### 任务 4：创建 `app/repositories/payable_repo.py` — 应付数据访问层

**文件：**
- 创建：`app/repositories/payable_repo.py`

- [ ] **步骤 1：编写 `app/repositories/payable_repo.py`**

将 `finance_service.py` 中 `get_payables()`、`_get_payable_by_id()`、`soft_delete_payable()` 的 SQL 逻辑提取到 Repository 层，对齐 `receivable_repo.py` 的架构模式。

```python
# -*- coding: utf-8 -*-
from utils.database import DBConnection


class PayableRepository:

    _CUSTOMER_EXPR = """
        CASE
            WHEN p.CustomerType = 'Customer' THEN c.CustomerName
            WHEN p.CustomerType = 'Merchant' THEN m.MerchantName
            ELSE p.VendorName
        END
    """

    _BASE_JOINS = """
        LEFT JOIN Sys_Dictionary sd ON p.ExpenseTypeID = sd.DictID AND sd.DictType = 'expense_item_expend'
        LEFT JOIN ExpenseType et ON p.ExpenseTypeID = et.ExpenseTypeID AND sd.DictID IS NULL
        LEFT JOIN Merchant m ON p.CustomerType = 'Merchant' AND p.CustomerID = m.MerchantID
        LEFT JOIN Customer c ON p.CustomerType = 'Customer' AND p.CustomerID = c.CustomerID
    """

    def get_list(self, page=1, per_page=10, search=None, status=None, include_deleted=False):
        with DBConnection() as conn:
            cursor = conn.cursor()

            base_query = f"""
                SELECT p.PayableID, p.VendorName, p.ExpenseTypeID,
                       ISNULL(sd.DictName, et.ExpenseTypeName) AS ExpenseTypeName,
                       p.Amount, p.PaidAmount,
                       p.RemainingAmount, p.DueDate, p.Status,
                       p.Description, p.CreateTime, p.UpdateTime,
                       p.CustomerType, p.CustomerID, p.ExpenseOrderID,
                       {self._CUSTOMER_EXPR} AS CustomerName
                FROM Payable p
                {self._BASE_JOINS}
            """

            count_query = f"""
                SELECT COUNT(*) FROM Payable p
                {self._BASE_JOINS}
            """

            sum_query = f"""
                SELECT ISNULL(SUM(p.Amount), 0), ISNULL(SUM(p.PaidAmount), 0), ISNULL(SUM(p.RemainingAmount), 0)
                FROM Payable p
                {self._BASE_JOINS}
            """

            conditions = []
            params = []

            if not include_deleted:
                conditions.append("p.IsActive = 1")

            if search:
                conditions.append("(p.VendorName LIKE ? OR m.MerchantName LIKE ? OR c.CustomerName LIKE ?)")
                p = f'%{search}%'
                params.extend([p, p, p])

            if status:
                conditions.append("p.Status = ?")
                params.append(status)

            where_clause = ""
            if conditions:
                where_clause = " WHERE " + " AND ".join(conditions)
                base_query += where_clause
                count_query += where_clause
                sum_query += where_clause

            offset = (page - 1) * per_page
            base_query += " ORDER BY p.PayableID DESC OFFSET ? ROWS FETCH NEXT ? ROWS ONLY"
            params.extend([offset, per_page])

            cursor.execute(base_query, params)
            rows = cursor.fetchall()

            count_params = params[:-2]
            cursor.execute(count_query, count_params)
            total_count = cursor.fetchone()[0]

            cursor.execute(sum_query, count_params)
            sum_row = cursor.fetchone()
            summaries = {
                'total_amount': float(sum_row[0]),
                'total_paid': float(sum_row[1]),
                'total_remaining': float(sum_row[2]),
            }

            return rows, total_count, summaries

    def get_by_id(self, payable_id, include_deleted=False):
        with DBConnection() as conn:
            cursor = conn.cursor()
            sql = f"""
                SELECT p.PayableID, p.VendorName, p.ExpenseTypeID,
                       ISNULL(sd.DictName, et.ExpenseTypeName) AS ExpenseTypeName,
                       p.Amount, p.PaidAmount,
                       p.RemainingAmount, p.DueDate, p.Status,
                       p.Description, p.ReferenceID, p.ReferenceType,
                       p.CreateTime, p.UpdateTime,
                       p.CustomerType, p.CustomerID,
                       {self._CUSTOMER_EXPR} AS CustomerName
                FROM Payable p
                {self._BASE_JOINS}
                WHERE p.PayableID = ?
            """
            if not include_deleted:
                sql += " AND p.IsActive = 1"

            cursor.execute(sql, (payable_id,))
            return cursor.fetchone()

    def get_list_by_customer(self, page=1, per_page=10, search=None, status=None):
        with DBConnection() as conn:
            cursor = conn.cursor()

            base_query = f"""
                SELECT
                    p.CustomerType,
                    p.CustomerID,
                    {self._CUSTOMER_EXPR} AS CustomerName,
                    COUNT(*) AS RecordCount,
                    SUM(p.Amount) AS TotalAmount,
                    SUM(p.PaidAmount) AS TotalPaid,
                    SUM(p.RemainingAmount) AS TotalRemaining,
                    MIN(p.DueDate) AS EarliestDueDate
                FROM Payable p
                {self._BASE_JOINS}
                WHERE p.IsActive = 1
            """

            conditions = []
            params = []

            if search:
                conditions.append(f"({self._CUSTOMER_EXPR} LIKE ?)")
                params.append(f'%{search}%')

            if status:
                conditions.append("p.Status = ?")
                params.append(status)

            extra_where = ""
            if conditions:
                extra_where = " AND " + " AND ".join(conditions)

            group_clause = f" GROUP BY p.CustomerType, p.CustomerID, {self._CUSTOMER_EXPR}"

            count_query = f"""
                SELECT COUNT(*) FROM (
                    SELECT p.CustomerType, p.CustomerID, {self._CUSTOMER_EXPR} AS CustomerName
                    FROM Payable p
                    {self._BASE_JOINS}
                    WHERE p.IsActive = 1
                    {extra_where}
                    GROUP BY p.CustomerType, p.CustomerID, {self._CUSTOMER_EXPR}
                ) sub
            """
            count_params = list(params)
            cursor.execute(count_query, count_params)
            total_count = cursor.fetchone()[0]

            sum_query = f"""
                SELECT ISNULL(SUM(sub.TotalAmount), 0), ISNULL(SUM(sub.TotalPaid), 0),
                       ISNULL(SUM(sub.TotalRemaining), 0), ISNULL(SUM(sub.RecordCount), 0)
                FROM (
                    SELECT
                        COUNT(*) AS RecordCount,
                        SUM(p.Amount) AS TotalAmount,
                        SUM(p.PaidAmount) AS TotalPaid,
                        SUM(p.RemainingAmount) AS TotalRemaining
                    FROM Payable p
                    {self._BASE_JOINS}
                    WHERE p.IsActive = 1
                    {extra_where}
                    GROUP BY p.CustomerType, p.CustomerID, {self._CUSTOMER_EXPR}
                ) sub
            """
            cursor.execute(sum_query, count_params)
            sum_row = cursor.fetchone()

            offset = (page - 1) * per_page
            base_query += extra_where + group_clause
            base_query += " ORDER BY TotalRemaining DESC, CustomerName OFFSET ? ROWS FETCH NEXT ? ROWS ONLY"
            params.extend([offset, per_page])

            cursor.execute(base_query, params)
            rows = cursor.fetchall()

            return rows, total_count, sum_row

    def create(self, vendor_name, expense_type_id, amount, due_date,
               description=None, customer_type='Merchant', customer_id=None):
        with DBConnection() as conn:
            cursor = conn.cursor()
            sql = """
                INSERT INTO Payable (VendorName, ExpenseTypeID, Amount, DueDate,
                                     Status, PaidAmount, RemainingAmount, Description,
                                     CustomerType, CustomerID)
                OUTPUT INSERTED.PayableID
                VALUES (?, ?, ?, ?, N'未付款', 0, ?, ?, ?, ?)
            """
            cursor.execute(sql, vendor_name, int(expense_type_id),
                           float(amount), due_date, float(amount), description,
                           customer_type, int(customer_id) if customer_id else None)
            row = cursor.fetchone()
            new_id = row[0] if row else None
            conn.commit()
            return new_id

    def soft_delete(self, payable_id, deleted_by, delete_reason=None):
        with DBConnection() as conn:
            cursor = conn.cursor()
            sql = """
                UPDATE Payable
                SET IsActive = 0,
                    DeletedBy = ?,
                    DeletedAt = GETDATE(),
                    DeleteReason = ?,
                    UpdateTime = GETDATE()
                WHERE PayableID = ? AND IsActive = 1
            """
            cursor.execute(sql, deleted_by, delete_reason, payable_id)
            affected = cursor.rowcount
            conn.commit()
            return affected

    def check_has_payment(self, payable_id):
        with DBConnection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT COUNT(*) FROM PaymentRecord
                WHERE PayableID = ?
            """, (payable_id,))
            return cursor.fetchone()[0]
```

- [ ] **步骤 2：验证模块可导入**

运行：`cd d:\BaiduSyncdisk\HF_metalmarket && python -c "from app.repositories.payable_repo import PayableRepository; print('OK')"`
预期：输出 `OK`

- [ ] **步骤 3：Commit**

```bash
git add app/repositories/payable_repo.py
git commit -m "feat: 添加应付账款数据访问层，对齐 receivable_repo 架构"
```

---

### 任务 5：重构 `receivable_service.py` — 使用 `format_utils`

**文件：**
- 修改：`app/services/receivable_service.py`

- [ ] **步骤 1：替换导入和删除内部函数**

将文件头部的 `_format_date` / `_format_datetime` 删除，改为从 `utils.format_utils` 导入。

**修改前（第1-24行）：**
```python
# -*- coding: utf-8 -*-
import datetime
from app.repositories.receivable_repo import ReceivableRepository
from utils.database import execute_query


def _format_date(val, fmt='%Y-%m-%d'):
    if not val:
        return ''
    if isinstance(val, str):
        return val[:10] if len(val) >= 10 else val
    if isinstance(val, (datetime.datetime, datetime.date)):
        return val.strftime(fmt)
    return str(val)


def _format_datetime(val):
    if not val:
        return ''
    if isinstance(val, str):
        return val[:16] if len(val) >= 16 else val
    if isinstance(val, datetime.datetime):
        return val.strftime('%Y-%m-%d %H:%M')
    return str(val)
```

**修改后：**
```python
# -*- coding: utf-8 -*-
from app.repositories.receivable_repo import ReceivableRepository
from utils.database import execute_query
from utils.format_utils import format_date, format_datetime
```

- [ ] **步骤 2：替换方法内的函数调用**

在 `get_receivables()` 方法中，将 `_format_date(` 替换为 `format_date(`，将 `_format_datetime(` 替换为 `format_datetime(`。

涉及行：
- 第55行：`'due_date': _format_date(row.DueDate),` → `'due_date': format_date(row.DueDate),`
- 第58行：`'create_time': _format_datetime(row.CreateTime),` → `'create_time': format_datetime(row.CreateTime),`

- [ ] **步骤 3：验证服务可导入**

运行：`cd d:\BaiduSyncdisk\HF_metalmarket && python -c "from app.services.receivable_service import ReceivableService; print('OK')"`
预期：输出 `OK`

- [ ] **步骤 4：Commit**

```bash
git add app/services/receivable_service.py
git commit -m "refactor: receivable_service 使用通用 format_utils 替代内部日期函数"
```

---

### 任务 6：重构 `finance_service.py` — 使用 `sequence` + `format_utils` + `payable_repo`

**文件：**
- 修改：`app/services/finance_service.py`

- [ ] **步骤 1：更新导入**

**修改前（第1-13行）：**
```python
# -*- coding: utf-8 -*-
"""
财务管理服务层
负责收款核销、付款核销、直接记账、现金流水等核心业务组合逻辑
"""
import logging
import re
from datetime import datetime
from utils.database import DBConnection
from app.repositories.receivable_repo import ReceivableRepository
from app.repositories.collection_record_repo import CollectionRecordRepository
from app.repositories.cash_flow_repo import CashFlowRepository
from app.services.account_service import AccountService
```

**修改后：**
```python
# -*- coding: utf-8 -*-
import logging
import re
from datetime import datetime
from utils.database import DBConnection
from utils.format_utils import format_date, format_datetime, safe_float
from utils.sequence import generate_serial_no
from app.repositories.receivable_repo import ReceivableRepository
from app.repositories.collection_record_repo import CollectionRecordRepository
from app.repositories.cash_flow_repo import CashFlowRepository
from app.repositories.payable_repo import PayableRepository
from app.services.account_service import AccountService
```

- [ ] **步骤 2：更新 `__init__` 添加 payable_repo**

**修改前：**
```python
    def __init__(self):
        self.receivable_repo = ReceivableRepository()
        self.collection_repo = CollectionRecordRepository()
        self.cash_flow_repo = CashFlowRepository()
        self.account_svc = AccountService()
```

**修改后：**
```python
    def __init__(self):
        self.receivable_repo = ReceivableRepository()
        self.collection_repo = CollectionRecordRepository()
        self.cash_flow_repo = CashFlowRepository()
        self.payable_repo = PayableRepository()
        self.account_svc = AccountService()
```

- [ ] **步骤 3：替换 `_generate_transaction_no` 调用**

在 `collect_receivable()` 方法中（约第114行）：

**修改前：**
```python
                transaction_no = self._generate_transaction_no(cursor, 'CF')
```

**修改后：**
```python
                transaction_no = generate_serial_no(cursor, 'CF', 'CashFlow', 'TransactionNo')
```

在 `pay_payable()` 方法中（约第236行）：

**修改前：**
```python
                transaction_no = self._generate_transaction_no(cursor, 'CF')
```

**修改后：**
```python
                transaction_no = generate_serial_no(cursor, 'CF', 'CashFlow', 'TransactionNo')
```

在 `batch_pay_by_customer()` 方法中（约第634行）：

**修改前：**
```python
                    transaction_no = self._generate_transaction_no(cursor, 'CF')
```

**修改后：**
```python
                    transaction_no = generate_serial_no(cursor, 'CF', 'CashFlow', 'TransactionNo')
```

在 `direct_entry()` 方法中（约第1149行）：

**修改前：**
```python
                transaction_no = self._generate_transaction_no(cursor, 'CF')
```

**修改后：**
```python
                transaction_no = generate_serial_no(cursor, 'CF', 'CashFlow', 'TransactionNo')
```

- [ ] **步骤 4：重构 `get_payables()` 使用 `payable_repo`**

**修改前（第298-404行）：**
```python
    def get_payables(self, page=1, per_page=10, search=None, status=None):
        """获取应付账款列表（费用类型从字典表获取）"""
        with DBConnection() as conn:
            cursor = conn.cursor()
            # ... 约100行 SQL + 分页 + 行转字典逻辑 ...
```

**修改后：**
```python
    def get_payables(self, page=1, per_page=10, search=None, status=None):
        """获取应付账款列表"""
        rows, total_count, summaries = self.payable_repo.get_list(
            page=page, per_page=per_page, search=search, status=status
        )

        result_list = []
        for row in rows:
            result_list.append({
                'payable_id': row.PayableID,
                'vendor_name': row.VendorName,
                'customer_type': row.CustomerType or 'Merchant',
                'customer_id': row.CustomerID,
                'customer_name': row.CustomerName or row.VendorName,
                'expense_type_id': row.ExpenseTypeID,
                'expense_type_name': row.ExpenseTypeName,
                'amount': safe_float(row.Amount),
                'paid_amount': safe_float(row.PaidAmount),
                'remaining_amount': safe_float(row.RemainingAmount),
                'due_date': format_date(row.DueDate),
                'status': row.Status,
                'description': row.Description or '',
                'create_time': format_datetime(row.CreateTime),
                'expense_order_id': row.ExpenseOrderID,
            })

        return {
            'items': result_list,
            'total_count': total_count,
            'total_pages': (total_count + per_page - 1) // per_page if total_count > 0 else 0,
            'current_page': page,
            'summary': summaries
        }
```

- [ ] **步骤 5：重构 `get_payables_by_customer()` 使用 `payable_repo`**

**修改前（第406-535行）：**
```python
    def get_payables_by_customer(self, page=1, per_page=10, search=None, status=None):
        """按客户汇总应付账款"""
        with DBConnection() as conn:
            cursor = conn.cursor()
            # ... 约130行 SQL + 分页 + 行转字典逻辑 ...
```

**修改后：**
```python
    def get_payables_by_customer(self, page=1, per_page=10, search=None, status=None):
        """按客户汇总应付账款"""
        rows, total_count, sum_row = self.payable_repo.get_list_by_customer(
            page=page, per_page=per_page, search=search, status=status
        )

        items = []
        for row in rows:
            items.append({
                'customer_type': row.CustomerType or 'Merchant',
                'customer_id': row.CustomerID,
                'customer_name': row.CustomerName or '',
                'record_count': row.RecordCount,
                'total_amount': safe_float(row.TotalAmount),
                'total_paid': safe_float(row.TotalPaid),
                'total_remaining': safe_float(row.TotalRemaining),
                'earliest_due_date': format_date(row.EarliestDueDate),
            })

        return {
            'items': items,
            'total_count': total_count,
            'total_pages': (total_count + per_page - 1) // per_page if total_count > 0 else 0,
            'current_page': page,
            'summary': {
                'total_amount': safe_float(sum_row[0]),
                'total_paid': safe_float(sum_row[1]),
                'total_remaining': safe_float(sum_row[2]),
                'total_records': int(sum_row[3]),
            }
        }
```

- [ ] **步骤 6：重构 `_get_payable_by_id()` 使用 `payable_repo`**

**修改前（第272-296行）：**
```python
    def _get_payable_by_id(self, payable_id):
        """获取应付记录详情（费用类型从字典表获取）"""
        with DBConnection() as conn:
            cursor = conn.cursor()
            cursor.execute("""...""", (payable_id,))
            return cursor.fetchone()
```

**修改后：**
```python
    def _get_payable_by_id(self, payable_id):
        """获取应付记录详情"""
        return self.payable_repo.get_by_id(payable_id)
```

- [ ] **步骤 7：重构 `soft_delete_payable()` 使用 `payable_repo`**

**修改前（第678-727行）：**
```python
    def soft_delete_payable(self, payable_id, deleted_by, delete_reason=None):
        with DBConnection() as conn:
            cursor = conn.cursor()
            # ... 约50行 SQL 逻辑 ...
```

**修改后：**
```python
    def soft_delete_payable(self, payable_id, deleted_by, delete_reason=None):
        payable = self.payable_repo.get_by_id(payable_id)
        if not payable:
            return {'success': False, 'message': '应付记录不存在或已删除'}

        if payable.Status in ('已付款', '部分付款'):
            return {'success': False, 'message': f'状态为"{payable.Status}"的应付不允许删除，已有付款记录关联'}

        affected = self.payable_repo.soft_delete(payable_id, deleted_by, delete_reason)
        if affected > 0:
            return {'success': True, 'message': '删除成功'}
        else:
            return {'success': False, 'message': '删除失败，请重试'}
```

- [ ] **步骤 8：重构 `create_payable()` 使用 `payable_repo`**

**修改前（第729-787行）：**
```python
    def create_payable(self, vendor_name=None, ...):
        # ... 约60行含 SQL ...
```

**修改后：**
```python
    def create_payable(self, vendor_name=None, expense_type_id=None, amount=None, due_date=None,
                       description=None, created_by=None,
                       customer_type='Merchant', customer_id=None):
        resolved_name = vendor_name
        if customer_type and customer_id:
            if customer_type == 'Merchant':
                with DBConnection() as conn:
                    cursor = conn.cursor()
                    cursor.execute("SELECT MerchantName FROM Merchant WHERE MerchantID = ?", int(customer_id))
                    row = cursor.fetchone()
                    if row:
                        resolved_name = row.MerchantName
            elif customer_type == 'Customer':
                with DBConnection() as conn:
                    cursor = conn.cursor()
                    cursor.execute("SELECT CustomerName FROM Customer WHERE CustomerID = ?", int(customer_id))
                    row = cursor.fetchone()
                    if row:
                        resolved_name = row.CustomerName

        if not resolved_name:
            raise ValueError("请选择客户或输入供应商名称")
        if not expense_type_id:
            raise ValueError("请选择费用类型")
        from app.services.dict_service import DictService
        expense_items = DictService.get_expense_items('expense_item_expend')
        valid_ids = [item['dict_id'] for item in expense_items]
        if int(expense_type_id) not in valid_ids:
            raise ValueError("所选费用类型无效，请重新选择")
        if not amount or float(amount) <= 0:
            raise ValueError("应付金额必须大于0")
        if not due_date:
            raise ValueError("请选择到期日期")

        return self.payable_repo.create(
            vendor_name=resolved_name,
            expense_type_id=int(expense_type_id),
            amount=float(amount),
            due_date=due_date,
            description=description,
            customer_type=customer_type,
            customer_id=customer_id,
        )
```

- [ ] **步骤 9：替换日期格式化调用**

在 `get_payment_records()` 方法中（约第812-815行）：

**修改前：**
```python
                    'transaction_date': row.TransactionDate.strftime('%Y-%m-%d') if row.TransactionDate else '',
```

**修改后：**
```python
                    'transaction_date': format_date(row.TransactionDate),
```

**修改前：**
```python
                    'create_time': row.CreateTime.strftime('%Y-%m-%d %H:%M') if row.CreateTime else '',
```

**修改后：**
```python
                    'create_time': format_datetime(row.CreateTime),
```

在 `get_cash_flows()` 方法中（约第841-845行）：

**修改前：**
```python
                'transaction_date': row.TransactionDate.strftime('%Y-%m-%d') if row.TransactionDate else '',
```

**修改后：**
```python
                'transaction_date': format_date(row.TransactionDate),
```

**修改前：**
```python
                'create_time': row.CreateTime.strftime('%Y-%m-%d %H:%M') if row.CreateTime else '',
```

**修改后：**
```python
                'create_time': format_datetime(row.CreateTime),
```

在 `get_receivable_detail()` 方法中（约第890-918行）：

**修改前：**
```python
                'transaction_date': row.TransactionDate.strftime('%Y-%m-%d') if row.TransactionDate else '',
```

**修改后：**
```python
                'transaction_date': format_date(row.TransactionDate),
```

**修改前：**
```python
                'create_time': row.CreateTime.strftime('%Y-%m-%d %H:%M') if row.CreateTime else '',
```

**修改后：**
```python
                'create_time': format_datetime(row.CreateTime),
```

**修改前：**
```python
            'due_date': receivable.DueDate.strftime('%Y-%m-%d') if receivable.DueDate else '',
```

**修改后：**
```python
            'due_date': format_date(receivable.DueDate),
```

**修改前：**
```python
            'create_time': receivable.CreateTime.strftime('%Y-%m-%d %H:%M') if receivable.CreateTime else '',
```

**修改后：**
```python
            'create_time': format_datetime(receivable.CreateTime),
```

**修改前：**
```python
            'deleted_at': receivable.DeletedAt.strftime('%Y-%m-%d %H:%M') if hasattr(receivable, 'DeletedAt') and receivable.DeletedAt else '',
```

**修改后：**
```python
            'deleted_at': format_datetime(receivable.DeletedAt) if hasattr(receivable, 'DeletedAt') else '',
```

在 `_get_contract_summary()` 方法中（约第983-984行）：

**修改前：**
```python
                    'start_date': row.StartDate.strftime('%Y-%m-%d') if row.StartDate else '',
                    'end_date': row.EndDate.strftime('%Y-%m-%d') if row.EndDate else '',
```

**修改后：**
```python
                    'start_date': format_date(row.StartDate),
                    'end_date': format_date(row.EndDate),
```

- [ ] **步骤 10：删除 `_generate_transaction_no` 方法**

删除 `finance_service.py` 末尾的 `_generate_transaction_no` 方法（约第1190-1208行），因为已替换为 `generate_serial_no`。

- [ ] **步骤 11：验证服务可导入**

运行：`cd d:\BaiduSyncdisk\HF_metalmarket && python -c "from app.services.finance_service import FinanceService; print('OK')"`
预期：输出 `OK`

- [ ] **步骤 12：Commit**

```bash
git add app/services/finance_service.py
git commit -m "refactor: finance_service 使用通用工具和 payable_repo 替代重复代码"
```

---

### 任务 7：重构 `prepayment_service.py` — 使用 `format_utils`

**文件：**
- 修改：`app/services/prepayment_service.py`

- [ ] **步骤 1：添加导入**

在文件头部添加：
```python
from utils.format_utils import format_date, format_datetime, safe_float
```

- [ ] **步骤 2：替换所有日期格式化调用**

在 `get_prepayments()` 方法中（约第99行）：

**修改前：**
```python
                    'create_time': row.CreateTime.strftime('%Y-%m-%d %H:%M') if row.CreateTime else '',
```

**修改后：**
```python
                    'create_time': format_datetime(row.CreateTime),
```

在 `get_prepayment_by_id()` 方法中（约第146行）：

**修改前：**
```python
                'create_time': row.CreateTime.strftime('%Y-%m-%d %H:%M') if row.CreateTime else '',
```

**修改后：**
```python
                'create_time': format_datetime(row.CreateTime),
```

在 `get_apply_records()` 方法中（约第428行）：

**修改前：**
```python
                    'create_time': row.CreateTime.strftime('%Y-%m-%d %H:%M') if row.CreateTime else '',
```

**修改后：**
```python
                    'create_time': format_datetime(row.CreateTime),
```

在 `get_available_prepayments()` 方法中（约第457行）：

**修改前：**
```python
                    'create_time': row.CreateTime.strftime('%Y-%m-%d %H:%M') if row.CreateTime else '',
```

**修改后：**
```python
                    'create_time': format_datetime(row.CreateTime),
```

- [ ] **步骤 3：验证服务可导入**

运行：`cd d:\BaiduSyncdisk\HF_metalmarket && python -c "from app.services.prepayment_service import PrepaymentService; print('OK')"`
预期：输出 `OK`

- [ ] **步骤 4：Commit**

```bash
git add app/services/prepayment_service.py
git commit -m "refactor: prepayment_service 使用通用 format_utils 替代重复日期格式化"
```

---

### 任务 8：重构 `deposit_service.py` — 使用 `format_utils`

**文件：**
- 修改：`app/services/deposit_service.py`

- [ ] **步骤 1：添加导入**

在文件头部添加：
```python
from utils.format_utils import format_date, format_datetime, safe_float
```

- [ ] **步骤 2：替换所有日期格式化调用**

在 `get_deposits()` 方法中（约第100行）：

**修改前：**
```python
                    'create_time': row.CreateTime.strftime('%Y-%m-%d %H:%M') if row.CreateTime else '',
```

**修改后：**
```python
                    'create_time': format_datetime(row.CreateTime),
```

搜索文件中所有 `.strftime('%Y-%m-%d %H:%M') if` 和 `.strftime('%Y-%m-%d') if` 模式，逐一替换为 `format_datetime()` 和 `format_date()`。

- [ ] **步骤 3：验证服务可导入**

运行：`cd d:\BaiduSyncdisk\HF_metalmarket && python -c "from app.services.deposit_service import DepositService; print('OK')"`
预期：输出 `OK`

- [ ] **步骤 4：Commit**

```bash
git add app/services/deposit_service.py
git commit -m "refactor: deposit_service 使用通用 format_utils 替代重复日期格式化"
```

---

### 任务 9：重构 `account_service.py` — 使用 `format_utils`

**文件：**
- 修改：`app/services/account_service.py`

- [ ] **步骤 1：添加导入**

在文件头部添加：
```python
from utils.format_utils import format_datetime
```

- [ ] **步骤 2：替换所有日期格式化调用**

在 `get_accounts()` 方法中（约第53-54行）：

**修改前：**
```python
                    'create_time': row.CreateTime.strftime('%Y-%m-%d %H:%M') if row.CreateTime else '',
                    'update_time': row.UpdateTime.strftime('%Y-%m-%d %H:%M') if row.UpdateTime else '',
```

**修改后：**
```python
                    'create_time': format_datetime(row.CreateTime),
                    'update_time': format_datetime(row.UpdateTime),
```

- [ ] **步骤 3：验证服务可导入**

运行：`cd d:\BaiduSyncdisk\HF_metalmarket && python -c "from app.services.account_service import AccountService; print('OK')"`
预期：输出 `OK`

- [ ] **步骤 4：Commit**

```bash
git add app/services/account_service.py
git commit -m "refactor: account_service 使用通用 format_utils 替代重复日期格式化"
```

---

### 任务 10：重构 `expense_service.py` — 使用 `sequence` + `format_utils`

**文件：**
- 修改：`app/services/expense_service.py`

- [ ] **步骤 1：添加导入**

在文件头部添加：
```python
from utils.format_utils import format_date, format_datetime, safe_float
from utils.sequence import generate_serial_no
```

- [ ] **步骤 2：替换 `_generate_order_no` 调用**

搜索 `_generate_order_no` 的调用处，替换为：

**修改前：**
```python
        order_no = self._generate_order_no(cursor)
```

**修改后：**
```python
        order_no = generate_serial_no(cursor, 'EO', 'ExpenseOrder', 'OrderNo')
```

- [ ] **步骤 3：删除 `_generate_order_no` 方法**

删除 `expense_service.py` 中的 `_generate_order_no` 方法（约第288-306行）。

- [ ] **步骤 4：替换所有日期格式化调用**

搜索文件中所有 `.strftime('%Y-%m-%d %H:%M') if` 和 `.strftime('%Y-%m-%d') if` 模式，逐一替换为 `format_datetime()` 和 `format_date()`。

- [ ] **步骤 5：验证服务可导入**

运行：`cd d:\BaiduSyncdisk\HF_metalmarket && python -c "from app.services.expense_service import ExpenseService; print('OK')"`
预期：输出 `OK`

- [ ] **步骤 6：Commit**

```bash
git add app/services/expense_service.py
git commit -m "refactor: expense_service 使用通用 sequence 和 format_utils 替代重复代码"
```

---

### 任务 11：全局验证 — 确保所有修改后功能正常

**文件：**
- 无新文件

- [ ] **步骤 1：验证所有模块可正常导入**

运行：
```bash
cd d:\BaiduSyncdisk\HF_metalmarket && python -c "
from utils.format_utils import format_date, format_datetime, safe_float, safe_int
from utils.query_helper import build_where, paginate, paginate_result
from utils.sequence import generate_serial_no
from app.repositories.payable_repo import PayableRepository
from app.services.receivable_service import ReceivableService
from app.services.finance_service import FinanceService
from app.services.prepayment_service import PrepaymentService
from app.services.deposit_service import DepositService
from app.services.account_service import AccountService
from app.services.expense_service import ExpenseService
print('ALL OK')
"
```
预期：输出 `ALL OK`

- [ ] **步骤 2：验证 Flask 应用可启动**

运行：
```bash
cd d:\BaiduSyncdisk\HF_metalmarket && python -c "from app import create_app; app = create_app(); print('APP OK')"
```
预期：输出 `APP OK`

- [ ] **步骤 3：最终 Commit**

```bash
git add -A
git commit -m "chore: 通用工具类封装完成，消除应收/应付重复代码"
```

---

## 自检

### 1. 规格覆盖度

| 需求 | 对应任务 |
|------|---------|
| 日期格式化通用封装 | 任务 1（创建）+ 任务 5/6/7/8/9/10（使用） |
| 分页查询通用封装 | 任务 2（创建，供后续使用） |
| 条件构建通用封装 | 任务 2（创建，供后续使用） |
| 单号生成通用封装 | 任务 3（创建）+ 任务 6/10（使用） |
| PayableRepository | 任务 4（创建）+ 任务 6（使用） |
| 统一分页返回结构 | 任务 2 中 `paginate_result()` 函数 |
| safe_float/safe_int | 任务 1（创建）+ 任务 6（使用） |

### 2. 占位符扫描

无"待定"、"TODO"、"后续实现"等占位符。所有步骤均包含完整代码。

### 3. 类型一致性

- `format_date(val, fmt)` 签名在 `format_utils.py` 和所有调用处一致
- `format_datetime(val, fmt)` 签名一致
- `generate_serial_no(cursor, prefix, table_name, column_name)` 签名一致
- `PayableRepository` 的方法名与 `FinanceService` 中的调用一致
- `safe_float(val, default)` 签名一致

---

## 执行交接

计划已完成并保存到 `docs/superpowers/plans/2026-04-20-finance-utils-refactor.md`。两种执行方式：

**1. 子代理驱动（推荐）** - 每个任务调度一个新的子代理，任务间进行审查，快速迭代

**2. 内联执行** - 在当前会话中使用 executing-plans 执行任务，批量执行并设有检查点

选哪种方式？
