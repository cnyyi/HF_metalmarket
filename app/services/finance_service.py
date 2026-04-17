# -*- coding: utf-8 -*-
"""
财务管理服务层
负责收款核销、付款核销、直接记账、现金流水等核心业务组合逻辑
"""
import logging
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
                WHERE p.PayableID = ?
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
            """

            count_query = "SELECT COUNT(*) FROM Payable p"

            conditions = []
            params = []

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

            offset = (page - 1) * per_page
            base_query += " ORDER BY p.PayableID DESC OFFSET ? ROWS FETCH NEXT ? ROWS ONLY"
            params.extend([offset, per_page])

            cursor.execute(base_query, params)
            rows = cursor.fetchall()

            count_params = params[:-2]
            cursor.execute(count_query, count_params)
            total_count = cursor.fetchone()[0]

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
                    'due_date': row.DueDate.strftime('%Y-%m-%d') if row.DueDate else '',
                    'status': row.Status,
                    'description': row.Description or '',
                    'create_time': row.CreateTime.strftime('%Y-%m-%d %H:%M') if row.CreateTime else '',
                    'expense_order_id': row.ExpenseOrderID,
                })

            total_pages = (total_count + per_page - 1) // per_page if total_count > 0 else 0

            return {
                'items': result_list,
                'total_count': total_count,
                'total_pages': total_pages,
                'current_page': page
            }

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
