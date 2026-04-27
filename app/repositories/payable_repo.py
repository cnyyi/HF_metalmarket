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
