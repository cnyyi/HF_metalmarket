# -*- coding: utf-8 -*-
"""
水电表服务模块
提供水电表管理、抄表、费用计算等业务逻辑
"""

import pyodbc
from datetime import datetime, timedelta
from config import Config
from app.models.meter import WaterMeterModel, ElectricityMeterModel


def get_connection():
    """获取数据库连接"""
    return pyodbc.connect(Config.ODBC_CONNECTION_STRING)


class UtilityService:
    """水电表服务类"""
    
    # ========== 水电表管理 ==========
    
    def get_meter_list(self, meter_type='all', merchant_id=None):
        """
        获取水电表列表
        
        Args:
            meter_type: 表类型 (all/water/electricity)
            merchant_id: 商户 ID
            
        Returns:
            dict: 水电表列表
        """
        if meter_type == 'water':
            data = WaterMeterModel.get_all(merchant_id=merchant_id)
        elif meter_type == 'electricity':
            data = ElectricityMeterModel.get_all(merchant_id=merchant_id)
        else:
            water = WaterMeterModel.get_all(merchant_id=merchant_id)
            electricity = ElectricityMeterModel.get_all(merchant_id=merchant_id)
            data = water + electricity
        
        return {
            'success': True,
            'data': data
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
            data = WaterMeterModel.get_by_id(meter_id)
        else:
            data = ElectricityMeterModel.get_by_id(meter_id)
        
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
                meter_id = WaterMeterModel.create(data)
            else:
                meter_id = ElectricityMeterModel.create(data)

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
                WaterMeterModel.update(meter_id, data)
            else:
                ElectricityMeterModel.update(meter_id, data)
            
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
                if WaterMeterModel.check_contract_link(meter_id):
                    return {
                        'success': False,
                        'message': '该水电表关联了有效合同，无法删除'
                    }
                WaterMeterModel.delete(meter_id)
            else:
                if ElectricityMeterModel.check_contract_link(meter_id):
                    return {
                        'success': False,
                        'message': '该水电表关联了有效合同，无法删除'
                    }
                ElectricityMeterModel.delete(meter_id)
            
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
                WaterMeterModel.unlink_from_contract(meter_id)
            else:
                ElectricityMeterModel.unlink_from_contract(meter_id)
            
            return {
                'success': True,
                'message': '解除关联成功'
            }
        except Exception as e:
            return {
                'success': False,
                'message': f'解除关联失败：{str(e)}'
            }
    
    def _check_meter_number_exists(self, meter_number, meter_type):
        """
        检查表编号是否存在
        
        Args:
            meter_number: 表编号
            meter_type: 表类型
            
        Returns:
            bool: 是否存在
        """
        conn = get_connection()
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
        conn.close()
        
        return count > 0
    
    # ========== 抄表管理 ==========
    
    def get_meters_to_read(self, meter_type):
        """
        获取待抄表列表
        
        Args:
            meter_type: 表类型 (water/electricity)
            
        Returns:
            dict: 待抄表列表
        """
        conn = get_connection()
        cursor = conn.cursor()
        
        # 获取当前月份
        current_month = datetime.now().strftime('%Y-%m')
        
        if meter_type == 'water':
            table = 'WaterMeter'
            link_table = 'ContractWaterMeter'
        else:
            table = 'ElectricityMeter'
            link_table = 'ContractElectricityMeter'
        
        cursor.execute(f"""
            SELECT 
                m.MeterID,
                m.MeterNumber,
                m.MeterMultiplier,
                m.UnitPrice,
                m.CurrentReading as LastReading,
                cwm.ContractID,
                mer.MerchantID,
                mer.MerchantName,
                c.ContractNumber,
                ur.ReadingID as ExistingReadingID
            FROM {table} m
            INNER JOIN {link_table} cwm ON m.MeterID = cwm.MeterID
            INNER JOIN Contract c ON cwm.ContractID = c.ContractID
            INNER JOIN Merchant mer ON c.MerchantID = mer.MerchantID
            LEFT JOIN UtilityReading ur ON m.MeterID = ur.MeterID 
                AND ur.ReadingMonth = ?
                AND ur.MeterType = ?
            WHERE c.Status = N'有效'
            ORDER BY m.MeterNumber
        """, (current_month, 'water' if meter_type == 'water' else 'electricity'))
        
        rows = cursor.fetchall()
        conn.close()
        
        data = []
        for r in rows:
            # 如果已经抄过表，跳过
            if r.ExistingReadingID:
                continue
            
            data.append({
                'meter_id': r.MeterID,
                'meter_number': r.MeterNumber,
                'meter_multiplier': float(r.MeterMultiplier) if r.MeterMultiplier else 1,
                'unit_price': float(r.UnitPrice) if r.UnitPrice else 0,
                'last_reading': float(r.LastReading) if r.LastReading else 0,
                'contract_id': r.ContractID,
                'merchant_id': r.MerchantID,
                'merchant_name': r.MerchantName,
                'contract_number': r.ContractNumber
            })
        
        return {
            'success': True,
            'data': data
        }
    
    def submit_meter_readings(self, meter_type, readings):
        """
        提交抄表数据
        
        Args:
            meter_type: 表类型 (water/electricity)
            readings: 抄表数据列表
            
        Returns:
            dict: 提交结果
        """
        conn = get_connection()
        cursor = conn.cursor()
        
        try:
            for reading in readings:
                meter_id = reading['meter_id']
                current_reading = float(reading['current_reading'])
                
                # 获取表信息
                if meter_type == 'water':
                    meter_data = WaterMeterModel.get_by_id(meter_id)
                else:
                    meter_data = ElectricityMeterModel.get_by_id(meter_id)
                
                if not meter_data:
                    continue
                
                # 校验读数
                last_reading = meter_data['last_reading']
                if current_reading < last_reading:
                    return {
                        'success': False,
                        'message': f'表 {meter_data["meter_number"]} 当前读数不能小于上次读数 ({last_reading})'
                    }
                
                # 计算用量和金额
                meter_multiplier = meter_data['meter_multiplier']
                unit_price = meter_data['unit_price']
                
                usage = (current_reading - last_reading) * meter_multiplier
                total_amount = usage * unit_price
                
                # 插入抄表记录
                cursor.execute("""
                    INSERT INTO UtilityReading (
                        MeterID, MeterType, LastReading, CurrentReading,
                        Usage, UnitPrice, TotalAmount, ReadingDate, ReadingMonth
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, GETDATE(), FORMAT(GETDATE(), 'yyyy-MM'))
                    OUTPUT INSERTED.ReadingID
                """, (
                    meter_id,
                    'water' if meter_type == 'water' else 'electricity',
                    last_reading,
                    current_reading,
                    usage,
                    unit_price,
                    total_amount
                ))
                
                reading_id = cursor.fetchone()[0]
                
                # 更新表的当前读数
                if meter_type == 'water':
                    cursor.execute("""
                        UPDATE WaterMeter SET 
                            LastReading = CurrentReading,
                            CurrentReading = ?,
                            UpdateTime = GETDATE()
                        WHERE MeterID = ?
                    """, (current_reading, meter_id))
                else:
                    cursor.execute("""
                        UPDATE ElectricityMeter SET 
                            LastReading = CurrentReading,
                            CurrentReading = ?,
                            UpdateTime = GETDATE()
                        WHERE MeterID = ?
                    """, (current_reading, meter_id))
                
                # 生成应收账款
                self._create_receivable(reading_id, meter_type, meter_data)
            
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
        finally:
            conn.close()
    
    def _create_receivable(self, reading_id, meter_type, meter_data):
        """
        根据抄表记录生成应收账款
        
        Args:
            reading_id: 抄表记录 ID
            meter_type: 表类型
            meter_data: 表数据
        """
        conn = get_connection()
        cursor = conn.cursor()
        
        try:
            # 获取抄表记录
            cursor.execute("""
                SELECT ur.ReadingID, ur.TotalAmount, ur.ReadingMonth,
                       cwm.ContractID, c.MerchantID
                FROM UtilityReading ur
                INNER JOIN ContractWaterMeter cwm ON ur.MeterID = cwm.MeterID
                INNER JOIN Contract c ON cwm.ContractID = c.ContractID
                WHERE ur.ReadingID = ?
            """, (reading_id,))
            
            row = cursor.fetchone()
            if not row:
                return
            
            # 生成应收账款
            expense_type = '水费' if meter_type == 'water' else '电费'
            due_date = datetime.now() + timedelta(days=15)
            
            cursor.execute("""
                INSERT INTO Receivable (
                    MerchantID, ExpenseTypeID, Amount, Description,
                    DueDate, ReferenceID, ReferenceType, Status, CreateTime
                ) VALUES (?, ?, ?, ?, ?, ?, ?, N'未付款', GETDATE())
            """, (
                row.MerchantID,
                expense_type,
                row.TotalAmount,
                f'{row.ReadingMonth}{expense_type}',
                due_date,
                reading_id,
                'utility_reading'
            ))
            
        except Exception as e:
            # 记录错误但不抛出，避免影响抄表
            print(f'生成应收账款失败：{str(e)}')
    
    # ========== 数据接口 ==========
    
    def get_merchants_list(self):
        """
        获取商户列表
        
        Returns:
            dict: 商户列表
        """
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT MerchantID, MerchantName
            FROM Merchant
            WHERE Status = N'正常'
            ORDER BY MerchantName
        """)
        
        rows = cursor.fetchall()
        conn.close()
        
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
        conn = get_connection()
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
        conn.close()
        
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
