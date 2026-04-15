# -*- coding: utf-8 -*-
from app.repositories.receivable_repo import ReceivableRepository
from utils.database import execute_query


class ReceivableService:

    def __init__(self):
        self.repo = ReceivableRepository()

    def get_receivables(self, page=1, per_page=10, search=None, status=None):
        rows, total_count = self.repo.get_list(page=page, per_page=per_page, search=search, status=status)
        total_pages = (total_count + per_page - 1) // per_page if total_count > 0 else 0

        result_list = []
        for row in rows:
            result_list.append({
                'receivable_id': row.ReceivableID,
                'merchant_id': row.MerchantID,
                'merchant_name': row.CustomerName or '',  # 统一使用 CASE 合并后的名称
                'customer_type': row.CustomerType or 'Merchant',
                'customer_id': row.CustomerID or row.MerchantID,
                'expense_type_id': row.ExpenseTypeID,
                'expense_type_name': row.ExpenseTypeName,
                'amount': float(row.Amount),
                'paid_amount': float(row.PaidAmount),
                'remaining_amount': float(row.RemainingAmount),
                'due_date': row.DueDate.strftime('%Y-%m-%d') if row.DueDate else '',
                'status': row.Status,
                'description': row.Description or '',
                'create_time': row.CreateTime.strftime('%Y-%m-%d %H:%M') if row.CreateTime else '',
            })

        return {
            'items': result_list,
            'total_count': total_count,
            'total_pages': total_pages,
            'current_page': page
        }

    def create_receivable(self, merchant_id=None, expense_type_id=None, amount=None, due_date=None,
                          description=None, reference_id=None, reference_type=None,
                          customer_type='Merchant', customer_id=None):
        """创建应收账款

        Args:
            merchant_id: 商户ID（兼容旧调用，Merchant 类型时必填）
            customer_type: 客户类型 'Merchant' 或 'Customer'
            customer_id: 客户ID（Merchant类型=MerchantID，Customer类型=CustomerID）
        """
        if customer_type == 'Merchant':
            if not merchant_id and not customer_id:
                raise ValueError("请选择商户")
        else:
            if not customer_id:
                raise ValueError("请选择客户")

        if not expense_type_id:
            raise ValueError("请选择费用类型")
        if not amount or float(amount) <= 0:
            raise ValueError("应收金额必须大于0")
        if not due_date:
            raise ValueError("请选择到期日期")

        new_id = self.repo.create(
            merchant_id=int(merchant_id) if merchant_id else None,
            expense_type_id=int(expense_type_id),
            amount=float(amount),
            due_date=due_date,
            description=description,
            reference_id=reference_id,
            reference_type=reference_type,
            customer_type=customer_type,
            customer_id=int(customer_id) if customer_id else None
        )
        return new_id

    def pay(self, receivable_id, amount):
        receivable = self.repo.get_by_id(receivable_id)

        if not receivable:
            raise Exception("应收记录不存在")

        remaining = float(receivable.RemainingAmount)

        if amount <= 0:
            raise Exception("支付金额必须大于0")

        if amount > remaining:
            raise Exception("支付金额不能大于剩余金额")

        self.repo.update_payment(receivable_id, amount)

        new_remaining = remaining - amount

        if new_remaining == 0:
            self.repo.update_status(receivable_id, '已付款')
        else:
            self.repo.update_status(receivable_id, '部分付款')

        return True

    def check_overdue(self):
        overdue_list = self.repo.list_overdue()

        for item in overdue_list:
            self.repo.update_status(item.ReceivableID, '逾期')

        return len(overdue_list)

    @staticmethod
    def get_expense_types(direction=None):
        query = """
            SELECT ExpenseTypeID, ExpenseTypeName, ExpenseTypeCode, ExpenseDirection, Description
            FROM ExpenseType
            WHERE IsActive = 1
        """
        params = []

        if direction:
            query += " AND ExpenseDirection = ?"
            params.append(direction)

        query += " ORDER BY ExpenseTypeID"

        results = execute_query(query, tuple(params) if params else None, fetch_type='all')

        return [{
            'expense_type_id': r.ExpenseTypeID,
            'expense_type_name': r.ExpenseTypeName,
            'expense_type_code': r.ExpenseTypeCode,
            'expense_direction': r.ExpenseDirection,
            'description': r.Description or ''
        } for r in results]

    @staticmethod
    def search_merchants(keyword):
        query = """
            SELECT MerchantID, MerchantName, ContactPerson, Phone
            FROM Merchant
            WHERE MerchantName LIKE ? OR ContactPerson LIKE ? OR Phone LIKE ?
            ORDER BY MerchantID
        """
        search_param = f'%{keyword}%'
        results = execute_query(query, (search_param, search_param, search_param), fetch_type='all')

        return [{
            'merchant_id': r.MerchantID,
            'merchant_name': r.MerchantName,
            'contact_person': r.ContactPerson or '',
            'phone': r.Phone or ''
        } for r in results]
