# -*- coding: utf-8 -*-
"""
预收/预付管理服务层
负责预收预付的CRUD、冲抵核销等核心业务
"""
import logging
from datetime import datetime
from utils.database import DBConnection
from app.services.account_service import AccountService

logger = logging.getLogger(__name__)


class PrepaymentService:
    """预收/预付管理服务"""

    def __init__(self):
        self.account_svc = AccountService()

    # ========== 预收/预付 CRUD ==========

    def get_prepayments(self, page=1, per_page=10, direction=None,
                        customer_type=None, status=None, search=None):
        """获取预收/预付列表"""
        with DBConnection() as conn:
            cursor = conn.cursor()

            base_query = """
                SELECT p.PrepaymentID, p.Direction, p.CustomerType, p.CustomerID,
                       p.CustomerName, p.ExpenseTypeID,
                       ISNULL(sd.DictName, '') AS ExpenseTypeName,
                       p.TotalAmount, p.AppliedAmount, p.RemainingAmount,
                       p.Description, p.Status, p.AccountID,
                       ISNULL(a.AccountName, '') AS AccountName,
                       p.CreatedBy, ISNULL(u.RealName, '') AS OperatorName,
                       p.CreateTime, p.UpdateTime
                FROM Prepayment p
                LEFT JOIN Sys_Dictionary sd ON p.ExpenseTypeID = sd.DictID
                LEFT JOIN Account a ON p.AccountID = a.AccountID
                LEFT JOIN [User] u ON p.CreatedBy = u.UserID
            """
            count_query = "SELECT COUNT(*) FROM Prepayment p"

            conditions = []
            params = []

            if direction:
                conditions.append("p.Direction = ?")
                params.append(direction)

            if customer_type:
                conditions.append("p.CustomerType = ?")
                params.append(customer_type)

            if status:
                conditions.append("p.Status = ?")
                params.append(status)

            if search:
                conditions.append("p.CustomerName LIKE ?")
                params.append(f'%{search}%')

            where_clause = ""
            if conditions:
                where_clause = " WHERE " + " AND ".join(conditions)
                base_query += where_clause
                count_query += where_clause

            offset = (page - 1) * per_page
            base_query += " ORDER BY p.PrepaymentID DESC OFFSET ? ROWS FETCH NEXT ? ROWS ONLY"
            params.extend([offset, per_page])

            cursor.execute(base_query, params)
            rows = cursor.fetchall()

            count_params = params[:-2]
            cursor.execute(count_query, count_params)
            total_count = cursor.fetchone()[0]

            result_list = []
            for row in rows:
                result_list.append({
                    'prepayment_id': row.PrepaymentID,
                    'direction': row.Direction,
                    'direction_text': '预收' if row.Direction == 'income' else '预付',
                    'customer_type': row.CustomerType,
                    'customer_id': row.CustomerID,
                    'customer_name': row.CustomerName,
                    'expense_type_id': row.ExpenseTypeID,
                    'expense_type_name': row.ExpenseTypeName,
                    'total_amount': float(row.TotalAmount),
                    'applied_amount': float(row.AppliedAmount),
                    'remaining_amount': float(row.RemainingAmount),
                    'description': row.Description or '',
                    'status': row.Status,
                    'account_id': row.AccountID,
                    'account_name': row.AccountName,
                    'operator_name': row.OperatorName,
                    'create_time': row.CreateTime.strftime('%Y-%m-%d %H:%M') if row.CreateTime else '',
                })

            total_pages = (total_count + per_page - 1) // per_page if total_count > 0 else 0

            return {
                'items': result_list,
                'total_count': total_count,
                'total_pages': total_pages,
                'current_page': page
            }

    def get_prepayment_by_id(self, prepayment_id):
        """获取单条预收/预付详情"""
        with DBConnection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT p.PrepaymentID, p.Direction, p.CustomerType, p.CustomerID,
                       p.CustomerName, p.ExpenseTypeID,
                       ISNULL(sd.DictName, '') AS ExpenseTypeName,
                       p.TotalAmount, p.AppliedAmount, p.RemainingAmount,
                       p.Description, p.Status, p.AccountID, p.CashFlowID,
                       p.CreatedBy, p.CreateTime, p.UpdateTime
                FROM Prepayment p
                LEFT JOIN Sys_Dictionary sd ON p.ExpenseTypeID = sd.DictID
                WHERE p.PrepaymentID = ?
            """, (prepayment_id,))
            row = cursor.fetchone()
            if not row:
                return None
            return {
                'prepayment_id': row.PrepaymentID,
                'direction': row.Direction,
                'direction_text': '预收' if row.Direction == 'income' else '预付',
                'customer_type': row.CustomerType,
                'customer_id': row.CustomerID,
                'customer_name': row.CustomerName,
                'expense_type_id': row.ExpenseTypeID,
                'expense_type_name': row.ExpenseTypeName,
                'total_amount': float(row.TotalAmount),
                'applied_amount': float(row.AppliedAmount),
                'remaining_amount': float(row.RemainingAmount),
                'description': row.Description or '',
                'status': row.Status,
                'account_id': row.AccountID,
                'cash_flow_id': row.CashFlowID,
                'created_by': row.CreatedBy,
                'create_time': row.CreateTime.strftime('%Y-%m-%d %H:%M') if row.CreateTime else '',
            }

    def create_prepayment(self, direction, customer_type, customer_id,
                          customer_name, total_amount, account_id,
                          expense_type_id=None, description=None, created_by=None):
        """
        创建预收/预付（事务内完成四步联动）

        1. INSERT Prepayment
        2. INSERT CashFlow（预收→收入，预付→支出）
        3. UPDATE Account Balance
        4. UPDATE Prepayment SET CashFlowID
        """
        if direction not in ('income', 'expense'):
            raise ValueError("方向参数无效，必须是 income 或 expense")
        if not customer_name or not customer_name.strip():
            raise ValueError("客户名称不能为空")
        if not total_amount or float(total_amount) <= 0:
            raise ValueError("金额必须大于0")
        if not account_id:
            raise ValueError("请选择收支账户")

        # 验证账户
        account = self.account_svc.get_account_by_id(account_id)
        if not account:
            raise ValueError("账户不存在")
        if account['status'] != '有效':
            raise ValueError("该账户已停用")

        # 预付时检查余额
        if direction == 'expense' and account['balance'] < float(total_amount):
            raise ValueError(f"账户余额不足（当前余额: ¥{account['balance']:.2f}）")

        dir_text = '预收' if direction == 'income' else '预付'
        cf_direction = '收入' if direction == 'income' else '支出'

        try:
            with DBConnection() as conn:
                cursor = conn.cursor()

                # 1. INSERT Prepayment
                cursor.execute("""
                    INSERT INTO Prepayment (
                        Direction, CustomerType, CustomerID, CustomerName,
                        ExpenseTypeID, TotalAmount, AppliedAmount, RemainingAmount,
                        Description, Status, AccountID, CreatedBy
                    ) OUTPUT INSERTED.PrepaymentID
                    VALUES (?, ?, ?, ?, ?, ?, 0, ?, ?, N'未核销', ?, ?)
                """, (
                    direction, customer_type, int(customer_id),
                    customer_name.strip(),
                    int(expense_type_id) if expense_type_id else None,
                    float(total_amount), float(total_amount),
                    description.strip() if description else None,
                    account_id, created_by
                ))

                row = cursor.fetchone()
                prepayment_id = row[0]

                # 2. INSERT CashFlow
                from app.services.finance_service import FinanceService
                finance_svc = FinanceService()
                transaction_no = finance_svc._generate_transaction_no(cursor, 'CF')

                cursor.execute("""
                    INSERT INTO CashFlow (
                        Amount, Direction, ExpenseTypeID, Description,
                        TransactionDate, ReferenceID, ReferenceType, CreatedBy,
                        AccountID, TransactionNo
                    ) OUTPUT INSERTED.CashFlowID
                    VALUES (?, ?, ?, ?, GETDATE(), ?, N'prepayment', ?, ?, ?)
                """, (
                    float(total_amount),
                    cf_direction,
                    int(expense_type_id) if expense_type_id else None,
                    description or f'{dir_text} — {customer_name}',
                    prepayment_id,
                    created_by,
                    account_id,
                    transaction_no
                ))

                row = cursor.fetchone()
                cash_flow_id = row[0]

                # 3. UPDATE Account Balance
                bal_direction = 'income' if direction == 'income' else 'expense'
                self.account_svc._adjust_balance(cursor, account_id, float(total_amount), bal_direction)

                # 4. UPDATE Prepayment SET CashFlowID
                cursor.execute("""
                    UPDATE Prepayment SET CashFlowID = ? WHERE PrepaymentID = ?
                """, (cash_flow_id, prepayment_id))

                conn.commit()

            return prepayment_id

        except ValueError:
            raise
        except Exception as e:
            logger.error(f'创建预收/预付失败: {e}')
            raise ValueError(f'创建失败：{str(e)}')

    # ========== 冲抵核销 ==========

    def apply_prepayment(self, prepayment_id, target_items, created_by):
        """
        预收冲抵应收 / 预付冲抵应付

        Args:
            prepayment_id: 预收/预付ID
            target_items: [{'receivable_id': id, 'amount': float}, ...] 或 [{'payable_id': id, 'amount': float}, ...]
            created_by: 操作人ID

        支持一条预收冲抵多条应收/应付
        """
        prepayment = self.get_prepayment_by_id(prepayment_id)
        if not prepayment:
            return {'success': False, 'message': '预收/预付记录不存在'}
        if prepayment['status'] == '已核销':
            return {'success': False, 'message': '该记录已完全核销'}

        remaining = prepayment['remaining_amount']
        total_apply = sum(float(item['amount']) for item in target_items)

        if total_apply <= 0:
            return {'success': False, 'message': '冲抵金额必须大于0'}
        if total_apply > remaining + 0.01:  # 浮点容差
            return {'success': False, 'message': f'冲抵总额 ¥{total_apply:.2f} 超过剩余金额 ¥{remaining:.2f}'}

        direction = prepayment['direction']
        is_income = direction == 'income'

        try:
            with DBConnection() as conn:
                cursor = conn.cursor()

                applied_total = 0
                for item in target_items:
                    apply_amount = float(item['amount'])
                    if apply_amount <= 0:
                        continue

                    if is_income:
                        # 预收冲抵应收
                        receivable_id = item['receivable_id']
                        # 检查应收存在且属于同一客户
                        cursor.execute("""
                            SELECT ReceivableID, RemainingAmount, CustomerType, CustomerID
                            FROM Receivable WHERE ReceivableID = ? AND IsActive = 1
                        """, (receivable_id,))
                        rv = cursor.fetchone()
                        if not rv:
                            raise ValueError(f'应收记录 #{receivable_id} 不存在')
                        if rv.CustomerType != prepayment['customer_type'] or rv.CustomerID != prepayment['customer_id']:
                            raise ValueError(f'应收记录 #{receivable_id} 与预收客户不一致')

                        rv_remaining = float(rv.RemainingAmount)
                        if apply_amount > rv_remaining + 0.01:
                            raise ValueError(f'应收 #{receivable_id} 冲抵金额超过剩余金额')

                        # INSERT PrepaymentApply
                        cursor.execute("""
                            INSERT INTO PrepaymentApply (PrepaymentID, ReceivableID, Amount, Description, CreatedBy)
                            VALUES (?, ?, ?, ?, ?)
                        """, (prepayment_id, receivable_id, apply_amount,
                              f'预收#{prepayment_id}冲抵应收#{receivable_id}', created_by))

                        # UPDATE Receivable
                        cursor.execute("""
                            UPDATE Receivable
                            SET PaidAmount = PaidAmount + ?,
                                RemainingAmount = RemainingAmount - ?,
                                UpdateTime = GETDATE()
                            WHERE ReceivableID = ?
                        """, (apply_amount, apply_amount, receivable_id))

                        new_rv_remaining = rv_remaining - apply_amount
                        rv_status = '已付款' if new_rv_remaining <= 0.01 else '部分付款'
                        cursor.execute("""
                            UPDATE Receivable SET Status = ?, UpdateTime = GETDATE()
                            WHERE ReceivableID = ?
                        """, (rv_status, receivable_id))

                    else:
                        # 预付冲抵应付
                        payable_id = item['payable_id']
                        cursor.execute("""
                            SELECT PayableID, RemainingAmount, CustomerType, CustomerID
                            FROM Payable WHERE PayableID = ?
                        """, (payable_id,))
                        pv = cursor.fetchone()
                        if not pv:
                            raise ValueError(f'应付记录 #{payable_id} 不存在')
                        if pv.CustomerType != prepayment['customer_type'] or pv.CustomerID != prepayment['customer_id']:
                            raise ValueError(f'应付记录 #{payable_id} 与预付客户不一致')

                        pv_remaining = float(pv.RemainingAmount)
                        if apply_amount > pv_remaining + 0.01:
                            raise ValueError(f'应付 #{payable_id} 冲抵金额超过剩余金额')

                        # INSERT PrepaymentApply
                        cursor.execute("""
                            INSERT INTO PrepaymentApply (PrepaymentID, PayableID, Amount, Description, CreatedBy)
                            VALUES (?, ?, ?, ?, ?)
                        """, (prepayment_id, payable_id, apply_amount,
                              f'预付#{prepayment_id}冲抵应付#{payable_id}', created_by))

                        # UPDATE Payable
                        cursor.execute("""
                            UPDATE Payable
                            SET PaidAmount = PaidAmount + ?,
                                RemainingAmount = RemainingAmount - ?,
                                UpdateTime = GETDATE()
                            WHERE PayableID = ?
                        """, (apply_amount, apply_amount, payable_id))

                        new_pv_remaining = pv_remaining - apply_amount
                        pv_status = '已付款' if new_pv_remaining <= 0.01 else '部分付款'
                        cursor.execute("""
                            UPDATE Payable SET Status = ?, UpdateTime = GETDATE()
                            WHERE PayableID = ?
                        """, (pv_status, payable_id))

                    applied_total += apply_amount

                # UPDATE Prepayment
                new_applied = prepayment['applied_amount'] + applied_total
                new_remaining = prepayment['remaining_amount'] - applied_total
                new_status = '已核销' if new_remaining <= 0.01 else '部分核销'

                cursor.execute("""
                    UPDATE Prepayment
                    SET AppliedAmount = ?, RemainingAmount = ?,
                        Status = ?, UpdateTime = GETDATE()
                    WHERE PrepaymentID = ?
                """, (new_applied, new_remaining, new_status, prepayment_id))

                conn.commit()

            return {
                'success': True,
                'message': f'冲抵成功，共冲抵 ¥{applied_total:.2f}',
                'applied_total': applied_total,
                'new_remaining': new_remaining,
                'new_status': new_status
            }

        except ValueError as e:
            return {'success': False, 'message': str(e)}
        except Exception as e:
            logger.error(f'冲抵核销失败: {e}')
            return {'success': False, 'message': f'冲抵失败：{str(e)}'}

    def get_apply_records(self, prepayment_id):
        """获取预收/预付的冲抵明细"""
        with DBConnection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT pa.ApplyID, pa.PrepaymentID, pa.ReceivableID, pa.PayableID,
                       pa.Amount, pa.Description, pa.CreatedBy,
                       ISNULL(u.RealName, '') AS OperatorName,
                       pa.CreateTime
                FROM PrepaymentApply pa
                LEFT JOIN [User] u ON pa.CreatedBy = u.UserID
                WHERE pa.PrepaymentID = ?
                ORDER BY pa.CreateTime DESC
            """, (prepayment_id,))
            rows = cursor.fetchall()

            result = []
            for row in rows:
                result.append({
                    'apply_id': row.ApplyID,
                    'receivable_id': row.ReceivableID,
                    'payable_id': row.PayableID,
                    'amount': float(row.Amount),
                    'description': row.Description or '',
                    'operator_name': row.OperatorName,
                    'create_time': row.CreateTime.strftime('%Y-%m-%d %H:%M') if row.CreateTime else '',
                })
            return result

    def get_available_prepayments(self, direction, customer_type, customer_id):
        """获取可用于冲抵的预收/预付列表（未核销+部分核销）"""
        with DBConnection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT PrepaymentID, Direction, CustomerName, TotalAmount,
                       AppliedAmount, RemainingAmount, Status, CreateTime
                FROM Prepayment
                WHERE Direction = ? AND CustomerType = ? AND CustomerID = ?
                      AND Status IN (N'未核销', N'部分核销')
                ORDER BY CreateTime ASC
            """, (direction, customer_type, int(customer_id)))
            rows = cursor.fetchall()

            result = []
            for row in rows:
                result.append({
                    'prepayment_id': row.PrepaymentID,
                    'direction': row.Direction,
                    'direction_text': '预收' if row.Direction == 'income' else '预付',
                    'customer_name': row.CustomerName,
                    'total_amount': float(row.TotalAmount),
                    'applied_amount': float(row.AppliedAmount),
                    'remaining_amount': float(row.RemainingAmount),
                    'status': row.Status,
                    'create_time': row.CreateTime.strftime('%Y-%m-%d %H:%M') if row.CreateTime else '',
                })
            return result

    def get_summary(self, direction=None):
        """获取预收/预付汇总统计"""
        with DBConnection() as conn:
            cursor = conn.cursor()

            conditions = []
            params = []
            if direction:
                conditions.append("Direction = ?")
                params.append(direction)

            where = " WHERE " + " AND ".join(conditions) if conditions else ""

            cursor.execute(f"""
                SELECT
                    COUNT(*) AS TotalCount,
                    ISNULL(SUM(TotalAmount), 0) AS TotalAmount,
                    ISNULL(SUM(AppliedAmount), 0) AS TotalApplied,
                    ISNULL(SUM(RemainingAmount), 0) AS TotalRemaining
                FROM Prepayment
                {where}
            """, params)

            row = cursor.fetchone()
            return {
                'total_count': row.TotalCount,
                'total_amount': float(row.TotalAmount),
                'total_applied': float(row.TotalApplied),
                'total_remaining': float(row.TotalRemaining),
            }
