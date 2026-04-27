"""
后台管理服务层
"""
import logging
from datetime import datetime, timedelta

from utils.database import DBConnection

logger = logging.getLogger(__name__)


class AdminService:
    """后台首页与仪表盘相关服务"""

    @staticmethod
    def get_dashboard_stats():
        """获取仪表盘统计数据"""
        with DBConnection() as conn:
            cursor = conn.cursor()

            cursor.execute("""
                SELECT
                    ISNULL(SUM(CASE WHEN Status = N'未付款' THEN RemainingAmount ELSE 0 END), 0),
                    ISNULL(SUM(CASE WHEN Status = N'部分付款' THEN RemainingAmount ELSE 0 END), 0),
                    ISNULL(SUM(CASE WHEN Status = N'已付款' THEN Amount ELSE 0 END), 0),
                    COUNT(CASE WHEN Status = N'未付款' THEN 1 END),
                    COUNT(CASE WHEN Status = N'部分付款' THEN 1 END)
                FROM Receivable
                WHERE IsActive = 1
            """)
            recv_row = cursor.fetchone()
            receivable_unpaid = float(recv_row[0])
            receivable_partial = float(recv_row[1])
            receivable_collected = float(recv_row[2])
            unpaid_count = int(recv_row[3] or 0)
            partial_count = int(recv_row[4] or 0)

            cursor.execute("""
                SELECT
                    ISNULL(SUM(CASE WHEN Status = N'未付款' THEN RemainingAmount ELSE 0 END), 0),
                    ISNULL(SUM(CASE WHEN Status = N'已付款' THEN Amount ELSE 0 END), 0)
                FROM Payable
            """)
            pay_row = cursor.fetchone()
            payable_unpaid = float(pay_row[0])
            payable_paid = float(pay_row[1])

            today = datetime.now().strftime('%Y-%m-%d')
            cursor.execute("""
                SELECT
                    ISNULL(SUM(CASE WHEN Direction = N'收入' THEN Amount ELSE 0 END), 0),
                    ISNULL(SUM(CASE WHEN Direction = N'支出' THEN Amount ELSE 0 END), 0)
                FROM CashFlow
                WHERE CAST(TransactionDate AS DATE) = ?
            """, (today,))
            today_row = cursor.fetchone()
            today_income = float(today_row[0])
            today_expense = float(today_row[1])

            cursor.execute("""
                SELECT COUNT(*)
                FROM Contract
                WHERE Status IN (N'生效', N'有效')
                  AND StartDate <= CAST(GETDATE() AS DATE)
                  AND EndDate >= CAST(GETDATE() AS DATE)
            """)
            active_contracts = int(cursor.fetchone()[0])

            cursor.execute("SELECT COUNT(*) FROM Plot WHERE Status = N'已出租'")
            rented_plots = int(cursor.fetchone()[0])

            cursor.execute("SELECT COUNT(*) FROM Plot")
            total_plots = int(cursor.fetchone()[0])
            vacancy_rate = round((1 - rented_plots / max(total_plots, 1)) * 100, 1)

            months = []
            income_data = []
            expense_data = []
            for i in range(5, -1, -1):
                dt = datetime.now() - timedelta(days=i * 30)
                ym = dt.strftime('%Y-%m')
                label = dt.strftime('%m月')
                months.append(label)

                cursor.execute("""
                    SELECT
                        ISNULL(SUM(CASE WHEN Direction = N'收入' THEN Amount ELSE 0 END), 0),
                        ISNULL(SUM(CASE WHEN Direction = N'支出' THEN Amount ELSE 0 END), 0)
                    FROM CashFlow
                    WHERE FORMAT(TransactionDate, 'yyyy-MM') = ?
                """, (ym,))
                month_row = cursor.fetchone()
                income_data.append(float(month_row[0]))
                expense_data.append(float(month_row[1]))

            cursor.execute("""
                SELECT TOP 5
                    cf.Direction, cf.Amount, et.ExpenseTypeName,
                    cf.TransactionDate, cf.Description
                FROM CashFlow cf
                LEFT JOIN ExpenseType et ON cf.ExpenseTypeID = et.ExpenseTypeID
                ORDER BY cf.TransactionDate DESC, cf.CashFlowID DESC
            """)
            recent_rows = cursor.fetchall()
            recent_activities = []
            for row in recent_rows:
                recent_activities.append({
                    'direction': row[0],
                    'amount': float(row[1]),
                    'item': row[2] or '',
                    'date': row[3].strftime('%m-%d %H:%M') if row[3] else '',
                    'desc': row[4] or ''
                })

            cursor.execute("""
                SELECT TOP 5 r.ReceivableID, r.Amount, r.RemainingAmount,
                             r.DueDate, r.Description, m.MerchantName
                FROM Receivable r
                LEFT JOIN Merchant m ON r.MerchantID = m.MerchantID
                WHERE r.Status IN (N'未付款', N'部分付款')
                  AND r.DueDate IS NOT NULL
                  AND r.DueDate < CAST(GETDATE() AS DATE)
                  AND r.IsActive = 1
                ORDER BY r.DueDate ASC
            """)
            overdue_rows = cursor.fetchall()
            overdue_items = []
            for row in overdue_rows:
                overdue_items.append({
                    'id': row[0],
                    'total': float(row[1]),
                    'remaining': float(row[2]),
                    'due_date': row[3].strftime('%Y-%m-%d') if row[3] else '',
                    'desc': row[4] or '',
                    'customer': row[5] or ''
                })

            cursor.execute("""
                SELECT TOP 5 c.ContractID, c.ContractNumber, m.MerchantName, c.EndDate, c.Status
                FROM Contract c
                LEFT JOIN Merchant m ON c.MerchantID = m.MerchantID
                WHERE c.Status = N'生效'
                  AND c.EndDate BETWEEN CAST(GETDATE() AS DATE)
                                  AND DATEADD(DAY, 30, CAST(GETDATE() AS DATE))
                ORDER BY c.EndDate ASC
            """)
            contract_rows = cursor.fetchall()
            expiring_contracts = []
            for row in contract_rows:
                expiring_contracts.append({
                    'id': row[0],
                    'number': row[1],
                    'merchant': row[2],
                    'end_date': row[3].strftime('%Y-%m-%d') if row[3] else '',
                    'status': row[4]
                })

            cursor.execute("""
                SELECT
                    COUNT(*) as total,
                    ISNULL(SUM(CASE WHEN Status = N'已出租' THEN 1 ELSE 0 END), 0) as rented,
                    ISNULL(SUM(CASE WHEN Status != N'已出租' OR Status IS NULL THEN 1 ELSE 0 END), 0) as available
                FROM Plot
            """)
            plot_row = cursor.fetchone()
            plot_total = int(plot_row[0])
            plot_rented = int(plot_row[1])
            plot_available = int(plot_row[2])

            cursor.execute("""
                SELECT
                    ISNULL(PlotType, N'未分类') as PlotType,
                    ISNULL(SUM(Area), 0) as total_area,
                    ISNULL(SUM(CASE WHEN Status = N'已出租' THEN Area ELSE 0 END), 0) as rented_area,
                    ISNULL(SUM(CASE WHEN Status != N'已出租' OR Status IS NULL THEN Area ELSE 0 END), 0) as available_area
                FROM Plot
                GROUP BY PlotType
            """)
            plot_type_rows = cursor.fetchall()
            plot_types = []
            type_map = {'水泥地皮': 'cement', '钢结构厂房': 'steel', '砖混厂房': 'brick', '未分类': 'other'}
            for row in plot_type_rows:
                plot_types.append({
                    'name': row[0],
                    'key': type_map.get(row[0], 'other'),
                    'total_area': float(row[1]),
                    'rented_area': float(row[2]),
                    'available_area': float(row[3])
                })

            cursor.execute("""
                SELECT TOP 1 BelongMonth
                FROM UtilityReading
                WHERE MeterType = 'electricity'
                ORDER BY BelongMonth DESC
            """)
            latest_month_row = cursor.fetchone()
            latest_month = latest_month_row[0] if latest_month_row else None

            electricity_total_usage = 0
            electricity_total_amount = 0
            if latest_month:
                cursor.execute("""
                    SELECT
                        ISNULL(SUM([Usage]), 0),
                        ISNULL(SUM(TotalAmount), 0)
                    FROM UtilityReading
                    WHERE BelongMonth = ?
                      AND MeterType = 'electricity'
                """, (latest_month,))
                elec_row = cursor.fetchone()
                electricity_total_usage = float(elec_row[0])
                electricity_total_amount = float(elec_row[1])

            cursor.execute("""
                SELECT
                    COUNT(*),
                    ISNULL(SUM(NetWeight), 0),
                    ISNULL(SUM(ScaleFee), 0)
                FROM ScaleRecord
                WHERE CAST(ScaleTime AS DATE) = ?
            """, (today,))
            scale_row = cursor.fetchone()
            scale_vehicles = int(scale_row[0])
            scale_weight = float(scale_row[1])
            scale_fee = float(scale_row[2])

            return {
                'receivable': {
                    'unpaid': receivable_unpaid,
                    'partial': receivable_partial,
                    'collected': receivable_collected,
                    'unpaid_count': unpaid_count,
                    'partial_count': partial_count
                },
                'payable': {
                    'unpaid': payable_unpaid,
                    'paid': payable_paid
                },
                'today': {
                    'income': today_income,
                    'expense': today_expense,
                    'net': today_income - today_expense
                },
                'merchant': {
                    'active_count': active_contracts,
                    'rented_plots': rented_plots,
                    'total_plots': total_plots,
                    'vacancy_rate': vacancy_rate
                },
                'chart': {
                    'months': months,
                    'income': income_data,
                    'expense': expense_data
                },
                'recent_activities': recent_activities,
                'overdue_items': overdue_items,
                'expiring_contracts': expiring_contracts,
                'plot': {
                    'total': plot_total,
                    'rented': plot_rented,
                    'available': plot_available,
                    'types': plot_types
                },
                'electricity': {
                    'latest_month': latest_month or '',
                    'total_usage': electricity_total_usage,
                    'total_amount': electricity_total_amount
                },
                'scale': {
                    'vehicles': scale_vehicles,
                    'weight': scale_weight,
                    'fee': scale_fee
                }
            }
