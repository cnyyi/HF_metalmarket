# 垃圾费管理模块 实现计划

> **面向 AI 代理的工作者：** 必需子技能：使用 superpowers:subagent-driven-development（推荐）或 superpowers:executing-plans 逐任务实现此计划。步骤使用复选框（`- [ ]`）语法来跟踪进度。

**目标：** 新增垃圾费管理模块，按商户业态类型及租赁面积核算年度垃圾费，自动联动生成应收账款。

**架构：** Routes → Services → DBConnection 三层分离。新增 `garbage_fee_bp` 蓝图（`/garbage_fee`），服务层 `GarbageFeeService` 负责批量生成、CRUD、应收联动。业态单价和保底金额复用 `Sys_Dictionary` 的 `UnitPrice` 和新增 `MinAmount` 字段。

**技术栈：** Flask + pyodbc (MSSQL) + jQuery + Bootstrap 5

---

## 文件结构

| 操作 | 文件 | 职责 |
|------|------|------|
| 创建 | `scripts/add_garbage_fee_tables.sql` | 数据库迁移：建表、加字段、加字典、加权限 |
| 创建 | `app/services/garbage_fee_service.py` | 服务层：批量生成、CRUD、应收联动、导出 |
| 创建 | `app/routes/garbage_fee.py` | 路由层：页面渲染 + API |
| 创建 | `templates/garbage_fee/list.html` | 列表页（含编辑模态窗口） |
| 创建 | `templates/garbage_fee/generate.html` | 批量生成页 |
| 创建 | `templates/garbage_fee/detail.html` | 详情页 |
| 创建 | `scripts/add_garbage_fee_permission.py` | 权限初始化脚本 |
| 修改 | `app/__init__.py:29-48` | 注册 garbage_fee_bp 蓝图 |
| 修改 | `templates/admin_base.html:89-94` | 侧边栏添加垃圾费菜单项 |

---

### 任务 1：数据库迁移脚本

**文件：**
- 创建：`scripts/add_garbage_fee_tables.sql`

- [ ] **步骤 1：编写迁移 SQL 脚本**

```sql
-- ================================================
-- 垃圾费管理模块数据库迁移
-- ================================================

-- 1. Sys_Dictionary 添加 MinAmount 字段
IF NOT EXISTS (
    SELECT 1 FROM sys.columns
    WHERE object_id = OBJECT_ID('Sys_Dictionary') AND name = 'MinAmount'
)
BEGIN
    ALTER TABLE Sys_Dictionary ADD MinAmount DECIMAL(10,2) NULL;
    PRINT '已添加 MinAmount 字段到 Sys_Dictionary 表';
END
ELSE
BEGIN
    PRINT 'MinAmount 字段已存在，跳过';
END
GO

-- 2. 创建 GarbageFee 表
IF NOT EXISTS (SELECT * FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME = 'GarbageFee')
BEGIN
    CREATE TABLE GarbageFee (
        GarbageFeeID    INT IDENTITY(1,1) PRIMARY KEY,
        MerchantID      INT NOT NULL,
        Year            INT NOT NULL,
        BusinessType    NVARCHAR(100) NULL,
        RentalArea      DECIMAL(10,2) NULL,
        UnitPrice       DECIMAL(10,2) NULL,
        MinAmount       DECIMAL(10,2) NULL,
        CalculatedFee   DECIMAL(10,2) NULL,
        FinalFee        DECIMAL(10,2) NOT NULL,
        ReceivableID    INT NULL,
        Status          NVARCHAR(20) NOT NULL DEFAULT N'待收取',
        Description     NVARCHAR(500) NULL,
        CreateBy        INT NULL,
        CreateTime      DATETIME NULL DEFAULT GETDATE(),
        UpdateBy        INT NULL,
        UpdateTime      DATETIME NULL,
        CONSTRAINT UQ_GarbageFee_Merchant_Year UNIQUE (MerchantID, Year)
    );
    PRINT 'GarbageFee 表创建成功';
END
ELSE
BEGIN
    PRINT 'GarbageFee 表已存在，跳过';
END
GO

-- 3. 添加垃圾费收入类费用项字典
IF NOT EXISTS (SELECT 1 FROM Sys_Dictionary WHERE DictType = N'expense_item_income' AND DictCode = N'garbage_fee')
BEGIN
    INSERT INTO Sys_Dictionary (DictType, DictCode, DictName, Description, SortOrder, IsActive, CreateTime)
    VALUES (N'expense_item_income', N'garbage_fee', N'垃圾费', N'商户垃圾费收入', 8, 1, GETDATE());
    PRINT '已添加垃圾费费用项字典';
END
GO

-- 4. 创建索引
IF NOT EXISTS (
    SELECT 1 FROM sys.indexes WHERE object_id = OBJECT_ID('GarbageFee') AND name = 'idx_garbage_fee_year'
)
BEGIN
    CREATE INDEX idx_garbage_fee_year ON GarbageFee(Year);
    PRINT '已创建 idx_garbage_fee_year 索引';
END
GO

IF NOT EXISTS (
    SELECT 1 FROM sys.indexes WHERE object_id = OBJECT_ID('GarbageFee') AND name = 'idx_garbage_fee_status'
)
BEGIN
    CREATE INDEX idx_garbage_fee_status ON GarbageFee(Status);
    PRINT '已创建 idx_garbage_fee_status 索引';
END
GO

PRINT '========================================';
PRINT '垃圾费管理模块数据库迁移完成';
PRINT '========================================';
```

- [ ] **步骤 2：执行迁移脚本**

运行：`python -c "from utils.database import DBConnection; import sys; conn = DBConnection().__enter__(); cursor = conn.cursor(); [cursor.execute(stmt) for stmt in open('scripts/add_garbage_fee_tables.sql', encoding='utf-8').read().split('GO') if stmt.strip()]; conn.commit(); print('Migration done')"`

或者直接在 SSMS 中执行 `scripts/add_garbage_fee_tables.sql`。

预期：表创建成功，字段添加成功，字典项插入成功。

- [ ] **步骤 3：验证数据库变更**

运行以下查询确认：
- `SELECT * FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME = 'GarbageFee'` → 应有 1 行
- `SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('Sys_Dictionary') AND name = 'MinAmount'` → 应有 1 行
- `SELECT * FROM Sys_Dictionary WHERE DictType = N'expense_item_income' AND DictCode = N'garbage_fee'` → 应有 1 行

---

### 任务 2：服务层实现

**文件：**
- 创建：`app/services/garbage_fee_service.py`

- [ ] **步骤 1：编写 GarbageFeeService 完整代码**

```python
# -*- coding: utf-8 -*-
import logging
from datetime import datetime
from io import BytesIO
from utils.database import DBConnection
from utils.format_utils import format_date, format_datetime

logger = logging.getLogger(__name__)

GARBAGE_FEE_DICT_CODE = 'garbage_fee'
GARBAGE_FEE_DICT_NAME = '垃圾费'
GARBAGE_FEE_DICT_TYPE = 'expense_item_income'


def _get_garbage_fee_expense_type_id(cursor):
    cursor.execute("""
        SELECT DictID FROM Sys_Dictionary
        WHERE DictType = ? AND DictCode = ? AND IsActive = 1
    """, (GARBAGE_FEE_DICT_TYPE, GARBAGE_FEE_DICT_CODE))
    row = cursor.fetchone()
    if row:
        return row.DictID

    cursor.execute("""
        SELECT DictID FROM Sys_Dictionary
        WHERE DictType = ? AND DictName = ? AND IsActive = 1
    """, (GARBAGE_FEE_DICT_TYPE, GARBAGE_FEE_DICT_NAME))
    row = cursor.fetchone()
    if row:
        return row.DictID

    return None


class GarbageFeeService:

    def get_list(self, page=1, per_page=10, year=None, business_type=None,
                 status=None, search=None):
        with DBConnection() as conn:
            cursor = conn.cursor()

            base_query = """
                SELECT gf.GarbageFeeID, gf.MerchantID, gf.Year, gf.BusinessType,
                       gf.RentalArea, gf.UnitPrice, gf.MinAmount,
                       gf.CalculatedFee, gf.FinalFee, gf.ReceivableID,
                       gf.Status, gf.Description,
                       gf.CreateBy, gf.CreateTime, gf.UpdateBy, gf.UpdateTime,
                       m.MerchantName,
                       u.RealName AS CreateUserName
                FROM GarbageFee gf
                LEFT JOIN Merchant m ON gf.MerchantID = m.MerchantID
                LEFT JOIN [User] u ON gf.CreateBy = u.UserID
            """
            count_query = """
                SELECT COUNT(*) FROM GarbageFee gf
                LEFT JOIN Merchant m ON gf.MerchantID = m.MerchantID
            """
            summary_query = """
                SELECT ISNULL(COUNT(*), 0),
                       ISNULL(SUM(gf.RentalArea), 0),
                       ISNULL(SUM(gf.FinalFee), 0)
                FROM GarbageFee gf
                LEFT JOIN Merchant m ON gf.MerchantID = m.MerchantID
            """

            conditions = []
            params = []

            if year:
                conditions.append("gf.Year = ?")
                params.append(int(year))

            if business_type:
                conditions.append("gf.BusinessType = ?")
                params.append(business_type)

            if status:
                conditions.append("gf.Status = ?")
                params.append(status)

            if search:
                conditions.append("(m.MerchantName LIKE ? OR gf.Description LIKE ?)")
                p = f'%{search}%'
                params.extend([p, p])

            where_clause = ""
            if conditions:
                where_clause = " WHERE " + " AND ".join(conditions)
                base_query += where_clause
                count_query += where_clause
                summary_query += where_clause

            cursor.execute(count_query, tuple(params))
            total_count = cursor.fetchone()[0]

            cursor.execute(summary_query, tuple(params))
            summary_row = cursor.fetchone()
            summary = {
                'total_count': summary_row[0],
                'total_area': float(summary_row[1]),
                'total_fee': float(summary_row[2]),
            }

            offset = (page - 1) * per_page
            base_query += " ORDER BY gf.Year DESC, gf.GarbageFeeID DESC OFFSET ? ROWS FETCH NEXT ? ROWS ONLY"
            params.extend([offset, per_page])

            cursor.execute(base_query, tuple(params))
            rows = cursor.fetchall()

            items = []
            for row in rows:
                create_time = row.CreateTime
                create_time_str = create_time.strftime('%Y-%m-%d %H:%M') if create_time and hasattr(create_time, 'strftime') else ''
                items.append({
                    'garbage_fee_id': row.GarbageFeeID,
                    'merchant_id': row.MerchantID,
                    'merchant_name': row.MerchantName or '',
                    'year': row.Year,
                    'business_type': row.BusinessType or '',
                    'rental_area': float(row.RentalArea) if row.RentalArea else 0,
                    'unit_price': float(row.UnitPrice) if row.UnitPrice else 0,
                    'min_amount': float(row.MinAmount) if row.MinAmount else 0,
                    'calculated_fee': float(row.CalculatedFee) if row.CalculatedFee else 0,
                    'final_fee': float(row.FinalFee) if row.FinalFee else 0,
                    'receivable_id': row.ReceivableID,
                    'status': row.Status or '',
                    'description': row.Description or '',
                    'create_user_name': row.CreateUserName or '',
                    'create_time': create_time_str,
                })

            total_pages = (total_count + per_page - 1) // per_page if total_count > 0 else 1

            return {
                'items': items,
                'total': total_count,
                'page': page,
                'per_page': per_page,
                'total_pages': total_pages,
                'summary': summary,
            }

    def get_detail(self, garbage_fee_id):
        with DBConnection() as conn:
            cursor = conn.cursor()

            cursor.execute("""
                SELECT gf.GarbageFeeID, gf.MerchantID, gf.Year, gf.BusinessType,
                       gf.RentalArea, gf.UnitPrice, gf.MinAmount,
                       gf.CalculatedFee, gf.FinalFee, gf.ReceivableID,
                       gf.Status, gf.Description,
                       gf.CreateBy, gf.CreateTime, gf.UpdateBy, gf.UpdateTime,
                       m.MerchantName,
                       u.RealName AS CreateUserName
                FROM GarbageFee gf
                LEFT JOIN Merchant m ON gf.MerchantID = m.MerchantID
                LEFT JOIN [User] u ON gf.CreateBy = u.UserID
                WHERE gf.GarbageFeeID = ?
            """, (garbage_fee_id,))
            row = cursor.fetchone()
            if not row:
                return None

            create_time = row.CreateTime
            create_time_str = create_time.strftime('%Y-%m-%d %H:%M') if create_time and hasattr(create_time, 'strftime') else ''
            update_time = row.UpdateTime
            update_time_str = update_time.strftime('%Y-%m-%d %H:%M') if update_time and hasattr(update_time, 'strftime') else ''

            receivable_info = None
            if row.ReceivableID:
                cursor.execute("""
                    SELECT ReceivableID, Amount, PaidAmount, RemainingAmount, Status
                    FROM Receivable WHERE ReceivableID = ? AND IsActive = 1
                """, (row.ReceivableID,))
                rev_row = cursor.fetchone()
                if rev_row:
                    receivable_info = {
                        'receivable_id': rev_row.ReceivableID,
                        'amount': float(rev_row.Amount),
                        'paid_amount': float(rev_row.PaidAmount),
                        'remaining_amount': float(rev_row.RemainingAmount),
                        'status': rev_row.Status,
                    }

            return {
                'garbage_fee_id': row.GarbageFeeID,
                'merchant_id': row.MerchantID,
                'merchant_name': row.MerchantName or '',
                'year': row.Year,
                'business_type': row.BusinessType or '',
                'rental_area': float(row.RentalArea) if row.RentalArea else 0,
                'unit_price': float(row.UnitPrice) if row.UnitPrice else 0,
                'min_amount': float(row.MinAmount) if row.MinAmount else 0,
                'calculated_fee': float(row.CalculatedFee) if row.CalculatedFee else 0,
                'final_fee': float(row.FinalFee) if row.FinalFee else 0,
                'receivable_id': row.ReceivableID,
                'receivable_info': receivable_info,
                'status': row.Status or '',
                'description': row.Description or '',
                'create_user_name': row.CreateUserName or '',
                'create_time': create_time_str,
                'update_time': update_time_str,
            }

    def get_preview(self, year):
        with DBConnection() as conn:
            cursor = conn.cursor()

            cursor.execute("""
                SELECT m.MerchantID, m.MerchantName, m.BusinessType,
                       ISNULL(SUM(cp.Area), 0) AS TotalArea
                FROM Merchant m
                INNER JOIN Contract c ON m.MerchantID = c.MerchantID
                INNER JOIN ContractPlot cp ON c.ContractID = cp.ContractID
                WHERE c.Status = N'有效'
                  AND c.StartDate <= ?
                  AND c.EndDate >= ?
                GROUP BY m.MerchantID, m.MerchantName, m.BusinessType
                ORDER BY m.MerchantName
            """, (f'{year}-12-31', f'{year}-01-01'))
            rows = cursor.fetchall()

            items = []
            skipped = []

            for row in rows:
                merchant_id = row.MerchantID
                merchant_name = row.MerchantName or ''
                business_type = row.BusinessType or ''
                total_area = float(row.TotalArea)

                cursor.execute("""
                    SELECT GarbageFeeID FROM GarbageFee
                    WHERE MerchantID = ? AND Year = ?
                """, (merchant_id, year))
                if cursor.fetchone():
                    skipped.append({
                        'merchant_id': merchant_id,
                        'merchant_name': merchant_name,
                        'reason': '该年度已存在垃圾费记录',
                    })
                    continue

                unit_price = 0
                min_amount = 0
                if business_type:
                    cursor.execute("""
                        SELECT UnitPrice, MinAmount FROM Sys_Dictionary
                        WHERE DictType = N'business_type' AND DictName = ? AND IsActive = 1
                    """, (business_type,))
                    dict_row = cursor.fetchone()
                    if dict_row:
                        unit_price = float(dict_row.UnitPrice) if dict_row.UnitPrice else 0
                        min_amount = float(dict_row.MinAmount) if dict_row.MinAmount else 0

                if not business_type or (unit_price == 0 and min_amount == 0):
                    skipped.append({
                        'merchant_id': merchant_id,
                        'merchant_name': merchant_name,
                        'reason': '未设置业态类型或字典中无对应单价/保底',
                    })
                    continue

                calculated_fee = unit_price * total_area
                final_fee = max(calculated_fee, min_amount)

                items.append({
                    'merchant_id': merchant_id,
                    'merchant_name': merchant_name,
                    'business_type': business_type,
                    'rental_area': total_area,
                    'unit_price': unit_price,
                    'min_amount': min_amount,
                    'calculated_fee': round(calculated_fee, 2),
                    'final_fee': round(final_fee, 2),
                })

            return {
                'items': items,
                'skipped': skipped,
                'total_count': len(items) + len(skipped),
                'generate_count': len(items),
                'skip_count': len(skipped),
            }

    def batch_generate(self, year, created_by=None):
        with DBConnection() as conn:
            cursor = conn.cursor()

            expense_type_id = _get_garbage_fee_expense_type_id(cursor)
            if not expense_type_id:
                raise ValueError("未找到垃圾费费用类型字典项，请先执行数据库迁移脚本")

            cursor.execute("""
                SELECT m.MerchantID, m.MerchantName, m.BusinessType,
                       ISNULL(SUM(cp.Area), 0) AS TotalArea
                FROM Merchant m
                INNER JOIN Contract c ON m.MerchantID = c.MerchantID
                INNER JOIN ContractPlot cp ON c.ContractID = cp.ContractID
                WHERE c.Status = N'有效'
                  AND c.StartDate <= ?
                  AND c.EndDate >= ?
                GROUP BY m.MerchantID, m.MerchantName, m.BusinessType
                ORDER BY m.MerchantName
            """, (f'{year}-12-31', f'{year}-01-01'))
            rows = cursor.fetchall()

            success_count = 0
            skip_count = 0
            errors = []

            for row in rows:
                merchant_id = row.MerchantID
                merchant_name = row.MerchantName or ''
                business_type = row.BusinessType or ''
                total_area = float(row.TotalArea)

                try:
                    cursor.execute("""
                        SELECT GarbageFeeID FROM GarbageFee
                        WHERE MerchantID = ? AND Year = ?
                    """, (merchant_id, year))
                    if cursor.fetchone():
                        skip_count += 1
                        continue

                    unit_price = 0
                    min_amount = 0
                    if business_type:
                        cursor.execute("""
                            SELECT UnitPrice, MinAmount FROM Sys_Dictionary
                            WHERE DictType = N'business_type' AND DictName = ? AND IsActive = 1
                        """, (business_type,))
                        dict_row = cursor.fetchone()
                        if dict_row:
                            unit_price = float(dict_row.UnitPrice) if dict_row.UnitPrice else 0
                            min_amount = float(dict_row.MinAmount) if dict_row.MinAmount else 0

                    if not business_type or (unit_price == 0 and min_amount == 0):
                        skip_count += 1
                        continue

                    calculated_fee = round(unit_price * total_area, 2)
                    final_fee = round(max(calculated_fee, min_amount), 2)

                    cursor.execute("""
                        INSERT INTO GarbageFee (MerchantID, Year, BusinessType, RentalArea,
                                                UnitPrice, MinAmount, CalculatedFee, FinalFee,
                                                Status, CreateBy, CreateTime)
                        OUTPUT INSERTED.GarbageFeeID
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, N'待收取', ?, GETDATE())
                    """, (merchant_id, year, business_type, total_area,
                          unit_price, min_amount, calculated_fee, final_fee,
                          created_by))
                    gf_row = cursor.fetchone()
                    garbage_fee_id = gf_row[0]

                    cursor.execute("""
                        INSERT INTO Receivable (MerchantID, ExpenseTypeID, Amount, DueDate,
                                                Status, PaidAmount, RemainingAmount,
                                                Description, CustomerType, CustomerID,
                                                ReferenceType, ReferenceID)
                        OUTPUT INSERTED.ReceivableID
                        VALUES (?, ?, ?, ?, N'未付款', 0, ?, N'Merchant', ?, N'garbage_fee', ?)
                    """, (merchant_id, expense_type_id, final_fee,
                          f'{year}-12-31',
                          final_fee,
                          merchant_id, garbage_fee_id))
                    rev_row = cursor.fetchone()
                    receivable_id = rev_row[0]

                    cursor.execute("""
                        UPDATE GarbageFee SET ReceivableID = ? WHERE GarbageFeeID = ?
                    """, (receivable_id, garbage_fee_id))

                    success_count += 1

                except Exception as e:
                    errors.append(f'{merchant_name}: {str(e)}')
                    logger.error(f"批量生成垃圾费失败: MerchantID={merchant_id}, {e}")

            conn.commit()

            logger.info(f"垃圾费批量生成完成: 年度={year}, 成功={success_count}, 跳过={skip_count}, 错误={len(errors)}")
            return {
                'success_count': success_count,
                'skip_count': skip_count,
                'error_count': len(errors),
                'errors': errors,
            }

    def update_fee(self, garbage_fee_id, rental_area=None, unit_price=None,
                   min_amount=None, final_fee=None, status=None,
                   description=None, updated_by=None):
        with DBConnection() as conn:
            cursor = conn.cursor()

            cursor.execute("""
                SELECT GarbageFeeID, MerchantID, Year, FinalFee, ReceivableID, Status
                FROM GarbageFee WHERE GarbageFeeID = ?
            """, (garbage_fee_id,))
            row = cursor.fetchone()
            if not row:
                raise ValueError("垃圾费记录不存在")

            old_final_fee = float(row.FinalFee) if row.FinalFee else 0
            receivable_id = row.ReceivableID
            old_status = row.Status

            update_parts = []
            update_params = []

            if rental_area is not None:
                update_parts.append("RentalArea = ?")
                update_params.append(float(rental_area))

            if unit_price is not None:
                update_parts.append("UnitPrice = ?")
                update_params.append(float(unit_price))

            if min_amount is not None:
                update_parts.append("MinAmount = ?")
                update_params.append(float(min_amount))

            if rental_area is not None or unit_price is not None:
                new_area = float(rental_area) if rental_area is not None else float(row.RentalArea or 0)
                new_price = float(unit_price) if unit_price is not None else float(row.UnitPrice or 0)
                new_min = float(min_amount) if min_amount is not None else float(row.MinAmount or 0)
                calculated = round(new_price * new_area, 2)
                update_parts.append("CalculatedFee = ?")
                update_params.append(calculated)

                if final_fee is None:
                    final_fee = max(calculated, new_min)

            if final_fee is not None:
                update_parts.append("FinalFee = ?")
                update_params.append(float(final_fee))

            if status is not None:
                update_parts.append("Status = ?")
                update_params.append(status)

            if description is not None:
                update_parts.append("Description = ?")
                update_params.append(description)

            update_parts.append("UpdateBy = ?")
            update_params.append(updated_by)
            update_parts.append("UpdateTime = GETDATE()")

            update_params.append(garbage_fee_id)
            sql = f"UPDATE GarbageFee SET {', '.join(update_parts)} WHERE GarbageFeeID = ?"
            cursor.execute(sql, tuple(update_params))

            new_final_fee = float(final_fee) if final_fee is not None else old_final_fee

            if receivable_id:
                cursor.execute("""
                    SELECT ReceivableID, Status, PaidAmount, Amount
                    FROM Receivable WHERE ReceivableID = ? AND IsActive = 1
                """, (receivable_id,))
                rev_row = cursor.fetchone()

                if rev_row:
                    rev_status = rev_row.Status
                    rev_paid = float(rev_row.PaidAmount) if rev_row.PaidAmount else 0
                    rev_update_parts = []
                    rev_update_params = []

                    if abs(new_final_fee - old_final_fee) > 0.001:
                        if rev_status == '未付款':
                            rev_update_parts.append("Amount = ?")
                            rev_update_params.append(new_final_fee)
                            rev_update_parts.append("RemainingAmount = ?")
                            rev_update_params.append(new_final_fee)
                        elif rev_status == '部分付款':
                            new_remaining = new_final_fee - rev_paid
                            if new_remaining < 0:
                                raise ValueError(f"金额变更后剩余金额为负数（新总额{new_final_fee} - 已付{rev_paid}），请先处理收款记录")
                            rev_update_parts.append("Amount = ?")
                            rev_update_params.append(new_final_fee)
                            rev_update_parts.append("RemainingAmount = ?")
                            rev_update_params.append(new_remaining)
                            if new_remaining == 0:
                                rev_update_parts.append("Status = N'已付款'")

                    if status == '已收取' and rev_status != '已付款':
                        if 'Status' not in str(rev_update_parts):
                            rev_update_parts.append("Status = N'已付款'")
                        rev_update_parts.append("PaidAmount = Amount")

                    if rev_update_parts:
                        rev_update_params.append(receivable_id)
                        rev_sql = f"UPDATE Receivable SET {', '.join(rev_update_parts)} WHERE ReceivableID = ?"
                        cursor.execute(rev_sql, tuple(rev_update_params))

            conn.commit()

            logger.info(f"垃圾费记录更新成功: {garbage_fee_id}")
            return {'garbage_fee_id': garbage_fee_id}

    def delete_fee(self, garbage_fee_id):
        with DBConnection() as conn:
            cursor = conn.cursor()

            cursor.execute("SELECT GarbageFeeID, ReceivableID FROM GarbageFee WHERE GarbageFeeID = ?",
                           (garbage_fee_id,))
            row = cursor.fetchone()
            if not row:
                raise ValueError("垃圾费记录不存在")

            cursor.execute("DELETE FROM GarbageFee WHERE GarbageFeeID = ?", (garbage_fee_id,))

            conn.commit()
            logger.info(f"垃圾费记录删除成功: {garbage_fee_id}")
            return True

    def get_business_types(self):
        with DBConnection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT DictID, DictName, UnitPrice, MinAmount
                FROM Sys_Dictionary
                WHERE DictType = N'business_type' AND IsActive = 1
                ORDER BY SortOrder
            """)
            rows = cursor.fetchall()
            return [{'value': r.DictName, 'label': r.DictName,
                     'unit_price': float(r.UnitPrice) if r.UnitPrice else 0,
                     'min_amount': float(r.MinAmount) if r.MinAmount else 0}
                    for r in rows]

    def get_status_options(self):
        return [
            {'value': '待收取', 'label': '待收取'},
            {'value': '已收取', 'label': '已收取'},
        ]

    def export_fees(self, year=None, business_type=None, status=None, search=None):
        from openpyxl import Workbook
        from openpyxl.styles import Font, Alignment, Border, Side, PatternFill

        result = self.get_list(page=1, per_page=99999, year=year,
                               business_type=business_type, status=status, search=search)
        items = result['items']
        summary = result['summary']

        wb = Workbook()
        ws = wb.active
        ws.title = '垃圾费记录'

        header_font = Font(name='微软雅黑', bold=True, size=11, color='FFFFFF')
        header_fill = PatternFill(start_color='165DFF', end_color='165DFF', fill_type='solid')
        header_align = Alignment(horizontal='center', vertical='center', wrap_text=True)
        cell_align_center = Alignment(horizontal='center', vertical='center')
        cell_align_right = Alignment(horizontal='right', vertical='center')
        thin_border = Border(
            left=Side(style='thin'), right=Side(style='thin'),
            top=Side(style='thin'), bottom=Side(style='thin'),
        )
        summary_fill = PatternFill(start_color='E8F0FE', end_color='E8F0FE', fill_type='solid')
        summary_font = Font(name='微软雅黑', bold=True, size=11)

        title_font = Font(name='微软雅黑', bold=True, size=14)
        ws.merge_cells('A1:K1')
        ws['A1'] = f'{year or "全部年度"}垃圾费记录'
        ws['A1'].font = title_font
        ws['A1'].alignment = Alignment(horizontal='center', vertical='center')
        ws.row_dimensions[1].height = 35

        headers = ['序号', '商户名称', '年度', '业态类型', '租赁面积(亩)',
                   '业态单价(元/亩/年)', '保底金额(元)', '计算金额(元)',
                   '最终金额(元)', '状态', '备注']
        header_row = 3
        for col_idx, header in enumerate(headers, 1):
            cell = ws.cell(row=header_row, column=col_idx, value=header)
            cell.font = header_font
            cell.fill = header_fill
            cell.alignment = header_align
            cell.border = thin_border
        ws.row_dimensions[header_row].height = 30

        money_format = '#,##0.00'
        for idx, item in enumerate(items):
            row_num = header_row + 1 + idx
            data = [
                idx + 1,
                item['merchant_name'],
                item['year'],
                item['business_type'],
                item['rental_area'],
                item['unit_price'],
                item['min_amount'],
                item['calculated_fee'],
                item['final_fee'],
                item['status'],
                item['description'],
            ]
            aligns = [cell_align_center, cell_align_center, cell_align_center,
                      cell_align_center, cell_align_right, cell_align_right,
                      cell_align_right, cell_align_right, cell_align_right,
                      cell_align_center, Alignment(horizontal='left', vertical='center', wrap_text=True)]
            formats = [None, None, None, None, money_format, money_format,
                       money_format, money_format, money_format, None, None]
            for col_idx, (val, align, fmt) in enumerate(zip(data, aligns, formats), 1):
                cell = ws.cell(row=row_num, column=col_idx, value=val)
                cell.alignment = align
                cell.border = thin_border
                cell.font = Font(name='微软雅黑', size=10)
                if fmt:
                    cell.number_format = fmt

        summary_row = header_row + 1 + len(items)
        ws.merge_cells(f'A{summary_row}:D{summary_row}')
        summary_data = [
            ('合计', cell_align_center),
            ('', cell_align_center), ('', cell_align_center), ('', cell_align_center),
            (summary['total_area'], cell_align_right),
            ('', cell_align_right),
            ('', cell_align_right),
            ('', cell_align_right),
            (summary['total_fee'], cell_align_right),
            (f"{summary['total_count']}条", cell_align_center),
            ('', Alignment(horizontal='left', vertical='center')),
        ]
        for col_idx, (val, align) in enumerate(summary_data, 1):
            cell = ws.cell(row=summary_row, column=col_idx, value=val)
            cell.font = summary_font
            cell.fill = summary_fill
            cell.alignment = align
            cell.border = thin_border
            if col_idx in (5, 9):
                cell.number_format = money_format

        col_widths = [6, 18, 8, 12, 14, 18, 14, 14, 14, 8, 30]
        for i, width in enumerate(col_widths, 1):
            ws.column_dimensions[chr(64 + i)].width = width

        footer_row = summary_row + 1
        ws.merge_cells(f'A{footer_row}:K{footer_row}')
        ws.cell(row=footer_row, column=1,
                value=f'导出时间：{datetime.now().strftime("%Y-%m-%d %H:%M")}  共{len(items)}条记录')

        output = BytesIO()
        wb.save(output)
        output.seek(0)

        date_str = datetime.now().strftime('%Y%m%d')
        filename = f'垃圾费记录_{date_str}.xlsx'
        return output, filename
```

- [ ] **步骤 2：验证服务层代码无语法错误**

运行：`python -c "from app.services.garbage_fee_service import GarbageFeeService; print('OK')"`

预期：输出 `OK`

---

### 任务 3：路由层实现

**文件：**
- 创建：`app/routes/garbage_fee.py`

- [ ] **步骤 1：编写路由代码**

```python
# -*- coding: utf-8 -*-
from flask import Blueprint, render_template, request, jsonify, send_file
from flask_login import login_required, current_user
from app.routes.user import check_permission
from app.services.garbage_fee_service import GarbageFeeService
from app.api_response import handle_exception

garbage_fee_bp = Blueprint('garbage_fee', __name__)
garbage_fee_svc = GarbageFeeService()


@garbage_fee_bp.route('/')
@login_required
@check_permission('garbage_fee_view')
def index():
    return render_template('garbage_fee/list.html')


@garbage_fee_bp.route('/list')
@login_required
@check_permission('garbage_fee_view')
def fee_list():
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        year = request.args.get('year', '').strip()
        business_type = request.args.get('business_type', '').strip()
        status = request.args.get('status', '').strip()
        search = request.args.get('search', '').strip()

        result = garbage_fee_svc.get_list(
            page=page, per_page=per_page,
            year=year or None,
            business_type=business_type or None,
            status=status or None,
            search=search or None,
        )
        return jsonify({'success': True, 'data': result})
    except Exception as e:
        return handle_exception(e)


@garbage_fee_bp.route('/generate')
@login_required
@check_permission('garbage_fee_create')
def generate_page():
    return render_template('garbage_fee/generate.html')


@garbage_fee_bp.route('/generate', methods=['POST'])
@login_required
@check_permission('garbage_fee_create')
def generate():
    try:
        data = request.json
        year = data.get('year')
        if not year:
            raise ValueError("请选择年度")
        result = garbage_fee_svc.batch_generate(
            year=int(year),
            created_by=current_user.user_id,
        )
        return jsonify({'success': True, 'message': f"生成完成：成功{result['success_count']}条，跳过{result['skip_count']}条", 'data': result})
    except Exception as e:
        return handle_exception(e)


@garbage_fee_bp.route('/preview')
@login_required
@check_permission('garbage_fee_create')
def preview():
    try:
        year = request.args.get('year', '').strip()
        if not year:
            raise ValueError("请选择年度")
        result = garbage_fee_svc.get_preview(year=int(year))
        return jsonify({'success': True, 'data': result})
    except Exception as e:
        return handle_exception(e)


@garbage_fee_bp.route('/edit/<int:garbage_fee_id>', methods=['POST'])
@login_required
@check_permission('garbage_fee_edit')
def update_fee(garbage_fee_id):
    try:
        data = request.json
        result = garbage_fee_svc.update_fee(
            garbage_fee_id=garbage_fee_id,
            rental_area=data.get('rental_area'),
            unit_price=data.get('unit_price'),
            min_amount=data.get('min_amount'),
            final_fee=data.get('final_fee'),
            status=data.get('status'),
            description=data.get('description', '').strip() or None,
            updated_by=current_user.user_id,
        )
        return jsonify({'success': True, 'message': '更新成功', 'data': result})
    except Exception as e:
        return handle_exception(e)


@garbage_fee_bp.route('/detail/<int:garbage_fee_id>')
@login_required
@check_permission('garbage_fee_view')
def detail(garbage_fee_id):
    return render_template('garbage_fee/detail.html', garbage_fee_id=garbage_fee_id)


@garbage_fee_bp.route('/detail/<int:garbage_fee_id>/data')
@login_required
@check_permission('garbage_fee_view')
def detail_data(garbage_fee_id):
    try:
        data = garbage_fee_svc.get_detail(garbage_fee_id)
        if not data:
            return jsonify({'success': False, 'message': '垃圾费记录不存在'}), 404
        return jsonify({'success': True, 'data': data})
    except Exception as e:
        return handle_exception(e)


@garbage_fee_bp.route('/delete/<int:garbage_fee_id>', methods=['POST'])
@login_required
@check_permission('garbage_fee_delete')
def delete(garbage_fee_id):
    try:
        garbage_fee_svc.delete_fee(garbage_fee_id)
        return jsonify({'success': True, 'message': '删除成功'})
    except Exception as e:
        return handle_exception(e)


@garbage_fee_bp.route('/export')
@login_required
@check_permission('garbage_fee_view')
def export():
    try:
        year = request.args.get('year', '').strip()
        business_type = request.args.get('business_type', '').strip()
        status = request.args.get('status', '').strip()
        search = request.args.get('search', '').strip()

        output, filename = garbage_fee_svc.export_fees(
            year=year or None,
            business_type=business_type or None,
            status=status or None,
            search=search or None,
        )
        return send_file(
            output,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name=filename,
        )
    except Exception as e:
        return handle_exception(e)


@garbage_fee_bp.route('/business-types')
@login_required
@check_permission('garbage_fee_view')
def business_types():
    try:
        result = garbage_fee_svc.get_business_types()
        return jsonify({'success': True, 'data': result})
    except Exception as e:
        return handle_exception(e)


@garbage_fee_bp.route('/status-options')
@login_required
@check_permission('garbage_fee_view')
def status_options():
    try:
        result = garbage_fee_svc.get_status_options()
        return jsonify({'success': True, 'data': result})
    except Exception as e:
        return handle_exception(e)
```

- [ ] **步骤 2：验证路由代码无语法错误**

运行：`python -c "from app.routes.garbage_fee import garbage_fee_bp; print('OK')"`

预期：输出 `OK`

---

### 任务 4：注册蓝图

**文件：**
- 修改：`app/__init__.py:29-48`

- [ ] **步骤 1：在 blueprints 列表中添加 garbage_fee_bp**

在 `app/__init__.py` 的 `blueprints` 列表中，在 `('app.routes.garbage', 'garbage_bp', '/garbage', False)` 之后添加：

```python
        ('app.routes.garbage_fee', 'garbage_fee_bp', '/garbage_fee', False),
```

- [ ] **步骤 2：验证应用启动正常**

运行：`python -c "from app import create_app; app = create_app(); print('App created OK')"`

预期：输出 `App created OK`，无蓝图注册失败错误。

---

### 任务 5：列表页模板

**文件：**
- 创建：`templates/garbage_fee/list.html`

- [ ] **步骤 1：编写列表页 HTML**

```html
{% extends "admin_base.html" %}

{% block title %}垃圾费管理{% endblock %}

{% block breadcrumb %}
<span class="breadcrumb-sep"><i class="fa fa-chevron-right"></i></span>
<span class="breadcrumb-current">垃圾费管理</span>
{% endblock %}

{% block extra_css %}
<style>
    .badge { font-size: 0.8rem; padding: 0.4em 0.8em; border-radius: 0.5rem; }
</style>
{% endblock %}

{% block content %}
<div class="card">
    <div class="card-header">
        <div class="row">
            <div class="col-md-6">
                <h5 class="card-title mb-0"><i class="fa fa-recycle"></i> 垃圾费管理</h5>
            </div>
            <div class="col-md-6 text-end">
                <button type="button" class="btn btn-success me-2" id="btnExport">
                    <i class="fa fa-file-excel-o"></i> 导出Excel
                </button>
                <a href="{{ url_for('garbage_fee.generate_page') }}" class="btn btn-primary">
                    <i class="fa fa-magic"></i> 批量生成
                </a>
            </div>
        </div>
    </div>
    <div class="card-body">
        <div class="filter-form mb-4">
            <div class="row g-3">
                <div class="col-md-2">
                    <label class="form-label">年度</label>
                    <select class="form-select" id="filterYear">
                        <option value="">全部年度</option>
                    </select>
                </div>
                <div class="col-md-2">
                    <label class="form-label">业态类型</label>
                    <select class="form-select" id="filterBusinessType">
                        <option value="">全部业态</option>
                    </select>
                </div>
                <div class="col-md-2">
                    <label class="form-label">状态</label>
                    <select class="form-select" id="filterStatus">
                        <option value="">全部状态</option>
                        <option value="待收取">待收取</option>
                        <option value="已收取">已收取</option>
                    </select>
                </div>
                <div class="col-md-3">
                    <label class="form-label">搜索</label>
                    <div class="input-group">
                        <input type="text" class="form-control" id="searchInput" placeholder="搜索商户名/备注">
                        <button class="btn btn-primary" id="btnSearch"><i class="fa fa-search"></i></button>
                    </div>
                </div>
            </div>
        </div>

        <div class="table-responsive">
            <table class="table table-striped table-hover">
                <thead>
                    <tr>
                        <th class="text-center" style="width:50px;">序号</th>
                        <th class="text-center" style="width:160px;">商户名称</th>
                        <th class="text-center" style="width:70px;">年度</th>
                        <th class="text-center" style="width:100px;">业态类型</th>
                        <th class="text-center" style="width:100px;">面积(亩)</th>
                        <th class="text-center" style="width:120px;">单价(元/亩/年)</th>
                        <th class="text-center" style="width:100px;">保底(元)</th>
                        <th class="text-center" style="width:100px;">计算金额</th>
                        <th class="text-center" style="width:110px;">最终金额</th>
                        <th class="text-center" style="width:70px;">状态</th>
                        <th class="text-center" style="width:150px;">操作</th>
                    </tr>
                </thead>
                <tbody id="dataTableBody">
                    <tr><td colspan="11" class="text-center text-muted"><i class="fa fa-spinner fa-spin"></i> 加载中...</td></tr>
                </tbody>
                <tfoot id="tableFoot" style="display:none;">
                    <tr class="summary-row">
                        <td class="text-center" colspan="4">合计</td>
                        <td class="text-end" id="summaryArea">0.00</td>
                        <td colspan="3"></td>
                        <td class="text-end" id="summaryFee">¥0.00</td>
                        <td class="text-center" id="summaryCount">0 条</td>
                        <td></td>
                    </tr>
                </tfoot>
            </table>
        </div>

        <div class="row mt-3">
            <div class="col-md-6"><div id="pageInfo" class="text-muted"></div></div>
            <div class="col-md-6"><nav><ul class="pagination justify-content-end mb-0" id="pagination"></ul></nav></div>
        </div>
    </div>
</div>

<!-- 编辑模态窗口 -->
<div class="modal fade" id="editModal" tabindex="-1">
    <div class="modal-dialog modal-lg">
        <div class="modal-content">
            <div class="modal-header">
                <h5 class="modal-title"><i class="fa fa-edit"></i> 编辑垃圾费</h5>
                <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
            </div>
            <div class="modal-body">
                <input type="hidden" id="editId">
                <div class="row mb-3">
                    <div class="col-md-6">
                        <label class="form-label fw-bold">商户名称</label>
                        <input type="text" class="form-control" id="editMerchantName" readonly>
                    </div>
                    <div class="col-md-3">
                        <label class="form-label fw-bold">年度</label>
                        <input type="text" class="form-control" id="editYear" readonly>
                    </div>
                    <div class="col-md-3">
                        <label class="form-label fw-bold">业态类型</label>
                        <input type="text" class="form-control" id="editBusinessType" readonly>
                    </div>
                </div>
                <div class="row mb-3">
                    <div class="col-md-3">
                        <label class="form-label fw-bold">租赁面积(亩)</label>
                        <input type="number" class="form-control" id="editRentalArea" step="0.01" min="0">
                    </div>
                    <div class="col-md-3">
                        <label class="form-label fw-bold">单价(元/亩/年)</label>
                        <input type="number" class="form-control" id="editUnitPrice" step="0.01" min="0">
                    </div>
                    <div class="col-md-3">
                        <label class="form-label fw-bold">保底金额(元)</label>
                        <input type="number" class="form-control" id="editMinAmount" step="0.01" min="0">
                    </div>
                    <div class="col-md-3">
                        <label class="form-label fw-bold">最终金额(元)</label>
                        <input type="number" class="form-control" id="editFinalFee" step="0.01" min="0">
                    </div>
                </div>
                <div class="row mb-3">
                    <div class="col-md-3">
                        <label class="form-label fw-bold">计算金额(元)</label>
                        <input type="text" class="form-control" id="editCalculatedFee" readonly>
                    </div>
                    <div class="col-md-3">
                        <label class="form-label fw-bold">状态</label>
                        <select class="form-select" id="editStatus">
                            <option value="待收取">待收取</option>
                            <option value="已收取">已收取</option>
                        </select>
                    </div>
                    <div class="col-md-6">
                        <label class="form-label">备注</label>
                        <input type="text" class="form-control" id="editDescription" placeholder="备注（可选）">
                    </div>
                </div>
            </div>
            <div class="modal-footer">
                <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">取消</button>
                <button type="button" class="btn btn-primary" id="btnSaveEdit"><i class="fa fa-check"></i> 保存</button>
            </div>
        </div>
    </div>
</div>
{% endblock %}

{% block extra_js %}
<script>
$(function() {
    let currentPage = 1;
    let perPage = 10;

    function initYearFilter() {
        const currentYear = new Date().getFullYear();
        let html = '<option value="">全部年度</option>';
        for (let y = currentYear + 1; y >= currentYear - 5; y--) {
            html += '<option value="' + y + '">' + y + '年</option>';
        }
        $('#filterYear').html(html);
        $('#filterYear').val(currentYear);
    }

    function loadBusinessTypes() {
        $.get('{{ url_for("garbage_fee.business_types") }}', function(res) {
            if (res.success) {
                let html = '<option value="">全部业态</option>';
                res.data.forEach(function(item) {
                    html += '<option value="' + item.value + '">' + item.label + '</option>';
                });
                $('#filterBusinessType').html(html);
            }
        });
    }

    function loadData() {
        const year = $('#filterYear').val();
        const businessType = $('#filterBusinessType').val();
        const status = $('#filterStatus').val();
        const search = $('#searchInput').val().trim();

        $('#dataTableBody').html('<tr><td colspan="11" class="text-center text-muted"><i class="fa fa-spinner fa-spin"></i> 加载中...</td></tr>');
        $('#tableFoot').hide();

        $.ajax({
            url: '{{ url_for("garbage_fee.fee_list") }}',
            method: 'GET',
            data: { page: currentPage, per_page: perPage, year: year, business_type: businessType, status: status, search: search },
            success: function(res) {
                if (res.success) {
                    renderTable(res.data.items);
                    renderSummary(res.data.summary);
                    renderPagination('#pagination', { current_page: res.data.page, total_pages: res.data.total_pages, total: res.data.total }, function(page) {
                        currentPage = page;
                        loadData();
                    });
                    const start = (res.data.page - 1) * perPage + 1;
                    const end = Math.min(res.data.page * perPage, res.data.total);
                    $('#pageInfo').text(res.data.total === 0 ? '暂无数据' : '显示 ' + start + '-' + end + ' 条，共 ' + res.data.total + ' 条');
                } else {
                    showToast(res.message || '加载失败', 'danger');
                }
            },
            error: function() { showToast('网络错误', 'danger'); }
        });
    }

    function renderTable(data) {
        const tbody = $('#dataTableBody');
        tbody.empty();
        if (data.length === 0) {
            tbody.html('<tr><td colspan="11" class="text-center text-muted py-5"><i class="fa fa-inbox fa-3x mb-3"></i><p>暂无数据</p></td></tr>');
            return;
        }
        data.forEach(function(item, index) {
            const rowNum = (currentPage - 1) * perPage + index + 1;
            let statusBadge = '';
            if (item.status === '待收取') statusBadge = '<span class="badge bg-warning">待收取</span>';
            else if (item.status === '已收取') statusBadge = '<span class="badge bg-success">已收取</span>';
            else statusBadge = '<span class="badge bg-secondary">' + item.status + '</span>';

            tbody.append(`
                <tr>
                    <td class="text-center">${rowNum}</td>
                    <td class="text-center">${item.merchant_name}</td>
                    <td class="text-center">${item.year}</td>
                    <td class="text-center">${item.business_type || '—'}</td>
                    <td class="text-end">${item.rental_area.toFixed(2)}</td>
                    <td class="text-end">${item.unit_price.toFixed(2)}</td>
                    <td class="text-end">${item.min_amount.toFixed(2)}</td>
                    <td class="text-end">${item.calculated_fee.toFixed(2)}</td>
                    <td class="text-end fw-bold">¥${item.final_fee.toFixed(2)}</td>
                    <td class="text-center">${statusBadge}</td>
                    <td class="text-center" style="white-space:nowrap;">
                        <a href="/garbage_fee/detail/${item.garbage_fee_id}" class="btn btn-sm btn-outline-info me-1"><i class="fa fa-eye"></i></a>
                        <button class="btn btn-sm btn-outline-primary me-1 btn-edit" data-id="${item.garbage_fee_id}"><i class="fa fa-edit"></i></button>
                        <button class="btn btn-sm btn-outline-danger btn-delete" data-id="${item.garbage_fee_id}"><i class="fa fa-trash"></i></button>
                    </td>
                </tr>
            `);
        });
    }

    function renderSummary(summary) {
        if (!summary || summary.total_count === 0) { $('#tableFoot').hide(); return; }
        $('#summaryArea').text(summary.total_area.toFixed(2));
        $('#summaryFee').text('¥' + summary.total_fee.toFixed(2));
        $('#summaryCount').text(summary.total_count + ' 条');
        $('#tableFoot').show();
    }

    bindSearch('searchInput', 'btnSearch', function() { currentPage = 1; loadData(); });
    $('#filterYear, #filterBusinessType, #filterStatus').change(function() { currentPage = 1; loadData(); });

    // 编辑
    $(document).on('click', '.btn-edit', function() {
        const id = $(this).data('id');
        $.get('{{ url_for("garbage_fee.detail_data", garbage_fee_id=0) }}'.replace('/0', '/' + id), function(res) {
            if (res.success) {
                const d = res.data;
                $('#editId').val(d.garbage_fee_id);
                $('#editMerchantName').val(d.merchant_name);
                $('#editYear').val(d.year);
                $('#editBusinessType').val(d.business_type || '—');
                $('#editRentalArea').val(d.rental_area);
                $('#editUnitPrice').val(d.unit_price);
                $('#editMinAmount').val(d.min_amount);
                $('#editCalculatedFee').val(d.calculated_fee.toFixed(2));
                $('#editFinalFee').val(d.final_fee);
                $('#editStatus').val(d.status);
                $('#editDescription').val(d.description || '');
                new bootstrap.Modal($('#editModal')[0]).show();
            } else {
                showToast(res.message || '加载失败', 'danger');
            }
        });
    });

    function recalcEditFee() {
        const area = parseFloat($('#editRentalArea').val()) || 0;
        const price = parseFloat($('#editUnitPrice').val()) || 0;
        const minAmt = parseFloat($('#editMinAmount').val()) || 0;
        const calculated = area * price;
        $('#editCalculatedFee').val(calculated.toFixed(2));
        const finalFee = Math.max(calculated, minAmt);
        $('#editFinalFee').val(finalFee.toFixed(2));
    }
    $('#editRentalArea, #editUnitPrice, #editMinAmount').on('input', recalcEditFee);

    $('#btnSaveEdit').click(function() {
        const id = $('#editId').val();
        const data = {
            rental_area: $('#editRentalArea').val(),
            unit_price: $('#editUnitPrice').val(),
            min_amount: $('#editMinAmount').val(),
            final_fee: $('#editFinalFee').val(),
            status: $('#editStatus').val(),
            description: $('#editDescription').val().trim()
        };
        $.ajax({
            url: '{{ url_for("garbage_fee.update_fee", garbage_fee_id=0) }}'.replace('/0', '/' + id),
            method: 'POST',
            contentType: 'application/json',
            headers: { 'X-CSRFToken': getCSRFToken() },
            data: JSON.stringify(data),
            success: function(res) {
                if (res.success) {
                    showToast('更新成功', 'success');
                    bootstrap.Modal.getInstance($('#editModal')[0]).hide();
                    loadData();
                } else {
                    showToast(res.message || '更新失败', 'danger');
                }
            },
            error: function(xhr) {
                var msg = '网络错误';
                try { msg = xhr.responseJSON.message || msg; } catch(e) {}
                showToast(msg, 'danger');
            }
        });
    });

    // 删除
    $(document).on('click', '.btn-delete', function() {
        const id = $(this).data('id');
        if (confirm('确定要删除这条垃圾费记录吗？')) {
            $.ajax({
                url: '{{ url_for("garbage_fee.delete", garbage_fee_id=0) }}'.replace('/0', '/' + id),
                method: 'POST',
                headers: { 'X-CSRFToken': getCSRFToken() },
                success: function(res) {
                    if (res.success) { showToast('删除成功', 'success'); loadData(); }
                    else { showToast(res.message || '删除失败', 'danger'); }
                },
                error: function(xhr) {
                    var msg = '网络错误';
                    try { msg = xhr.responseJSON.message || msg; } catch(e) {}
                    showToast(msg, 'danger');
                }
            });
        }
    });

    // 导出
    $('#btnExport').click(function() {
        const params = new URLSearchParams();
        const year = $('#filterYear').val();
        const bt = $('#filterBusinessType').val();
        const st = $('#filterStatus').val();
        const search = $('#searchInput').val().trim();
        if (year) params.set('year', year);
        if (bt) params.set('business_type', bt);
        if (st) params.set('status', st);
        if (search) params.set('search', search);
        window.location.href = '{{ url_for("garbage_fee.export") }}?' + params.toString();
    });

    initYearFilter();
    loadBusinessTypes();
    loadData();
});
</script>
{% endblock %}
```

- [ ] **步骤 2：验证模板文件创建成功**

运行：`python -c "import os; print(os.path.exists('templates/garbage_fee/list.html'))"`

预期：输出 `True`

---

### 任务 6：批量生成页模板

**文件：**
- 创建：`templates/garbage_fee/generate.html`

- [ ] **步骤 1：编写批量生成页 HTML**

```html
{% extends "admin_base.html" %}

{% block title %}批量生成垃圾费{% endblock %}

{% block breadcrumb %}
<span class="breadcrumb-sep"><i class="fa fa-chevron-right"></i></span>
<a href="{{ url_for('garbage_fee.index') }}" class="breadcrumb-chip">垃圾费管理</a>
<span class="breadcrumb-sep"><i class="fa fa-chevron-right"></i></span>
<span class="breadcrumb-current">批量生成</span>
{% endblock %}

{% block content %}
<div class="card">
    <div class="card-header">
        <div class="row">
            <div class="col-md-6">
                <h5 class="card-title mb-0"><i class="fa fa-magic"></i> 批量生成垃圾费</h5>
            </div>
            <div class="col-md-6 text-end">
                <a href="{{ url_for('garbage_fee.index') }}" class="btn btn-secondary">
                    <i class="fa fa-arrow-left"></i> 返回列表
                </a>
            </div>
        </div>
    </div>
    <div class="card-body">
        <div class="alert alert-info mb-3">
            <i class="fa fa-info-circle"></i>
            <strong>说明：</strong>选择年度后点击"预览"，系统将自动计算所有有效合同商户的垃圾费。确认无误后点击"确认生成"。
        </div>

        <div class="row mb-4">
            <div class="col-md-3">
                <label class="form-label fw-bold">选择年度 <span class="text-danger">*</span></label>
                <select class="form-select" id="selectYear">
                </select>
            </div>
            <div class="col-md-3 d-flex align-items-end">
                <button type="button" class="btn btn-outline-primary w-100" id="btnPreview">
                    <i class="fa fa-eye"></i> 预览
                </button>
            </div>
        </div>

        <div id="previewArea" style="display:none;">
            <div class="row mb-3">
                <div class="col-md-12">
                    <div class="alert alert-success" id="previewSummary"></div>
                </div>
            </div>

            <div class="table-responsive">
                <table class="table table-striped table-hover">
                    <thead>
                        <tr>
                            <th class="text-center">序号</th>
                            <th class="text-center">商户名称</th>
                            <th class="text-center">业态类型</th>
                            <th class="text-center">面积(亩)</th>
                            <th class="text-center">单价(元/亩/年)</th>
                            <th class="text-center">保底(元)</th>
                            <th class="text-center">计算金额</th>
                            <th class="text-center">最终金额</th>
                        </tr>
                    </thead>
                    <tbody id="previewTableBody"></tbody>
                </table>
            </div>

            <div id="skippedArea" style="display:none;" class="mt-3">
                <h6 class="text-muted"><i class="fa fa-exclamation-triangle"></i> 跳过的商户</h6>
                <ul id="skippedList" class="text-muted small"></ul>
            </div>

            <div class="text-end mt-3">
                <button type="button" class="btn btn-primary btn-lg" id="btnGenerate">
                    <i class="fa fa-check"></i> 确认生成
                </button>
            </div>
        </div>
    </div>
</div>
{% endblock %}

{% block extra_js %}
<script>
$(function() {
    const currentYear = new Date().getFullYear();
    let html = '';
    for (let y = currentYear + 1; y >= currentYear - 5; y--) {
        html += '<option value="' + y + '">' + y + '年</option>';
    }
    $('#selectYear').html(html);
    $('#selectYear').val(currentYear);

    $('#btnPreview').click(function() {
        const year = $('#selectYear').val();
        if (!year) { showToast('请选择年度', 'danger'); return; }

        $('#btnPreview').prop('disabled', true).html('<i class="fa fa-spinner fa-spin"></i> 预览中...');

        $.get('{{ url_for("garbage_fee.preview") }}', { year: year }, function(res) {
            $('#btnPreview').prop('disabled', false).html('<i class="fa fa-eye"></i> 预览');
            if (res.success) {
                renderPreview(res.data);
            } else {
                showToast(res.message || '预览失败', 'danger');
            }
        }).fail(function() {
            $('#btnPreview').prop('disabled', false).html('<i class="fa fa-eye"></i> 预览');
            showToast('网络错误', 'danger');
        });
    });

    function renderPreview(data) {
        if (data.items.length === 0) {
            $('#previewSummary').removeClass('alert-success').addClass('alert-warning')
                .html('<i class="fa fa-exclamation-triangle"></i> 没有可生成的商户。请确认该年度有有效合同且业态单价已设置。');
            $('#previewArea').show();
            return;
        }

        $('#previewSummary').removeClass('alert-warning').addClass('alert-success')
            .html('<i class="fa fa-check-circle"></i> 共 <strong>' + data.generate_count + '</strong> 个商户可生成，'
                  + (data.skip_count > 0 ? '<strong>' + data.skip_count + '</strong> 个商户跳过。' : ''));

        const tbody = $('#previewTableBody');
        tbody.empty();
        data.items.forEach(function(item, idx) {
            tbody.append(`
                <tr>
                    <td class="text-center">${idx + 1}</td>
                    <td class="text-center">${item.merchant_name}</td>
                    <td class="text-center">${item.business_type}</td>
                    <td class="text-end">${item.rental_area.toFixed(2)}</td>
                    <td class="text-end">${item.unit_price.toFixed(2)}</td>
                    <td class="text-end">${item.min_amount.toFixed(2)}</td>
                    <td class="text-end">${item.calculated_fee.toFixed(2)}</td>
                    <td class="text-end fw-bold">¥${item.final_fee.toFixed(2)}</td>
                </tr>
            `);
        });

        if (data.skipped.length > 0) {
            const list = $('#skippedList');
            list.empty();
            data.skipped.forEach(function(s) {
                list.append('<li>' + s.merchant_name + '：' + s.reason + '</li>');
            });
            $('#skippedArea').show();
        } else {
            $('#skippedArea').hide();
        }

        $('#previewArea').show();
    }

    $('#btnGenerate').click(function() {
        const year = $('#selectYear').val();
        if (!year) { showToast('请选择年度', 'danger'); return; }

        if (!confirm('确认要为 ' + year + ' 年批量生成垃圾费吗？')) return;

        $('#btnGenerate').prop('disabled', true).html('<i class="fa fa-spinner fa-spin"></i> 生成中...');

        $.ajax({
            url: '{{ url_for("garbage_fee.generate") }}',
            method: 'POST',
            contentType: 'application/json',
            headers: { 'X-CSRFToken': getCSRFToken() },
            data: JSON.stringify({ year: parseInt(year) }),
            success: function(res) {
                $('#btnGenerate').prop('disabled', false).html('<i class="fa fa-check"></i> 确认生成');
                if (res.success) {
                    showToast(res.message, 'success');
                    setTimeout(function() { window.location.href = '{{ url_for("garbage_fee.index") }}'; }, 2000);
                } else {
                    showToast(res.message || '生成失败', 'danger');
                }
            },
            error: function(xhr) {
                $('#btnGenerate').prop('disabled', false).html('<i class="fa fa-check"></i> 确认生成');
                var msg = '网络错误';
                try { msg = xhr.responseJSON.message || msg; } catch(e) {}
                showToast(msg, 'danger');
            }
        });
    });
});
</script>
{% endblock %}
```

- [ ] **步骤 2：验证模板文件创建成功**

运行：`python -c "import os; print(os.path.exists('templates/garbage_fee/generate.html'))"`

预期：输出 `True`

---

### 任务 7：详情页模板

**文件：**
- 创建：`templates/garbage_fee/detail.html`

- [ ] **步骤 1：编写详情页 HTML**

```html
{% extends "admin_base.html" %}

{% block title %}垃圾费详情{% endblock %}

{% block breadcrumb %}
<span class="breadcrumb-sep"><i class="fa fa-chevron-right"></i></span>
<a href="{{ url_for('garbage_fee.index') }}" class="breadcrumb-chip">垃圾费管理</a>
<span class="breadcrumb-sep"><i class="fa fa-chevron-right"></i></span>
<span class="breadcrumb-current">记录详情</span>
{% endblock %}

{% block extra_css %}
<style>
    .detail-item { margin-bottom: 12px; }
    .detail-label { font-weight: 600; color: var(--color-text-muted); }
    .detail-value { font-size: 1.05rem; }
</style>
{% endblock %}

{% block content %}
<div class="card">
    <div class="card-header">
        <div class="row">
            <div class="col-md-6">
                <h5 class="card-title mb-0"><i class="fa fa-eye"></i> 垃圾费详情</h5>
            </div>
            <div class="col-md-6 text-end">
                <a href="{{ url_for('garbage_fee.index') }}" class="btn btn-secondary">
                    <i class="fa fa-arrow-left"></i> 返回列表
                </a>
            </div>
        </div>
    </div>
    <div class="card-body">
        <div id="detailContent">
            <div class="text-center py-5">
                <i class="fa fa-spinner fa-spin fa-3x text-muted"></i>
                <p class="mt-2 text-muted">加载中...</p>
            </div>
        </div>
    </div>
</div>
{% endblock %}

{% block extra_js %}
<script>
$(function() {
    const id = '{{ garbage_fee_id }}';

    $.get('{{ url_for("garbage_fee.detail_data", garbage_fee_id=0) }}'.replace('/0', '/' + id), function(res) {
        if (res.success) {
            renderDetail(res.data);
        } else {
            $('#detailContent').html('<div class="text-center py-5"><i class="fa fa-exclamation-triangle fa-3x text-danger"></i><p class="mt-2 text-danger">' + (res.message || '加载失败') + '</p></div>');
        }
    });

    function renderDetail(data) {
        let statusBadge = '';
        if (data.status === '待收取') statusBadge = '<span class="badge bg-warning">待收取</span>';
        else if (data.status === '已收取') statusBadge = '<span class="badge bg-success">已收取</span>';
        else statusBadge = '<span class="badge bg-secondary">' + data.status + '</span>';

        let receivableHtml = '—';
        if (data.receivable_info) {
            const r = data.receivable_info;
            receivableHtml = '<a href="{{ url_for("finance.receivable") }}" target="_blank" class="text-primary">应收 #' + r.receivable_id + '</a>'
                + ' <small class="text-muted">(' + r.status + '，¥' + r.remaining_amount.toFixed(2) + ' 未收)</small>';
        }

        const html = `
            <div class="row">
                <div class="col-md-6">
                    <div class="detail-item"><span class="detail-label">商户名称：</span><span class="detail-value">${data.merchant_name}</span></div>
                    <div class="detail-item"><span class="detail-label">年度：</span><span class="detail-value">${data.year}</span></div>
                    <div class="detail-item"><span class="detail-label">业态类型：</span><span class="detail-value">${data.business_type || '—'}</span></div>
                    <div class="detail-item"><span class="detail-label">租赁面积：</span><span class="detail-value">${data.rental_area.toFixed(2)} 亩</span></div>
                    <div class="detail-item"><span class="detail-label">业态单价：</span><span class="detail-value">¥${data.unit_price.toFixed(2)}/亩/年</span></div>
                </div>
                <div class="col-md-6">
                    <div class="detail-item"><span class="detail-label">保底金额：</span><span class="detail-value">¥${data.min_amount.toFixed(2)}</span></div>
                    <div class="detail-item"><span class="detail-label">计算金额：</span><span class="detail-value">¥${data.calculated_fee.toFixed(2)}</span></div>
                    <div class="detail-item"><span class="detail-label">最终金额：</span><span class="detail-value fw-bold text-primary">¥${data.final_fee.toFixed(2)}</span></div>
                    <div class="detail-item"><span class="detail-label">状态：</span><span class="detail-value">${statusBadge}</span></div>
                    <div class="detail-item"><span class="detail-label">关联应收：</span><span class="detail-value">${receivableHtml}</span></div>
                    <div class="detail-item"><span class="detail-label">备注：</span><span class="detail-value">${data.description || '无'}</span></div>
                </div>
            </div>
            <hr>
            <div class="row text-muted small">
                <div class="col-md-6"><span class="detail-label">创建人：</span>${data.create_user_name || '—'} &nbsp; <span class="detail-label">创建时间：</span>${data.create_time}</div>
                <div class="col-md-6">${data.update_time ? '<span class="detail-label">更新时间：</span>' + data.update_time : ''}</div>
            </div>
        `;
        $('#detailContent').html(html);
    }
});
</script>
{% endblock %}
```

- [ ] **步骤 2：验证模板文件创建成功**

运行：`python -c "import os; print(os.path.exists('templates/garbage_fee/detail.html'))"`

预期：输出 `True`

---

### 任务 8：侧边栏菜单

**文件：**
- 修改：`templates/admin_base.html:89-94`

- [ ] **步骤 1：在侧边栏添加垃圾费菜单项**

在 `admin_base.html` 中，在垃圾清运菜单项之后添加垃圾费菜单项：

找到：
```html
                {% if current_user.has_permission('garbage_view') %}
                <a class="sidebar-item {% if request.endpoint and 'garbage' in request.endpoint %}active{% endif %}" href="{{ url_for('garbage.index') }}">
                    <i class="fa fa-trash-o"></i>
                    <span class="sidebar-item-text">垃圾清运</span>
                </a>
                {% endif %}
```

在其后添加：
```html
                {% if current_user.has_permission('garbage_fee_view') %}
                <a class="sidebar-item {% if request.endpoint and 'garbage_fee' in request.endpoint %}active{% endif %}" href="{{ url_for('garbage_fee.index') }}">
                    <i class="fa fa-recycle"></i>
                    <span class="sidebar-item-text">垃圾费</span>
                </a>
                {% endif %}
```

- [ ] **步骤 2：验证侧边栏修改正确**

运行：`python -c "from jinja2 import Environment, FileSystemLoader; env = Environment(loader=FileSystemLoader('templates')); t = env.get_template('admin_base.html'); print('Template OK')"`

预期：输出 `Template OK`

---

### 任务 9：权限初始化脚本

**文件：**
- 创建：`scripts/add_garbage_fee_permission.py`

- [ ] **步骤 1：编写权限初始化脚本**

```python
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))

from dotenv import load_dotenv
load_dotenv()

from flask import Flask
from config import Config
from utils.database import execute_query, execute_update
import datetime

app = Flask(__name__)
app.config.from_object(Config)

PERMISSIONS = [
    ('garbage_fee_view', '垃圾费查看', '市场管理', 'view', 901),
    ('garbage_fee_create', '垃圾费新增', '市场管理', 'create', 902),
    ('garbage_fee_edit', '垃圾费编辑', '市场管理', 'edit', 903),
    ('garbage_fee_delete', '垃圾费删除', '市场管理', 'delete', 904),
]

MANAGE_CODE = 'garbage_fee_manage'
MANAGE_NAME = '垃圾费管理'

with app.app_context():
    for code, name, module, action, sort_order in PERMISSIONS:
        existing = execute_query("SELECT PermissionID FROM Permission WHERE PermissionCode = N'" + code + "'", fetch_type='one')
        if existing:
            print(f'{code} already exists, ID: {existing.PermissionID}')
        else:
            execute_update("""INSERT INTO Permission (PermissionName, PermissionCode, Description, ModuleName, Action, SortOrder, IsActive, CreateTime)
                VALUES (?, ?, ?, ?, ?, ?, 1, ?)""", (name, code, name, module, action, sort_order, datetime.datetime.now()))
            print(f'{code} added successfully')

    existing_manage = execute_query("SELECT PermissionID FROM Permission WHERE PermissionCode = N'" + MANAGE_CODE + "'", fetch_type='one')
    if not existing_manage:
        execute_update("""INSERT INTO Permission (PermissionName, PermissionCode, Description, ModuleName, Action, SortOrder, IsActive, CreateTime)
            VALUES (?, ?, ?, ?, 'manage', 900, 1, ?)""", (MANAGE_NAME, MANAGE_CODE, MANAGE_NAME, '市场管理', datetime.datetime.now()))
        print(f'{MANAGE_CODE} added successfully')
    else:
        print(f'{MANAGE_CODE} already exists')

    for role_code in ['admin', 'staff']:
        role = execute_query("SELECT RoleID FROM Role WHERE RoleCode = N'" + role_code + "'", fetch_type='one')
        if not role:
            print(f'Role {role_code} not found, skipping')
            continue

        for code, name, module, action, sort_order in PERMISSIONS:
            perm = execute_query("SELECT PermissionID FROM Permission WHERE PermissionCode = N'" + code + "'", fetch_type='one')
            if not perm:
                continue
            existing_rp = execute_query("SELECT * FROM RolePermission WHERE RoleID = ? AND PermissionID = ?", (role.RoleID, perm.PermissionID), fetch_type='one')
            if not existing_rp:
                execute_update("INSERT INTO RolePermission (RoleID, PermissionID, CreateTime) VALUES (?, ?, ?)", (role.RoleID, perm.PermissionID, datetime.datetime.now()))
                print(f'Assigned {code} to {role_code}')

        manage_perm = execute_query("SELECT PermissionID FROM Permission WHERE PermissionCode = N'" + MANAGE_CODE + "'", fetch_type='one')
        if manage_perm:
            existing_rp = execute_query("SELECT * FROM RolePermission WHERE RoleID = ? AND PermissionID = ?", (role.RoleID, manage_perm.PermissionID), fetch_type='one')
            if not existing_rp:
                execute_update("INSERT INTO RolePermission (RoleID, PermissionID, CreateTime) VALUES (?, ?, ?)", (role.RoleID, manage_perm.PermissionID, datetime.datetime.now()))
                print(f'Assigned {MANAGE_CODE} to {role_code}')

    print('Done!')
```

- [ ] **步骤 2：执行权限初始化脚本**

运行：`python scripts/add_garbage_fee_permission.py`

预期：输出各权限添加成功信息。

- [ ] **步骤 3：更新 migrate_crud_permissions.py**

在 `utils/migrate_crud_permissions.py` 的 `PERMISSIONS_DATA` 列表末尾（`dict_delete` 之后）添加：

```python
    ('garbage_fee_view', '垃圾费查看', '市场管理', 'view', 901),
    ('garbage_fee_create', '垃圾费新增', '市场管理', 'create', 902),
    ('garbage_fee_edit', '垃圾费编辑', '市场管理', 'edit', 903),
    ('garbage_fee_delete', '垃圾费删除', '市场管理', 'delete', 904),
```

在 `MANAGE_TO_CRUD` 字典中添加：

```python
    'garbage_fee_manage': ['garbage_fee_view', 'garbage_fee_create', 'garbage_fee_edit', 'garbage_fee_delete'],
```

---

### 任务 10：端到端验证

- [ ] **步骤 1：启动应用**

运行：`python app.py`

预期：应用正常启动，无蓝图注册失败错误。

- [ ] **步骤 2：验证列表页可访问**

浏览器访问 `/garbage_fee/`，应显示垃圾费列表页（空数据）。

- [ ] **步骤 3：验证批量生成页可访问**

浏览器访问 `/garbage_fee/generate`，应显示批量生成页面。

- [ ] **步骤 4：验证侧边栏菜单**

侧边栏"市场管理"区域应显示"垃圾费"菜单项（需用有 `garbage_fee_view` 权限的账号登录）。

- [ ] **步骤 5：验证字典管理页面可维护 MinAmount**

访问字典管理页面，筛选 `business_type` 类型，应能看到 UnitPrice 和 MinAmount 列，可编辑保存。

- [ ] **步骤 6：Commit**

```bash
git add scripts/add_garbage_fee_tables.sql app/services/garbage_fee_service.py app/routes/garbage_fee.py templates/garbage_fee/ scripts/add_garbage_fee_permission.py app/__init__.py templates/admin_base.html utils/migrate_crud_permissions.py
git commit -m "feat: 新增垃圾费管理模块

- 按商户业态类型及租赁面积核算年度垃圾费
- 计算公式：max(业态单价 × 租赁面积, 保底金额)
- 批量生成 + 单个编辑（模态窗口）
- 自动联动创建/更新应收账款
- 导出 Excel 功能"
```
