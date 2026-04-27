# -*- coding: utf-8 -*-
"""
保证金/押金管理服务层
负责押金的CRUD、退还、扣除、转抵等核心业务
"""
import logging
from datetime import datetime
from utils.database import DBConnection
from utils.format_utils import format_date, format_datetime
from utils.sequence import generate_serial_no
from app.services.account_service import AccountService

logger = logging.getLogger(__name__)


class DepositService:
    """保证金/押金管理服务"""

    def __init__(self):
        self.account_svc = AccountService()

    # ========== 押金 CRUD ==========

    def get_deposits(self, page=1, per_page=10, customer_type=None,
                     deposit_type=None, status=None, search=None):
        """获取押金列表"""
        with DBConnection() as conn:
            cursor = conn.cursor()

            base_query = """
                SELECT d.DepositID, d.CustomerType, d.CustomerID, d.CustomerName,
                       d.DepositType, dt.DictName AS DepositTypeName,
                       d.Amount, d.RefundAmount, d.DeductAmount, d.TransferAmount,
                       d.Status, d.AccountID, ISNULL(a.AccountName, '') AS AccountName,
                       d.RelatedContractID, d.Description,
                       d.CreatedBy, ISNULL(u.RealName, '') AS OperatorName,
                       d.CreateTime, d.UpdateTime
                FROM Deposit d
                LEFT JOIN Sys_Dictionary dt ON d.DepositType = dt.DictCode AND dt.DictType = 'deposit_type'
                LEFT JOIN Account a ON d.AccountID = a.AccountID
                LEFT JOIN [User] u ON d.CreatedBy = u.UserID
            """
            count_query = "SELECT COUNT(*) FROM Deposit d"

            conditions = []
            params = []

            if customer_type:
                conditions.append("d.CustomerType = ?")
                params.append(customer_type)

            if deposit_type:
                conditions.append("d.DepositType = ?")
                params.append(deposit_type)

            if status:
                conditions.append("d.Status = ?")
                params.append(status)

            if search:
                conditions.append("d.CustomerName LIKE ?")
                params.append(f'%{search}%')

            where_clause = ""
            if conditions:
                where_clause = " WHERE " + " AND ".join(conditions)
                base_query += where_clause
                count_query += where_clause

            offset = (page - 1) * per_page
            base_query += " ORDER BY d.DepositID DESC OFFSET ? ROWS FETCH NEXT ? ROWS ONLY"
            params.extend([offset, per_page])

            cursor.execute(base_query, params)
            rows = cursor.fetchall()

            count_params = params[:-2]
            cursor.execute(count_query, count_params)
            total_count = cursor.fetchone()[0]

            result_list = []
            for row in rows:
                remaining = float(row.Amount) - float(row.RefundAmount) - float(row.DeductAmount) - float(row.TransferAmount)
                result_list.append({
                    'deposit_id': row.DepositID,
                    'customer_type': row.CustomerType,
                    'customer_id': row.CustomerID,
                    'customer_name': row.CustomerName,
                    'deposit_type': row.DepositType,
                    'deposit_type_name': row.DepositTypeName or row.DepositType,
                    'amount': float(row.Amount),
                    'refund_amount': float(row.RefundAmount),
                    'deduct_amount': float(row.DeductAmount),
                    'transfer_amount': float(row.TransferAmount),
                    'remaining_amount': remaining,
                    'status': row.Status,
                    'account_id': row.AccountID,
                    'account_name': row.AccountName,
                    'related_contract_id': row.RelatedContractID,
                    'description': row.Description or '',
                    'operator_name': row.OperatorName,
                    'create_time': format_datetime(row.CreateTime),
                })

            total_pages = (total_count + per_page - 1) // per_page if total_count > 0 else 0

            return {
                'items': result_list,
                'total_count': total_count,
                'total_pages': total_pages,
                'current_page': page
            }

    def get_deposit_by_id(self, deposit_id):
        """获取单条押金详情"""
        with DBConnection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT d.DepositID, d.CustomerType, d.CustomerID, d.CustomerName,
                       d.DepositType, dt.DictName AS DepositTypeName,
                       d.Amount, d.RefundAmount, d.DeductAmount, d.TransferAmount,
                       d.Status, d.AccountID, d.CashFlowID,
                       d.RelatedContractID, d.Description,
                       d.CreatedBy, d.CreateTime, d.UpdateTime
                FROM Deposit d
                LEFT JOIN Sys_Dictionary dt ON d.DepositType = dt.DictCode AND dt.DictType = 'deposit_type'
                WHERE d.DepositID = ?
            """, (deposit_id,))
            row = cursor.fetchone()
            if not row:
                return None

            remaining = float(row.Amount) - float(row.RefundAmount) - float(row.DeductAmount) - float(row.TransferAmount)
            return {
                'deposit_id': row.DepositID,
                'customer_type': row.CustomerType,
                'customer_id': row.CustomerID,
                'customer_name': row.CustomerName,
                'deposit_type': row.DepositType,
                'deposit_type_name': row.DepositTypeName or row.DepositType,
                'amount': float(row.Amount),
                'refund_amount': float(row.RefundAmount),
                'deduct_amount': float(row.DeductAmount),
                'transfer_amount': float(row.TransferAmount),
                'remaining_amount': remaining,
                'status': row.Status,
                'account_id': row.AccountID,
                'cash_flow_id': row.CashFlowID,
                'related_contract_id': row.RelatedContractID,
                'description': row.Description or '',
                'created_by': row.CreatedBy,
                'create_time': format_datetime(row.CreateTime),
            }

    def create_deposit(self, customer_type, customer_id, customer_name,
                       deposit_type, amount, account_id,
                       related_contract_id=None, description=None, created_by=None):
        """
        收取押金（事务内完成四步联动）

        1. INSERT Deposit
        2. INSERT CashFlow（收入）
        3. UPDATE Account Balance（+）
        4. UPDATE Deposit SET CashFlowID
        """
        if not customer_name or not customer_name.strip():
            raise ValueError("客户名称不能为空")
        if not deposit_type:
            raise ValueError("请选择押金类型")
        if not amount or float(amount) <= 0:
            raise ValueError("金额必须大于0")
        if not account_id:
            raise ValueError("请选择收款账户")

        # 验证账户
        account = self.account_svc.get_account_by_id(account_id)
        if not account:
            raise ValueError("账户不存在")
        if account['status'] != '有效':
            raise ValueError("该账户已停用")

        try:
            with DBConnection() as conn:
                cursor = conn.cursor()

                # 1. INSERT Deposit
                cursor.execute("""
                    INSERT INTO Deposit (
                        CustomerType, CustomerID, CustomerName, DepositType,
                        Amount, RefundAmount, DeductAmount, TransferAmount,
                        Status, AccountID, RelatedContractID, Description, CreatedBy
                    ) OUTPUT INSERTED.DepositID
                    VALUES (?, ?, ?, ?, ?, 0, 0, 0, N'收取中', ?, ?, ?, ?)
                """, (
                    customer_type, int(customer_id), customer_name.strip(),
                    deposit_type, float(amount),
                    account_id,
                    int(related_contract_id) if related_contract_id else None,
                    description.strip() if description else None,
                    created_by
                ))

                row = cursor.fetchone()
                deposit_id = row[0]

                # 2. INSERT CashFlow
                transaction_no = generate_serial_no(cursor, 'CF', 'CashFlow', 'TransactionNo')

                cursor.execute("""
                    INSERT INTO CashFlow (
                        Amount, Direction, ExpenseTypeID, Description,
                        TransactionDate, ReferenceID, ReferenceType, CreatedBy,
                        AccountID, TransactionNo
                    ) OUTPUT INSERTED.CashFlowID
                    VALUES (?, N'收入', NULL, ?, GETDATE(), ?, N'deposit', ?, ?, ?)
                """, (
                    float(amount),
                    description or f'收取押金 — {customer_name}',
                    deposit_id,
                    created_by,
                    account_id,
                    transaction_no
                ))

                row = cursor.fetchone()
                cash_flow_id = row[0]

                # 3. UPDATE Account Balance
                self.account_svc._adjust_balance(cursor, account_id, float(amount), 'income')

                # 4. UPDATE Deposit SET CashFlowID
                cursor.execute("""
                    UPDATE Deposit SET CashFlowID = ? WHERE DepositID = ?
                """, (cash_flow_id, deposit_id))

                conn.commit()

            return deposit_id

        except ValueError:
            raise
        except Exception as e:
            logger.error(f'收取押金失败: {e}')
            raise ValueError(f'收取失败：{str(e)}')

    # ========== 押金操作：退还 / 扣除 / 转抵 ==========

    def refund_deposit(self, deposit_id, amount, account_id, description=None, created_by=None):
        """
        退还押金（事务内三步联动）

        1. INSERT DepositOperation (refund)
        2. INSERT CashFlow (支出)
        3. UPDATE Account Balance (-)
        4. UPDATE Deposit (RefundAmount +, Status)
        """
        deposit = self.get_deposit_by_id(deposit_id)
        if not deposit:
            return {'success': False, 'message': '押金记录不存在'}

        remaining = deposit['remaining_amount']
        if float(amount) <= 0:
            return {'success': False, 'message': '退还金额必须大于0'}
        if float(amount) > remaining + 0.01:
            return {'success': False, 'message': f'退还金额超过剩余金额 ¥{remaining:.2f}'}

        # 验证账户
        account = self.account_svc.get_account_by_id(account_id)
        if not account:
            return {'success': False, 'message': '账户不存在'}
        if account['status'] != '有效':
            return {'success': False, 'message': '该账户已停用'}
        if account['balance'] < float(amount):
            return {'success': False, 'message': f'账户余额不足（当前余额: ¥{account["balance"]:.2f}）'}

        try:
            with DBConnection() as conn:
                cursor = conn.cursor()

                # 1. INSERT DepositOperation
                cursor.execute("""
                    INSERT INTO DepositOperation (DepositID, OperationType, Amount, AccountID, Description, CreatedBy)
                    OUTPUT INSERTED.OperationID
                    VALUES (?, N'refund', ?, ?, ?, ?)
                """, (deposit_id, float(amount), account_id,
                      description or f'退还押金 — {deposit["customer_name"]}', created_by))

                operation_id = cursor.fetchone()[0]

                # 2. INSERT CashFlow
                transaction_no = generate_serial_no(cursor, 'CF', 'CashFlow', 'TransactionNo')

                cursor.execute("""
                    INSERT INTO CashFlow (
                        Amount, Direction, ExpenseTypeID, Description,
                        TransactionDate, ReferenceID, ReferenceType, CreatedBy,
                        AccountID, TransactionNo
                    ) OUTPUT INSERTED.CashFlowID
                    VALUES (?, N'支出', NULL, ?, GETDATE(), ?, N'deposit_refund', ?, ?, ?)
                """, (
                    float(amount),
                    description or f'退还押金 — {deposit["customer_name"]}',
                    operation_id,
                    created_by,
                    account_id,
                    transaction_no
                ))

                cash_flow_id = cursor.fetchone()[0]

                # UPDATE DepositOperation SET CashFlowID
                cursor.execute("""
                    UPDATE DepositOperation SET CashFlowID = ? WHERE OperationID = ?
                """, (cash_flow_id, operation_id))

                # 3. UPDATE Account Balance
                self.account_svc._adjust_balance(cursor, account_id, float(amount), 'expense')

                # 4. UPDATE Deposit
                new_refund = deposit['refund_amount'] + float(amount)
                new_remaining = deposit['remaining_amount'] - float(amount)
                new_status = '已结清' if new_remaining <= 0.01 else '部分退还'

                cursor.execute("""
                    UPDATE Deposit SET RefundAmount = ?, Status = ?, UpdateTime = GETDATE()
                    WHERE DepositID = ?
                """, (new_refund, new_status, deposit_id))

                conn.commit()

            return {
                'success': True,
                'message': f'退还成功，金额 ¥{float(amount):.2f}',
                'operation_id': operation_id
            }

        except ValueError as e:
            return {'success': False, 'message': str(e)}
        except Exception as e:
            logger.error(f'退还押金失败: {e}')
            return {'success': False, 'message': f'退还失败：{str(e)}'}

    def deduct_deposit(self, deposit_id, amount, expense_type_id=None, description=None, created_by=None):
        """
        扣除押金（不产生资金流出，只减少押金余额，用于扣违约金等）

        1. INSERT DepositOperation (deduct)
        2. UPDATE Deposit (DeductAmount +, Status)
        """
        deposit = self.get_deposit_by_id(deposit_id)
        if not deposit:
            return {'success': False, 'message': '押金记录不存在'}

        remaining = deposit['remaining_amount']
        if float(amount) <= 0:
            return {'success': False, 'message': '扣除金额必须大于0'}
        if float(amount) > remaining + 0.01:
            return {'success': False, 'message': f'扣除金额超过剩余金额 ¥{remaining:.2f}'}

        try:
            with DBConnection() as conn:
                cursor = conn.cursor()

                # 1. INSERT DepositOperation
                cursor.execute("""
                    INSERT INTO DepositOperation (DepositID, OperationType, Amount, Description, CreatedBy)
                    VALUES (?, N'deduct', ?, ?, ?)
                """, (deposit_id, float(amount),
                      description or f'扣除押金 — {deposit["customer_name"]}', created_by))

                # 2. UPDATE Deposit
                new_deduct = deposit['deduct_amount'] + float(amount)
                new_remaining = deposit['remaining_amount'] - float(amount)
                new_status = '已结清' if new_remaining <= 0.01 else '部分退还'

                cursor.execute("""
                    UPDATE Deposit SET DeductAmount = ?, Status = ?, UpdateTime = GETDATE()
                    WHERE DepositID = ?
                """, (new_deduct, new_status, deposit_id))

                conn.commit()

            return {
                'success': True,
                'message': f'扣除成功，金额 ¥{float(amount):.2f}'
            }

        except Exception as e:
            logger.error(f'扣除押金失败: {e}')
            return {'success': False, 'message': f'扣除失败：{str(e)}'}

    def transfer_deposit(self, deposit_id, receivable_id, amount, description=None, created_by=None):
        """
        押金转抵应收（只允许转抵同一商户的应收）

        1. INSERT DepositOperation (transfer)
        2. UPDATE Receivable (PaidAmount+, RemainingAmount-, Status)
        3. UPDATE Deposit (TransferAmount+, Status)
        """
        deposit = self.get_deposit_by_id(deposit_id)
        if not deposit:
            return {'success': False, 'message': '押金记录不存在'}

        remaining = deposit['remaining_amount']
        if float(amount) <= 0:
            return {'success': False, 'message': '转抵金额必须大于0'}
        if float(amount) > remaining + 0.01:
            return {'success': False, 'message': f'转抵金额超过剩余金额 ¥{remaining:.2f}'}

        try:
            with DBConnection() as conn:
                cursor = conn.cursor()

                # 检查应收存在且属于同一客户
                cursor.execute("""
                    SELECT ReceivableID, RemainingAmount, CustomerType, CustomerID
                    FROM Receivable WHERE ReceivableID = ? AND IsActive = 1
                """, (receivable_id,))
                rv = cursor.fetchone()
                if not rv:
                    return {'success': False, 'message': f'应收记录 #{receivable_id} 不存在'}

                # 限制：只允许转抵同一商户的应收
                if rv.CustomerType != deposit['customer_type'] or rv.CustomerID != deposit['customer_id']:
                    return {'success': False, 'message': '押金只能转抵同一商户的应收'}

                rv_remaining = float(rv.RemainingAmount)
                if float(amount) > rv_remaining + 0.01:
                    return {'success': False, 'message': f'转抵金额超过应收剩余金额 ¥{rv_remaining:.2f}'}

                # 1. INSERT DepositOperation
                cursor.execute("""
                    INSERT INTO DepositOperation (DepositID, OperationType, Amount, ReceivableID, Description, CreatedBy)
                    VALUES (?, N'transfer', ?, ?, ?, ?)
                """, (deposit_id, float(amount), receivable_id,
                      description or f'押金转抵应收#{receivable_id}', created_by))

                # 2. UPDATE Receivable
                cursor.execute("""
                    UPDATE Receivable
                    SET PaidAmount = PaidAmount + ?,
                        RemainingAmount = RemainingAmount - ?,
                        UpdateTime = GETDATE()
                    WHERE ReceivableID = ?
                """, (float(amount), float(amount), receivable_id))

                new_rv_remaining = rv_remaining - float(amount)
                rv_status = '已付款' if new_rv_remaining <= 0.01 else '部分付款'
                cursor.execute("""
                    UPDATE Receivable SET Status = ?, UpdateTime = GETDATE()
                    WHERE ReceivableID = ?
                """, (rv_status, receivable_id))

                # 3. UPDATE Deposit
                new_transfer = deposit['transfer_amount'] + float(amount)
                new_remaining = deposit['remaining_amount'] - float(amount)
                new_status = '已结清' if new_remaining <= 0.01 else '部分退还'

                cursor.execute("""
                    UPDATE Deposit SET TransferAmount = ?, Status = ?, UpdateTime = GETDATE()
                    WHERE DepositID = ?
                """, (new_transfer, new_status, deposit_id))

                conn.commit()

            return {
                'success': True,
                'message': f'转抵成功，金额 ¥{float(amount):.2f}'
            }

        except Exception as e:
            logger.error(f'押金转抵失败: {e}')
            return {'success': False, 'message': f'转抵失败：{str(e)}'}

    def get_operations(self, deposit_id):
        """获取押金操作记录"""
        with DBConnection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT o.OperationID, o.DepositID, o.OperationType, o.Amount,
                       o.AccountID, ISNULL(a.AccountName, '') AS AccountName,
                       o.ReceivableID, o.CashFlowID,
                       o.Description, o.CreatedBy,
                       ISNULL(u.RealName, '') AS OperatorName,
                       o.CreateTime
                FROM DepositOperation o
                LEFT JOIN Account a ON o.AccountID = a.AccountID
                LEFT JOIN [User] u ON o.CreatedBy = u.UserID
                WHERE o.DepositID = ?
                ORDER BY o.CreateTime DESC
            """, (deposit_id,))
            rows = cursor.fetchall()

            type_map = {'refund': '退还', 'deduct': '扣除', 'transfer': '转抵'}
            result = []
            for row in rows:
                result.append({
                    'operation_id': row.OperationID,
                    'operation_type': row.OperationType,
                    'operation_type_text': type_map.get(row.OperationType, row.OperationType),
                    'amount': float(row.Amount),
                    'account_id': row.AccountID,
                    'account_name': row.AccountName,
                    'receivable_id': row.ReceivableID,
                    'cash_flow_id': row.CashFlowID,
                    'description': row.Description or '',
                    'operator_name': row.OperatorName,
                    'create_time': format_datetime(row.CreateTime),
                })
            return result

    def get_summary(self):
        """获取押金汇总统计"""
        with DBConnection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT
                    COUNT(*) AS TotalCount,
                    ISNULL(SUM(Amount), 0) AS TotalAmount,
                    ISNULL(SUM(RefundAmount), 0) AS TotalRefund,
                    ISNULL(SUM(DeductAmount), 0) AS TotalDeduct,
                    ISNULL(SUM(TransferAmount), 0) AS TotalTransfer,
                    ISNULL(SUM(Amount - RefundAmount - DeductAmount - TransferAmount), 0) AS TotalRemaining
                FROM Deposit
            """)
            row = cursor.fetchone()
            return {
                'total_count': row.TotalCount,
                'total_amount': float(row.TotalAmount),
                'total_refund': float(row.TotalRefund),
                'total_deduct': float(row.TotalDeduct),
                'total_transfer': float(row.TotalTransfer),
                'total_remaining': float(row.TotalRemaining),
            }
