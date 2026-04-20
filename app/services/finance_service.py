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

logger = logging.getLogger(__name__)


class FinanceService:
    """财务管理服务 — 统管跨表事务的业务组合"""

    def __init__(self):
        self.receivable_repo = ReceivableRepository()
        self.collection_repo = CollectionRecordRepository()
        self.cash_flow_repo = CashFlowRepository()
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
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    receivable_id,
                    receivable.MerchantID,
                    amount,
                    payment_method,
                    transaction_date,
                    description,
                    created_by
                ))

                # 获取新插入的 CollectionRecordID
                cursor.execute("SELECT CAST(SCOPE_IDENTITY() AS INT)")
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
                transaction_no = self._generate_transaction_no(cursor, 'CF')
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
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
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

                # 获取新插入的 PaymentRecordID
                cursor.execute("SELECT CAST(SCOPE_IDENTITY() AS INT)")
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
                transaction_no = self._generate_transaction_no(cursor, 'CF')
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
        """获取应付记录详情（费用类型从字典表获取）"""
        with DBConnection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT p.PayableID, p.VendorName, p.ExpenseTypeID,
                       ISNULL(sd.DictName, et.ExpenseTypeName) AS ExpenseTypeName,
                       p.Amount, p.PaidAmount,
                       p.RemainingAmount, p.DueDate, p.Status,
                       p.Description, p.ReferenceID, p.ReferenceType,
                       p.CreateTime, p.UpdateTime,
                       p.CustomerType, p.CustomerID,
                       CASE
                           WHEN p.CustomerType = 'Customer' THEN c.CustomerName
                           WHEN p.CustomerType = 'Merchant' THEN m.MerchantName
                           ELSE p.VendorName
                       END AS CustomerName
                FROM Payable p
                LEFT JOIN Sys_Dictionary sd ON p.ExpenseTypeID = sd.DictID AND sd.DictType = 'expense_item_expend'
                LEFT JOIN ExpenseType et ON p.ExpenseTypeID = et.ExpenseTypeID AND sd.DictID IS NULL
                LEFT JOIN Merchant m ON p.CustomerType = 'Merchant' AND p.CustomerID = m.MerchantID
                LEFT JOIN Customer c ON p.CustomerType = 'Customer' AND p.CustomerID = c.CustomerID
                WHERE p.PayableID = ? AND p.IsActive = 1
            """, (payable_id,))
            return cursor.fetchone()

    def get_payables(self, page=1, per_page=10, search=None, status=None):
        """获取应付账款列表（费用类型从字典表获取）"""
        with DBConnection() as conn:
            cursor = conn.cursor()

            base_query = """
                SELECT p.PayableID, p.VendorName, p.ExpenseTypeID,
                       ISNULL(sd.DictName, et.ExpenseTypeName) AS ExpenseTypeName,
                       p.Amount, p.PaidAmount,
                       p.RemainingAmount, p.DueDate, p.Status,
                       p.Description, p.CreateTime, p.UpdateTime,
                       p.CustomerType, p.CustomerID, p.ExpenseOrderID,
                       CASE
                           WHEN p.CustomerType = 'Customer' THEN c.CustomerName
                           WHEN p.CustomerType = 'Merchant' THEN m.MerchantName
                           ELSE p.VendorName
                       END AS CustomerName
                FROM Payable p
                LEFT JOIN Sys_Dictionary sd ON p.ExpenseTypeID = sd.DictID AND sd.DictType = 'expense_item_expend'
                LEFT JOIN ExpenseType et ON p.ExpenseTypeID = et.ExpenseTypeID AND sd.DictID IS NULL
                LEFT JOIN Merchant m ON p.CustomerType = 'Merchant' AND p.CustomerID = m.MerchantID
                LEFT JOIN Customer c ON p.CustomerType = 'Customer' AND p.CustomerID = c.CustomerID
                WHERE p.IsActive = 1
            """

            count_query = """
                SELECT COUNT(*) FROM Payable p
                LEFT JOIN Merchant m ON p.CustomerType = 'Merchant' AND p.CustomerID = m.MerchantID
                LEFT JOIN Customer c ON p.CustomerType = 'Customer' AND p.CustomerID = c.CustomerID
                WHERE p.IsActive = 1
            """

            conditions = []
            params = []

            if search:
                conditions.append("(p.VendorName LIKE ? OR m.MerchantName LIKE ? OR c.CustomerName LIKE ?)")
                p = f'%{search}%'
                params.extend([p, p, p])

            if status:
                conditions.append("p.Status = ?")
                params.append(status)

            if conditions:
                where_clause = " AND " + " AND ".join(conditions)
                base_query += where_clause
                count_query += where_clause

            offset = (page - 1) * per_page
            base_query += " ORDER BY p.PayableID DESC OFFSET ? ROWS FETCH NEXT ? ROWS ONLY"
            params.extend([offset, per_page])

            cursor.execute(base_query, params)
            rows = cursor.fetchall()

            count_params = params[:-2]
            cursor.execute(count_query, count_params)
            total_count = cursor.fetchone()[0]

            sum_query = """
                SELECT ISNULL(SUM(p.Amount), 0), ISNULL(SUM(p.PaidAmount), 0), ISNULL(SUM(p.RemainingAmount), 0)
                FROM Payable p
                LEFT JOIN Merchant m ON p.CustomerType = 'Merchant' AND p.CustomerID = m.MerchantID
                LEFT JOIN Customer c ON p.CustomerType = 'Customer' AND p.CustomerID = c.CustomerID
            """
            if conditions:
                sum_query += where_clause
            cursor.execute(sum_query, count_params)
            sum_row = cursor.fetchone()
            total_amount_sum = float(sum_row[0])
            total_paid_sum = float(sum_row[1])
            total_remaining_sum = float(sum_row[2])

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
                    'amount': float(row.Amount),
                    'paid_amount': float(row.PaidAmount),
                    'remaining_amount': float(row.RemainingAmount),
                    'due_date': row.DueDate.strftime('%Y-%m-%d') if row.DueDate and hasattr(row.DueDate, 'strftime') else (str(row.DueDate)[:10] if row.DueDate else ''),
                    'status': row.Status,
                    'description': row.Description or '',
                    'create_time': row.CreateTime.strftime('%Y-%m-%d %H:%M') if row.CreateTime and hasattr(row.CreateTime, 'strftime') else (str(row.CreateTime)[:16] if row.CreateTime else ''),
                    'expense_order_id': row.ExpenseOrderID,
                })

            total_pages = (total_count + per_page - 1) // per_page if total_count > 0 else 0

            return {
                'items': result_list,
                'total_count': total_count,
                'total_pages': total_pages,
                'current_page': page,
                'summary': {
                    'total_amount': total_amount_sum,
                    'total_paid': total_paid_sum,
                    'total_remaining': total_remaining_sum
                }
            }

    def get_payables_by_customer(self, page=1, per_page=10, search=None, status=None):
        """按客户汇总应付账款：每位客户一条记录，应付/已付/未付合计"""
        with DBConnection() as conn:
            cursor = conn.cursor()

            # 构建客户名称表达式（与 get_payables 一致）
            customer_expr = """
                CASE
                    WHEN p.CustomerType = 'Customer' THEN c.CustomerName
                    WHEN p.CustomerType = 'Merchant' THEN m.MerchantName
                    ELSE p.VendorName
                END
            """

            base_query = f"""
                SELECT
                    p.CustomerType,
                    p.CustomerID,
                    {customer_expr} AS CustomerName,
                    COUNT(*) AS RecordCount,
                    SUM(p.Amount) AS TotalAmount,
                    SUM(p.PaidAmount) AS TotalPaid,
                    SUM(p.RemainingAmount) AS TotalRemaining,
                    MIN(p.DueDate) AS EarliestDueDate
                FROM Payable p
                LEFT JOIN Merchant m ON p.CustomerType = 'Merchant' AND p.CustomerID = m.MerchantID
                LEFT JOIN Customer c ON p.CustomerType = 'Customer' AND p.CustomerID = c.CustomerID
                WHERE p.IsActive = 1
            """

            conditions = []
            params = []

            if search:
                conditions.append(f"({customer_expr} LIKE ?)")
                params.append(f'%{search}%')

            if status:
                conditions.append("p.Status = ?")
                params.append(status)

            extra_where = ""
            if conditions:
                extra_where = " AND " + " AND ".join(conditions)

            # GROUP BY
            group_clause = f"""
                GROUP BY p.CustomerType, p.CustomerID, {customer_expr}
            """

            # 总数（按客户分组后的组数）
            count_query = f"""
                SELECT COUNT(*) FROM (
                    SELECT p.CustomerType, p.CustomerID, {customer_expr} AS CustomerName
                    FROM Payable p
                    LEFT JOIN Merchant m ON p.CustomerType = 'Merchant' AND p.CustomerID = m.MerchantID
                    LEFT JOIN Customer c ON p.CustomerType = 'Customer' AND p.CustomerID = c.CustomerID
                    WHERE p.IsActive = 1
                    {extra_where}
                    GROUP BY p.CustomerType, p.CustomerID, {customer_expr}
                ) sub
            """
            count_params = list(params)
            cursor.execute(count_query, count_params)
            total_count = cursor.fetchone()[0]

            sum_query = f"""
                SELECT ISNULL(SUM(sub.TotalAmount), 0), ISNULL(SUM(sub.TotalPaid), 0), ISNULL(SUM(sub.TotalRemaining), 0), ISNULL(SUM(sub.RecordCount), 0)
                FROM (
                    SELECT
                        COUNT(*) AS RecordCount,
                        SUM(p.Amount) AS TotalAmount,
                        SUM(p.PaidAmount) AS TotalPaid,
                        SUM(p.RemainingAmount) AS TotalRemaining
                    FROM Payable p
                    LEFT JOIN Merchant m ON p.CustomerType = 'Merchant' AND p.CustomerID = m.MerchantID
                    LEFT JOIN Customer c ON p.CustomerType = 'Customer' AND p.CustomerID = c.CustomerID
                    WHERE p.IsActive = 1
                    {extra_where}
                    GROUP BY p.CustomerType, p.CustomerID, {customer_expr}
                ) sub
            """
            cursor.execute(sum_query, count_params)
            sum_row = cursor.fetchone()
            summary_total_amount = float(sum_row[0])
            summary_total_paid = float(sum_row[1])
            summary_total_remaining = float(sum_row[2])
            summary_total_records = int(sum_row[3])

            # 分页数据
            offset = (page - 1) * per_page
            base_query += extra_where + group_clause
            base_query += " ORDER BY TotalRemaining DESC, CustomerName OFFSET ? ROWS FETCH NEXT ? ROWS ONLY"
            params.extend([offset, per_page])

            cursor.execute(base_query, params)
            rows = cursor.fetchall()

            items = []
            for row in rows:
                due_date = row.EarliestDueDate
                if due_date:
                    due_date_str = due_date.strftime('%Y-%m-%d') if hasattr(due_date, 'strftime') else str(due_date)[:10]
                else:
                    due_date_str = ''
                items.append({
                    'customer_type': row.CustomerType or 'Merchant',
                    'customer_id': row.CustomerID,
                    'customer_name': row.CustomerName or '',
                    'record_count': row.RecordCount,
                    'total_amount': float(row.TotalAmount) if row.TotalAmount else 0,
                    'total_paid': float(row.TotalPaid) if row.TotalPaid else 0,
                    'total_remaining': float(row.TotalRemaining) if row.TotalRemaining else 0,
                    'earliest_due_date': due_date_str,
                })

            total_pages = (total_count + per_page - 1) // per_page if total_count > 0 else 0

            return {
                'items': items,
                'total_count': total_count,
                'total_pages': total_pages,
                'current_page': page,
                'summary': {
                    'total_amount': summary_total_amount,
                    'total_paid': summary_total_paid,
                    'total_remaining': summary_total_remaining,
                    'total_records': summary_total_records
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
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
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

                    cursor.execute("SELECT CAST(SCOPE_IDENTITY() AS INT)")
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
                    transaction_no = self._generate_transaction_no(cursor, 'CF')
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

    def soft_delete_payable(self, payable_id, deleted_by, delete_reason=None):
        """
        软删除应付账款

        业务规则：
        - 已付款/部分付款的应付禁止删除（已有关联付款记录）
        - 未付款的应付允许软删除，需记录删除原因

        Args:
            payable_id: 应付ID
            deleted_by: 删除操作人UserID
            delete_reason: 删除原因

        Returns:
            dict: {success, message}
        """
        with DBConnection() as conn:
            cursor = conn.cursor()

            # 1. 检查应付是否存在且有效
            cursor.execute("""
                SELECT PayableID, Status, PaidAmount, RemainingAmount, VendorName, Amount
                FROM Payable WHERE PayableID = ? AND IsActive = 1
            """, (payable_id,))
            row = cursor.fetchone()
            if not row:
                return {'success': False, 'message': '应付记录不存在或已删除'}

            # 2. 状态检查：已付款/部分付款不允许删除
            if row.Status in ('已付款', '部分付款'):
                return {'success': False, 'message': f'状态为"{row.Status}"的应付不允许删除，已有付款记录关联'}

            # 3. 执行软删除
            cursor.execute("""
                UPDATE Payable
                SET IsActive = 0,
                    DeletedBy = ?,
                    DeletedAt = GETDATE(),
                    DeleteReason = ?,
                    UpdateTime = GETDATE()
                WHERE PayableID = ?
            """, (deleted_by, delete_reason, payable_id))

            affected = cursor.rowcount
            conn.commit()

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

        with DBConnection() as conn:
            cursor = conn.cursor()
            sql = """
                INSERT INTO Payable (VendorName, ExpenseTypeID, Amount, DueDate,
                                     Status, PaidAmount, RemainingAmount, Description,
                                     CustomerType, CustomerID)
                OUTPUT INSERTED.PayableID
                VALUES (?, ?, ?, ?, N'未付款', 0, ?, ?, ?, ?)
            """
            cursor.execute(sql, resolved_name, int(expense_type_id),
                           float(amount), due_date, float(amount), description,
                           customer_type, int(customer_id) if customer_id else None)
            row = cursor.fetchone()
            new_id = row[0] if row else None
            conn.commit()
            return new_id

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
                    'transaction_date': row.TransactionDate.strftime('%Y-%m-%d') if row.TransactionDate else '',
                    'description': row.Description or '',
                    'operator_name': row.OperatorName or '',
                    'create_time': row.CreateTime.strftime('%Y-%m-%d %H:%M') if row.CreateTime else '',
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
                'transaction_date': row.TransactionDate.strftime('%Y-%m-%d') if row.TransactionDate else '',
                'reference_id': row.ReferenceID,
                'reference_type': row.ReferenceType or '',
                'operator_name': row.OperatorName or '',
                'create_time': row.CreateTime.strftime('%Y-%m-%d %H:%M') if row.CreateTime else '',
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
                'transaction_date': row.TransactionDate.strftime('%Y-%m-%d') if row.TransactionDate else '',
                'description': row.Description or '',
                'operator_name': row.OperatorName or '',
                'create_time': row.CreateTime.strftime('%Y-%m-%d %H:%M') if row.CreateTime else '',
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
            'due_date': receivable.DueDate.strftime('%Y-%m-%d') if receivable.DueDate else '',
            'status': receivable.Status,
            'description': receivable.Description or '',
            'reference_id': receivable.ReferenceID,
            'reference_type': receivable.ReferenceType or '',
            'create_time': receivable.CreateTime.strftime('%Y-%m-%d %H:%M') if receivable.CreateTime else '',
            'is_active': bool(receivable.IsActive) if hasattr(receivable, 'IsActive') else True,
            'deleted_at': receivable.DeletedAt.strftime('%Y-%m-%d %H:%M') if hasattr(receivable, 'DeletedAt') and receivable.DeletedAt else '',
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
                    'start_date': row.StartDate.strftime('%Y-%m-%d') if row.StartDate else '',
                    'end_date': row.EndDate.strftime('%Y-%m-%d') if row.EndDate else '',
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
                transaction_no = self._generate_transaction_no(cursor, 'CF')
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

    # ========== 辅助方法 ==========

    def _generate_transaction_no(self, cursor, prefix='CF'):
        """生成交易流水号（格式：CF20260415001）"""
        today = datetime.now().strftime('%Y%m%d')
        like_pattern = f'{prefix}{today}%'

        cursor.execute("""
            SELECT TransactionNo FROM CashFlow
            WHERE TransactionNo LIKE ?
            ORDER BY TransactionNo DESC
        """, (like_pattern,))
        row = cursor.fetchone()

        if row and row.TransactionNo:
            last_seq = int(row.TransactionNo[len(prefix) + 8:])
            new_seq = last_seq + 1
        else:
            new_seq = 1

        return f'{prefix}{today}{new_seq:03d}'
