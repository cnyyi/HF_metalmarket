"""
后台管理首页蓝图
"""
from flask import Blueprint, render_template, jsonify
from flask_login import login_required, current_user
from datetime import datetime, timedelta
from utils.database import DBConnection

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')


@admin_bp.route('/')
@login_required
def index():
    """后台管理首页"""
    current_time = datetime.now()
    return render_template('admin/index.html', current_time=current_time)


@admin_bp.route('/api/dashboard/stats')
@login_required
def dashboard_stats():
    """仪表盘统计数据API"""
    try:
        with DBConnection() as conn:
            cursor = conn.cursor()

            # 1. 应收统计
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

            # 2. 应付统计
            cursor.execute("""
                SELECT
                    ISNULL(SUM(CASE WHEN Status = N'未付款' THEN RemainingAmount ELSE 0 END), 0),
                    ISNULL(SUM(CASE WHEN Status = N'已付款' THEN Amount ELSE 0 END), 0)
                FROM Payable
            """)
            pay_row = cursor.fetchone()
            payable_unpaid = float(pay_row[0])
            payable_paid = float(pay_row[1])

            # 3. 今日收支
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

            # 4. 在租商户数（当前日期处于合同有效期内）& 空置率
            cursor.execute("""
                SELECT COUNT(DISTINCT MerchantID)
                FROM Contract
                WHERE Status = N'生效'
                  AND StartDate <= CAST(GETDATE() AS DATE)
                  AND EndDate >= CAST(GETDATE() AS DATE)
            """)
            active_merchants = int(cursor.fetchone()[0])

            cursor.execute("""
                SELECT COUNT(*) FROM Plot WHERE Status = N'已出租'
            """)
            rented_plots = int(cursor.fetchone()[0])

            cursor.execute("""
                SELECT COUNT(*) FROM Plot
            """)
            total_plots = int(cursor.fetchone()[0])
            vacancy_rate = round((1 - rented_plots / max(total_plots, 1)) * 100, 1)

            # 5. 近6个月收支柱形图
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
                m_row = cursor.fetchone()
                income_data.append(float(m_row[0]))
                expense_data.append(float(m_row[1]))

            # 6. 最近5条操作记录（收款/付款）
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
            for r in recent_rows:
                recent_activities.append({
                    'direction': r[0],
                    'amount': float(r[1]),
                    'item': r[2] or '',
                    'date': r[3].strftime('%m-%d %H:%M') if r[3] else '',
                    'desc': r[4] or ''
                })

            # 7. 逾期应收
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
            for r in overdue_rows:
                overdue_items.append({
                    'id': r[0],
                    'total': float(r[1]),
                    'remaining': float(r[2]),
                    'due_date': r[3].strftime('%Y-%m-%d') if r[3] else '',
                    'desc': r[4] or '',
                    'customer': r[5] or ''
                })

            # 8. 即将到期合同（30天内）
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
            for r in contract_rows:
                expiring_contracts.append({
                    'id': r[0],
                    'number': r[1],
                    'merchant': r[2],
                    'end_date': r[3].strftime('%Y-%m-%d') if r[3] else '',
                    'status': r[4]
                })

            # 9. 地块统计
            # 总量统计
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

            # 按类型统计面积
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
            for r in plot_type_rows:
                plot_types.append({
                    'name': r[0],
                    'key': type_map.get(r[0], 'other'),
                    'total_area': float(r[1]),
                    'rented_area': float(r[2]),
                    'available_area': float(r[3])
                })

            # 10. 最近电费统计
            # 查询 UtilityReading 表最新月份的电费数据
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

            # 11. 当日过磅统计（按 ScaleTime 过磅完成时间过滤）
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

            return jsonify({
                'success': True,
                'data': {
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
                        'active_count': active_merchants,
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
            })
    except Exception as e:
        import logging
        logging.getLogger(__name__).error(f'dashboard_stats API异常: {e}', exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
