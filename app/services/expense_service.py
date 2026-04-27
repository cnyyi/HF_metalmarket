# -*- coding: utf-8 -*-
"""
费用单服务层
负责费用单的创建、查询、详情等业务逻辑，确认后自动联动生成应付账款
"""
import logging
from utils.database import DBConnection
from utils.format_utils import format_date, format_datetime
from utils.sequence import generate_serial_no
from app.services.dict_service import DictService

logger = logging.getLogger(__name__)


class ExpenseService:
    """费用单管理服务"""

    # ========== 列表查询 ==========

    def get_orders(self, page=1, per_page=10, search=None, category=None,
                   date_from=None, date_to=None):
        """获取费用单分页列表"""
        with DBConnection() as conn:
            cursor = conn.cursor()

            base_query = """
                SELECT eo.OrderID, eo.OrderNo, eo.ExpenseCategory, eo.VendorName,
                       eo.TotalAmount, eo.OrderDate, eo.Description, eo.Status,
                       eo.CreateBy, eo.CreateTime,
                       u.RealName AS CreateByName,
                       (SELECT COUNT(*) FROM ExpenseOrderItem WHERE OrderID = eo.OrderID) AS ItemCount
                FROM ExpenseOrder eo
                LEFT JOIN [User] u ON eo.CreateBy = u.UserID
            """
            count_query = "SELECT COUNT(*) FROM ExpenseOrder eo"

            conditions = []
            params = []

            if search:
                conditions.append("(eo.OrderNo LIKE ? OR eo.VendorName LIKE ?)")
                p = f'%{search}%'
                params.extend([p, p])

            if category:
                conditions.append("eo.ExpenseCategory = ?")
                params.append(category)

            if date_from:
                conditions.append("eo.OrderDate >= ?")
                params.append(date_from)

            if date_to:
                conditions.append("eo.OrderDate <= ?")
                params.append(date_to)

            where_clause = ""
            if conditions:
                where_clause = " WHERE " + " AND ".join(conditions)
                base_query += where_clause
                count_query += where_clause

            # 总数
            cursor.execute(count_query, tuple(params))
            total_count = cursor.fetchone()[0]

            # 分页
            offset = (page - 1) * per_page
            base_query += " ORDER BY eo.CreateTime DESC OFFSET ? ROWS FETCH NEXT ? ROWS ONLY"
            params.extend([offset, per_page])

            cursor.execute(base_query, tuple(params))
            rows = cursor.fetchall()

            items = []
            for row in rows:
                items.append({
                    'order_id': row.OrderID,
                    'order_no': row.OrderNo,
                    'expense_category': row.ExpenseCategory,
                    'vendor_name': row.VendorName,
                    'total_amount': float(row.TotalAmount),
                    'order_date': format_date(row.OrderDate),
                    'description': row.Description or '',
                    'status': row.Status,
                    'create_by_name': row.CreateByName or '',
                    'create_time': format_datetime(row.CreateTime),
                    'item_count': row.ItemCount,
                })

            total_pages = (total_count + per_page - 1) // per_page if total_count > 0 else 1

            return {
                'items': items,
                'total': total_count,
                'page': page,
                'per_page': per_page,
                'total_pages': total_pages,
            }

    # ========== 详情查询 ==========

    def get_order_detail(self, order_id):
        """获取费用单详情（含明细行和应付状态）"""
        with DBConnection() as conn:
            cursor = conn.cursor()

            # 主表
            cursor.execute("""
                SELECT eo.OrderID, eo.OrderNo, eo.ExpenseCategory, eo.VendorName,
                       eo.TotalAmount, eo.OrderDate, eo.Description, eo.Status,
                       eo.CreateBy, eo.CreateTime,
                       u.RealName AS CreateByName
                FROM ExpenseOrder eo
                LEFT JOIN [User] u ON eo.CreateBy = u.UserID
                WHERE eo.OrderID = ?
            """, (order_id,))
            row = cursor.fetchone()
            if not row:
                return None

            order = {
                'order_id': row.OrderID,
                'order_no': row.OrderNo,
                'expense_category': row.ExpenseCategory,
                'vendor_name': row.VendorName,
                'total_amount': float(row.TotalAmount),
                'order_date': format_date(row.OrderDate),
                'description': row.Description or '',
                'status': row.Status,
                'create_by_name': row.CreateByName or '',
                'create_time': format_datetime(row.CreateTime),
            }

            # 明细行（含应付状态）
            cursor.execute("""
                SELECT eoi.ItemID, eoi.ExpenseTypeID, eoi.ItemDescription, eoi.Amount,
                       eoi.WorkerName, eoi.WorkDate, eoi.PayableID,
                       d.DictName AS ExpenseTypeName,
                       p.Status AS PayableStatus,
                       p.PaidAmount AS PayablePaidAmount
                FROM ExpenseOrderItem eoi
                LEFT JOIN Sys_Dictionary d ON eoi.ExpenseTypeID = d.DictID
                LEFT JOIN Payable p ON eoi.PayableID = p.PayableID
                WHERE eoi.OrderID = ?
                ORDER BY eoi.ItemID
            """, (order_id,))
            item_rows = cursor.fetchall()

            items = []
            for ir in item_rows:
                items.append({
                    'item_id': ir.ItemID,
                    'expense_type_id': ir.ExpenseTypeID,
                    'expense_type_name': ir.ExpenseTypeName or '',
                    'item_description': ir.ItemDescription or '',
                    'amount': float(ir.Amount),
                    'worker_name': ir.WorkerName or '',
                    'work_date': format_date(ir.WorkDate),
                    'payable_id': ir.PayableID,
                    'payable_status': ir.PayableStatus or '',
                    'payable_paid_amount': float(ir.PayablePaidAmount) if ir.PayablePaidAmount else 0,
                })

            order['items'] = items
            return order

    # ========== 创建费用单 ==========

    def create_order(self, expense_category, vendor_name, order_date, items,
                     description=None, created_by=None):
        """
        创建费用单（建单即确认，事务内完成：建单+明细+生成Payable+回写PayableID）

        Args:
            expense_category: 费用大类（字典名称，如"垃圾清运"）
            vendor_name: 供应商/收款方
            order_date: 费用日期 (str YYYY-MM-DD)
            items: 明细行列表 [{'expense_type_id':int, 'item_description':str, 'amount':float, 'worker_name':str?, 'work_date':str?}]
            description: 备注
            created_by: 创建人 UserID

        Returns:
            dict: {'order_id': int, 'order_no': str, 'payable_count': int}
        """
        # 参数校验
        if not vendor_name or not vendor_name.strip():
            raise ValueError("供应商/收款方不能为空")
        if not order_date:
            raise ValueError("请选择费用日期")
        if not items or len(items) == 0:
            raise ValueError("至少添加一条明细行")

        # 校验费用项
        expense_items = DictService.get_expense_items('expense_item_expend')
        valid_expense_ids = {item['dict_id'] for item in expense_items}

        total_amount = 0
        for i, item in enumerate(items):
            if not item.get('expense_type_id'):
                raise ValueError(f"第{i+1}行：请选择费用项")
            if int(item['expense_type_id']) not in valid_expense_ids:
                raise ValueError(f"第{i+1}行：费用项无效")
            if not item.get('amount') or float(item['amount']) <= 0:
                raise ValueError(f"第{i+1}行：金额必须大于0")
            total_amount += float(item['amount'])

        with DBConnection() as conn:
            cursor = conn.cursor()

            # 1. 生成单号
            order_no = generate_serial_no(cursor, 'EO', 'ExpenseOrder', 'OrderNo')

            # 2. 插入费用单主表
            cursor.execute("""
                INSERT INTO ExpenseOrder (OrderNo, ExpenseCategory, VendorName, TotalAmount,
                                          OrderDate, Description, Status, CreateBy)
                OUTPUT INSERTED.OrderID
                VALUES (?, ?, ?, ?, ?, ?, N'已确认', ?)
            """, (
                order_no, expense_category, vendor_name.strip(),
                total_amount, order_date,
                description.strip() if description else None,
                created_by
            ))
            row = cursor.fetchone()
            order_id = row[0]

            # 3. 逐条插入明细行 + 生成 Payable + 回写 PayableID
            payable_count = 0
            for item in items:
                expense_type_id = int(item['expense_type_id'])
                amount = float(item['amount'])
                item_desc = (item.get('item_description') or '').strip() or None
                worker_name = (item.get('worker_name') or '').strip() or None
                work_date = item.get('work_date') or None

                # 插入明细行
                cursor.execute("""
                    INSERT INTO ExpenseOrderItem (OrderID, ExpenseTypeID, ItemDescription,
                                                   Amount, WorkerName, WorkDate)
                    OUTPUT INSERTED.ItemID
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (order_id, expense_type_id, item_desc, amount, worker_name, work_date))
                item_row = cursor.fetchone()
                item_id = item_row[0]

                # 拼接 Payable.Description
                expense_name = ''
                for ei in expense_items:
                    if ei['dict_id'] == expense_type_id:
                        expense_name = ei['dict_name']
                        break
                payable_desc = f"{expense_category} - {expense_name}"
                if item_desc:
                    payable_desc += f" - {item_desc}"

                # 插入 Payable
                cursor.execute("""
                    INSERT INTO Payable (VendorName, ExpenseTypeID, Amount, DueDate,
                                         Status, PaidAmount, RemainingAmount, Description,
                                         ReferenceType, ReferenceID, ExpenseOrderID)
                    OUTPUT INSERTED.PayableID
                    VALUES (?, ?, ?, ?, N'未付款', 0, ?, ?, N'expense_order', ?, ?)
                """, (
                    vendor_name.strip(), expense_type_id, amount,
                    order_date, amount, payable_desc,
                    order_id, order_id
                ))
                payable_row = cursor.fetchone()
                payable_id = payable_row[0]

                # 回写 PayableID 到明细行
                cursor.execute("""
                    UPDATE ExpenseOrderItem SET PayableID = ? WHERE ItemID = ?
                """, (payable_id, item_id))

                payable_count += 1

            conn.commit()

            logger.info(f"费用单创建成功: {order_no}, 生成{payable_count}笔应付")
            return {
                'order_id': order_id,
                'order_no': order_no,
                'payable_count': payable_count,
            }

    # ========== 统计 ==========

    def get_summary(self, category=None, date_from=None, date_to=None):
        """获取费用单汇总统计"""
        with DBConnection() as conn:
            cursor = conn.cursor()

            query = "SELECT ISNULL(SUM(TotalAmount), 0) FROM ExpenseOrder"
            conditions = []
            params = []

            if category:
                conditions.append("ExpenseCategory = ?")
                params.append(category)
            if date_from:
                conditions.append("OrderDate >= ?")
                params.append(date_from)
            if date_to:
                conditions.append("OrderDate <= ?")
                params.append(date_to)

            if conditions:
                query += " WHERE " + " AND ".join(conditions)

            cursor.execute(query, tuple(params))
            row = cursor.fetchone()
            return float(row[0])
