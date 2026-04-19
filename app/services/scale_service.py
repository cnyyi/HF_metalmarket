# -*- coding: utf-8 -*-
"""磅秤管理服务层 — 管理端数据查询（全量，无商户隔离）"""
import logging
from datetime import datetime
from utils.database import execute_query

logger = logging.getLogger(__name__)


class ScaleService:

    @staticmethod
    def get_scale_list():
        rows = execute_query("""
            SELECT ScaleID, ScaleNumber, ScaleName, Location,
                   MaximumCapacity, Unit, Status, Description,
                   CreateTime, UpdateTime
            FROM Scale
            ORDER BY ScaleID
        """, fetch_type='all')

        items = []
        for r in rows:
            items.append({
                'scale_id': r.ScaleID,
                'scale_number': r.ScaleNumber or '',
                'scale_name': r.ScaleName or '',
                'location': r.Location or '',
                'maximum_capacity': float(r.MaximumCapacity) if r.MaximumCapacity else 0,
                'unit': r.Unit or '',
                'status': r.Status or '',
                'description': r.Description or '',
                'create_time': r.CreateTime.strftime('%Y-%m-%d %H:%M') if r.CreateTime else '',
                'update_time': r.UpdateTime.strftime('%Y-%m-%d %H:%M') if r.UpdateTime else '',
            })
        return items

    @staticmethod
    def get_scale_records(page=1, per_page=20, keyword=None, start_date=None, end_date=None):
        conditions = []
        params = []

        if keyword:
            conditions.append("(sr.LicensePlate LIKE ? OR sr.ProductName LIKE ? OR sr.SenderName LIKE ? OR sr.ReceiverName LIKE ? OR sr.SourceSerialNo LIKE ?)")
            kw = f'%{keyword}%'
            params.extend([kw, kw, kw, kw, kw])

        if start_date:
            conditions.append("sr.ScaleTime >= ?")
            params.append(start_date)

        if end_date:
            conditions.append("sr.ScaleTime < ?")
            params.append(end_date + ' 23:59:59')

        where = " AND ".join(conditions) if conditions else "1=1"

        count_query = f"SELECT COUNT(*) AS cnt FROM ScaleRecord sr WHERE {where}"
        count_result = execute_query(count_query, tuple(params), fetch_type='one')
        total_count = count_result.cnt if count_result else 0

        offset = (page - 1) * per_page
        data_query = f"""
            SELECT sr.ScaleRecordID, sr.ScaleID, sr.MerchantID,
                   sr.SourceSerialNo, sr.WeighType,
                   sr.GrossWeight, sr.TareWeight, sr.NetWeight,
                   sr.DeductWeight, sr.ActualWeight,
                   sr.UnitPrice, sr.TotalAmount, sr.ScaleFee,
                   sr.LicensePlate, sr.ProductName,
                   sr.SenderName, sr.ReceiverName,
                   sr.GrossTime, sr.TareTime, sr.ScaleTime,
                   sr.GrossOperator, sr.TareOperator, sr.Operator,
                   sr.Description, sr.CreateTime,
                   s.ScaleName,
                   m.MerchantName
            FROM ScaleRecord sr
            LEFT JOIN Scale s ON sr.ScaleID = s.ScaleID
            LEFT JOIN Merchant m ON sr.MerchantID = m.MerchantID
            WHERE {where}
            ORDER BY sr.ScaleTime DESC
            OFFSET ? ROWS FETCH NEXT ? ROWS ONLY
        """
        params.extend([offset, per_page])
        rows = execute_query(data_query, tuple(params), fetch_type='all')

        items = []
        for r in rows:
            items.append({
                'scale_record_id': r.ScaleRecordID,
                'scale_id': r.ScaleID,
                'merchant_id': r.MerchantID,
                'source_serial_no': getattr(r, 'SourceSerialNo', '') or '',
                'weigh_type': getattr(r, 'WeighType', '') or '',
                'gross_weight': float(r.GrossWeight) if r.GrossWeight else 0,
                'tare_weight': float(r.TareWeight) if r.TareWeight else 0,
                'net_weight': float(r.NetWeight) if r.NetWeight else 0,
                'deduct_weight': float(getattr(r, 'DeductWeight', 0) or 0),
                'actual_weight': float(getattr(r, 'ActualWeight', 0) or 0),
                'unit_price': float(r.UnitPrice) if r.UnitPrice else 0,
                'total_amount': float(r.TotalAmount) if r.TotalAmount else 0,
                'scale_fee': float(getattr(r, 'ScaleFee', 0) or 0),
                'license_plate': r.LicensePlate or '',
                'product_name': r.ProductName or '',
                'sender_name': getattr(r, 'SenderName', '') or '',
                'receiver_name': getattr(r, 'ReceiverName', '') or '',
                'gross_time': r.GrossTime.strftime('%Y-%m-%d %H:%M') if getattr(r, 'GrossTime', None) else '',
                'tare_time': r.TareTime.strftime('%Y-%m-%d %H:%M') if getattr(r, 'TareTime', None) else '',
                'scale_time': r.ScaleTime.strftime('%Y-%m-%d %H:%M') if r.ScaleTime else '',
                'gross_operator': getattr(r, 'GrossOperator', '') or '',
                'tare_operator': getattr(r, 'TareOperator', '') or '',
                'operator': r.Operator or '',
                'description': r.Description or '',
                'create_time': r.CreateTime.strftime('%Y-%m-%d %H:%M') if r.CreateTime else '',
                'scale_name': getattr(r, 'ScaleName', '') or '',
                'merchant_name': getattr(r, 'MerchantName', '') or '',
            })

        total_pages = (total_count + per_page - 1) // per_page if total_count > 0 else 0
        return {
            'items': items,
            'total_count': total_count,
            'total_pages': total_pages,
            'current_page': page
        }

    @staticmethod
    def get_scale_record_detail(record_id):
        row = execute_query("""
            SELECT sr.ScaleRecordID, sr.ScaleID, sr.MerchantID,
                   sr.SourceSerialNo, sr.WeighType,
                   sr.GrossWeight, sr.TareWeight, sr.NetWeight,
                   sr.DeductWeight, sr.ActualWeight,
                   sr.UnitPrice, sr.TotalAmount, sr.ScaleFee,
                   sr.LicensePlate, sr.ProductName,
                   sr.SenderName, sr.ReceiverName,
                   sr.GrossTime, sr.TareTime, sr.ScaleTime,
                   sr.GrossOperator, sr.TareOperator, sr.Operator,
                   sr.Description, sr.CreateTime,
                   s.ScaleName,
                   m.MerchantName
            FROM ScaleRecord sr
            LEFT JOIN Scale s ON sr.ScaleID = s.ScaleID
            LEFT JOIN Merchant m ON sr.MerchantID = m.MerchantID
            WHERE sr.ScaleRecordID = ?
        """, (record_id,), fetch_type='one')

        if not row:
            return None

        r = row
        return {
            'scale_record_id': r.ScaleRecordID,
            'scale_id': r.ScaleID,
            'merchant_id': r.MerchantID,
            'source_serial_no': getattr(r, 'SourceSerialNo', '') or '',
            'weigh_type': getattr(r, 'WeighType', '') or '',
            'gross_weight': float(r.GrossWeight) if r.GrossWeight else 0,
            'tare_weight': float(r.TareWeight) if r.TareWeight else 0,
            'net_weight': float(r.NetWeight) if r.NetWeight else 0,
            'deduct_weight': float(getattr(r, 'DeductWeight', 0) or 0),
            'actual_weight': float(getattr(r, 'ActualWeight', 0) or 0),
            'unit_price': float(r.UnitPrice) if r.UnitPrice else 0,
            'total_amount': float(r.TotalAmount) if r.TotalAmount else 0,
            'scale_fee': float(getattr(r, 'ScaleFee', 0) or 0),
            'license_plate': r.LicensePlate or '',
            'product_name': r.ProductName or '',
            'sender_name': getattr(r, 'SenderName', '') or '',
            'receiver_name': getattr(r, 'ReceiverName', '') or '',
            'gross_time': r.GrossTime.strftime('%Y-%m-%d %H:%M:%S') if getattr(r, 'GrossTime', None) else '',
            'tare_time': r.TareTime.strftime('%Y-%m-%d %H:%M:%S') if getattr(r, 'TareTime', None) else '',
            'scale_time': r.ScaleTime.strftime('%Y-%m-%d %H:%M:%S') if r.ScaleTime else '',
            'gross_operator': getattr(r, 'GrossOperator', '') or '',
            'tare_operator': getattr(r, 'TareOperator', '') or '',
            'operator': r.Operator or '',
            'description': r.Description or '',
            'create_time': r.CreateTime.strftime('%Y-%m-%d %H:%M:%S') if r.CreateTime else '',
            'scale_name': getattr(r, 'ScaleName', '') or '',
            'merchant_name': getattr(r, 'MerchantName', '') or '',
        }

    @staticmethod
    def get_dashboard_overview():
        today_str = datetime.now().strftime('%Y-%m-%d')

        inbound_row = execute_query("""
            SELECT COUNT(*), ISNULL(SUM(NetWeight), 0), ISNULL(SUM(ScaleFee), 0)
            FROM ScaleRecord
            WHERE CAST(ScaleTime AS DATE) = ?
              AND TareTime IS NULL
        """, (today_str,), fetch_type='one')

        outbound_row = execute_query("""
            SELECT COUNT(*), ISNULL(SUM(NetWeight), 0), ISNULL(SUM(ScaleFee), 0)
            FROM ScaleRecord
            WHERE CAST(ScaleTime AS DATE) = ?
              AND TareTime IS NOT NULL
        """, (today_str,), fetch_type='one')

        return {
            'inbound': {
                'vehicles': int(inbound_row[0]) if inbound_row else 0,
                'cargo_weight': float(inbound_row[1]) if inbound_row else 0,
                'fee': float(inbound_row[2]) if inbound_row else 0,
            },
            'outbound': {
                'vehicles': int(outbound_row[0]) if outbound_row else 0,
                'cargo_weight': float(outbound_row[1]) if outbound_row else 0,
                'fee': float(outbound_row[2]) if outbound_row else 0,
            }
        }

    @staticmethod
    def get_monthly_trend(year, month):
        month_str = f'{int(year):04d}-{int(month):02d}'

        if int(month) == 12:
            next_month_str = f'{int(year)+1:04d}-01'
        else:
            next_month_str = f'{int(year):04d}-{int(month)+1:02d}'

        days_in_month_row = execute_query("""
            SELECT DAY(DATEADD(DAY, -1, DATEADD(MONTH, 1, ? + '-01')))
        """, (month_str,), fetch_type='one')
        days_in_month = days_in_month_row[0] if days_in_month_row else 30

        rows = execute_query("""
            SELECT
                DAY(ScaleTime) AS DayNum,
                COUNT(*) AS VehicleCount,
                ISNULL(SUM(NetWeight), 0) AS CargoWeight,
                ISNULL(SUM(ScaleFee), 0) AS FeeAmount
            FROM ScaleRecord
            WHERE FORMAT(ScaleTime, 'yyyy-MM') = ?
            GROUP BY DAY(ScaleTime)
            ORDER BY DayNum
        """, (month_str,), fetch_type='all')

        data_map = {}
        for r in rows:
            data_map[int(r[0])] = {
                'vehicles': int(r[1]),
                'cargo_weight': float(r[2]),
                'fee': float(r[3]),
            }

        max_day = days_in_month
        if year == str(datetime.now().year) and int(month) == datetime.now().month:
            max_day = datetime.now().day

        labels = []
        vehicles = []
        cargo_weights = []
        fees = []
        for d in range(1, max_day + 1):
            labels.append(f'{d}日')
            entry = data_map.get(d, {'vehicles': 0, 'cargo_weight': 0, 'fee': 0})
            vehicles.append(entry['vehicles'])
            cargo_weights.append(round(entry['cargo_weight'] / 1000, 2))
            fees.append(round(entry['fee'], 2))

        return {
            'labels': labels,
            'vehicles': vehicles,
            'cargo_weights': cargo_weights,
            'fees': fees,
        }

    @staticmethod
    def get_today_records(page=1, per_page=15, keyword=None):
        today_str = datetime.now().strftime('%Y-%m-%d')

        conditions = ["CAST(sr.ScaleTime AS DATE) = ?"]
        params = [today_str]

        if keyword:
            conditions.append("(sr.LicensePlate LIKE ? OR sr.ProductName LIKE ? OR sr.SourceSerialNo LIKE ?)")
            kw = f'%{keyword}%'
            params.extend([kw, kw, kw])

        where = " AND ".join(conditions)

        count_query = f"SELECT COUNT(*) AS cnt FROM ScaleRecord sr WHERE {where}"
        count_result = execute_query(count_query, tuple(params), fetch_type='one')
        total_count = count_result.cnt if count_result else 0

        offset = (page - 1) * per_page
        data_query = f"""
            SELECT sr.ScaleRecordID, sr.SourceSerialNo, sr.WeighType,
                   sr.GrossWeight, sr.TareWeight, sr.NetWeight,
                   sr.DeductWeight, sr.ActualWeight,
                   sr.UnitPrice, sr.TotalAmount, sr.ScaleFee,
                   sr.LicensePlate, sr.ProductName,
                   sr.SenderName, sr.ReceiverName,
                   sr.GrossTime, sr.TareTime, sr.ScaleTime,
                   sr.GrossOperator, sr.TareOperator, sr.Operator,
                   sr.Description,
                   m.MerchantName
            FROM ScaleRecord sr
            LEFT JOIN Merchant m ON sr.MerchantID = m.MerchantID
            WHERE {where}
            ORDER BY sr.ScaleTime DESC
            OFFSET ? ROWS FETCH NEXT ? ROWS ONLY
        """
        params.extend([offset, per_page])
        rows = execute_query(data_query, tuple(params), fetch_type='all')

        items = []
        for r in rows:
            has_tare = getattr(r, 'TareTime', None) is not None
            direction = '出场' if has_tare else '进场'
            items.append({
                'scale_record_id': r.ScaleRecordID,
                'source_serial_no': getattr(r, 'SourceSerialNo', '') or '',
                'weigh_type': getattr(r, 'WeighType', '') or '',
                'direction': direction,
                'gross_weight': float(r.GrossWeight) if r.GrossWeight else 0,
                'tare_weight': float(r.TareWeight) if r.TareWeight else 0,
                'net_weight': float(r.NetWeight) if r.NetWeight else 0,
                'deduct_weight': float(getattr(r, 'DeductWeight', 0) or 0),
                'actual_weight': float(getattr(r, 'ActualWeight', 0) or 0),
                'unit_price': float(r.UnitPrice) if r.UnitPrice else 0,
                'total_amount': float(r.TotalAmount) if r.TotalAmount else 0,
                'scale_fee': float(getattr(r, 'ScaleFee', 0) or 0),
                'license_plate': r.LicensePlate or '',
                'product_name': r.ProductName or '',
                'sender_name': getattr(r, 'SenderName', '') or '',
                'receiver_name': getattr(r, 'ReceiverName', '') or '',
                'gross_time': r.GrossTime.strftime('%H:%M') if getattr(r, 'GrossTime', None) else '',
                'tare_time': r.TareTime.strftime('%H:%M') if getattr(r, 'TareTime', None) else '',
                'scale_time': r.ScaleTime.strftime('%H:%M') if r.ScaleTime else '',
                'operator': r.Operator or '',
                'merchant_name': getattr(r, 'MerchantName', '') or '',
                'description': r.Description or '',
            })

        total_pages = (total_count + per_page - 1) // per_page if total_count > 0 else 0
        return {
            'items': items,
            'total_count': total_count,
            'total_pages': total_pages,
            'current_page': page
        }
