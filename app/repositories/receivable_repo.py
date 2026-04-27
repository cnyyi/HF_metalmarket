# -*- coding: utf-8 -*-
from utils.database import DBConnection


class ReceivableRepository:

    def get_list(self, page=1, per_page=10, search=None, status=None, expense_type_id=None, include_deleted=False):
        with DBConnection() as conn:
            cursor = conn.cursor()

            # 使用 CASE + LEFT JOIN 同时支持 Merchant 和 Customer
            # 费用类型优先从字典表获取，兼容旧 ExpenseType 数据
            base_query = """
                SELECT r.ReceivableID, r.MerchantID,
                       CASE
                           WHEN r.CustomerType = 'Customer' THEN c.CustomerName
                           ELSE m.MerchantName
                       END AS CustomerName,
                       r.CustomerType, r.CustomerID,
                       r.ExpenseTypeID, ISNULL(sd.DictName, et.ExpenseTypeName) AS ExpenseTypeName,
                       r.Amount, r.PaidAmount, r.RemainingAmount,
                       r.ProductName, r.Specification, r.Quantity, r.UnitID, r.UnitPrice,
                       ISNULL(ud.DictName, '') AS UnitName,
                       r.DueDate, r.Status, r.Description,
                       r.ReferenceID, r.ReferenceType,
                       r.CreateTime, r.UpdateTime,
                       r.IsActive, r.DeletedBy, r.DeletedAt, r.DeleteReason
                FROM Receivable r
                LEFT JOIN Sys_Dictionary sd ON r.ExpenseTypeID = sd.DictID AND sd.DictType = 'expense_item_income'
                LEFT JOIN ExpenseType et ON r.ExpenseTypeID = et.ExpenseTypeID AND sd.DictID IS NULL
                LEFT JOIN Merchant m ON r.CustomerType <> 'Customer' AND r.MerchantID = m.MerchantID
                LEFT JOIN Customer c ON r.CustomerType = 'Customer' AND r.CustomerID = c.CustomerID
                LEFT JOIN Sys_Dictionary ud ON r.UnitID = ud.DictID AND ud.DictType = 'unit_type'
            """

            count_query = "SELECT COUNT(*) FROM Receivable r"
            sum_query = """
                SELECT ISNULL(SUM(r.Amount), 0), ISNULL(SUM(r.PaidAmount), 0), ISNULL(SUM(r.RemainingAmount), 0)
                FROM Receivable r
                LEFT JOIN Merchant m ON r.CustomerType <> 'Customer' AND r.MerchantID = m.MerchantID
                LEFT JOIN Customer c ON r.CustomerType = 'Customer' AND r.CustomerID = c.CustomerID
            """

            conditions = []
            params = []

            # 默认不显示已删除的记录
            if not include_deleted:
                conditions.append("r.IsActive = 1")

            if search:
                conditions.append("(m.MerchantName LIKE ? OR c.CustomerName LIKE ?)")
                p = f'%{search}%'
                params.extend([p, p])

            if status:
                conditions.append("r.Status = ?")
                params.append(status)

            if expense_type_id:
                conditions.append("r.ExpenseTypeID = ?")
                params.append(expense_type_id)

            where_clause = ""
            if conditions:
                where_clause = " WHERE " + " AND ".join(conditions)
                base_query += where_clause
                count_query += where_clause
                sum_query += where_clause

            offset = (page - 1) * per_page
            base_query += " ORDER BY r.ReceivableID DESC OFFSET ? ROWS FETCH NEXT ? ROWS ONLY"
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

    def get_by_id(self, receivable_id, include_deleted=False):
        with DBConnection() as conn:
            cursor = conn.cursor()
            sql = """
                SELECT r.ReceivableID, r.MerchantID,
                       CASE
                           WHEN r.CustomerType = 'Customer' THEN c.CustomerName
                           ELSE m.MerchantName
                       END AS CustomerName,
                       r.CustomerType, r.CustomerID,
                       r.ExpenseTypeID, ISNULL(sd.DictName, et.ExpenseTypeName) AS ExpenseTypeName,
                       r.Amount, r.PaidAmount, r.RemainingAmount,
                       r.ProductName, r.Specification, r.Quantity, r.UnitID, r.UnitPrice,
                       ISNULL(ud.DictName, '') AS UnitName,
                       r.DueDate, r.Status, r.Description,
                       r.ReferenceID, r.ReferenceType,
                       r.CreateTime, r.UpdateTime,
                       r.IsActive, r.DeletedBy, r.DeletedAt, r.DeleteReason
                FROM Receivable r
                LEFT JOIN Sys_Dictionary sd ON r.ExpenseTypeID = sd.DictID AND sd.DictType = 'expense_item_income'
                LEFT JOIN ExpenseType et ON r.ExpenseTypeID = et.ExpenseTypeID AND sd.DictID IS NULL
                LEFT JOIN Merchant m ON r.CustomerType <> 'Customer' AND r.MerchantID = m.MerchantID
                LEFT JOIN Customer c ON r.CustomerType = 'Customer' AND r.CustomerID = c.CustomerID
                LEFT JOIN Sys_Dictionary ud ON r.UnitID = ud.DictID AND ud.DictType = 'unit_type'
                WHERE r.ReceivableID = ?
            """
            if not include_deleted:
                sql += " AND r.IsActive = 1"

            cursor.execute(sql, receivable_id)
            return cursor.fetchone()

    def create(self, merchant_id=None, expense_type_id=None, amount=None, due_date=None,
               description=None, reference_id=None, reference_type=None,
               customer_type='Merchant', customer_id=None,
               product_name=None, specification=None, quantity=None, unit_id=None, unit_price=None):
        with DBConnection() as conn:
            cursor = conn.cursor()
            # 如果是 Merchant 类型，兼容旧逻辑
            if customer_type == 'Merchant' and customer_id and not merchant_id:
                merchant_id = customer_id
            if customer_type == 'Merchant' and merchant_id and not customer_id:
                customer_id = merchant_id

            sql = """
                INSERT INTO Receivable (MerchantID, ExpenseTypeID, Amount, DueDate, Status, PaidAmount, RemainingAmount,
                                        Description, ReferenceID, ReferenceType, CustomerType, CustomerID,
                                        ProductName, Specification, Quantity, UnitID, UnitPrice)
                OUTPUT INSERTED.ReceivableID
                VALUES (?, ?, ?, ?, N'未付款', 0, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
            cursor.execute(sql, merchant_id, expense_type_id, amount, due_date, amount,
                           description, reference_id, reference_type, customer_type, customer_id,
                           product_name, specification, quantity, unit_id, unit_price)
            row = cursor.fetchone()
            new_id = row[0] if row else None
            conn.commit()

            return new_id

    def update_payment(self, receivable_id, amount):
        with DBConnection() as conn:
            cursor = conn.cursor()
            sql = """
                UPDATE Receivable
                SET PaidAmount = PaidAmount + ?,
                    RemainingAmount = RemainingAmount - ?,
                    UpdateTime = GETDATE()
                WHERE ReceivableID = ?
            """
            cursor.execute(sql, amount, amount, receivable_id)
            conn.commit()

    def update_status(self, receivable_id, status):
        with DBConnection() as conn:
            cursor = conn.cursor()
            sql = """
                UPDATE Receivable
                SET Status = ?, UpdateTime = GETDATE()
                WHERE ReceivableID = ?
            """
            cursor.execute(sql, status, receivable_id)
            conn.commit()

    def list_overdue(self):
        with DBConnection() as conn:
            cursor = conn.cursor()
            sql = """
                SELECT * FROM Receivable
                WHERE DueDate < GETDATE() AND Status != N'已付款' AND IsActive = 1
            """
            cursor.execute(sql)
            return cursor.fetchall()

    def soft_delete(self, receivable_id, deleted_by, delete_reason=None):
        """软删除应收账款"""
        with DBConnection() as conn:
            cursor = conn.cursor()
            sql = """
                UPDATE Receivable
                SET IsActive = 0,
                    DeletedBy = ?,
                    DeletedAt = GETDATE(),
                    DeleteReason = ?,
                    UpdateTime = GETDATE()
                WHERE ReceivableID = ? AND IsActive = 1
            """
            cursor.execute(sql, deleted_by, delete_reason, receivable_id)
            affected = cursor.rowcount
            conn.commit()
            return affected

    _CUSTOMER_EXPR = """
        CASE
            WHEN r.CustomerType = 'Customer' THEN c.CustomerName
            ELSE m.MerchantName
        END
    """

    _BASE_JOINS = """
        LEFT JOIN Sys_Dictionary sd ON r.ExpenseTypeID = sd.DictID AND sd.DictType = 'expense_item_income'
        LEFT JOIN ExpenseType et ON r.ExpenseTypeID = et.ExpenseTypeID AND sd.DictID IS NULL
        LEFT JOIN Merchant m ON r.CustomerType <> 'Customer' AND r.MerchantID = m.MerchantID
        LEFT JOIN Customer c ON r.CustomerType = 'Customer' AND r.CustomerID = c.CustomerID
    """

    def get_list_by_customer(self, page=1, per_page=10, search=None, status=None, expense_type_id=None):
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

            conditions = []
            params = []

            if search:
                conditions.append(f"({self._CUSTOMER_EXPR} LIKE ?)")
                params.append(f'%{search}%')

            if status:
                conditions.append("r.Status = ?")
                params.append(status)

            if expense_type_id:
                conditions.append("r.ExpenseTypeID = ?")
                params.append(expense_type_id)

            extra_where = ""
            if conditions:
                extra_where = " AND " + " AND ".join(conditions)

            group_clause = f" GROUP BY r.CustomerType, r.CustomerID, {self._CUSTOMER_EXPR}"

            count_query = f"""
                SELECT COUNT(*) FROM (
                    SELECT r.CustomerType, r.CustomerID, {self._CUSTOMER_EXPR} AS CustomerName
                    FROM Receivable r
                    {self._BASE_JOINS}
                    WHERE r.IsActive = 1
                    {extra_where}
                    GROUP BY r.CustomerType, r.CustomerID, {self._CUSTOMER_EXPR}
                ) sub
            """
            count_params = list(params)
            cursor.execute(count_query, count_params)
            total_count = cursor.fetchone()[0]

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
            cursor.execute(sum_query, count_params)
            sum_row = cursor.fetchone()

            offset = (page - 1) * per_page
            base_query += extra_where + group_clause
            base_query += " ORDER BY TotalRemaining DESC, CustomerName OFFSET ? ROWS FETCH NEXT ? ROWS ONLY"
            params.extend([offset, per_page])

            cursor.execute(base_query, params)
            rows = cursor.fetchall()

            return rows, total_count, sum_row

    def check_has_collection(self, receivable_id):
        """检查应收是否有关联的收款记录"""
        with DBConnection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT COUNT(*) FROM CollectionRecord
                WHERE ReceivableID = ?
            """, (receivable_id,))
            return cursor.fetchone()[0]

    def check_has_prepayment_apply(self, receivable_id):
        """检查应收是否有关联的预收冲抵记录"""
        with DBConnection() as conn:
            cursor = conn.cursor()
            # 先检查 PrepaymentApply 表是否存在（P2 功能可能未部署）
            cursor.execute("""
                SELECT COUNT(*) FROM INFORMATION_SCHEMA.TABLES 
                WHERE TABLE_NAME = 'PrepaymentApply'
            """)
            if cursor.fetchone()[0] == 0:
                return 0
            cursor.execute("""
                SELECT COUNT(*) FROM PrepaymentApply
                WHERE ReceivableID = ?
            """, (receivable_id,))
            return cursor.fetchone()[0]

    def check_has_deposit_transfer(self, receivable_id):
        """检查应收是否有关联的押金转抵记录"""
        with DBConnection() as conn:
            cursor = conn.cursor()
            # 先检查 DepositTransfer 表是否存在（P2 功能可能未部署）
            cursor.execute("""
                SELECT COUNT(*) FROM INFORMATION_SCHEMA.TABLES 
                WHERE TABLE_NAME = 'DepositTransfer'
            """)
            if cursor.fetchone()[0] == 0:
                return 0
            cursor.execute("""
                SELECT COUNT(*) FROM DepositTransfer
                WHERE ReceivableID = ?
            """, (receivable_id,))
            return cursor.fetchone()[0]
