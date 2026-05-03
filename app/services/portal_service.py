# -*- coding: utf-8 -*-
"""商户门户服务层 — 商户数据查询（带商户隔离）"""
import logging
from utils.database import execute_query

logger = logging.getLogger(__name__)


class PortalService:
    """商户门户服务 — 所有查询均需传入 merchant_id 做数据隔离"""

    @staticmethod
    def get_dashboard(merchant_id):
        """获取商户首页统计数据"""
        stats = {}

        # 生效合同数
        row = execute_query("""
            SELECT COUNT(*) AS cnt FROM Contract
            WHERE MerchantID = ? AND Status = N'生效'
        """, (merchant_id,), fetch_type='one')
        stats['active_contracts'] = row.cnt if row else 0

        # 待缴金额
        row = execute_query("""
            SELECT ISNULL(SUM(RemainingAmount), 0) AS total
            FROM Receivable
            WHERE (MerchantID = ? OR CustomerID = ?)
              AND CustomerType = 'Merchant'
              AND Status != N'已付款'
              AND IsActive = 1
        """, (merchant_id, merchant_id), fetch_type='one')
        stats['pending_amount'] = float(row.total) if row else 0

        # 本月水电费
        row = execute_query("""
            SELECT ISNULL(SUM(TotalAmount), 0) AS total
            FROM UtilityReading
            WHERE MerchantID = ?
              AND YEAR(ReadingDate) = YEAR(GETDATE())
              AND MONTH(ReadingDate) = MONTH(GETDATE())
        """, (merchant_id,), fetch_type='one')
        stats['monthly_utility'] = float(row.total) if row else 0

        # 本月过磅次数
        row = execute_query("""
            SELECT COUNT(*) AS cnt
            FROM ScaleRecord
            WHERE MerchantID = ?
              AND YEAR(ScaleTime) = YEAR(GETDATE())
              AND MONTH(ScaleTime) = MONTH(GETDATE())
        """, (merchant_id,), fetch_type='one')
        stats['monthly_scale_count'] = row.cnt if row else 0

        # 即将到期合同（30天内）
        rows = execute_query("""
            SELECT TOP 5 ContractID, ContractName, EndDate
            FROM Contract
            WHERE MerchantID = ? AND Status = N'生效'
              AND EndDate BETWEEN GETDATE() AND DATEADD(DAY, 30, GETDATE())
            ORDER BY EndDate
        """, (merchant_id,), fetch_type='all')
        stats['expiring_contracts'] = [{
            'contract_id': r.ContractID,
            'contract_name': r.ContractName,
            'end_date': r.EndDate.strftime('%Y-%m-%d') if r.EndDate else ''
        } for r in rows]

        # 逾期未缴账单
        rows = execute_query("""
            SELECT TOP 5 ReceivableID, Amount, RemainingAmount, DueDate,
                   ISNULL(sd.DictName, et.ExpenseTypeName) AS ExpenseTypeName
            FROM Receivable r
            LEFT JOIN Sys_Dictionary sd ON r.ExpenseTypeID = sd.DictID AND sd.DictType = 'expense_item_income'
            LEFT JOIN ExpenseType et ON r.ExpenseTypeID = et.ExpenseTypeID AND sd.DictID IS NULL
            WHERE (r.MerchantID = ? OR r.CustomerID = ?)
              AND r.CustomerType = 'Merchant'
              AND r.Status != N'已付款'
              AND r.DueDate < GETDATE()
              AND r.IsActive = 1
            ORDER BY r.DueDate
        """, (merchant_id, merchant_id), fetch_type='all')
        stats['overdue_receivables'] = [{
            'receivable_id': r.ReceivableID,
            'amount': float(r.Amount),
            'remaining_amount': float(r.RemainingAmount),
            'due_date': r.DueDate.strftime('%Y-%m-%d') if r.DueDate else '',
            'expense_type_name': r.ExpenseTypeName or ''
        } for r in rows]

        return stats

    @staticmethod
    def get_contracts(merchant_id, page=1, per_page=10):
        """获取商户的合同列表"""
        count_query = """
            SELECT COUNT(*) AS cnt FROM Contract WHERE MerchantID = ?
        """
        data_query = """
            SELECT c.ContractID, c.ContractName, c.ContractNumber, c.StartDate, c.EndDate,
                   c.ContractAmount, c.ActualAmount, c.Status, c.BusinessType,
                   p.PlotNumber, p.PlotName
            FROM Contract c
            LEFT JOIN Plot p ON c.PlotID = p.PlotID
            WHERE c.MerchantID = ?
            ORDER BY c.CreateTime DESC
            OFFSET ? ROWS FETCH NEXT ? ROWS ONLY
        """
        count_result = execute_query(count_query, (merchant_id,), fetch_type='one')
        total_count = count_result.cnt if count_result else 0

        offset = (page - 1) * per_page
        rows = execute_query(data_query, (merchant_id, offset, per_page), fetch_type='all')

        items = []
        for r in rows:
            items.append({
                'contract_id': r.ContractID,
                'contract_name': r.ContractName,
                'contract_number': getattr(r, 'ContractNumber', '') or '',
                'start_date': r.StartDate.strftime('%Y-%m-%d') if r.StartDate else '',
                'end_date': r.EndDate.strftime('%Y-%m-%d') if r.EndDate else '',
                'contract_amount': float(r.ContractAmount) if r.ContractAmount else 0,
                'actual_amount': float(r.ActualAmount) if r.ActualAmount else 0,
                'status': r.Status or '',
                'business_type': r.BusinessType or '',
                'plot_number': getattr(r, 'PlotNumber', '') or '',
                'plot_name': getattr(r, 'PlotName', '') or '',
            })

        total_pages = (total_count + per_page - 1) // per_page if total_count > 0 else 0
        return {
            'items': items,
            'total_count': total_count,
            'total_pages': total_pages,
            'current_page': page
        }

    @staticmethod
    def get_receivables(merchant_id, page=1, per_page=10, status=None):
        """获取商户的应收/缴费记录"""
        conditions = ["(r.MerchantID = ? OR r.CustomerID = ?)", "r.CustomerType = 'Merchant'", "r.IsActive = 1"]
        params = [merchant_id, merchant_id]

        if status:
            conditions.append("r.Status = ?")
            params.append(status)

        where = " AND ".join(conditions)

        count_query = f"SELECT COUNT(*) AS cnt FROM Receivable r WHERE {where}"
        count_result = execute_query(count_query, tuple(params), fetch_type='one')
        total_count = count_result.cnt if count_result else 0

        offset = (page - 1) * per_page
        data_query = f"""
            SELECT r.ReceivableID, r.Amount, r.PaidAmount, r.RemainingAmount,
                   r.DueDate, r.Status, r.Description,
                   ISNULL(sd.DictName, et.ExpenseTypeName) AS ExpenseTypeName
            FROM Receivable r
            LEFT JOIN Sys_Dictionary sd ON r.ExpenseTypeID = sd.DictID AND sd.DictType = 'expense_item_income'
            LEFT JOIN ExpenseType et ON r.ExpenseTypeID = et.ExpenseTypeID AND sd.DictID IS NULL
            WHERE {where}
            ORDER BY r.DueDate DESC
            OFFSET ? ROWS FETCH NEXT ? ROWS ONLY
        """
        params.extend([offset, per_page])
        rows = execute_query(data_query, tuple(params), fetch_type='all')

        items = []
        for r in rows:
            items.append({
                'receivable_id': r.ReceivableID,
                'amount': float(r.Amount),
                'paid_amount': float(r.PaidAmount),
                'remaining_amount': float(r.RemainingAmount),
                'due_date': r.DueDate.strftime('%Y-%m-%d') if r.DueDate else '',
                'status': r.Status or '',
                'description': r.Description or '',
                'expense_type_name': r.ExpenseTypeName or '',
            })

        total_pages = (total_count + per_page - 1) // per_page if total_count > 0 else 0
        return {
            'items': items,
            'total_count': total_count,
            'total_pages': total_pages,
            'current_page': page
        }

    @staticmethod
    def get_scale_records(merchant_id, page=1, per_page=10):
        """获取商户的过磅记录"""
        count_query = "SELECT COUNT(*) AS cnt FROM ScaleRecord WHERE MerchantID = ?"
        count_result = execute_query(count_query, (merchant_id,), fetch_type='one')
        total_count = count_result.cnt if count_result else 0

        offset = (page - 1) * per_page
        data_query = """
            SELECT ScaleRecordID, GrossWeight, TareWeight, NetWeight,
                   UnitPrice, TotalAmount, LicensePlate, ProductName,
                   Operator, ScaleTime, Description
            FROM ScaleRecord
            WHERE MerchantID = ?
            ORDER BY ScaleTime DESC
            OFFSET ? ROWS FETCH NEXT ? ROWS ONLY
        """
        rows = execute_query(data_query, (merchant_id, offset, per_page), fetch_type='all')

        items = []
        for r in rows:
            items.append({
                'scale_record_id': r.ScaleRecordID,
                'gross_weight': float(r.GrossWeight) if r.GrossWeight else 0,
                'tare_weight': float(r.TareWeight) if r.TareWeight else 0,
                'net_weight': float(r.NetWeight) if r.NetWeight else 0,
                'unit_price': float(r.UnitPrice) if r.UnitPrice else 0,
                'total_amount': float(r.TotalAmount) if r.TotalAmount else 0,
                'license_plate': r.LicensePlate or '',
                'product_name': r.ProductName or '',
                'operator': r.Operator or '',
                'scale_time': r.ScaleTime.strftime('%Y-%m-%d %H:%M') if r.ScaleTime else '',
                'description': r.Description or '',
            })

        total_pages = (total_count + per_page - 1) // per_page if total_count > 0 else 0
        return {
            'items': items,
            'total_count': total_count,
            'total_pages': total_pages,
            'current_page': page
        }

    @staticmethod
    def get_utility_readings(merchant_id, page=1, per_page=10):
        """获取商户的水电抄表记录"""
        count_query = "SELECT COUNT(*) AS cnt FROM UtilityReading WHERE MerchantID = ?"
        count_result = execute_query(count_query, (merchant_id,), fetch_type='one')
        total_count = count_result.cnt if count_result else 0

        offset = (page - 1) * per_page
        data_query = """
            SELECT ur.ReadingID, ur.ReadingDate, ur.PreviousReading, ur.CurrentReading,
                   ur.Usage, ur.UnitPrice, ur.TotalAmount, ur.Status, ur.ReadingType,
                   m.MeterNumber
            FROM UtilityReading ur
            LEFT JOIN Meter m ON ur.MeterID = m.MeterID
            WHERE ur.MerchantID = ?
            ORDER BY ur.ReadingDate DESC
            OFFSET ? ROWS FETCH NEXT ? ROWS ONLY
        """
        rows = execute_query(data_query, (merchant_id, offset, per_page), fetch_type='all')

        items = []
        for r in rows:
            items.append({
                'reading_id': r.ReadingID,
                'reading_date': r.ReadingDate.strftime('%Y-%m-%d') if r.ReadingDate else '',
                'previous_reading': float(r.PreviousReading) if r.PreviousReading else 0,
                'current_reading': float(r.CurrentReading) if r.CurrentReading else 0,
                'usage': float(r.Usage) if r.Usage else 0,
                'unit_price': float(r.UnitPrice) if r.UnitPrice else 0,
                'total_amount': float(r.TotalAmount) if r.TotalAmount else 0,
                'status': r.Status or '',
                'reading_type': r.ReadingType or '',
                'meter_number': getattr(r, 'MeterNumber', '') or '',
            })

        total_pages = (total_count + per_page - 1) // per_page if total_count > 0 else 0
        return {
            'items': items,
            'total_count': total_count,
            'total_pages': total_pages,
            'current_page': page
        }
