# -*- coding: utf-8 -*-
from utils.database import DBConnection


class CashFlowRepository:
    """现金流水数据访问层"""

    def create(self, amount, direction, expense_type_id, description,
               transaction_date, reference_id, reference_type, created_by):
        """
        创建现金流水记录

        Returns:
            int: 新创建的流水ID
        """
        with DBConnection() as conn:
            cursor = conn.cursor()
            sql = """
                INSERT INTO CashFlow (
                    Amount, Direction, ExpenseTypeID, Description,
                    TransactionDate, ReferenceID, ReferenceType, CreatedBy
                ) OUTPUT INSERTED.CashFlowID
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """
            cursor.execute(sql, amount, direction, expense_type_id,
                           description, transaction_date, reference_id,
                           reference_type, created_by)
            row = cursor.fetchone()
            new_id = row[0] if row else None
            conn.commit()
            return new_id

    def get_list(self, page=1, per_page=10, direction=None, expense_type_id=None,
                 start_date=None, end_date=None, account_id=None):
        """分页获取现金流水列表"""
        with DBConnection() as conn:
            cursor = conn.cursor()

            base_query = """
                SELECT cf.CashFlowID, cf.Amount, cf.Direction,
                       cf.ExpenseTypeID, ISNULL(sd.DictName, et.ExpenseTypeName) AS ExpenseTypeName,
                       cf.Description, cf.TransactionDate,
                       cf.ReferenceID, cf.ReferenceType,
                       cf.CreatedBy, u.RealName AS OperatorName,
                       cf.CreateTime,
                       cf.AccountID, ISNULL(a.AccountName, '') AS AccountName,
                       cf.TransactionNo
                FROM CashFlow cf
                LEFT JOIN Sys_Dictionary sd ON cf.ExpenseTypeID = sd.DictID
                LEFT JOIN ExpenseType et ON cf.ExpenseTypeID = et.ExpenseTypeID AND sd.DictID IS NULL
                LEFT JOIN [User] u ON cf.CreatedBy = u.UserID
                LEFT JOIN Account a ON cf.AccountID = a.AccountID
            """

            count_query = "SELECT COUNT(*) FROM CashFlow cf"

            conditions = []
            params = []

            if direction:
                conditions.append("cf.Direction = ?")
                params.append(direction)

            if expense_type_id:
                conditions.append("cf.ExpenseTypeID = ?")
                params.append(expense_type_id)

            if start_date:
                conditions.append("cf.TransactionDate >= ?")
                params.append(start_date)

            if end_date:
                conditions.append("cf.TransactionDate <= ?")
                params.append(end_date + ' 23:59:59' if len(end_date) == 10 else end_date)

            if account_id:
                conditions.append("cf.AccountID = ?")
                params.append(account_id)

            where_clause = ""
            if conditions:
                where_clause = " WHERE " + " AND ".join(conditions)
                base_query += where_clause
                count_query += where_clause

            offset = (page - 1) * per_page
            base_query += " ORDER BY cf.CashFlowID DESC OFFSET ? ROWS FETCH NEXT ? ROWS ONLY"
            params.extend([offset, per_page])

            cursor.execute(base_query, params)
            rows = cursor.fetchall()

            count_params = params[:-2]
            cursor.execute(count_query, count_params)
            total_count = cursor.fetchone()[0]

            return rows, total_count

    def get_summary(self, start_date=None, end_date=None):
        """获取收支汇总"""
        with DBConnection() as conn:
            cursor = conn.cursor()

            conditions = []
            params = []

            if start_date:
                conditions.append("TransactionDate >= ?")
                params.append(start_date)

            if end_date:
                conditions.append("TransactionDate <= ?")
                params.append(end_date + ' 23:59:59' if len(end_date) == 10 else end_date)

            where_clause = ""
            if conditions:
                where_clause = " WHERE " + " AND ".join(conditions)

            sql = f"""
                SELECT 
                    ISNULL(SUM(CASE WHEN Direction = N'收入' THEN Amount ELSE 0 END), 0) AS TotalIncome,
                    ISNULL(SUM(CASE WHEN Direction = N'支出' THEN Amount ELSE 0 END), 0) AS TotalExpense,
                    ISNULL(SUM(CASE WHEN Direction = N'收入' THEN Amount ELSE -Amount END), 0) AS NetCashFlow
                FROM CashFlow
                {where_clause}
            """

            cursor.execute(sql, params)
            return cursor.fetchone()
