# -*- coding: utf-8 -*-
"""
合同管理服务
"""
import logging
from utils.database import DBConnection
from datetime import datetime
import re

logger = logging.getLogger(__name__)

RENT_EXPENSE_DICT_CODE = 'rent'
RENT_EXPENSE_DICT_NAME = '租金'
RENT_EXPENSE_DICT_TYPE = 'expense_item_income'


def _get_rent_expense_type_id(cursor):
    expense_type_id = None

    cursor.execute("""
        SELECT DictID FROM Sys_Dictionary
        WHERE DictType = ? AND DictCode = ? AND IsActive = 1
    """, (RENT_EXPENSE_DICT_TYPE, RENT_EXPENSE_DICT_CODE))
    row = cursor.fetchone()
    if row:
        return row.DictID

    cursor.execute("""
        SELECT DictID FROM Sys_Dictionary
        WHERE DictType = ? AND DictName = ? AND IsActive = 1
    """, (RENT_EXPENSE_DICT_TYPE, RENT_EXPENSE_DICT_NAME))
    row = cursor.fetchone()
    if row:
        return row.DictID

    try:
        cursor.execute(
            "SELECT ExpenseTypeID FROM ExpenseType WHERE ExpenseTypeCode = ? AND IsActive = 1",
            (RENT_EXPENSE_DICT_CODE,)
        )
        row = cursor.fetchone()
        if row:
            expense_type_id = row.ExpenseTypeID
    except Exception:
        pass

    return expense_type_id


class ContractService:
    @staticmethod
    def get_contract_periods():
        """
        获取合同期年列表
        """
        with DBConnection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT DictName
                FROM Sys_Dictionary
                WHERE DictType = N'contract_period'
                ORDER BY SortOrder
            """)
            
            periods = [r.DictName for r in cursor.fetchall()]
        
        return periods

    @staticmethod
    def get_available_merchants(period):
        """
        获取商户列表（允许同一商户多合同，标注已有合同信息）
        """
        with DBConnection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT m.MerchantID, m.MerchantName,
                       CASE WHEN c.ContractID IS NOT NULL THEN 1 ELSE 0 END AS HasContract,
                       ISNULL(c.ContractCount, 0) AS ContractCount
                FROM Merchant m
                LEFT JOIN (
                    SELECT MerchantID, MIN(ContractID) AS ContractID, COUNT(*) AS ContractCount
                    FROM Contract
                    WHERE ContractPeriod = ?
                    GROUP BY MerchantID
                ) c ON m.MerchantID = c.MerchantID
                ORDER BY m.MerchantName
            """, (period,))
            
            merchants = [{
                'merchant_id': r.MerchantID,
                'merchant_name': r.MerchantName,
                'has_contract': bool(r.HasContract),
                'contract_count': r.ContractCount
            } for r in cursor.fetchall()]
        
        return merchants

    @staticmethod
    def get_available_plots(period):
        """
        获取可用地块列表（排除已有活跃合同关联的地块）
        """
        with DBConnection() as conn:
            cursor = conn.cursor()
            
            # 查询可用地块，排除已被占用（结束日期 > 当前日期 -1 个月）的地块
            cursor.execute("""
                SELECT p.PlotID, p.PlotNumber, p.PlotName, p.Area, p.UnitPrice, p.MonthlyRent, p.YearlyRent, p.ImagePath
                FROM Plot p
                WHERE p.PlotID NOT IN (
                    SELECT cp.PlotID 
                    FROM ContractPlot cp
                    INNER JOIN Contract c ON cp.ContractID = c.ContractID
                    WHERE c.EndDate > DATEADD(MONTH, -1, GETDATE())
                )
                ORDER BY p.PlotNumber
            """)
            
            plots = [{
                'plot_id': r.PlotID,
                'plot_number': r.PlotNumber,
                'plot_name': r.PlotName,
                'area': float(r.Area) if r.Area else 0,
                'unit_price': float(r.UnitPrice) if r.UnitPrice else 0,
                'monthly_rent': float(r.MonthlyRent) if r.MonthlyRent else 0,
                'yearly_rent': float(r.YearlyRent) if r.YearlyRent else 0,
                'image_path': r.ImagePath
            } for r in cursor.fetchall()]
        
        return plots

    @staticmethod
    def generate_contract_number(period, merchant_id):
        """
        生成合同编号（同一商户同日多合同自动递增序号）
        """
        match = re.search(r'第(\d+)期第(\d+)年', period)
        if match:
            period_code = match.group(1) + match.group(2)
        else:
            return None
        
        date_str = datetime.now().strftime('%Y%m%d')
        merchant_id_padded = str(merchant_id).zfill(3)
        base_number = f"ZTHYHT{period_code}{date_str}{merchant_id_padded}"
        
        # 检查编号是否已存在，若存在则追加序号
        try:
            with DBConnection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT ContractNumber FROM Contract
                    WHERE ContractNumber LIKE ?
                    ORDER BY ContractNumber DESC
                """, (base_number + '%',))
                existing = cursor.fetchall()
                
                if not existing:
                    return base_number
                
                # 已有同基础编号，找最大序号
                max_seq = 0
                for row in existing:
                    num = row.ContractNumber
                    if num == base_number:
                        max_seq = max(max_seq, 1)
                    elif num.startswith(base_number + '-'):
                        try:
                            seq = int(num.split('-')[-1])
                            max_seq = max(max_seq, seq)
                        except ValueError:
                            pass
                
                return f"{base_number}-{max_seq + 1}"
        except Exception:
            return base_number

    # 允许排序的字段映射（防SQL注入）
    SORT_FIELD_MAP = {
        'contract_number': 'c.ContractNumber',
        'merchant_name': 'm.MerchantName',
        'contract_period': 'c.ContractPeriod',
        'contact_person': 'm.ContactPerson',
        'start_date': 'c.StartDate',
        'end_date': 'c.EndDate',
        'contract_amount': 'c.ActualAmount',
    }

    @staticmethod
    def get_contract_list(page, per_page, search, sort_by='create_time', sort_order='desc'):
        """
        获取合同列表（支持排序）
        """
        try:
            with DBConnection() as conn:
                cursor = conn.cursor()
                
                where_clause = "WHERE 1=1"
                params = []
                
                if search:
                    where_clause += " AND (c.ContractNumber LIKE ? OR m.MerchantName LIKE ?)"
                    search_param = f"%{search}%"
                    params.extend([search_param, search_param])
                
                # 排序字段安全映射
                order_field = ContractService.SORT_FIELD_MAP.get(sort_by, 'c.CreateTime')
                order_dir = 'DESC' if sort_order.lower() == 'desc' else 'ASC'
                
                offset = (page - 1) * per_page
                
                cursor.execute(f"SELECT COUNT(*) FROM Contract c LEFT JOIN Merchant m ON c.MerchantID = m.MerchantID {where_clause}", params)
                total = cursor.fetchone()[0]
                
                cursor.execute(f"""
                    SELECT c.ContractID, c.ContractNumber, c.ContractPeriod, c.ActualAmount as ActualAmount, m.MerchantName, m.ContactPerson,
                           c.StartDate, c.EndDate, c.Status, c.CreateTime,
                           (SELECT COUNT(*) FROM ContractPlot cp WHERE cp.ContractID = c.ContractID) as PlotCount
                    FROM Contract c
                    LEFT JOIN Merchant m ON c.MerchantID = m.MerchantID
                    {where_clause}
                    ORDER BY {order_field} {order_dir}
                    OFFSET ? ROWS FETCH NEXT ? ROWS ONLY
                """, params + [offset, per_page])
                
                contracts = []
                for r in cursor.fetchall():
                    actual_amount_val = r.ActualAmount if hasattr(r, 'ActualAmount') else (r[2] if len(r) > 2 else 0)
                    contracts.append({
                        'contract_id': r.ContractID,
                        'contract_number': r.ContractNumber,
                        'contract_period': r.ContractPeriod or '-',
                        'actual_amount': float(actual_amount_val) if actual_amount_val is not None else 0,
                        'merchant_name': r.MerchantName or '-',
                        'contact_person': r.ContactPerson or '-',
                        'plot_count': r.PlotCount,
                        'start_date': r.StartDate.strftime('%Y-%m-%d') if r.StartDate else None,
                        'end_date': r.EndDate.strftime('%Y-%m-%d') if r.EndDate else None,
                        'status': r.Status or '生效',
                        'create_time': r.CreateTime.strftime('%Y-%m-%d %H:%M:%S') if r.CreateTime else None
                    })
            
            return True, {
                'contracts': contracts,
                'total': total,
                'page': page,
                'per_page': per_page,
                'total_pages': (total + per_page - 1) // per_page
            }
        except Exception as e:
            logger.error(f"获取合同列表失败: {e}", exc_info=True)
            return False, str(e)

    @staticmethod
    def add_contract(period, merchant_id, plot_ids, start_date, end_date, rent_adjust, description):
        """
        添加合同
        """
        try:
            # 确保 rent_adjust 为数值类型
            rent_adjust = float(rent_adjust) if rent_adjust is not None else 0
            
            start_date_obj = datetime.strptime(start_date, '%Y-%m-%d')
            end_date_obj = datetime.strptime(end_date, '%Y-%m-%d')
            
            if end_date_obj <= start_date_obj:
                return False, '结束日期必须晚于开始日期'
            
            contract_number = ContractService.generate_contract_number(period, merchant_id)
            if not contract_number:
                return False, f'合同编号生成失败，period格式错误： {period}'
            
            contract_name = f"{period}-{merchant_id}号合同"
            
            with DBConnection() as conn:
                cursor = conn.cursor()
                
                total_rent = 0
                for plot_id in plot_ids:
                    cursor.execute("SELECT YearlyRent, UnitPrice, Area FROM Plot WHERE PlotID = ?", (int(plot_id),))
                    result = cursor.fetchone()
                    if result and result.YearlyRent:
                        total_rent += float(result.YearlyRent)

                cursor.execute("""
                    INSERT INTO Contract (
                        ContractNumber, ContractName, MerchantID, ContractPeriod, StartDate, EndDate,
                        ContractAmount, AmountReduction, ActualAmount, PaymentMethod, ContractPeriodYear, BusinessType, Status, Description, CreateTime
                    ) OUTPUT INSERTED.ContractID
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, GETDATE())
                """, (
                    contract_number,
                    contract_name,
                    merchant_id,
                    period,
                    start_date_obj,
                    end_date_obj,
                    total_rent,
                    rent_adjust,
                    total_rent + rent_adjust,
                    '银行转账',
                    1,
                    '租赁',
                    '生效',
                    description
                ))

                result = cursor.fetchone()
                contract_id = result[0] if result else None
                
                if not contract_id:
                    # OUTPUT INSERTED 失败时回退到 SCOPE_IDENTITY
                    try:
                        cursor.execute("SELECT CAST(SCOPE_IDENTITY() AS INT)")
                        fallback = cursor.fetchone()
                        contract_id = fallback[0] if fallback else None
                    except Exception:
                        pass
                
                logger.info(f"合同{contract_number}：contract_id={contract_id}, type={type(contract_id)}")

                if contract_id:
                    for plot_id in plot_ids:
                        cursor.execute("SELECT UnitPrice, Area FROM Plot WHERE PlotID = ?", (int(plot_id),))
                        plot_result = cursor.fetchone()
                        unit_price = float(plot_result.UnitPrice) if plot_result and plot_result.UnitPrice else 0
                        area = float(plot_result.Area) if plot_result and plot_result.Area else 0
                        monthly_price = unit_price * area
                        
                        cursor.execute("""
                            INSERT INTO ContractPlot (ContractID, PlotID, UnitPrice, Area, MonthlyPrice)
                            VALUES (?, ?, ?, ?, ?)
                        """, (contract_id, int(plot_id), unit_price, area, monthly_price))

                    actual_amount = total_rent + rent_adjust
                    logger.info(f"合同{contract_number}：total_rent={total_rent}, rent_adjust={rent_adjust}(type={type(rent_adjust)}), actual_amount={actual_amount}")
                    
                    if actual_amount > 0:
                        expense_type_id = _get_rent_expense_type_id(cursor)
                        logger.info(f"合同{contract_number}：expense_type_id={expense_type_id}")

                        if not expense_type_id:
                            logger.warning(f"合同{contract_number}：未找到租金费用类型，应收未创建")

                        if expense_type_id:
                            due_date = end_date_obj
                            recv_description = f'{period}租金'

                            cursor.execute("""
                                SELECT 1 FROM Receivable
                                WHERE ReferenceID = ? AND ReferenceType = N'contract'
                                  AND IsActive = 1
                            """, (contract_id,))
                            existing = cursor.fetchone()
                            logger.info(f"合同{contract_number}：应收已存在检查结果={existing}")
                            
                            if not existing:
                                cursor.execute("""
                                    INSERT INTO Receivable (
                                        MerchantID, ExpenseTypeID, Amount, Description,
                                        DueDate, ReferenceID, ReferenceType, Status,
                                        PaidAmount, RemainingAmount, CustomerType, CustomerID,
                                        IsActive, CreateTime
                                    ) VALUES (?, ?, ?, ?, ?, ?, ?, N'未付款', 0, ?, N'Merchant', ?, 1, GETDATE())
                                """, (
                                    merchant_id,
                                    expense_type_id,
                                    actual_amount,
                                    recv_description,
                                    due_date,
                                    contract_id,
                                    'contract',
                                    actual_amount,
                                    merchant_id
                                ))
                                logger.info(f"合同{contract_number}：联动创建应收成功，金额={actual_amount}")
                            else:
                                logger.info(f"合同{contract_number}：应收已存在，跳过创建")
                    else:
                        logger.warning(f"合同{contract_number}：actual_amount={actual_amount}<=0，跳过创建应收")
                
                conn.commit()
            
            return True, contract_number
        except Exception as e:
            logger.error(f"添加合同失败: {e}", exc_info=True)
            return False, str(e)

    @staticmethod
    def get_contract_detail(contract_id):
        """
        获取合同详情
        """
        try:
            with DBConnection() as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT c.ContractID, c.ContractNumber, c.ContractName, c.MerchantID, m.MerchantName, m.ContactPerson,
                           c.ContractPeriod, c.StartDate, c.EndDate, c.ContractAmount, c.AmountReduction,
                           c.ActualAmount, c.Status, c.Description, c.CreateTime
                    FROM Contract c
                    LEFT JOIN Merchant m ON c.MerchantID = m.MerchantID
                    WHERE c.ContractID = ?
                """, (contract_id,))
                
                row = cursor.fetchone()
                if not row:
                    return False, '合同不存在'
                
                contract = {
                    'contract_id': row.ContractID,
                    'contract_number': row.ContractNumber,
                    'contract_name': row.ContractName,
                    'merchant_id': row.MerchantID,
                    'merchant_name': row.MerchantName or '-',
                    'contact_person': row.ContactPerson or '-',
                    'contract_period': row.ContractPeriod,
                    'start_date': row.StartDate.strftime('%Y-%m-%d') if row.StartDate else None,
                    'end_date': row.EndDate.strftime('%Y-%m-%d') if row.EndDate else None,
                    'contract_amount': float(row.ContractAmount) if row.ContractAmount else 0,
                    'amount_reduction': float(row.AmountReduction) if row.AmountReduction else 0,
                    'actual_amount': float(row.ActualAmount) if row.ActualAmount else 0,
                    'status': row.Status or '生效',
                    'description': row.Description or '',
                    'create_time': row.CreateTime.strftime('%Y-%m-%d %H:%M:%S') if row.CreateTime else None
                }
                
                cursor.execute("""
                    SELECT cp.PlotID, cp.UnitPrice, cp.Area, cp.MonthlyPrice, p.PlotNumber, p.PlotName, p.YearlyRent, p.ImagePath
                    FROM ContractPlot cp
                    LEFT JOIN Plot p ON cp.PlotID = p.PlotID
                    WHERE cp.ContractID = ?
                """, (contract_id,))
                
                plots = []
                for p in cursor.fetchall():
                    plots.append({
                        'plot_id': p.PlotID,
                        'plot_number': p.PlotNumber,
                        'plot_name': p.PlotName,
                        'area': float(p.Area) if p.Area else 0,
                        'unit_price': float(p.UnitPrice) if p.UnitPrice else 0,
                        'monthly_rent': float(p.MonthlyPrice) if p.MonthlyPrice else 0,
                        'yearly_rent': float(p.YearlyRent) if p.YearlyRent else 0,
                        'image_path': p.ImagePath
                    })
                
                contract['plots'] = plots

                cursor.execute("""
                    SELECT cem.ContractMeterID, cem.MeterID, em.MeterNumber, em.InstallationLocation,
                           cem.StartReading, cem.UnitPrice, cem.Status
                    FROM ContractElectricityMeter cem
                    INNER JOIN ElectricityMeter em ON cem.MeterID = em.MeterID
                    WHERE cem.ContractID = ?
                    ORDER BY cem.ContractMeterID
                """, (contract_id,))
                electricity_meters = []
                for em in cursor.fetchall():
                    electricity_meters.append({
                        'contract_meter_id': em.ContractMeterID,
                        'meter_id': em.MeterID,
                        'meter_number': em.MeterNumber or '',
                        'installation_location': em.InstallationLocation or '',
                        'start_reading': float(em.StartReading) if em.StartReading else 0,
                        'unit_price': float(em.UnitPrice) if em.UnitPrice else 0,
                        'status': em.Status or '启用',
                    })
                contract['electricity_meters'] = electricity_meters

                cursor.execute("""
                    SELECT r.ReceivableID, r.Amount, r.PaidAmount, r.RemainingAmount,
                           r.Status, r.DueDate, r.Description
                    FROM Receivable r
                    WHERE r.ReferenceID = ? AND r.ReferenceType = N'contract' AND r.IsActive = 1
                """, (contract_id,))
                recv_rows = cursor.fetchall()

                total_receivable = 0
                total_paid = 0
                total_remaining = 0
                receivable_ids = []
                for rv in recv_rows:
                    amt = float(rv.Amount) if rv.Amount else 0
                    paid = float(rv.PaidAmount) if rv.PaidAmount else 0
                    remaining = float(rv.RemainingAmount) if rv.RemainingAmount else 0
                    total_receivable += amt
                    total_paid += paid
                    total_remaining += remaining
                    receivable_ids.append(rv.ReceivableID)

                payment_progress = round(total_paid / total_receivable * 100, 1) if total_receivable > 0 else 0

                contract['payment_progress'] = {
                    'total_receivable': round(total_receivable, 2),
                    'total_paid': round(total_paid, 2),
                    'total_remaining': round(total_remaining, 2),
                    'progress_percent': payment_progress,
                }

                collection_records = []
                if receivable_ids:
                    placeholders = ','.join(['?'] * len(receivable_ids))
                    cursor.execute(f"""
                        SELECT cr.CollectionRecordID, cr.ReceivableID, cr.Amount,
                               cr.PaymentMethod, cr.TransactionDate, cr.Description,
                               u.RealName AS OperatorName, cr.CreateTime
                        FROM CollectionRecord cr
                        LEFT JOIN [User] u ON cr.CreatedBy = u.UserID
                        WHERE cr.ReceivableID IN ({placeholders})
                        ORDER BY cr.TransactionDate DESC, cr.CreateTime DESC
                    """, *receivable_ids)
                    for cr in cursor.fetchall():
                        collection_records.append({
                            'collection_record_id': cr.CollectionRecordID,
                            'receivable_id': cr.ReceivableID,
                            'amount': float(cr.Amount) if cr.Amount else 0,
                            'payment_method': cr.PaymentMethod or '',
                            'transaction_date': cr.TransactionDate.strftime('%Y-%m-%d') if cr.TransactionDate else '',
                            'description': cr.Description or '',
                            'operator_name': cr.OperatorName or '',
                            'create_time': cr.CreateTime.strftime('%Y-%m-%d %H:%M') if cr.CreateTime else '',
                        })

                contract['collection_records'] = collection_records
            
            return True, contract
        except Exception as e:
            logger.error(f"获取合同详情失败: {e}", exc_info=True)
            return False, str(e)

    @staticmethod
    def update_contract(contract_id, start_date, end_date, rent_adjust, description, status, plot_ids):
        """
        更新合同
        """
        try:
            # 确保 rent_adjust 为数值类型
            rent_adjust = float(rent_adjust) if rent_adjust is not None else 0
            
            start_date_obj = datetime.strptime(start_date, '%Y-%m-%d')
            end_date_obj = datetime.strptime(end_date, '%Y-%m-%d')
            
            if end_date_obj <= start_date_obj:
                return False, '结束日期必须晚于开始日期'

            with DBConnection() as conn:
                cursor = conn.cursor()

                cursor.execute("SELECT ContractPeriod FROM Contract WHERE ContractID = ?", (contract_id,))
                contract_row = cursor.fetchone()
                if not contract_row:
                    return False, '合同不存在'

                total_rent = 0
                for plot_id in plot_ids:
                    cursor.execute("SELECT YearlyRent FROM Plot WHERE PlotID = ?", (int(plot_id),))
                    result = cursor.fetchone()
                    if result and result.YearlyRent:
                        total_rent += float(result.YearlyRent)

                cursor.execute("""
                    UPDATE Contract
                    SET StartDate = ?, EndDate = ?, ContractAmount = ?, AmountReduction = ?,
                        ActualAmount = ?, Description = ?, Status = ?, UpdateTime = GETDATE()
                    WHERE ContractID = ?
                """, (
                    start_date_obj,
                    end_date_obj,
                    total_rent,
                    rent_adjust,
                    total_rent + rent_adjust,
                    description,
                    status,
                    contract_id
                ))
                
                cursor.execute("DELETE FROM ContractPlot WHERE ContractID = ?", (contract_id,))
                
                for plot_id in plot_ids:
                    cursor.execute("SELECT UnitPrice, Area FROM Plot WHERE PlotID = ?", (int(plot_id),))
                    plot_result = cursor.fetchone()
                    unit_price = float(plot_result.UnitPrice) if plot_result and plot_result.UnitPrice else 0
                    area = float(plot_result.Area) if plot_result and plot_result.Area else 0
                    monthly_price = unit_price * area
                    
                    cursor.execute("""
                        INSERT INTO ContractPlot (ContractID, PlotID, UnitPrice, Area, MonthlyPrice)
                        VALUES (?, ?, ?, ?, ?)
                    """, (contract_id, int(plot_id), unit_price, area, monthly_price))

                # 同步更新关联的应收记录
                actual_amount = total_rent + rent_adjust
                expense_type_id = _get_rent_expense_type_id(cursor)
                
                # 获取商户ID（用于创建新应收）
                cursor.execute("SELECT MerchantID FROM Contract WHERE ContractID = ?", (contract_id,))
                merchant_row = cursor.fetchone()
                merchant_id = merchant_row.MerchantID if merchant_row else None
                
                cursor.execute("""
                    SELECT ReceivableID, Amount, PaidAmount FROM Receivable
                    WHERE ReferenceID = ? AND ReferenceType = N'contract' AND IsActive = 1
                """, (contract_id,))
                existing_recv = cursor.fetchone()
                
                if existing_recv and actual_amount > 0:
                    # 更新已有应收的金额和描述
                    paid = float(existing_recv.PaidAmount) if existing_recv.PaidAmount else 0
                    new_remaining = actual_amount - paid
                    cursor.execute("""
                        UPDATE Receivable
                        SET Amount = ?, RemainingAmount = ?, 
                            Description = ?, ExpenseTypeID = ?
                        WHERE ReceivableID = ?
                    """, (actual_amount, new_remaining, f'{contract_row.ContractPeriod}租金', expense_type_id, existing_recv.ReceivableID))
                    logger.info(f"合同{contract_id}更新：同步更新应收{existing_recv.ReceivableID}，金额={actual_amount}")
                elif not existing_recv and actual_amount > 0 and expense_type_id and merchant_id:
                    # 应收不存在但金额>0，创建新应收
                    cursor.execute("""
                        INSERT INTO Receivable (
                            MerchantID, ExpenseTypeID, Amount, Description,
                            DueDate, ReferenceID, ReferenceType, Status,
                            PaidAmount, RemainingAmount, CustomerType, CustomerID,
                            IsActive, CreateTime
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, N'未付款', 0, ?, N'Merchant', ?, 1, GETDATE())
                    """, (
                        merchant_id,
                        expense_type_id,
                        actual_amount,
                        f'{contract_row.ContractPeriod}租金',
                        end_date_obj,
                        contract_id,
                        'contract',
                        actual_amount,
                        merchant_id
                    ))
                    logger.info(f"合同{contract_id}更新：创建新应收，金额={actual_amount}")
                
                conn.commit()
            
            return True, '合同更新成功'
        except Exception as e:
            logger.error(f"更新合同失败: {e}", exc_info=True)
            return False, str(e)

    @staticmethod
    def delete_contract(contract_id):
        """
        删除合同
        """
        try:
            with DBConnection() as conn:
                cursor = conn.cursor()
                
                cursor.execute("DELETE FROM ContractPlot WHERE ContractID = ?", (contract_id,))
                cursor.execute("DELETE FROM Contract WHERE ContractID = ?", (contract_id,))
                
                conn.commit()
            
            return True, '删除成功'
        except Exception as e:
            logger.error(f"删除合同失败: {e}", exc_info=True)
            return False, str(e)

    def get_rent_overview():
        with DBConnection() as conn:
            cursor = conn.cursor()

            cursor.execute("""
                SELECT DictID FROM Sys_Dictionary
                WHERE DictType = ? AND DictCode = ? AND IsActive = 1
            """, (RENT_EXPENSE_DICT_TYPE, RENT_EXPENSE_DICT_CODE))
            dict_row = cursor.fetchone()
            if not dict_row:
                cursor.execute("""
                    SELECT DictID FROM Sys_Dictionary
                    WHERE DictType = ? AND DictName = ? AND IsActive = 1
                """, (RENT_EXPENSE_DICT_TYPE, RENT_EXPENSE_DICT_NAME))
                dict_row = cursor.fetchone()

            expense_type_id = dict_row.DictID if dict_row else None

            cursor.execute("""
                SELECT FORMAT(c.StartDate, N'yyyy-MM') AS Month,
                       ISNULL(SUM(r.Amount), 0) AS TotalReceivable
                FROM Receivable r
                INNER JOIN Contract c ON r.ReferenceType = N'contract' AND r.ReferenceID = c.ContractID
                WHERE r.IsActive = 1
                  AND r.ExpenseTypeID = ?
                  AND c.Status = N'生效'
                GROUP BY FORMAT(c.StartDate, N'yyyy-MM')
                ORDER BY Month
            """, (expense_type_id,))
            receivable_rows = cursor.fetchall()

            cursor.execute("""
                SELECT FORMAT(c.StartDate, N'yyyy-MM') AS Month,
                       ISNULL(SUM(cr.Amount), 0) AS TotalCollected
                FROM CollectionRecord cr
                INNER JOIN Receivable r ON cr.ReceivableID = r.ReceivableID
                INNER JOIN Contract c ON r.ReferenceType = N'contract' AND r.ReferenceID = c.ContractID
                WHERE r.IsActive = 1
                  AND r.ExpenseTypeID = ?
                  AND c.Status = N'生效'
                GROUP BY FORMAT(c.StartDate, N'yyyy-MM')
                ORDER BY Month
            """, (expense_type_id,))
            collected_rows = cursor.fetchall()

            receivable_map = {r.Month: float(r.TotalReceivable) for r in receivable_rows}
            collected_map = {r.Month: float(r.TotalCollected) for r in collected_rows}

            all_months = sorted(set(list(receivable_map.keys()) + list(collected_map.keys())))

            if not all_months:
                return {'months': [], 'receivable': [], 'collected': []}

            recent_months = all_months[-12:] if len(all_months) > 12 else all_months

            months = []
            receivable_data = []
            collected_data = []
            for m in recent_months:
                months.append(m)
                receivable_data.append(receivable_map.get(m, 0))
                collected_data.append(collected_map.get(m, 0))

            return {
                'months': months,
                'receivable': receivable_data,
                'collected': collected_data,
            }

    # ========== Agent 查询方法 ==========

    @staticmethod
    def get_expiring_contracts(days=30, merchant_id=None, source='admin'):
        with DBConnection() as conn:
            cursor = conn.cursor()
            merchant_filter = ''
            params = [days]
            if source == 'wx' and merchant_id:
                merchant_filter = "AND c.MerchantID = ?"
                params.append(merchant_id)
            cursor.execute(f"""
                SELECT TOP 500 c.ContractID, c.ContractNo, c.EndDate, c.ActualAmount,
                       c.Status, m.MerchantName
                FROM Contract c
                INNER JOIN Merchant m ON c.MerchantID = m.MerchantID
                WHERE c.EndDate >= CAST(GETDATE() AS DATE)
                  AND c.EndDate <= DATEADD(DAY, ?, CAST(GETDATE() AS DATE))
                  AND c.Status = N'生效'
                  {merchant_filter}
                ORDER BY c.EndDate
            """, params)
            rows = cursor.fetchall()
            return [{'contract_id': row.ContractID, 'contract_no': row.ContractNo,
                     'end_date': row.EndDate.strftime('%Y-%m-%d') if row.EndDate else '',
                     'actual_amount': round(float(row.ActualAmount or 0), 2),
                     'status': row.Status, 'merchant_name': row.MerchantName} for row in rows]

    @staticmethod
    def get_contract_stats(merchant_id=None, source='admin'):
        with DBConnection() as conn:
            cursor = conn.cursor()
            merchant_filter = ''
            params = []
            if source == 'wx' and merchant_id:
                merchant_filter = "WHERE MerchantID = ?"
                params = [merchant_id]
            cursor.execute(f"""
                SELECT Status, COUNT(*) AS count, SUM(ISNULL(ActualAmount, 0)) AS total_amount
                FROM Contract
                {merchant_filter}
                GROUP BY Status
            """, params)
            rows = cursor.fetchall()
            return [{'status': row.Status, 'count': row.count,
                     'total_amount': round(float(row.total_amount or 0), 2)} for row in rows]