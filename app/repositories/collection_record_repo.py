# -*- coding: utf-8 -*-
from utils.database import DBConnection


class CollectionRecordRepository:
    """收款记录数据访问层"""

    def create(self, receivable_id, merchant_id, amount, payment_method,
               transaction_date, description, created_by):
        """
        创建收款记录

        Returns:
            int: 新创建的收款记录ID
        """
        with DBConnection() as conn:
            cursor = conn.cursor()
            sql = """
                INSERT INTO CollectionRecord (
                    ReceivableID, MerchantID, Amount, PaymentMethod,
                    TransactionDate, Description, CreatedBy
                ) OUTPUT INSERTED.CollectionRecordID
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """
            cursor.execute(sql, receivable_id, merchant_id, amount,
                           payment_method, transaction_date, description,
                           created_by)
            row = cursor.fetchone()
            new_id = row[0] if row else None
            conn.commit()
            return new_id

    def get_by_receivable_id(self, receivable_id):
        """获取某条应收的所有收款记录"""
        with DBConnection() as conn:
            cursor = conn.cursor()
            sql = """
                SELECT cr.CollectionRecordID, cr.ReceivableID, cr.MerchantID,
                       cr.Amount, cr.PaymentMethod, cr.TransactionDate,
                       cr.Description, cr.CreatedBy, cr.CreateTime,
                       m.MerchantName, u.RealName AS OperatorName
                FROM CollectionRecord cr
                INNER JOIN Merchant m ON cr.MerchantID = m.MerchantID
                LEFT JOIN [User] u ON cr.CreatedBy = u.UserID
                WHERE cr.ReceivableID = ?
                ORDER BY cr.CreateTime DESC
            """
            cursor.execute(sql, (receivable_id,))
            return cursor.fetchall()
