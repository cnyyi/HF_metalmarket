# -*- coding: utf-8 -*-
"""
水电表服务模块
提供水电表管理、抄表、费用计算等业务逻辑
"""

from datetime import datetime, timedelta
import logging
from utils.database import DBConnection
from app.models.meter import WaterMeter, ElectricityMeter

logger = logging.getLogger(__name__)


class UtilityService:
    """水电表服务类"""
    
    # ========== 水电表管理 ==========
    
    def get_meter_list(self, meter_type='all', merchant_id=None):
        """
        获取水电表列表（旧方法，保持兼容）
        
        Args:
            meter_type: 表类型 (all/water/electricity)
            merchant_id: 商户 ID
            
        Returns:
            dict: 水电表列表
        """
        if meter_type == 'water':
            data = WaterMeter.get_all(merchant_id=merchant_id)
        elif meter_type == 'electricity':
            data = ElectricityMeter.get_all(merchant_id=merchant_id)
        else:
            water = WaterMeter.get_all(merchant_id=merchant_id)
            electricity = ElectricityMeter.get_all(merchant_id=merchant_id)
            data = water + electricity
        
        return {
            'success': True,
            'data': data
        }

    def get_reading_data(self, belong_month, meter_type=None):
        belong_month_display = belong_month.replace('-', '年') + '月'

        electricity_data = []
        water_data = []

        with DBConnection() as conn:
            cursor = conn.cursor()

            types_to_query = []
            if not meter_type or meter_type == 'electricity':
                types_to_query.append('electricity')
            if not meter_type or meter_type == 'water':
                types_to_query.append('water')

            for mtype in types_to_query:
                sql = """
                    SELECT ur.ReadingID, ur.MeterID, ur.MeterType,
                           ur.LastReading, ur.CurrentReading, ur.Usage,
                           ur.UnitPrice, ur.TotalAmount,
                           ur.ContractID, ur.MerchantID,
                           m.MerchantName,
                           CASE
                               WHEN ur.MeterType = N'electricity' THEN em.MeterNumber
                               WHEN ur.MeterType = N'water' THEN wm.MeterNumber
                           END AS MeterNumber,
                           CASE
                               WHEN ur.MeterType = N'electricity' THEN ISNULL(em.MeterMultiplier, 1)
                               WHEN ur.MeterType = N'water' THEN ISNULL(wm.MeterMultiplier, 1)
                           END AS MeterMultiplier
                    FROM UtilityReading ur
                    INNER JOIN Merchant m ON ur.MerchantID = m.MerchantID
                    LEFT JOIN ElectricityMeter em ON ur.MeterID = em.MeterID AND ur.MeterType = N'electricity'
                    LEFT JOIN WaterMeter wm ON ur.MeterID = wm.MeterID AND ur.MeterType = N'water'
                    WHERE ur.BelongMonth = ?
                      AND ur.MeterType = ?
                    ORDER BY m.MerchantName, ur.ContractID, MeterNumber
                """
                cursor.execute(sql, belong_month_display, mtype)
                rows = cursor.fetchall()

                contract_totals = {}
                for row in rows:
                    cid = row.ContractID or 0
                    if cid not in contract_totals:
                        contract_totals[cid] = 0.0
                    contract_totals[cid] += float(row.TotalAmount) if row.TotalAmount else 0.0

                items = []
                for row in rows:
                    cid = row.ContractID or 0
                    items.append({
                        'reading_id': row.ReadingID,
                        'meter_id': row.MeterID,
                        'meter_number': row.MeterNumber or '',
                        'meter_type': row.MeterType,
                        'merchant_id': row.MerchantID,
                        'merchant_name': row.MerchantName or '',
                        'contract_id': cid,
                        'last_reading': float(row.LastReading) if row.LastReading else 0.0,
                        'current_reading': float(row.CurrentReading) if row.CurrentReading else 0.0,
                        'usage': float(row.Usage) if row.Usage else 0.0,
                        'unit_price': float(row.UnitPrice) if row.UnitPrice else 0.0,
                        'total_amount': float(row.TotalAmount) if row.TotalAmount else 0.0,
                        'meter_multiplier': float(row.MeterMultiplier) if row.MeterMultiplier else 1.0,
                        'contract_total': round(contract_totals.get(cid, 0.0), 2)
                    })

                if mtype == 'electricity':
                    electricity_data = items
                else:
                    water_data = items

        return {
            'success': True,
            'data': {
                'electricity': electricity_data,
                'water': water_data
            }
        }
    
    def _delete_reading_and_receivables(self, cursor, reading_id):
        total_amount = 0.0

        cursor.execute("""
            SELECT ur.MeterType, ur.MerchantID, ur.TotalAmount, ur.BelongMonth
            FROM UtilityReading ur
            WHERE ur.ReadingID = ?
        """, (reading_id,))
        reading_row = cursor.fetchone()

        if not reading_row:
            return False

        total_amount = float(reading_row.TotalAmount) if reading_row.TotalAmount else 0.0

        # 1. 处理旧版应收：通过 ReferenceID 直接关联 (utility_reading)
        cursor.execute("""
            SELECT ReceivableID, Amount, RemainingAmount, PaidAmount
            FROM Receivable
            WHERE ReferenceID = ? AND ReferenceType = N'utility_reading'
        """, (reading_id,))
        old_receivables = cursor.fetchall()

        for rv in old_receivables:
            cursor.execute("""
                DELETE FROM ReceivableDetail WHERE ReceivableID = ?
            """, (rv.ReceivableID,))
            cursor.execute("""
                DELETE FROM Receivable WHERE ReceivableID = ?
            """, (rv.ReceivableID,))
            logger.info(f'删除旧版应收，ID: {rv.ReceivableID}')

        # 2. 处理新版合并应收：通过 ReceivableDetail 关联 (utility_reading_merged)
        cursor.execute("""
            SELECT r.ReceivableID, r.Amount, r.RemainingAmount, r.PaidAmount
            FROM Receivable r
            INNER JOIN ReceivableDetail rd ON r.ReceivableID = rd.ReceivableID
            WHERE rd.ReadingID = ?
        """, (reading_id,))
        merged_receivables = cursor.fetchall()

        for rv in merged_receivables:
            receivable_id = rv.ReceivableID
            receivable_amount = float(rv.Amount)
            remaining_amount = float(rv.RemainingAmount)
            new_amount = round(receivable_amount - total_amount, 2)
            new_remaining = round(remaining_amount - total_amount, 2)

            if new_amount <= 0:
                cursor.execute("""
                    DELETE FROM ReceivableDetail WHERE ReceivableID = ?
                """, (receivable_id,))
                cursor.execute("""
                    DELETE FROM Receivable WHERE ReceivableID = ?
                """, (receivable_id,))
                logger.info(f'删除合并应收，ID: {receivable_id}')
            else:
                cursor.execute("""
                    UPDATE Receivable SET Amount = ?, RemainingAmount = ?
                    WHERE ReceivableID = ?
                """, (new_amount, new_remaining, receivable_id))
                cursor.execute("""
                    DELETE FROM ReceivableDetail
                    WHERE ReceivableID = ? AND ReadingID = ?
                """, (receivable_id, reading_id))
                logger.info(f'更新合并应收，ID: {receivable_id}, 新金额: {new_amount}')

        # 3. 删除抄表记录
        cursor.execute("""
            DELETE FROM UtilityReading WHERE ReadingID = ?
        """, (reading_id,))

        return True

    def delete_reading(self, reading_id):
        try:
            logger.info(f'开始删除抄表记录，ID: {reading_id}')
            with DBConnection() as conn:
                cursor = conn.cursor()

                result = self._delete_reading_and_receivables(cursor, reading_id)

                if not result:
                    logger.warning(f'抄表记录不存在，ID: {reading_id}')
                    return {'success': False, 'message': '抄表记录不存在'}

                conn.commit()
                logger.info(f'删除抄表记录成功，ID: {reading_id}')
                return {'success': True, 'message': '抄表记录删除成功'}

        except Exception as e:
            logger.error(f'删除抄表记录失败，ID: {reading_id}, 错误: {str(e)}')
            return {'success': False, 'message': f'删除失败：{str(e)}'}

    def delete_readings_batch(self, reading_ids):
        try:
            if not reading_ids or len(reading_ids) == 0:
                return {'success': False, 'message': '请选择要删除的抄表记录'}

            deleted_count = 0
            with DBConnection() as conn:
                cursor = conn.cursor()

                for reading_id in reading_ids:
                    try:
                        result = self._delete_reading_and_receivables(cursor, reading_id)
                        if result:
                            deleted_count += 1
                    except Exception as e:
                        logger.error(f'删除抄表记录 {reading_id} 失败：{str(e)}')
                        continue

                conn.commit()

                return {
                    'success': True,
                    'message': f'成功删除 {deleted_count} 条抄表记录',
                    'deleted_count': deleted_count
                }

        except Exception as e:
            logger.error(f'批量删除失败：{str(e)}')
            return {'success': False, 'message': f'批量删除失败：{str(e)}'}
    
    def get_meter_list_paginated(self, meter_number='', meter_type='all', page=1, page_size=20):
        """
        获取水电表列表（分页+筛选）
        
        Args:
            meter_number: 表编号（模糊查询）
            meter_type: 表类型
            page: 页码
            page_size: 每页数量
            
        Returns:
            dict: {success, data, total, page, page_size}
        """
        try:
            with DBConnection() as conn:
                cursor = conn.cursor()
                
                # 构建WHERE条件
                where_clauses = []
                params = []
                
                if meter_number:
                    where_clauses.append("MeterNumber LIKE ?")
                    params.append(f"%{meter_number}%")
                
                if meter_type != 'all':
                    where_clauses.append("MeterType = ?")
                    params.append(meter_type)
                
                where_sql = " AND ".join(where_clauses) if where_clauses else "1=1"
                
                # 查询总数 - WaterMeter
                count_sql_water = f"SELECT COUNT(*) FROM WaterMeter WHERE {where_sql}"
                cursor.execute(count_sql_water, params)
                total_water = cursor.fetchone()[0]
                
                # 查询总数 - ElectricityMeter
                count_sql_elec = f"SELECT COUNT(*) FROM ElectricityMeter WHERE {where_sql}"
                cursor.execute(count_sql_elec, params)
                total_elec = cursor.fetchone()[0]
                
                total = total_water + total_elec
                
                # 分页查询 - WaterMeter
                offset = (page - 1) * page_size
                data_sql_water = f"""
                    SELECT MeterID, MeterNumber, MeterType, MeterMultiplier, InstallationDate, InitReading,
                           CreateTime, Status, 'water' as SourceTable
                    FROM WaterMeter
                    WHERE {where_sql}
                """

                data_sql_elec = f"""
                    SELECT MeterID, MeterNumber, MeterType, MeterMultiplier, InstallationDate, InitReading,
                           CreateTime, Status, 'electricity' as SourceTable
                    FROM ElectricityMeter
                    WHERE {where_sql}
                """
                
                # 合并查询结果
                data_sql = f"""
                    SELECT * FROM (
                        {data_sql_water}
                        UNION ALL
                        {data_sql_elec}
                    ) AS CombinedResults
                    ORDER BY CreateTime DESC
                    OFFSET ? ROWS FETCH NEXT ? ROWS ONLY
                """
                
                params_with_paging = params + params + [offset, page_size]
                cursor.execute(data_sql, params_with_paging)
                rows = cursor.fetchall()
            
            # 检查绑定状态并构建返回数据
            data = []
            for row in rows:
                meter_type_val = row.MeterType if hasattr(row, 'MeterType') else row[2]
                meter_id_val = row.MeterID if hasattr(row, 'MeterID') else row[0]
                source_table = row.SourceTable if hasattr(row, 'SourceTable') else row[8]
                
                binding_info = self._check_meter_binding(meter_id_val, source_table)
                
                installation_date = ''
                if hasattr(row, 'InstallationDate'):
                    if row.InstallationDate:
                        if hasattr(row.InstallationDate, 'strftime'):
                            installation_date = row.InstallationDate.strftime('%Y-%m-%d')
                        else:
                            installation_date = str(row.InstallationDate)
                else:
                    if row[4]:
                        if hasattr(row[4], 'strftime'):
                            installation_date = row[4].strftime('%Y-%m-%d')
                        else:
                            installation_date = str(row[4])
                
                # 处理create_time
                create_time = ''
                if hasattr(row, 'CreateTime'):
                    if row.CreateTime:
                        if hasattr(row.CreateTime, 'strftime'):
                            create_time = row.CreateTime.strftime('%Y-%m-%d')
                        else:
                            create_time = str(row.CreateTime)
                else:
                    if row[6]:
                        if hasattr(row[6], 'strftime'):
                            create_time = row[6].strftime('%Y-%m-%d')
                        else:
                            create_time = str(row[6])
                
                data.append({
                    'meter_id': row.MeterID if hasattr(row, 'MeterID') else row[0],
                    'meter_number': row.MeterNumber if hasattr(row, 'MeterNumber') else row[1],
                    'meter_type': meter_type_val,
                    'meter_multiplier': float(row.MeterMultiplier) if (hasattr(row, 'MeterMultiplier') and row.MeterMultiplier) else float(row[3]) if row[3] else 1,
                    'installation_date': installation_date,
                    'init_reading': float(row.InitReading) if (hasattr(row, 'InitReading') and row.InitReading) else float(row[5]) if row[5] else 0,
                    'create_time': create_time,
                    'status': row.Status if hasattr(row, 'Status') else row[7],
                    'is_bound': binding_info['is_bound'],
                    'merchant_name': binding_info['merchant_name'] if binding_info['is_bound'] else '未关联',
                    'binding_status': binding_info['binding_status']
                })
            
            return {
                'success': True,
                'data': data,
                'total': total,
                'page': page,
                'page_size': page_size
            }
        except Exception as e:
            return {
                'success': False,
                'message': str(e)
            }
    
    def _check_meter_binding(self, meter_id, meter_type):
        """
        检查水电表是否已绑定合同，并获取商户名称和绑定状态
        
        Args:
            meter_id: 水电表ID
            meter_type: 表类型（water/electricity）
            
        Returns:
            dict: {is_bound: bool, merchant_name: str, binding_status: str}
        """
        try:
            with DBConnection() as conn:
                cursor = conn.cursor()
                
                if meter_type == 'water':
                    cursor.execute("""
                        SELECT m.MerchantName, cwm.Status
                        FROM ContractWaterMeter cwm
                        INNER JOIN Contract c ON cwm.ContractID = c.ContractID
                        INNER JOIN Merchant m ON c.MerchantID = m.MerchantID
                        WHERE cwm.MeterID = ?
                    """, (meter_id,))
                else:
                    cursor.execute("""
                        SELECT m.MerchantName, cem.Status
                        FROM ContractElectricityMeter cem
                        INNER JOIN Contract c ON cem.ContractID = c.ContractID
                        INNER JOIN Merchant m ON c.MerchantID = m.MerchantID
                        WHERE cem.MeterID = ?
                    """, (meter_id,))
                
                row = cursor.fetchone()
                
                if row:
                    binding_status = row.Status or '启用'
                    return {
                        'is_bound': True,
                        'merchant_name': row.MerchantName or '',
                        'binding_status': binding_status
                    }
                else:
                    return {
                        'is_bound': False,
                        'merchant_name': '',
                        'binding_status': ''
                    }
        except:
            return {
                'is_bound': False,
                'merchant_name': '',
                'binding_status': ''
            }
    
    def get_valid_contracts(self):
        """
        获取有效合同列表
        有效期：起始日期 ≤ 今天 ≤ 结束日期+3个月
        """
        try:
            with DBConnection() as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT c.ContractID, c.ContractNumber, m.MerchantName,
                           c.StartDate, c.EndDate
                    FROM Contract c
                    INNER JOIN Merchant m ON c.MerchantID = m.MerchantID
                    WHERE c.StartDate <= GETDATE()
                      AND DATEADD(MONTH, 3, c.EndDate) >= GETDATE()
                    ORDER BY c.ContractNumber
                """)
                
                rows = cursor.fetchall()
            
            return {
                'success': True,
                'data': [{
                    'contract_id': r.ContractID,
                    'contract_number': r.ContractNumber,
                    'merchant_name': r.MerchantName,
                    'start_date': r.StartDate.strftime('%Y-%m-%d'),
                    'end_date': r.EndDate.strftime('%Y-%m-%d')
                } for r in rows]
            }
        except Exception as e:
            return {
                'success': False,
                'message': str(e)
            }
    
    def bind_meter_to_contract(self, meter_id, meter_type, contract_id, unit_price=0):
        """
        绑定水电表到合同
        
        Args:
            meter_id: 水电表ID
            meter_type: 表类型（water/electricity）
            contract_id: 合同ID
            unit_price: 单价（元/度 或 元/吨）
            
        Returns:
            dict: {success, message}
        """
        try:
            with DBConnection() as conn:
                cursor = conn.cursor()
                
                if meter_type == 'water':
                    cursor.execute("""
                        INSERT INTO ContractWaterMeter (ContractID, MeterID, StartReading, UnitPrice, Status)
                        VALUES (?, ?,
                            (SELECT InitReading FROM WaterMeter WHERE MeterID = ?),
                            ?, N'启用')
                    """, (contract_id, meter_id, meter_id, unit_price))
                else:
                    cursor.execute("""
                        INSERT INTO ContractElectricityMeter (ContractID, MeterID, StartReading, UnitPrice, Status)
                        VALUES (?, ?,
                            (SELECT InitReading FROM ElectricityMeter WHERE MeterID = ?),
                            ?, N'启用')
                    """, (contract_id, meter_id, meter_id, unit_price))
                
                conn.commit()
            
            return {
                'success': True,
                'message': '绑定成功'
            }
        except Exception as e:
            return {
                'success': False,
                'message': str(e)
            }
    
    def unbind_meter_from_contract(self, meter_id, meter_type):
        """
        解绑水电表
        
        Args:
            meter_id: 水电表ID
            meter_type: 表类型（water/electricity）
            
        Returns:
            dict: {success, message}
        """
        try:
            with DBConnection() as conn:
                cursor = conn.cursor()
                
                if meter_type == 'water':
                    cursor.execute("""
                        DELETE FROM ContractWaterMeter WHERE MeterID = ?
                    """, (meter_id,))
                else:
                    cursor.execute("""
                        DELETE FROM ContractElectricityMeter WHERE MeterID = ?
                    """, (meter_id,))
                
                conn.commit()
            
            return {
                'success': True,
                'message': '解绑成功'
            }
        except Exception as e:
            return {
                'success': False,
                'message': str(e)
            }
    
    def toggle_meter_binding_status(self, meter_id, meter_type, contract_id=None):
        """
        切换水电表绑定状态的启用/停用
        
        Args:
            meter_id: 水电表ID
            meter_type: 表类型（water/electricity）
            contract_id: 合同ID（可选，不传则切换该表所有绑定）
            
        Returns:
            dict: {success, message, new_status}
        """
        try:
            with DBConnection() as conn:
                cursor = conn.cursor()
                
                if meter_type == 'water':
                    link_table = 'ContractWaterMeter'
                else:
                    link_table = 'ContractElectricityMeter'
                
                # 查询当前状态
                if contract_id:
                    cursor.execute(f"""
                        SELECT Status FROM {link_table} WHERE MeterID = ? AND ContractID = ?
                    """, (meter_id, contract_id))
                else:
                    cursor.execute(f"""
                        SELECT Status FROM {link_table} WHERE MeterID = ?
                    """, (meter_id,))
                
                row = cursor.fetchone()
                if not row:
                    return {
                        'success': False,
                        'message': '未找到绑定记录'
                    }
                
                current_status = row.Status or '启用'
                new_status = '未启用' if current_status == '启用' else '启用'
                
                # 切换状态
                if contract_id:
                    cursor.execute(f"""
                        UPDATE {link_table} SET Status = ? WHERE MeterID = ? AND ContractID = ?
                    """, (new_status, meter_id, contract_id))
                else:
                    cursor.execute(f"""
                        UPDATE {link_table} SET Status = ? WHERE MeterID = ?
                    """, (new_status, meter_id))
                
                conn.commit()
                
                return {
                    'success': True,
                    'message': f'已{"停用" if new_status == "未启用" else "启用"}该电表绑定',
                    'new_status': new_status
                }
        except Exception as e:
            return {
                'success': False,
                'message': str(e)
            }
    
    def get_meter_detail(self, meter_id, meter_type):
        """
        获取水电表明细
        
        Args:
            meter_id: 表 ID
            meter_type: 表类型 (water/electricity)
            
        Returns:
            dict: 水电表明细
        """
        if meter_type == 'water':
            data = WaterMeter.get_by_id(meter_id)
        else:
            data = ElectricityMeter.get_by_id(meter_id)
        
        if data:
            return {
                'success': True,
                'data': data
            }
        return {
            'success': False,
            'message': '水电表不存在'
        }
    
    def create_meter(self, meter_type, data):
        """
        创建水电表

        Args:
            meter_type: 表类型 (water/electricity)
            data: 表数据

        Returns:
            dict: 创建结果
        """
        try:
            if self._check_meter_number_exists(data['meter_number'], meter_type):
                return {
                    'success': False,
                    'message': f'表编号 {data["meter_number"]} 已存在'
                }

            if meter_type == 'water':
                meter_id = WaterMeter.create(data)
            else:
                meter_id = ElectricityMeter.create(data)

            return {
                'success': True,
                'message': '水电表创建成功',
                'meter_id': meter_id
            }
        except Exception as e:
            return {
                'success': False,
                'message': f'创建失败：{str(e)}'
            }
    
    def update_meter(self, meter_id, meter_type, data):
        """
        更新水电表
        
        Args:
            meter_id: 表 ID
            meter_type: 表类型 (water/electricity)
            data: 表数据
            
        Returns:
            dict: 更新结果
        """
        try:
            if meter_type == 'water':
                WaterMeter.update(meter_id, data)
            else:
                ElectricityMeter.update(meter_id, data)
            
            return {
                'success': True,
                'message': '水电表更新成功'
            }
        except Exception as e:
            return {
                'success': False,
                'message': f'更新失败：{str(e)}'
            }
    
    def delete_meter(self, meter_id, meter_type):
        """
        删除水电表
        
        Args:
            meter_id: 表 ID
            meter_type: 表类型 (water/electricity)
            
        Returns:
            dict: 删除结果
        """
        try:
            # 检查是否关联了有效合同
            if meter_type == 'water':
                if WaterMeter.check_contract_link(meter_id):
                    return {
                        'success': False,
                        'message': '该水电表关联了有效合同，无法删除'
                    }
                WaterMeter.delete(meter_id)
            else:
                if ElectricityMeter.check_contract_link(meter_id):
                    return {
                        'success': False,
                        'message': '该水电表关联了有效合同，无法删除'
                    }
                ElectricityMeter.delete(meter_id)
            
            return {
                'success': True,
                'message': '水电表删除成功'
            }
        except Exception as e:
            return {
                'success': False,
                'message': f'删除失败：{str(e)}'
            }
    
    def unlink_meter(self, meter_id, meter_type):
        """
        解除水电表与合同的关联
        
        Args:
            meter_id: 表 ID
            meter_type: 表类型 (water/electricity)
            
        Returns:
            dict: 解绑结果
        """
        try:
            if meter_type == 'water':
                WaterMeter.unlink_from_contract(meter_id)
            else:
                ElectricityMeter.unlink_from_contract(meter_id)
            
            return {
                'success': True,
                'message': '解除关联成功'
            }
        except Exception as e:
            return {
                'success': False,
                'message': f'解除关联失败：{str(e)}'
            }
    
    def pay_reading(self, merchant_id, belong_month, meter_type, account_id, amount, created_by):
        """
        抄表数据快捷收费 — 走应收核销流程

        1. 根据 merchant_id + belong_month + meter_type 查找合并应收记录
        2. 调用 finance_service.collect_receivable 进行核销（5步联动）
        3. 若无应收记录，走直接记账

        Args:
            merchant_id: 商户ID
            belong_month: 所属月份（格式 "YYYY年MM月"）
            meter_type: 表类型（electricity/water）
            account_id: 收款账户ID
            amount: 交费金额
            created_by: 操作人ID

        Returns:
            dict: {success, message}
        """
        from app.services.finance_service import FinanceService
        from app.services.account_service import AccountService
        from datetime import date

        finance_svc = FinanceService()

        if amount <= 0:
            return {'success': False, 'message': '交费金额必须大于0'}

        # 查找该商户当月对应表类型的合并应收
        expense_name = '电费' if meter_type == 'electricity' else '水费'

        # 获取费用类型ID — 优先从字典表查，兼容旧 ExpenseType 表
        with DBConnection() as conn:
            cursor = conn.cursor()

            # 字典表查找
            cursor.execute("""
                SELECT DictID FROM Sys_Dictionary
                WHERE DictType = ? AND DictName = ? AND IsActive = 1
            """, ('expense_item_income', expense_name))
            dict_row = cursor.fetchone()
            expense_type_id = dict_row.DictID if dict_row else None

            if not expense_type_id:
                # 兼容旧 ExpenseType 表
                expense_code = 'electricity' if meter_type == 'electricity' else 'water'
                cursor.execute(
                    "SELECT ExpenseTypeID FROM ExpenseType WHERE ExpenseTypeCode = ? AND IsActive = 1",
                    (expense_code,)
                )
                et_row = cursor.fetchone()
                expense_type_id = et_row.ExpenseTypeID if et_row else None

            # 查找合并应收
            receivable_id = None
            if expense_type_id:
                cursor.execute("""
                    SELECT TOP 1 r.ReceivableID, r.Amount, r.RemainingAmount, r.Status
                    FROM Receivable r
                    WHERE r.MerchantID = ?
                      AND r.ExpenseTypeID = ?
                      AND r.ReferenceType = N'utility_reading_merged'
                      AND r.Description LIKE ?
                      AND r.Status IN (N'未付款', N'部分付款')
                      AND r.IsActive = 1
                    ORDER BY r.ReceivableID DESC
                """, (merchant_id, expense_type_id, f'{belong_month}{expense_name}%'))
                rv_row = cursor.fetchone()
                if rv_row:
                    receivable_id = rv_row.ReceivableID

        if receivable_id:
            # 走应收核销流程
            result = finance_svc.collect_receivable(
                receivable_id=receivable_id,
                amount=amount,
                payment_method='现金',
                transaction_date=date.today().strftime('%Y-%m-%d'),
                description=f'{belong_month}{expense_name}收费',
                created_by=created_by,
                account_id=account_id
            )
            if result.get('success'):
                result['message'] = f'收费成功，已核销应收账款'
            return result
        else:
            # 无应收记录，走直接记账
            if not expense_type_id:
                return {'success': False, 'message': f'未找到"{expense_name}"费用类型，请先配置'}

            result = finance_svc.direct_entry(
                direction='income',
                amount=amount,
                account_id=account_id,
                expense_type_id=expense_type_id,
                transaction_date=date.today().strftime('%Y-%m-%d'),
                description=f'{belong_month}{expense_name}收费（无应收记录，直接记账）',
                created_by=created_by
            )
            if result.get('success'):
                result['message'] = f'收费成功（直接记账，无关联应收）'
            return result

    def _check_meter_number_exists(self, meter_number, meter_type):
        """
        检查表编号是否存在
        
        Args:
            meter_number: 表编号
            meter_type: 表类型
            
        Returns:
            bool: 是否存在
        """
        with DBConnection() as conn:
            cursor = conn.cursor()
            
            if meter_type == 'water':
                cursor.execute("""
                    SELECT COUNT(*) FROM WaterMeter WHERE MeterNumber = ?
                """, (meter_number,))
            else:
                cursor.execute("""
                    SELECT COUNT(*) FROM ElectricityMeter WHERE MeterNumber = ?
                """, (meter_number,))
            
            count = cursor.fetchone()[0]
        
        return count > 0
    
    # ========== 抄表管理 ==========
    
    def get_meters_to_read(self, meter_type, belong_month=None):
        """
        获取待抄表列表，按所属月份过滤已抄表的记录
        
        Args:
            meter_type: 表类型 (water/electricity)
            belong_month: 所属月份 (YYYY-MM格式)，用于过滤已存在抄表数据的商户
            
        Returns:
            dict: 待抄表列表
        """
        with DBConnection() as conn:
            cursor = conn.cursor()
            
            if meter_type == 'water':
                table = 'WaterMeter'
                link_table = 'ContractWaterMeter'
            else:
                table = 'ElectricityMeter'
                link_table = 'ContractElectricityMeter'
            
            # 构建 NOT EXISTS 子查询：排除指定月份已有抄表记录的 (MeterID, ContractID) 对
            if belong_month:
                parts = belong_month.split('-')
                belong_month_display = f"{parts[0]}年{parts[1]}月"
                not_exists_sql = """
                    AND NOT EXISTS (
                        SELECT 1 FROM UtilityReading ex
                        WHERE ex.MeterID = m.MeterID
                          AND ex.ContractID = cwm.ContractID
                          AND ex.MeterType = ?
                          AND ex.BelongMonth = ?
                    )
                """
                not_exists_params = [
                    'water' if meter_type == 'water' else 'electricity',
                    belong_month_display
                ]
            else:
                not_exists_sql = ""
                not_exists_params = []
            
            # 查询有效合同关联的电表，并获取上月表底
            # 上月表底优先从 UtilityReading 中早于当前所属月份的最新记录获取
            # 若无抄表记录，则使用电表的 InitReading（初始表底）
            # 合同有效性判断：起始日期 ≤ 当前日期 ≤ (结束日期 + 3个月)
            # 注意：table/link_table 来自硬编码映射（非用户输入），安全可接受
            cursor.execute(f"""
                SELECT
                    m.MeterID,
                    m.MeterNumber,
                    m.InitReading,
                    m.MeterMultiplier,
                    cwm.ContractID,
                    cwm.UnitPrice,
                    mer.MerchantID,
                    mer.MerchantName,
                    c.ContractNumber,
                    ISNULL(
                        (SELECT TOP 1 ur2.CurrentReading
                         FROM UtilityReading ur2
                         WHERE ur2.MeterID = m.MeterID
                           AND ur2.MeterType = ?
                           AND ur2.BelongMonth < ?
                         ORDER BY ur2.ReadingDate DESC),
                        m.InitReading
                    ) as LastReading
                FROM {table} m
                INNER JOIN {link_table} cwm ON m.MeterID = cwm.MeterID
                INNER JOIN Contract c ON cwm.ContractID = c.ContractID
                INNER JOIN Merchant mer ON c.MerchantID = mer.MerchantID
                WHERE c.StartDate <= GETDATE()
                  AND DATEADD(MONTH, 3, c.EndDate) >= GETDATE()
                  AND (cwm.Status IS NULL OR cwm.Status <> N'未启用')
                  {not_exists_sql}
                ORDER BY mer.MerchantName, m.MeterNumber
            """, [
                'water' if meter_type == 'water' else 'electricity',
                belong_month_display if belong_month else '9999年99月'
            ] + not_exists_params)
            
            rows = cursor.fetchall()
        
        data = []
        for r in rows:
            data.append({
                'meter_id': r.MeterID,
                'meter_number': r.MeterNumber,
                'meter_multiplier': float(r.MeterMultiplier) if r.MeterMultiplier else 1,
                'last_reading': float(r.LastReading) if r.LastReading else 0,
                'unit_price': float(r.UnitPrice) if r.UnitPrice else 0,
                'contract_id': r.ContractID,
                'merchant_id': r.MerchantID,
                'merchant_name': r.MerchantName,
                'contract_number': r.ContractNumber
            })
        
        return {
            'success': True,
            'data': data,
            'total': len(data)
        }
    
    def submit_meter_readings(self, meter_type, readings, reading_date=None, belong_month=None):
        """
        提交抄表数据
        
        Args:
            meter_type: 表类型 (water/electricity)
            readings: 抄表数据列表
            reading_date: 抄表日期 (YYYY-MM-DD格式)，默认为当前日期
            belong_month: 所属月份 (YYYY-MM格式)，用于标识费用归属月份
            
        Returns:
            dict: 提交结果
        """
        with DBConnection() as conn:
            cursor = conn.cursor()

            belong_month_display = ''
            if belong_month:
                try:
                    parts = belong_month.split('-')
                    belong_month_display = f"{parts[0]}年{parts[1]}月"
                except (ValueError, IndexError):
                    belong_month_display = ''

            try:
                # 收集所有抄表记录信息，用于按商户合并生成应收
                inserted_readings = []  # [{merchant_id, reading_id, total_amount}, ...]

                for reading in readings:
                    meter_id = reading['meter_id']
                    current_reading = float(reading['current_reading'])

                    # 获取表信息
                    if meter_type == 'water':
                        meter_data = WaterMeter.get_by_id(meter_id)
                    else:
                        meter_data = ElectricityMeter.get_by_id(meter_id)

                    if not meter_data:
                        continue

                    # 校验读数：last_reading 需从 UtilityReading 最新记录获取，而非 get_by_id 的 init_reading
                    last_reading = self._get_last_reading(cursor, meter_id, meter_type, belong_month_display)
                    if current_reading < last_reading:
                        return {
                            'success': False,
                            'message': f'表 {meter_data["meter_number"]} 当前读数不能小于上次读数 ({last_reading})'
                        }

                    # 获取单价、合同ID和商户ID（从合同关联表 JOIN Contract）
                    if meter_type == 'water':
                        cursor.execute("""
                            SELECT cwm.UnitPrice, cwm.ContractID, c.MerchantID
                            FROM ContractWaterMeter cwm
                            INNER JOIN Contract c ON cwm.ContractID = c.ContractID
                            WHERE cwm.MeterID = ?
                        """, (meter_id,))
                    else:
                        cursor.execute("""
                            SELECT cem.UnitPrice, cem.ContractID, c.MerchantID
                            FROM ContractElectricityMeter cem
                            INNER JOIN Contract c ON cem.ContractID = c.ContractID
                            WHERE cem.MeterID = ?
                        """, (meter_id,))

                    price_row = cursor.fetchone()

                    # 未绑定合同的表不能抄表
                    if not price_row:
                        return {
                            'success': False,
                            'message': f'表 {meter_data["meter_number"]} 尚未绑定合同，请先完成合同关联后再抄表'
                        }

                    unit_price = float(price_row.UnitPrice) if price_row.UnitPrice else 0
                    contract_id = price_row.ContractID
                    merchant_id = price_row.MerchantID

                    # 计算用量和金额
                    meter_multiplier = meter_data.get('meter_multiplier', 1)
                    usage = (current_reading - last_reading) * meter_multiplier
                    total_amount = usage * unit_price

                    # 确定抄表日期和月份（Python 端处理，避免 SQL 拼接注入风险）
                    if reading_date:
                        # 使用前端传递的日期，在 Python 端格式化
                        try:
                            parsed_date = datetime.strptime(reading_date, '%Y-%m-%d')
                            actual_date = parsed_date
                            reading_month = reading_date[:7]  # yyyy-MM
                        except ValueError:
                            # 日期格式不合法时回退到当前日期
                            actual_date = datetime.now()
                            reading_month = actual_date.strftime('%Y-%m')
                    else:
                        # 使用当前日期
                        actual_date = datetime.now()
                        reading_month = actual_date.strftime('%Y-%m')

                    # 插入抄表记录（全部使用参数化查询，无 f-string SQL 拼接）
                    # 获取当前操作用户ID（由路由层从current_user注入）
                    created_by = reading.get('created_by', 0)

                    cursor.execute("""
                        INSERT INTO UtilityReading (
                            MeterID, MeterType, LastReading, CurrentReading,
                            Usage, UnitPrice, TotalAmount, ReadingDate, ReadingMonth,
                            ContractID, MerchantID, CreatedBy, BelongMonth
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        meter_id,
                        'water' if meter_type == 'water' else 'electricity',
                        last_reading,
                        current_reading,
                        usage,
                        unit_price,
                        total_amount,
                        actual_date,
                        reading_month,
                        contract_id,
                        merchant_id,
                        created_by,
                        belong_month_display
                    ))

                    # 获取新插入的记录ID
                    cursor.execute("SELECT CAST(SCOPE_IDENTITY() AS INT)")
                    reading_id = cursor.fetchone()[0]

                    # 更新表的更新时间（不再维护 LastReading/CurrentReading，抄表数据统一在 UtilityReading 中查询）
                    if meter_type == 'water':
                        cursor.execute("""
                            UPDATE WaterMeter SET
                                UpdateTime = GETDATE()
                            WHERE MeterID = ?
                        """, (meter_id,))
                    else:
                        cursor.execute("""
                            UPDATE ElectricityMeter SET
                                UpdateTime = GETDATE()
                            WHERE MeterID = ?
                        """, (meter_id,))

                    # 收集抄表记录信息，稍后按商户合并生成应收
                    inserted_readings.append({
                        'merchant_id': merchant_id,
                        'reading_id': reading_id,
                        'total_amount': total_amount
                    })

                # 按商户合并生成应收账款（同一商户同月份同费用类型只生成一条应收）
                self._create_merged_receivables(conn, cursor, inserted_readings, meter_type,
                                                belong_month_display or reading_month)

                conn.commit()

                return {
                    'success': True,
                    'message': f'成功提交 {len(readings)} 条抄表记录'
                }

            except Exception as e:
                conn.rollback()
                return {
                    'success': False,
                    'message': f'提交失败：{str(e)}'
                }
    
    def _create_merged_receivables(self, conn, cursor, inserted_readings, meter_type, reading_month):
        """
        按商户合并生成应收账款（同一商户同月份同费用类型只生成一条应收）

        逻辑：
        1. 按商户分组，汇总本次抄表金额
        2. 查找该商户当月同费用类型是否已存在合并应收
        3. 如已存在：累加金额、更新描述、补充关联明细
        4. 如不存在：新建合并应收 + 关联明细

        Args:
            conn: 数据库连接（由调用方事务提供）
            cursor: 数据库游标（由调用方事务提供）
            inserted_readings: 本次插入的抄表记录列表 [{merchant_id, reading_id, total_amount}, ...]
            meter_type: 表类型（water/electricity）
            reading_month: 抄表月份（如"2026年03月"）
        """
        try:
            if not inserted_readings:
                return

            # 获取费用类型ID（优先从字典表获取，兼容旧 ExpenseType 表）
            expense_code = 'water' if meter_type == 'water' else 'electricity'
            cursor.execute(
                "SELECT DictID FROM Sys_Dictionary WHERE DictCode = ? AND DictType = N'expense_item_income' AND IsActive = 1",
                (expense_code,)
            )
            et_row = cursor.fetchone()
            if not et_row:
                # 回退到旧表
                cursor.execute(
                    "SELECT ExpenseTypeID FROM ExpenseType WHERE ExpenseTypeCode = ? AND IsActive = 1",
                    (expense_code,)
                )
                et_row = cursor.fetchone()
            if not et_row:
                logger.warning(f'未找到费用类型: {expense_code}，跳过生成应收')
                return
            expense_type_id = et_row[0]

            # 按商户分组：合并金额、收集 reading_id 列表
            merchant_groups = {}  # {merchant_id: {'total_amount': float, 'reading_ids': [int]}}
            for item in inserted_readings:
                mid = item['merchant_id']
                if mid not in merchant_groups:
                    merchant_groups[mid] = {'total_amount': 0.0, 'reading_ids': []}
                merchant_groups[mid]['total_amount'] += item['total_amount']
                merchant_groups[mid]['reading_ids'].append(item['reading_id'])

            expense_name = '水费' if meter_type == 'water' else '电费'

            for merchant_id, group in merchant_groups.items():
                total_amount = round(group['total_amount'], 2)
                if total_amount <= 0:
                    logger.info(f'商户 {merchant_id} {expense_name}合计金额为0，跳过生成应收')
                    continue

                # 查找该商户当月同费用类型是否已存在合并应收
                # 通过 ReceivableDetail 关联 UtilityReading，匹配 BelongMonth 来判断
                cursor.execute("""
                    SELECT r.ReceivableID, r.Amount, r.RemainingAmount, r.PaidAmount
                    FROM Receivable r
                    WHERE r.MerchantID = ?
                      AND r.ExpenseTypeID = ?
                      AND r.ReferenceType = N'utility_reading_merged'
                      AND r.Description LIKE ?
                      AND r.IsActive = 1
                """, (merchant_id, expense_type_id, f'{reading_month}{expense_name}%'))
                existing = cursor.fetchone()

                if existing:
                    # ---- 更新已有应收：累加金额 ----
                    receivable_id = existing.ReceivableID
                    old_amount = float(existing.Amount)
                    new_amount = round(old_amount + total_amount, 2)
                    # RemainingAmount 也要累加（未付款部分同步增长）
                    old_remaining = float(existing.RemainingAmount)
                    new_remaining = round(old_remaining + total_amount, 2)

                    # 统计该应收下当前关联的抄表明细总数（用于更新描述）
                    cursor.execute(
                        "SELECT COUNT(*) FROM ReceivableDetail WHERE ReceivableID = ?",
                        (receivable_id,)
                    )
                    existing_detail_count = cursor.fetchone()[0]
                    new_detail_count = existing_detail_count + len(group['reading_ids'])

                    description = f'{reading_month}{expense_name}（{new_detail_count}块表）'

                    cursor.execute("""
                        UPDATE Receivable
                        SET Amount = ?, RemainingAmount = ?, Description = ?
                        WHERE ReceivableID = ?
                    """, (new_amount, new_remaining, description, receivable_id))

                    # 补充关联本次抄表明细
                    for rid in group['reading_ids']:
                        cursor.execute("""
                            IF NOT EXISTS (SELECT 1 FROM ReceivableDetail WHERE ReceivableID = ? AND ReadingID = ?)
                            BEGIN
                                INSERT INTO ReceivableDetail (ReceivableID, ReadingID) VALUES (?, ?)
                            END
                        """, (receivable_id, rid, receivable_id, rid))

                    logger.info(f'商户 {merchant_id} 更新合并应收 {receivable_id}：{expense_name}累计{new_amount}元（新增{total_amount}元），共{new_detail_count}块表')
                else:
                    # ---- 新建合并应收 ----
                    due_date = datetime.now() + timedelta(days=15)
                    description = f'{reading_month}{expense_name}（{len(group["reading_ids"])}块表）'
                    first_reading_id = group['reading_ids'][0]

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
                        total_amount,
                        description,
                        due_date,
                        first_reading_id,
                        'utility_reading_merged',
                        total_amount,
                        merchant_id
                    ))

                    receivable_id_row = cursor.execute("SELECT CAST(SCOPE_IDENTITY() AS INT)")
                    receivable_id = receivable_id_row.fetchone()[0]

                    # 为本次所有抄表记录建立关联
                    for rid in group['reading_ids']:
                        cursor.execute("""
                            IF NOT EXISTS (SELECT 1 FROM ReceivableDetail WHERE ReceivableID = ? AND ReadingID = ?)
                            BEGIN
                                INSERT INTO ReceivableDetail (ReceivableID, ReadingID) VALUES (?, ?)
                            END
                        """, (receivable_id, rid, receivable_id, rid))

                    logger.info(f'商户 {merchant_id} 生成合并应收 {receivable_id}：{expense_name}{total_amount}元，含{len(group["reading_ids"])}条抄表记录')

        except Exception as e:
            logger.error(f'合并生成应收账款失败：{str(e)}')
            raise  # re-raise 让外层 rollback

    def _create_receivable(self, conn, cursor, reading_id, meter_type, reading_month):
        """
        根据单条抄表记录生成应收账款（已弃用，保留兼容旧数据）

        旧逻辑：每条抄表记录单独生成一条应收。
        新逻辑：由 _create_merged_receivables 按商户合并生成。
        此方法仅在需要单独补录单条抄表的应收时使用。
        """
        try:
            cursor.execute("""
                SELECT 1 FROM Receivable
                WHERE ReferenceID = ? AND ReferenceType = N'utility_reading'
            """, (reading_id,))
            if cursor.fetchone():
                logger.info(f'抄表记录 {reading_id} 已生成应收账款，跳过')
                return

            if meter_type == 'water':
                join_sql = """
                    INNER JOIN ContractWaterMeter cwm ON ur.MeterID = cwm.MeterID
                """
                alias = 'cwm'
            else:
                join_sql = """
                    INNER JOIN ContractElectricityMeter cem ON ur.MeterID = cem.MeterID
                """
                alias = 'cem'

            query = f"""
                SELECT ur.ReadingID, ur.TotalAmount, ur.ReadingMonth,
                       c.ContractID, c.MerchantID
                FROM UtilityReading ur
                {join_sql}
                INNER JOIN Contract c ON {alias}.ContractID = c.ContractID
                WHERE ur.ReadingID = ?
            """
            cursor.execute(query, (reading_id,))

            row = cursor.fetchone()
            if not row:
                logger.warning(f'抄表记录 {reading_id} 未找到合同关联信息，跳过生成应收')
                return

            if not row.TotalAmount or float(row.TotalAmount) == 0:
                logger.info(f'抄表记录 {reading_id} 金额为0，跳过生成应收')
                return

            expense_code = 'water' if meter_type == 'water' else 'electricity'
            cursor.execute(
                "SELECT ExpenseTypeID FROM ExpenseType WHERE ExpenseTypeCode = ? AND IsActive = 1",
                (expense_code,)
            )
            et_row = cursor.fetchone()
            if not et_row:
                logger.warning(f'未找到费用类型: {expense_code}，跳过生成应收')
                return
            expense_type_id = et_row.ExpenseTypeID

            due_date = datetime.now() + timedelta(days=15)

            expense_name = '水费' if meter_type == 'water' else '电费'
            description = f'{reading_month or row.ReadingMonth}{expense_name}'

            cursor.execute("""
                INSERT INTO Receivable (
                    MerchantID, ExpenseTypeID, Amount, Description,
                    DueDate, ReferenceID, ReferenceType, Status,
                    PaidAmount, RemainingAmount, CustomerType, CustomerID,
                    CreateTime
                ) VALUES (?, ?, ?, ?, ?, ?, ?, N'未付款', 0, ?, N'Merchant', ?, GETDATE())
            """, (
                row.MerchantID,
                expense_type_id,
                row.TotalAmount,
                description,
                due_date,
                reading_id,
                'utility_reading',
                row.TotalAmount,
                row.MerchantID
            ))

        except Exception as e:
            logger.error(f'生成应收账款失败：{str(e)}')
    
    def _get_last_reading(self, cursor, meter_id, meter_type, belong_month=None):
        """
        获取电表/水表的上次抄表读数（从 UtilityReading 最新记录获取）
        若无抄表记录，则使用表的 InitReading（初始表底）

        Args:
            cursor: 数据库游标
            meter_id: 表ID
            meter_type: 表类型 (water/electricity)
            belong_month: 当前所属月份（格式"YYYY年MM月"），用于过滤当月及之后的记录

        Returns:
            float: 上次抄表读数
        """
        meter_type_str = 'water' if meter_type == 'water' else 'electricity'
        table = 'WaterMeter' if meter_type == 'water' else 'ElectricityMeter'

        if belong_month:
            cursor.execute(f"""
                SELECT ISNULL(
                    (SELECT TOP 1 ur2.CurrentReading
                     FROM UtilityReading ur2
                     WHERE ur2.MeterID = ?
                       AND ur2.MeterType = ?
                       AND ur2.BelongMonth < ?
                     ORDER BY ur2.ReadingDate DESC),
                    (SELECT InitReading FROM {table} WHERE MeterID = ?)
                ) as LastReading
            """, (meter_id, meter_type_str, belong_month, meter_id))
        else:
            cursor.execute(f"""
                SELECT ISNULL(
                    (SELECT TOP 1 ur2.CurrentReading
                     FROM UtilityReading ur2
                     WHERE ur2.MeterID = ?
                       AND ur2.MeterType = ?
                     ORDER BY ur2.ReadingDate DESC),
                    (SELECT InitReading FROM {table} WHERE MeterID = ?)
                ) as LastReading
            """, (meter_id, meter_type_str, meter_id))

        row = cursor.fetchone()
        return float(row.LastReading) if row and row.LastReading else 0

    # ========== 数据接口 ==========
    
    def get_merchants_list(self):
        """
        获取商户列表
        
        Returns:
            dict: 商户列表
        """
        with DBConnection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT MerchantID, MerchantName
                FROM Merchant
                WHERE Status = N'正常'
                ORDER BY MerchantName
            """)
            
            rows = cursor.fetchall()
        
        return {
            'success': True,
            'data': [{
                'merchant_id': r.MerchantID,
                'merchant_name': r.MerchantName
            } for r in rows]
        }
    
    def get_contracts_list(self):
        """
        获取可关联的合同列表（当前日期在合同有效期内的合同）
        
        Returns:
            dict: 合同列表
        """
        with DBConnection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT c.ContractID, c.ContractNumber, m.MerchantName, c.StartDate, c.EndDate
                FROM Contract c
                INNER JOIN Merchant m ON c.MerchantID = m.MerchantID
                WHERE c.StartDate <= GETDATE()
                  AND c.EndDate >= GETDATE()
                ORDER BY c.ContractNumber
            """)
            
            rows = cursor.fetchall()
        
        return {
            'success': True,
            'data': [{
                'contract_id': r.ContractID,
                'contract_number': r.ContractNumber,
                'merchant_name': r.MerchantName,
                'start_date': r.StartDate.strftime('%Y-%m-%d') if r.StartDate else '',
                'end_date': r.EndDate.strftime('%Y-%m-%d') if r.EndDate else ''
            } for r in rows]
        }
