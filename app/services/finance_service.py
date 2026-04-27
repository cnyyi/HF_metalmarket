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

logger = logging.getLogger(__name__)


class FinanceService:
    """财务管理服务 — 统管跨表事务的业务组合"""

    def __init__(self):
        self.receivable_repo = ReceivableRepository()
        self.collection_repo = CollectionRecordRepository()
        self.cash_flow_repo = CashFlowRepository()
        self.payable_repo = PayableRepository()
        self.account_svc = AccountService()

    # ========== 应收 — 收款核销 ==========

    def collect_receivable(self, receivable_id, amount, payment_method,
                           transaction_date, description, created_by,
                           account_id=None):
        """
        收款核销（事务内完成五步联动）

        1. INSERT CollectionRecord
        2. UPDATE Receivable SET PaidAmount/RemainingAmount
        3. UPDATE Receivable SET Status
        4. INSERT CashFlow（含 AccountID）
        5. UPDATE Account Balance

        Args:
            receivable_id: 应收记录ID
            amount: 收款金额
            payment_method: 付款方式
            transaction_date: 交易日期
            description: 备注
            created_by: 操作人ID
            account_id: 收款账户ID（可选，默认取默认账户）

        Returns:
            dict: {'success': True/False, 'message': str}
        """
        # 先验证应收记录
        receivable = self.receivable_repo.get_by_id(receivable_id)
        if not receivable:
            return {'success': False, 'message': '应收记录不存在'}

        remaining = float(receivable.RemainingAmount)
        if amount <= 0:
            return {'success': False, 'message': '收款金额必须大于0'}
        if amount > remaining:
            return {'success': False, 'message': f'收款金额不能大于剩余金额 ¥{remaining:.2f}'}

        # 确定账户
        if not account_id:
            account_id = self.account_svc.get_default_account_id()
        if not account_id:
            return {'success': False, 'message': '未找到有效收款账户，请先配置账户'}

        try:
            with DBConnection() as conn:
                cursor = conn.cursor()

                # 1. INSERT CollectionRecord
                cursor.execute("""
                    INSERT INTO CollectionRecord (
                        ReceivableID, MerchantID, Amount, PaymentMethod,
                        TransactionDate, Description, CreatedBy
                    ) OUTPUT INSERTED.CollectionRecordID
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    receivable_id,
                    receivable.MerchantID,
                    amount,
                    payment_method,
                    transaction_date,
                    description,
                    created_by
                ))

                collection_id = cursor.fetchone()[0]

                # 2. UPDATE Receivable — 更新已付/剩余金额
                cursor.execute("""
                    UPDATE Receivable
                    SET PaidAmount = PaidAmount + ?,
                        RemainingAmount = RemainingAmount - ?,
                        UpdateTime = GETDATE()
                    WHERE ReceivableID = ?
                """, (amount, amount, receivable_id))

                # 3. UPDATE Receivable — 更新状态
                new_remaining = remaining - amount
                if new_remaining <= 0.01:  # 浮点精度处理
                    new_status = '已付款'
                else:
                    new_status = '部分付款'
                cursor.execute("""
                    UPDATE Receivable SET Status = ?, UpdateTime = GETDATE()
                    WHERE ReceivableID = ?
                """, (new_status, receivable_id))

                # 4. INSERT CashFlow（含 AccountID 和 TransactionNo）
                transaction_no = generate_serial_no(cursor, 'CF', 'CashFlow', 'TransactionNo')
                cursor.execute("""
                    INSERT INTO CashFlow (
                        Amount, Direction, ExpenseTypeID, Description,
                        TransactionDate, ReferenceID, ReferenceType, CreatedBy,
                        AccountID, TransactionNo
                    ) VALUES (?, N'收入', ?, ?, ?, ?, N'collection_record', ?, ?, ?)
                """, (
                    amount,
                    receivable.ExpenseTypeID,
                    description or f'收款 — 应收#{receivable_id}',
                    transaction_date,
                    collection_id,
                    created_by,
                    account_id,
                    transaction_no
                ))

                # 5. UPDATE Account Balance
                self.account_svc._adjust_balance(cursor, account_id, amount, 'income')

                conn.commit()

            return {
                'success': True,
                'message': '收款成功',
                'collection_id': collection_id,
                'new_remaining': new_remaining
            }

        except Exception as e:
            logger.error(f'收款核销失败: {e}')
            return {'success': False, 'message': f'收款失败：{str(e)}'}

    # ========== 应付 — 付款核销 ==========

    def pay_payable(self, payable_id, amount, payment_method,
                    transaction_date, description, created_by,
                    account_id=None):
        """
        付款核销（事务内完成五步联动）

        1. INSERT PaymentRecord
        2. UPDATE Payable SET PaidAmount/RemainingAmount
        3. UPDATE Payable SET Status
        4. INSERT CashFlow（含 AccountID）
        5. UPDATE Account Balance

        Args:
            payable_id: 应付记录ID
            amount: 付款金额
            payment_method: 付款方式
            transaction_date: 交易日期
            description: 备注
            created_by: 操作人ID
            account_id: 付款账户ID（可选，默认取默认账户）

        Returns:
            dict: {'success': True/False, 'message': str}
        """
        # 先验证应付记录
        payable = self._get_payable_by_id(payable_id)
        if not payable:
            return {'success': False, 'message': '应付记录不存在'}

        remaining = float(payable.RemainingAmount)
        if amount <= 0:
            return {'success': False, 'message': '付款金额必须大于0'}
        if amount > remaining:
            return {'success': False, 'message': f'付款金额不能大于剩余金额 ¥{remaining:.2f}'}

        # 确定账户
        if not account_id:
            account_id = self.account_svc.get_default_account_id()
        if not account_id:
            return {'success': False, 'message': '未找到有效付款账户，请先配置账户'}

        try:
            with DBConnection() as conn:
                cursor = conn.cursor()

                # 1. INSERT PaymentRecord
                cursor.execute("""
                    INSERT INTO PaymentRecord (
                        PayableID, VendorName, Amount, PaymentMethod,
                        TransactionDate, Description, CreatedBy, CustomerType
                    ) OUTPUT INSERTED.PaymentRecordID
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    payable_id,
                    payable.VendorName,
                    amount,
                    payment_method,
                    transaction_date,
                    description,
                    created_by,
                    getattr(payable, 'CustomerType', None)
                ))

                payment_id = cursor.fetchone()[0]

                # 2. UPDATE Payable — 更新已付/剩余金额
                cursor.execute("""
                    UPDATE Payable
                    SET PaidAmount = PaidAmount + ?,
                        RemainingAmount = RemainingAmount - ?,
                        UpdateTime = GETDATE()
                    WHERE PayableID = ?
                """, (amount, amount, payable_id))

                # 3. UPDATE Payable — 更新状态
                new_remaining = remaining - amount
                if new_remaining <= 0.01:
                    new_status = '已付款'
                else:
                    new_status = '部分付款'
                cursor.execute("""
                    UPDATE Payable SET Status = ?, UpdateTime = GETDATE()
                    WHERE PayableID = ?
                """, (new_status, payable_id))

                # 4. INSERT CashFlow（含 AccountID 和 TransactionNo）
                transaction_no = generate_serial_no(cursor, 'CF', 'CashFlow', 'TransactionNo')
                cursor.execute("""
                    INSERT INTO CashFlow (
                        Amount, Direction, ExpenseTypeID, Description,
                        TransactionDate, ReferenceID, ReferenceType, CreatedBy,
                        AccountID, TransactionNo
                    ) VALUES (?, N'支出', ?, ?, ?, ?, N'payment_record', ?, ?, ?)
                """, (
                    amount,
                    payable.ExpenseTypeID,
                    description or f'付款 — 应付#{payable_id}',
                    transaction_date,
                    payment_id,
                    created_by,
                    account_id,
                    transaction_no
                ))

                # 5. UPDATE Account Balance
                self.account_svc._adjust_balance(cursor, account_id, amount, 'expense')

                conn.commit()

            return {
                'success': True,
                'message': '付款成功',
                'payment_id': payment_id,
                'new_remaining': new_remaining
            }

        except Exception as e:
            logger.error(f'付款核销失败: {e}')
            return {'success': False, 'message': f'付款失败：{str(e)}'}

    # ========== 应付 CRUD ==========

    def _get_payable_by_id(self, payable_id):
        """获取应付记录详情"""
        return self.payable_repo.get_by_id(payable_id)

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

    def batch_pay_by_customer(self, customer_type, customer_id, total_amount,
                               payment_method, transaction_date, description,
                               created_by, account_id=None):
        """
        按客户批量付款核销（事务内完成）

        查询该客户所有未付款应付，按到期日升序排列，
        逐条核销直到金额用完。不足完全抵扣的最后一条记为部分付款。

        Returns:
            dict: {'success': True/False, 'message': str, 'details': [...]}
        """
        if total_amount <= 0:
            return {'success': False, 'message': '付款金额必须大于0'}

        # 确定账户
        if not account_id:
            account_id = self.account_svc.get_default_account_id()
        if not account_id:
            return {'success': False, 'message': '未找到有效付款账户，请先配置账户'}

        details = []  # 记录每条核销明细
        remaining_pay = total_amount

        try:
            with DBConnection() as conn:
                cursor = conn.cursor()

                # 查询该客户所有未结清应付，按到期日升序
                cursor.execute("""
                    SELECT PayableID, VendorName, ExpenseTypeID,
                           Amount, PaidAmount, RemainingAmount, DueDate, Status,
                           CustomerType
                    FROM Payable
                    WHERE CustomerType = ? AND CustomerID = ?
                      AND IsActive = 1
                      AND Status IN (N'未付款', N'部分付款')
                    ORDER BY DueDate ASC, PayableID ASC
                """, (customer_type, customer_id))
                payables = cursor.fetchall()

                if not payables:
                    return {'success': False, 'message': '该客户没有待付款的应付记录'}

                # 计算总未付金额
                total_remaining = sum(float(p.RemainingAmount) for p in payables)
                if total_amount > total_remaining + 0.01:
                    return {'success': False, 'message': f'付款金额 ¥{total_amount:.2f} 超过该客户总未付金额 ¥{total_remaining:.2f}'}

                for p in payables:
                    if remaining_pay <= 0.01:
                        break

                    p_remaining = float(p.RemainingAmount)
                    pay_for_this = min(remaining_pay, p_remaining)

                    # 1. INSERT PaymentRecord
                    cursor.execute("""
                        INSERT INTO PaymentRecord (
                            PayableID, VendorName, Amount, PaymentMethod,
                            TransactionDate, Description, CreatedBy, CustomerType
                        ) OUTPUT INSERTED.PaymentRecordID
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        p.PayableID,
                        p.VendorName,
                        pay_for_this,
                        payment_method,
                        transaction_date,
                        description,
                        created_by,
                        p.CustomerType
                    ))

                    payment_id = cursor.fetchone()[0]

                    # 2. UPDATE Payable — 更新已付/剩余金额
                    cursor.execute("""
                        UPDATE Payable
                        SET PaidAmount = PaidAmount + ?,
                            RemainingAmount = RemainingAmount - ?,
                            UpdateTime = GETDATE()
                        WHERE PayableID = ?
                    """, (pay_for_this, pay_for_this, p.PayableID))

                    # 3. UPDATE Payable — 更新状态
                    new_remaining = p_remaining - pay_for_this
                    if new_remaining <= 0.01:
                        new_status = '已付款'
                    else:
                        new_status = '部分付款'
                    cursor.execute("""
                        UPDATE Payable SET Status = ?, UpdateTime = GETDATE()
                        WHERE PayableID = ?
                    """, (new_status, p.PayableID))

                    # 4. INSERT CashFlow
                    transaction_no = generate_serial_no(cursor, 'CF', 'CashFlow', 'TransactionNo')
                    cursor.execute("""
                        INSERT INTO CashFlow (
                            Amount, Direction, ExpenseTypeID, Description,
                            TransactionDate, ReferenceID, ReferenceType, CreatedBy,
                            AccountID, TransactionNo
                        ) VALUES (?, N'支出', ?, ?, ?, ?, N'payment_record', ?, ?, ?)
                    """, (
                        pay_for_this,
                        p.ExpenseTypeID,
                        description or f'批量付款 — 应付#{p.PayableID}',
                        transaction_date,
                        payment_id,
                        created_by,
                        account_id,
                        transaction_no
                    ))

                    # 5. UPDATE Account Balance
                    self.account_svc._adjust_balance(cursor, account_id, pay_for_this, 'expense')

                    details.append({
                        'payable_id': p.PayableID,
                        'paid_amount': round(pay_for_this, 2),
                        'original_remaining': round(p_remaining, 2),
                        'new_remaining': round(new_remaining, 2),
                        'new_status': new_status,
                    })

                    remaining_pay -= pay_for_this

                conn.commit()

            return {
                'success': True,
                'message': f'批量付款成功，共核销 {len(details)} 条应付记录',
                'total_paid': round(total_amount - remaining_pay, 2),
                'details': details
            }

        except Exception as e:
            logger.error(f'批量付款核销失败: {e}')
            return {'success': False, 'message': f'批量付款失败：{str(e)}'}

    def batch_collect_by_customer(self, customer_type, customer_id, total_amount,
                                   payment_method, transaction_date, description,
                                   created_by, account_id=None,
                                   collect_mode='cash', prepayment_id=None):
        if collect_mode == 'prepayment':
            return self._batch_collect_by_prepayment(
                customer_type, customer_id, total_amount,
                prepayment_id, description, created_by
            )

        with DBConnection() as conn:
            cursor = conn.cursor()

            customer_name = self._resolve_customer_name(cursor, customer_type, customer_id)
            if not customer_name:
                return {'success': False, 'message': '客户不存在'}

            receivables = self._get_unpaid_receivables(cursor, customer_type, customer_id)
            if not receivables:
                return {'success': False, 'message': '该客户没有未收回应收'}

            remaining_amount = float(total_amount)
            collected_count = 0

            for r in receivables:
                if remaining_amount <= 0.01:
                    break

                receivable_id = r.ReceivableID
                current_remaining = float(r.RemainingAmount)
                collect_for_this = min(remaining_amount, current_remaining)
                new_remaining = current_remaining - collect_for_this

                if new_remaining <= 0.01:
                    new_status = '已付款'
                else:
                    new_status = '部分付款'

                cursor.execute("""
                    INSERT INTO CollectionRecord (ReceivableID, MerchantID, Amount, PaymentMethod, TransactionDate, Description, CreatedBy, CustomerType)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, receivable_id, customer_id, collect_for_this, payment_method, transaction_date, description, created_by, customer_type)

                cursor.execute("""
                    UPDATE Receivable
                    SET PaidAmount = PaidAmount + ?, RemainingAmount = RemainingAmount - ?, UpdateTime = GETDATE()
                    WHERE ReceivableID = ?
                """, collect_for_this, collect_for_this, receivable_id)

                cursor.execute("""
                    UPDATE Receivable SET Status = ?, UpdateTime = GETDATE() WHERE ReceivableID = ?
                """, new_status, receivable_id)

                default_account = self._get_default_account_id(cursor) if not account_id else account_id
                cursor.execute("""
                    INSERT INTO CashFlow (Amount, Direction, ExpenseTypeID, Description, TransactionDate, ReferenceID, ReferenceType, CreatedBy, AccountID)
                    VALUES (?, N'收入', NULL, ?, ?, ?, N'collection_record', ?, ?)
                """, collect_for_this, f'批量收款-{customer_name}', transaction_date, receivable_id, created_by, default_account)

                if default_account:
                    cursor.execute("""
                        UPDATE Account SET Balance = Balance + ? WHERE AccountID = ?
                    """, collect_for_this, default_account)

                remaining_amount -= collect_for_this
                collected_count += 1

            conn.commit()

            return {
                'success': True,
                'message': f'批量收款成功，共核销 {collected_count} 条应收',
                'collected_count': collected_count,
                'actual_amount': float(total_amount) - remaining_amount,
            }

    def _resolve_customer_name(self, cursor, customer_type, customer_id):
        if customer_type == 'Customer':
            cursor.execute("SELECT CustomerName FROM Customer WHERE CustomerID = ?", customer_id)
        else:
            cursor.execute("SELECT MerchantName FROM Merchant WHERE MerchantID = ?", customer_id)
        row = cursor.fetchone()
        return row[0] if row else None

    def _get_unpaid_receivables(self, cursor, customer_type, customer_id):
        cursor.execute("""
            SELECT ReceivableID, RemainingAmount, DueDate
            FROM Receivable
            WHERE CustomerType = ? AND CustomerID = ? AND Status != N'已付款' AND IsActive = 1
            ORDER BY DueDate ASC
        """, customer_type, customer_id)
        return cursor.fetchall()

    def _get_default_account_id(self, cursor):
        cursor.execute("SELECT AccountID FROM Account WHERE IsDefault = 1 AND Status = N'有效'")
        row = cursor.fetchone()
        return row[0] if row else None

    def _batch_collect_by_prepayment(self, customer_type, customer_id, total_amount,
                                      prepayment_id, description, created_by):
        with DBConnection() as conn:
            cursor = conn.cursor()

            cursor.execute("""
                SELECT PrepaymentID, RemainingAmount, CustomerName
                FROM Prepayment
                WHERE PrepaymentID = ? AND Direction = N'income' AND Status != N'已核销'
            """, prepayment_id)
            prepay_row = cursor.fetchone()
            if not prepay_row:
                return {'success': False, 'message': '预收记录不存在或已核销'}

            prepay_remaining = float(prepay_row.RemainingAmount)
            if float(total_amount) > prepay_remaining:
                return {'success': False, 'message': f'冲抵金额超过预收余额（¥{prepay_remaining:.2f}）'}

            receivables = self._get_unpaid_receivables(cursor, customer_type, customer_id)
            if not receivables:
                return {'success': False, 'message': '该客户没有未收回应收'}

            remaining_amount = float(total_amount)
            collected_count = 0

            for r in receivables:
                if remaining_amount <= 0.01:
                    break

                receivable_id = r.ReceivableID
                current_remaining = float(r.RemainingAmount)
                collect_for_this = min(remaining_amount, current_remaining)
                new_remaining = current_remaining - collect_for_this

                if new_remaining <= 0.01:
                    new_status = '已付款'
                else:
                    new_status = '部分付款'

                cursor.execute("""
                    INSERT INTO CollectionRecord (ReceivableID, MerchantID, Amount, PaymentMethod, TransactionDate, Description, CreatedBy, CustomerType)
                    VALUES (?, ?, ?, N'预收冲抵', GETDATE(), ?, ?, ?)
                """, receivable_id, customer_id, collect_for_this, description, created_by, customer_type)

                cursor.execute("""
                    UPDATE Receivable
                    SET PaidAmount = PaidAmount + ?, RemainingAmount = RemainingAmount - ?, Status = ?, UpdateTime = GETDATE()
                    WHERE ReceivableID = ?
                """, collect_for_this, collect_for_this, new_status, receivable_id)

                remaining_amount -= collect_for_this
                collected_count += 1

            actual_amount = float(total_amount) - remaining_amount

            cursor.execute("""
                UPDATE Prepayment
                SET AppliedAmount = AppliedAmount + ?, RemainingAmount = RemainingAmount - ?, UpdateTime = GETDATE()
                WHERE PrepaymentID = ?
            """, actual_amount, actual_amount, prepayment_id)

            new_prepay_remaining = prepay_remaining - actual_amount
            if new_prepay_remaining <= 0.01:
                cursor.execute("UPDATE Prepayment SET Status = N'已核销' WHERE PrepaymentID = ?", prepayment_id)
            else:
                cursor.execute("UPDATE Prepayment SET Status = N'部分核销' WHERE PrepaymentID = ?", prepayment_id)

            cursor.execute("""
                INSERT INTO PrepaymentApply (PrepaymentID, ReceivableID, Amount, Description, CreatedBy)
                VALUES (?, NULL, ?, ?, ?)
            """, prepayment_id, actual_amount, description, created_by)

            conn.commit()

            return {
                'success': True,
                'message': f'预收冲抵成功，共核销 {collected_count} 条应收',
                'collected_count': collected_count,
                'actual_amount': actual_amount,
            }

    def soft_delete_payable(self, payable_id, deleted_by, delete_reason=None):
        """软删除应付账款"""
        payable = self.payable_repo.get_by_id(payable_id)
        if not payable:
            return {'success': False, 'message': '应付记录不存在或已删除'}

        if payable.Status in ('已付款', '部分付款'):
            return {'success': False, 'message': f'状态为"{payable.Status}"的应付不允许删除，已有付款记录关联'}

        payment_count = self.payable_repo.check_has_payment(payable_id)
        if payment_count > 0:
            return {'success': False, 'message': f'该应付已有 {payment_count} 条付款记录，不允许删除'}

        affected = self.payable_repo.soft_delete(payable_id, deleted_by, delete_reason)
        if affected > 0:
            return {'success': True, 'message': '删除成功'}
        else:
            return {'success': False, 'message': '删除失败，请重试'}

    def create_payable(self, vendor_name=None, expense_type_id=None, amount=None, due_date=None,
                       description=None, created_by=None,
                       customer_type='Merchant', customer_id=None):
        """新增应付账款

        Args:
            vendor_name: 供应商名称（兼容旧调用，Merchant/Customer 类型可选）
            customer_type: 客户类型 'Merchant' 或 'Customer'
            customer_id: 客户ID
        """
        # 解析名称
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
        # 验证费用类型存在于字典表
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

    def get_payment_records(self, payable_id):
        """获取某条应付的付款历史"""
        with DBConnection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT pr.PaymentRecordID, pr.PayableID, pr.VendorName,
                       pr.Amount, pr.PaymentMethod, pr.TransactionDate,
                       pr.Description, pr.CreatedBy, pr.CreateTime,
                       u.RealName AS OperatorName
                FROM PaymentRecord pr
                LEFT JOIN [User] u ON pr.CreatedBy = u.UserID
                WHERE pr.PayableID = ?
                ORDER BY pr.CreateTime DESC
            """, (payable_id,))
            rows = cursor.fetchall()

            result = []
            for row in rows:
                result.append({
                    'payment_record_id': row.PaymentRecordID,
                    'vendor_name': row.VendorName,
                    'amount': float(row.Amount),
                    'payment_method': row.PaymentMethod,
                    'transaction_date': format_date(row.TransactionDate),
                    'description': row.Description or '',
                    'operator_name': row.OperatorName or '',
                    'create_time': format_datetime(row.CreateTime),
                })
            return result

    # ========== 现金流水 ==========

    def get_cash_flows(self, page=1, per_page=10, direction=None,
                       expense_type_id=None, start_date=None, end_date=None,
                       account_id=None):
        """获取现金流水列表"""
        rows, total_count = self.cash_flow_repo.get_list(
            page=page, per_page=per_page, direction=direction,
            expense_type_id=expense_type_id,
            start_date=start_date, end_date=end_date,
            account_id=account_id
        )

        result_list = []
        for row in rows:
            result_list.append({
                'cash_flow_id': row.CashFlowID,
                'amount': float(row.Amount),
                'direction': row.Direction,
                'expense_type_id': row.ExpenseTypeID,
                'expense_type_name': row.ExpenseTypeName,
                'description': row.Description or '',
                'transaction_date': format_date(row.TransactionDate),
                'reference_id': row.ReferenceID,
                'reference_type': row.ReferenceType or '',
                'operator_name': row.OperatorName or '',
                'create_time': format_datetime(row.CreateTime),
                'account_id': row.AccountID,
                'account_name': getattr(row, 'AccountName', '') or '',
                'transaction_no': getattr(row, 'TransactionNo', '') or '',
                'linked_receivable_id': getattr(row, 'LinkedReceivableID', None),
                'linked_payable_id': getattr(row, 'LinkedPayableID', None),
            })

        total_pages = (total_count + per_page - 1) // per_page if total_count > 0 else 0

        return {
            'items': result_list,
            'total_count': total_count,
            'total_pages': total_pages,
            'current_page': page
        }

    def get_cash_flow_summary(self, start_date=None, end_date=None):
        """获取收支汇总统计"""
        row = self.cash_flow_repo.get_summary(start_date=start_date, end_date=end_date)
        if row:
            return {
                'total_income': float(row.TotalIncome),
                'total_expense': float(row.TotalExpense),
                'net_cash_flow': float(row.NetCashFlow)
            }
        return {
            'total_income': 0,
            'total_expense': 0,
            'net_cash_flow': 0
        }

    def get_receivable_detail(self, receivable_id):
        """获取应收详情（含收款历史、关联合同/抄表数据）"""
        receivable = self.receivable_repo.get_by_id(receivable_id)
        if not receivable:
            return None

        records = self.collection_repo.get_by_receivable_id(receivable_id)
        collection_list = []
        for row in records:
            collection_list.append({
                'collection_record_id': row.CollectionRecordID,
                'amount': float(row.Amount),
                'payment_method': row.PaymentMethod,
                'transaction_date': format_date(row.TransactionDate),
                'description': row.Description or '',
                'operator_name': row.OperatorName or '',
                'create_time': format_datetime(row.CreateTime),
            })

        data = {
            'receivable_id': receivable.ReceivableID,
            'merchant_id': receivable.MerchantID,
            'merchant_name': receivable.CustomerName or '',
            'customer_type': receivable.CustomerType or 'Merchant',
            'customer_id': receivable.CustomerID or receivable.MerchantID,
            'expense_type_id': receivable.ExpenseTypeID,
            'expense_type_name': receivable.ExpenseTypeName,
            'amount': float(receivable.Amount),
            'paid_amount': float(receivable.PaidAmount),
            'remaining_amount': float(receivable.RemainingAmount),
            'product_name': receivable.ProductName or '',
            'specification': receivable.Specification or '',
            'quantity': float(receivable.Quantity) if receivable.Quantity else None,
            'unit_id': receivable.UnitID,
            'unit_name': receivable.UnitName or '',
            'unit_price': float(receivable.UnitPrice) if receivable.UnitPrice else None,
            'due_date': format_date(receivable.DueDate),
            'status': receivable.Status,
            'description': receivable.Description or '',
            'reference_id': receivable.ReferenceID,
            'reference_type': receivable.ReferenceType or '',
            'create_time': format_datetime(receivable.CreateTime),
            'is_active': bool(receivable.IsActive) if hasattr(receivable, 'IsActive') else True,
            'deleted_at': format_datetime(receivable.DeletedAt) if hasattr(receivable, 'DeletedAt') else '',
            'delete_reason': receivable.DeleteReason or '' if hasattr(receivable, 'DeleteReason') else '',
            'collection_records': collection_list
        }

        expense_name = receivable.ExpenseTypeName or ''
        ref_type = receivable.ReferenceType or ''

        if (expense_name == '租金' or ref_type == 'contract') and receivable.ReferenceID:
            contract_data = self._get_contract_summary(receivable.ReferenceID)
            if contract_data:
                data['contract_info'] = contract_data

        if expense_name in ('电费', '水费') or ref_type in ('utility_reading_merged', 'utility_reading'):
            reading_data = self._get_utility_readings(receivable_id)
            if reading_data:
                data['utility_readings'] = reading_data

        return data

    def _get_contract_summary(self, contract_id):
        """获取合同摘要信息（含关联合同地块）"""
        try:
            with DBConnection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT c.ContractID, c.ContractNumber, c.ContractName,
                           c.MerchantID, m.MerchantName,
                           c.StartDate, c.EndDate,
                           c.ContractAmount, c.AmountReduction, c.ActualAmount,
                           c.Status, c.PaymentMethod, c.ContractPeriod
                    FROM Contract c
                    LEFT JOIN Merchant m ON c.MerchantID = m.MerchantID
                    WHERE c.ContractID = ?
                """, contract_id)
                row = cursor.fetchone()
                if not row:
                    return None

                cursor.execute("""
                    SELECT cp.PlotID, cp.UnitPrice, cp.Area, cp.MonthlyPrice,
                           p.PlotNumber, p.PlotName
                    FROM ContractPlot cp
                    LEFT JOIN Plot p ON cp.PlotID = p.PlotID
                    WHERE cp.ContractID = ?
                """, contract_id)
                plots = []
                for plot in cursor.fetchall():
                    plots.append({
                        'plot_number': plot.PlotNumber or '',
                        'plot_name': plot.PlotName or '',
                        'area': float(plot.Area) if plot.Area else 0,
                        'monthly_price': float(plot.MonthlyPrice) if plot.MonthlyPrice else 0,
                    })
                plot_numbers = ', '.join([plot['plot_number'] for plot in plots if plot['plot_number']])

                return {
                    'contract_id': row.ContractID,
                    'contract_number': row.ContractNumber or '',
                    'contract_name': row.ContractName or '',
                    'merchant_name': row.MerchantName or '',
                    'plot_numbers': plot_numbers,
                    'plots': plots,
                    'start_date': format_date(row.StartDate),
                    'end_date': format_date(row.EndDate),
                    'contract_amount': float(row.ContractAmount) if row.ContractAmount else 0,
                    'amount_reduction': float(row.AmountReduction) if row.AmountReduction else 0,
                    'actual_amount': float(row.ActualAmount) if row.ActualAmount else 0,
                    'status': row.Status or '',
                    'payment_method': row.PaymentMethod or '',
                    'contract_period': row.ContractPeriod or '',
                }
        except Exception:
            return None

    def _get_utility_readings(self, receivable_id):
        """获取关联的抄表数据列表"""
        try:
            utility_select = """
                SELECT ur.ReadingID, ur.MeterID, ur.MeterType,
                       ur.LastReading, ur.CurrentReading, ur.Usage, ur.UnitPrice, ur.TotalAmount,
                       ur.BelongMonth, ur.ReadingDate, ur.ReadingMonth,
                       CASE
                           WHEN ur.MeterType = N'electricity' THEN ISNULL(em.MeterMultiplier, 1)
                           WHEN ur.MeterType = N'water' THEN ISNULL(wm.MeterMultiplier, 1)
                           ELSE 1
                       END AS MeterMultiplier,
                       CASE
                           WHEN ur.MeterType = N'electricity' THEN em.MeterNumber
                           WHEN ur.MeterType = N'water' THEN wm.MeterNumber
                           ELSE ''
                       END AS MeterNumber,
                       CASE
                           WHEN ur.MeterType = N'electricity' THEN ISNULL(em.InstallationLocation, '')
                           WHEN ur.MeterType = N'water' THEN ISNULL(wm.InstallationLocation, '')
                           ELSE ''
                       END AS InstallationLocation
            """
            utility_joins = """
                LEFT JOIN ElectricityMeter em ON ur.MeterType = N'electricity' AND ur.MeterID = em.MeterID
                LEFT JOIN WaterMeter wm ON ur.MeterType = N'water' AND ur.MeterID = wm.MeterID
            """

            with DBConnection() as conn:
                cursor = conn.cursor()
                rows = []

                cursor.execute(f"""
                    {utility_select}
                    FROM ReceivableDetail rd
                    INNER JOIN UtilityReading ur ON rd.ReadingID = ur.ReadingID
                    {utility_joins}
                    WHERE rd.ReceivableID = ?
                    ORDER BY ur.MeterType, ur.MeterID
                """, receivable_id)
                rows = cursor.fetchall()

                if not rows:
                    cursor.execute(f"""
                        {utility_select}
                        FROM UtilityReading ur
                        {utility_joins}
                        WHERE ur.ReadingID IN (
                            SELECT ReferenceID FROM Receivable
                            WHERE ReceivableID = ? AND ReferenceType = N'utility_reading'
                        )
                        ORDER BY ur.MeterType, ur.MeterID
                    """, receivable_id)
                    rows = cursor.fetchall()

                if not rows:
                    cursor.execute("""
                        SELECT MerchantID, Description, ExpenseTypeID
                        FROM Receivable WHERE ReceivableID = ?
                    """, receivable_id)
                    receivable = cursor.fetchone()
                    if receivable and receivable.MerchantID and receivable.Description:
                        month_match = re.search(r'(\d{4}年\d{2}月)', receivable.Description)
                        belong_month = month_match.group(1) if month_match else ''
                        meter_type = 'water' if '水费' in (receivable.Description or '') else 'electricity'

                        if belong_month:
                            cursor.execute(f"""
                                {utility_select}
                                FROM UtilityReading ur
                                {utility_joins}
                                WHERE ur.MerchantID = ? AND ur.BelongMonth = ? AND ur.MeterType = ?
                                ORDER BY ur.MeterID
                            """, receivable.MerchantID, belong_month, meter_type)
                            rows = cursor.fetchall()

                if not rows:
                    return []

                result = []
                total_amount = 0
                for row in rows:
                    subtotal = float(row.TotalAmount) if row.TotalAmount else 0
                    total_amount += subtotal
                    result.append({
                        'reading_id': row.ReadingID,
                        'meter_number': row.MeterNumber or '',
                        'meter_type': row.MeterType or '',
                        'installation_location': row.InstallationLocation or '',
                        'belong_month': row.BelongMonth or row.ReadingMonth or '',
                        'last_reading': float(row.LastReading) if row.LastReading else 0,
                        'current_reading': float(row.CurrentReading) if row.CurrentReading else 0,
                        'meter_multiplier': float(row.MeterMultiplier) if row.MeterMultiplier else 1,
                        'usage': float(row.Usage) if row.Usage else 0,
                        'unit_price': float(row.UnitPrice) if row.UnitPrice else 0,
                        'subtotal': subtotal,
                    })

                return {
                    'items': result,
                    'total_amount': total_amount
                }
        except Exception:
            return []

    # ========== 直接记账 ==========

    def direct_entry(self, direction, amount, account_id, expense_type_id,
                     transaction_date, description, created_by):
        """
        直接记账（无需应收/应付前置）

        Args:
            direction: 'income' 或 'expense'
            amount: 金额
            account_id: 收支账户
            expense_type_id: 费用类型
            transaction_date: 交易日期
            description: 备注
            created_by: 操作人ID

        Returns:
            dict: {'success': True/False, 'message': str, 'cash_flow_id': int}
        """
        # 参数校验
        if direction not in ('income', 'expense'):
            return {'success': False, 'message': '方向参数无效'}
        if not amount or float(amount) <= 0:
            return {'success': False, 'message': '金额必须大于0'}
        if not account_id:
            return {'success': False, 'message': '请选择收支账户'}
        if not expense_type_id:
            return {'success': False, 'message': '请选择费用类型'}
        if not transaction_date:
            return {'success': False, 'message': '请选择交易日期'}

        # 验证账户存在且有效
        account = self.account_svc.get_account_by_id(account_id)
        if not account:
            return {'success': False, 'message': '账户不存在'}
        if account['status'] != '有效':
            return {'success': False, 'message': '该账户已停用'}

        # 支出时检查余额
        if direction == 'expense' and account['balance'] < float(amount):
            return {'success': False, 'message': f'账户余额不足（当前余额: ¥{account["balance"]:.2f}）'}

        dir_text = '收入' if direction == 'income' else '支出'

        try:
            with DBConnection() as conn:
                cursor = conn.cursor()

                # 1. INSERT CashFlow
                transaction_no = generate_serial_no(cursor, 'CF', 'CashFlow', 'TransactionNo')
                cursor.execute("""
                    INSERT INTO CashFlow (
                        Amount, Direction, ExpenseTypeID, Description,
                        TransactionDate, ReferenceID, ReferenceType, CreatedBy,
                        AccountID, TransactionNo
                    ) OUTPUT INSERTED.CashFlowID
                    VALUES (?, ?, ?, ?, ?, NULL, N'direct_entry', ?, ?, ?)
                """, (
                    float(amount),
                    dir_text,
                    int(expense_type_id),
                    description or f'直接记账 — {dir_text}',
                    transaction_date,
                    created_by,
                    account_id,
                    transaction_no
                ))

                row = cursor.fetchone()
                cash_flow_id = row[0] if row else None

                # 2. UPDATE Account Balance
                self.account_svc._adjust_balance(cursor, account_id, float(amount), direction)

                conn.commit()

            return {
                'success': True,
                'message': f'{dir_text}记账成功',
                'cash_flow_id': cash_flow_id
            }

        except ValueError as e:
            return {'success': False, 'message': str(e)}
        except Exception as e:
            logger.error(f'直接记账失败: {e}')
            return {'success': False, 'message': f'记账失败：{str(e)}'}

    # ========== 客户交易历史 ==========

    def get_customer_transactions(self, customer_type, customer_id,
                                  tx_type=None, page=1, per_page=10):
        """
        获取客户的全维度财务交易记录

        合并5类财务数据：应收、应付、预收/预付、押金、现金流水，
        按时间倒序排列并分页返回。

        Args:
            customer_type: 'Merchant' 或 'Customer'
            customer_id: 客户ID
            tx_type: 可选筛选类型 receivable/payable/prepayment/deposit/cashflow
            page: 页码
            per_page: 每页条数
        """
        all_items = []

        if not tx_type or tx_type == 'receivable':
            all_items.extend(self._query_receivable_items(customer_type, customer_id))

        if not tx_type or tx_type == 'payable':
            all_items.extend(self._query_payable_items(customer_type, customer_id))

        if not tx_type or tx_type == 'prepayment':
            all_items.extend(self._query_prepayment_items(customer_type, customer_id))

        if not tx_type or tx_type == 'deposit':
            all_items.extend(self._query_deposit_items(customer_type, customer_id))

        if not tx_type or tx_type == 'cashflow':
            all_items.extend(self._query_cashflow_items(customer_type, customer_id))

        all_items.sort(key=lambda x: x.get('_sort_date', ''), reverse=True)

        summary = self._calc_customer_summary(customer_type, customer_id)

        total_count = len(all_items)
        total_pages = (total_count + per_page - 1) // per_page if total_count > 0 else 0
        start = (page - 1) * per_page
        page_items = all_items[start:start + per_page]

        for item in page_items:
            item.pop('_sort_date', None)

        return {
            'items': page_items,
            'total_count': total_count,
            'total_pages': total_pages,
            'current_page': page,
            'summary': summary
        }

    def _query_receivable_items(self, customer_type, customer_id):
        with DBConnection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT r.ReceivableID, r.Amount, r.PaidAmount, r.RemainingAmount,
                       r.Status, r.DueDate, r.Description, r.CreateTime,
                       ISNULL(sd.DictName, N'') AS ExpenseTypeName
                FROM Receivable r
                LEFT JOIN Sys_Dictionary sd ON r.ExpenseTypeID = sd.DictID
                WHERE r.CustomerType = ? AND r.CustomerID = ?
                  AND r.IsActive = 1
                ORDER BY r.CreateTime DESC
            """, (customer_type, customer_id))
            rows = cursor.fetchall()
            items = []
            for row in rows:
                items.append({
                    'type': 'receivable',
                    'type_label': '应收',
                    'id': row.ReceivableID,
                    'amount': safe_float(row.Amount),
                    'paid_amount': safe_float(row.PaidAmount),
                    'remaining_amount': safe_float(row.RemainingAmount),
                    'status': row.Status or '',
                    'expense_type_name': row.ExpenseTypeName,
                    'description': row.Description or '',
                    'transaction_date': format_date(row.DueDate),
                    'create_time': format_datetime(row.CreateTime),
                    '_sort_date': format_datetime(row.CreateTime),
                })
            return items

    def _query_payable_items(self, customer_type, customer_id):
        with DBConnection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT p.PayableID, p.Amount, p.PaidAmount, p.RemainingAmount,
                       p.Status, p.DueDate, p.Description, p.CreateTime,
                       ISNULL(sd.DictName, N'') AS ExpenseTypeName
                FROM Payable p
                LEFT JOIN Sys_Dictionary sd ON p.ExpenseTypeID = sd.DictID
                WHERE p.CustomerType = ? AND p.CustomerID = ?
                  AND p.IsActive = 1
                ORDER BY p.CreateTime DESC
            """, (customer_type, customer_id))
            rows = cursor.fetchall()
            items = []
            for row in rows:
                items.append({
                    'type': 'payable',
                    'type_label': '应付',
                    'id': row.PayableID,
                    'amount': safe_float(row.Amount),
                    'paid_amount': safe_float(row.PaidAmount),
                    'remaining_amount': safe_float(row.RemainingAmount),
                    'status': row.Status or '',
                    'expense_type_name': row.ExpenseTypeName,
                    'description': row.Description or '',
                    'transaction_date': format_date(row.DueDate),
                    'create_time': format_datetime(row.CreateTime),
                    '_sort_date': format_datetime(row.CreateTime),
                })
            return items

    def _query_prepayment_items(self, customer_type, customer_id):
        with DBConnection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT pp.PrepaymentID, pp.Direction, pp.TotalAmount,
                       pp.AppliedAmount, pp.RemainingAmount,
                       pp.Status, pp.Description, pp.CreateTime,
                       ISNULL(sd.DictName, N'') AS ExpenseTypeName
                FROM Prepayment pp
                LEFT JOIN Sys_Dictionary sd ON pp.ExpenseTypeID = sd.DictID
                WHERE pp.CustomerType = ? AND pp.CustomerID = ?
                ORDER BY pp.CreateTime DESC
            """, (customer_type, customer_id))
            rows = cursor.fetchall()
            items = []
            for row in rows:
                direction_text = '预收' if row.Direction == 'income' else '预付'
                items.append({
                    'type': 'prepayment',
                    'type_label': direction_text,
                    'id': row.PrepaymentID,
                    'amount': safe_float(row.TotalAmount),
                    'paid_amount': safe_float(row.AppliedAmount),
                    'remaining_amount': safe_float(row.RemainingAmount),
                    'status': row.Status or '',
                    'expense_type_name': row.ExpenseTypeName,
                    'description': row.Description or '',
                    'transaction_date': '',
                    'create_time': format_datetime(row.CreateTime),
                    '_sort_date': format_datetime(row.CreateTime),
                })
            return items

    def _query_deposit_items(self, customer_type, customer_id):
        with DBConnection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT d.DepositID, d.DepositType, d.Amount,
                       d.RefundAmount, d.DeductAmount, d.TransferAmount,
                       d.Status, d.Description, d.CreateTime,
                       ISNULL(sd.DictName, N'') AS DepositTypeName
                FROM Deposit d
                LEFT JOIN Sys_Dictionary sd ON d.DepositType = sd.DictCode AND sd.DictType = N'deposit_type'
                WHERE d.CustomerType = ? AND d.CustomerID = ?
                ORDER BY d.CreateTime DESC
            """, (customer_type, customer_id))
            rows = cursor.fetchall()
            items = []
            for row in rows:
                remaining = safe_float(row.Amount) - safe_float(row.RefundAmount) \
                            - safe_float(row.DeductAmount) - safe_float(row.TransferAmount)
                items.append({
                    'type': 'deposit',
                    'type_label': '押金',
                    'id': row.DepositID,
                    'amount': safe_float(row.Amount),
                    'paid_amount': safe_float(row.RefundAmount) + safe_float(row.DeductAmount) + safe_float(row.TransferAmount),
                    'remaining_amount': remaining,
                    'status': row.Status or '',
                    'expense_type_name': row.DepositTypeName or '',
                    'description': row.Description or '',
                    'transaction_date': '',
                    'create_time': format_datetime(row.CreateTime),
                    '_sort_date': format_datetime(row.CreateTime),
                })
            return items

    def _query_cashflow_items(self, customer_type, customer_id):
        with DBConnection() as conn:
            cursor = conn.cursor()
            receivable_condition = """
                EXISTS (
                    SELECT 1 FROM Receivable r
                    WHERE r.ReceivableID = cf.ReferenceID
                      AND cf.ReferenceType = N'collection_record'
                      AND r.CustomerType = ? AND r.CustomerID = ?
                )
            """
            payable_condition = """
                EXISTS (
                    SELECT 1 FROM Payable p
                    INNER JOIN PaymentRecord pr ON pr.PayableID = p.PayableID
                    WHERE pr.PaymentRecordID = cf.ReferenceID
                      AND cf.ReferenceType = N'payment_record'
                      AND p.CustomerType = ? AND p.CustomerID = ?
                )
            """
            deposit_condition = """
                EXISTS (
                    SELECT 1 FROM Deposit d
                    WHERE d.DepositID = cf.ReferenceID
                      AND cf.ReferenceType = N'deposit'
                      AND d.CustomerType = ? AND d.CustomerID = ?
                )
            """
            deposit_refund_condition = """
                EXISTS (
                    SELECT 1 FROM DepositOperation dop
                    INNER JOIN Deposit d ON dop.DepositID = d.DepositID
                    WHERE dop.OperationID = cf.ReferenceID
                      AND cf.ReferenceType = N'deposit_refund'
                      AND d.CustomerType = ? AND d.CustomerID = ?
                )
            """
            prepayment_condition = """
                EXISTS (
                    SELECT 1 FROM Prepayment pp
                    WHERE pp.PrepaymentID = cf.ReferenceID
                      AND cf.ReferenceType = N'prepayment'
                      AND pp.CustomerType = ? AND pp.CustomerID = ?
                )
            """
            cursor.execute(f"""
                SELECT cf.CashFlowID, cf.Amount, cf.Direction,
                       cf.TransactionDate, cf.Description, cf.CreateTime,
                       ISNULL(sd.DictName, N'') AS ExpenseTypeName
                FROM CashFlow cf
                LEFT JOIN Sys_Dictionary sd ON cf.ExpenseTypeID = sd.DictID
                WHERE (
                    ({receivable_condition}) OR ({payable_condition})
                    OR ({deposit_condition}) OR ({deposit_refund_condition})
                    OR ({prepayment_condition})
                )
                ORDER BY cf.CreateTime DESC
            """, (customer_type, customer_id, customer_type, customer_id,
                  customer_type, customer_id, customer_type, customer_id,
                  customer_type, customer_id))
            rows = cursor.fetchall()
            items = []
            for row in rows:
                direction_text = '收入' if row.Direction == '收入' else '支出'
                items.append({
                    'type': 'cashflow',
                    'type_label': '流水-' + direction_text,
                    'id': row.CashFlowID,
                    'amount': safe_float(row.Amount),
                    'paid_amount': 0,
                    'remaining_amount': 0,
                    'status': direction_text,
                    'expense_type_name': row.ExpenseTypeName,
                    'description': row.Description or '',
                    'transaction_date': format_date(row.TransactionDate),
                    'create_time': format_datetime(row.CreateTime),
                    '_sort_date': format_datetime(row.CreateTime),
                })
            return items

    def _calc_customer_summary(self, customer_type, customer_id):
        with DBConnection() as conn:
            cursor = conn.cursor()

            cursor.execute("""
                SELECT ISNULL(SUM(Amount), 0), ISNULL(SUM(RemainingAmount), 0)
                FROM Receivable
                WHERE CustomerType = ? AND CustomerID = ? AND IsActive = 1
            """, (customer_type, customer_id))
            row = cursor.fetchone()
            total_receivable = safe_float(row[1]) if row else 0

            cursor.execute("""
                SELECT ISNULL(SUM(Amount), 0), ISNULL(SUM(RemainingAmount), 0)
                FROM Payable
                WHERE CustomerType = ? AND CustomerID = ? AND IsActive = 1
            """, (customer_type, customer_id))
            row = cursor.fetchone()
            total_payable = safe_float(row[1]) if row else 0

            cursor.execute("""
                SELECT ISNULL(SUM(RemainingAmount), 0)
                FROM Prepayment
                WHERE CustomerType = ? AND CustomerID = ? AND Direction = N'income'
            """, (customer_type, customer_id))
            row = cursor.fetchone()
            total_prepayment = safe_float(row[0]) if row else 0

            cursor.execute("""
                SELECT ISNULL(SUM(Amount - RefundAmount - DeductAmount - TransferAmount), 0)
                FROM Deposit
                WHERE CustomerType = ? AND CustomerID = ?
            """, (customer_type, customer_id))
            row = cursor.fetchone()
            total_deposit = safe_float(row[0]) if row else 0

            total_cashflow = total_receivable - total_payable

            return {
                'total_receivable': total_receivable,
                'total_payable': total_payable,
                'total_prepayment': total_prepayment,
                'total_deposit': total_deposit,
                'total_cashflow': total_cashflow,
            }
