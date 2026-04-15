# -*- coding: utf-8 -*-
from utils.database import DBConnection


class ReceivableRepository:

    def get_list(self, page=1, per_page=10, search=None, status=None):
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
                       r.DueDate, r.Status, r.Description,
                       r.ReferenceID, r.ReferenceType,
                       r.CreateTime, r.UpdateTime
                FROM Receivable r
                LEFT JOIN Sys_Dictionary sd ON r.ExpenseTypeID = sd.DictID AND sd.DictType = 'expense_item_income'
                LEFT JOIN ExpenseType et ON r.ExpenseTypeID = et.ExpenseTypeID AND sd.DictID IS NULL
                LEFT JOIN Merchant m ON r.CustomerType <> 'Customer' AND r.MerchantID = m.MerchantID
                LEFT JOIN Customer c ON r.CustomerType = 'Customer' AND r.CustomerID = c.CustomerID
            """

            count_query = "SELECT COUNT(*) FROM Receivable r"

            conditions = []
            params = []

            if search:
                conditions.append("(m.MerchantName LIKE ? OR c.CustomerName LIKE ?)")
                p = f'%{search}%'
                params.extend([p, p])

            if status:
                conditions.append("r.Status = ?")
                params.append(status)

            where_clause = ""
            if conditions:
                where_clause = " WHERE " + " AND ".join(conditions)
                base_query += where_clause
                count_query += where_clause

            offset = (page - 1) * per_page
            base_query += " ORDER BY r.ReceivableID DESC OFFSET ? ROWS FETCH NEXT ? ROWS ONLY"
            params.extend([offset, per_page])

            cursor.execute(base_query, params)
            rows = cursor.fetchall()

            count_params = params[:-2]
            cursor.execute(count_query, count_params)
            total_count = cursor.fetchone()[0]

            return rows, total_count

    def get_by_id(self, receivable_id):
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
                       r.DueDate, r.Status, r.Description,
                       r.ReferenceID, r.ReferenceType,
                       r.CreateTime, r.UpdateTime
                FROM Receivable r
                LEFT JOIN Sys_Dictionary sd ON r.ExpenseTypeID = sd.DictID AND sd.DictType = 'expense_item_income'
                LEFT JOIN ExpenseType et ON r.ExpenseTypeID = et.ExpenseTypeID AND sd.DictID IS NULL
                LEFT JOIN Merchant m ON r.CustomerType <> 'Customer' AND r.MerchantID = m.MerchantID
                LEFT JOIN Customer c ON r.CustomerType = 'Customer' AND r.CustomerID = c.CustomerID
                WHERE r.ReceivableID = ?
            """
            cursor.execute(sql, receivable_id)
            return cursor.fetchone()

    def create(self, merchant_id=None, expense_type_id=None, amount=None, due_date=None,
               description=None, reference_id=None, reference_type=None,
               customer_type='Merchant', customer_id=None):
        with DBConnection() as conn:
            cursor = conn.cursor()
            # 如果是 Merchant 类型，兼容旧逻辑
            if customer_type == 'Merchant' and customer_id and not merchant_id:
                merchant_id = customer_id
            if customer_type == 'Merchant' and merchant_id and not customer_id:
                customer_id = merchant_id

            sql = """
                INSERT INTO Receivable (MerchantID, ExpenseTypeID, Amount, DueDate, Status, PaidAmount, RemainingAmount,
                                        Description, ReferenceID, ReferenceType, CustomerType, CustomerID)
                OUTPUT INSERTED.ReceivableID
                VALUES (?, ?, ?, ?, N'未付款', 0, ?, ?, ?, ?, ?, ?)
            """
            cursor.execute(sql, merchant_id, expense_type_id, amount, due_date, amount,
                           description, reference_id, reference_type, customer_type, customer_id)
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
                WHERE DueDate < GETDATE() AND Status != N'已付款'
            """
            cursor.execute(sql)
            return cursor.fetchall()

    def delete(self, receivable_id):
        with DBConnection() as conn:
            cursor = conn.cursor()
            sql = "DELETE FROM Receivable WHERE ReceivableID = ?"
            cursor.execute(sql, receivable_id)
            conn.commit()
            return cursor.rowcount
