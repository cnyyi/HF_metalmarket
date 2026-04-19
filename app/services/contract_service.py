# -*- coding: utf-8 -*-
"""
合同管理服务
"""
import logging
from utils.database import DBConnection
from datetime import datetime
import re

logger = logging.getLogger(__name__)

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
        获取可用商户列表
        """
        with DBConnection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT m.MerchantID, m.MerchantName
                FROM Merchant m
                WHERE m.MerchantID NOT IN (
                    SELECT MerchantID FROM Contract
                    WHERE ContractPeriod = ?
                )
                ORDER BY m.MerchantName
            """, (period,))
            
            merchants = [{
                'merchant_id': r.MerchantID,
                'merchant_name': r.MerchantName
            } for r in cursor.fetchall()]
        
        return merchants

    @staticmethod
    def get_available_plots(period):
        """
        获取可用地块列表
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
        生成合同编号
        """
        match = re.search(r'第(\d+)期第(\d+)年', period)
        if match:
            period_code = match.group(1) + match.group(2)
        else:
            return None
        
        date_str = datetime.now().strftime('%Y%m%d')
        merchant_id_padded = str(merchant_id).zfill(3)
        return f"ZTHYHT{period_code}{date_str}{merchant_id_padded}"

    @staticmethod
    def get_contract_list(page, per_page, search):
        """
        获取合同列表
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
                
                offset = (page - 1) * per_page
                
                cursor.execute(f"SELECT COUNT(*) FROM Contract c LEFT JOIN Merchant m ON c.MerchantID = m.MerchantID {where_clause}", params)
                total = cursor.fetchone()[0]
                
                cursor.execute(f"""
                    SELECT c.ContractID, c.ContractNumber, c.ActualAmount as ActualAmount, m.MerchantName, m.ContactPerson,
                           c.StartDate, c.EndDate, c.Status, c.CreateTime,
                           (SELECT COUNT(*) FROM ContractPlot cp WHERE cp.ContractID = c.ContractID) as PlotCount
                    FROM Contract c
                    LEFT JOIN Merchant m ON c.MerchantID = m.MerchantID
                    {where_clause}
                    ORDER BY c.CreateTime DESC
                    OFFSET ? ROWS FETCH NEXT ? ROWS ONLY
                """, params + [offset, per_page])
                
                contracts = []
                for r in cursor.fetchall():
                    actual_amount_val = r.ActualAmount if hasattr(r, 'ActualAmount') else (r[2] if len(r) > 2 else 0)
                    contracts.append({
                        'contract_id': r.ContractID,
                        'contract_number': r.ContractNumber,
                        'actual_amount': float(actual_amount_val) if actual_amount_val is not None else 0,
                        'merchant_name': r.MerchantName or '-',
                        'contact_person': r.ContactPerson or '-',
                        'plot_count': r.PlotCount,
                        'start_date': r.StartDate.strftime('%Y-%m-%d') if r.StartDate else None,
                        'end_date': r.EndDate.strftime('%Y-%m-%d') if r.EndDate else None,
                        'status': r.Status or '有效',
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
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, GETDATE())
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
                    '有效',
                    description
                ))

                cursor.execute("SELECT CAST(SCOPE_IDENTITY() AS INT)")
                result = cursor.fetchone()
                contract_id = result[0] if result else None
                
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
                    if actual_amount > 0:
                        # 优先从字典表查找租金费用类型
                        cursor.execute("""
                            SELECT DictID FROM Sys_Dictionary
                            WHERE DictType = N'expense_item_income' AND DictName = N'租金' AND IsActive = 1
                        """)
                        et_row = cursor.fetchone()
                        expense_type_id = et_row.DictID if et_row else None

                        # 兼容旧 ExpenseType 表
                        if not expense_type_id:
                            cursor.execute(
                                "SELECT ExpenseTypeID FROM ExpenseType WHERE ExpenseTypeCode = N'rent' AND IsActive = 1"
                            )
                            et_row = cursor.fetchone()
                            expense_type_id = et_row.ExpenseTypeID if et_row else None

                        if expense_type_id:
                            due_date = end_date_obj
                            description = f'{period}租金'

                            cursor.execute("""
                                SELECT 1 FROM Receivable
                                WHERE ReferenceID = ? AND ReferenceType = N'contract'
                                  AND IsActive = 1
                            """, (contract_id,))
                            if not cursor.fetchone():
                                cursor.execute("""
                                    INSERT INTO Receivable (
                                        MerchantID, ExpenseTypeID, Amount, Description,
                                        DueDate, ReferenceID, ReferenceType, Status,
                                        PaidAmount, RemainingAmount, CustomerType, CustomerID,
                                        CreateTime
                                    ) VALUES (?, ?, ?, ?, ?, ?, ?, N'未付款', 0, ?, N'Merchant', ?, GETDATE())
                                """, (
                                    merchant_id,
                                    expense_type_id,
                                    actual_amount,
                                    description,
                                    due_date,
                                    contract_id,
                                    'contract',
                                    actual_amount,
                                    merchant_id
                                ))
                
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
                    'status': row.Status or '有效',
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