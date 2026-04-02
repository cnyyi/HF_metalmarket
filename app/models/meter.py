# -*- coding: utf-8 -*-
"""
水电表模型模块
提供水电表相关的数据库操作
"""

import pyodbc
from datetime import datetime
from config import Config


def get_connection():
    """获取数据库连接"""
    return pyodbc.connect(Config.ODBC_CONNECTION_STRING)


class WaterMeterModel:
    """水表模型"""
    
    @staticmethod
    def get_all(merchant_id=None, meter_type=None):
        """
        获取所有水表（可筛选）
        
        Args:
            merchant_id: 商户 ID（可选）
            meter_type: 表类型（可选）
            
        Returns:
            list: 水表列表
        """
        conn = get_connection()
        cursor = conn.cursor()
        
        query = """
            SELECT 
                wm.MeterID,
                wm.MeterNumber,
                wm.MeterType,
                wm.MeterMultiplier,
                wm.InstallationLocation,
                wm.UnitPrice,
                wm.CurrentReading,
                wm.Status,
                wm.CreateTime,
                wm.UpdateTime,
                cm.ContractID,
                m.MerchantName,
                m.MerchantID
            FROM WaterMeter wm
            LEFT JOIN ContractWaterMeter cwm ON wm.MeterID = cwm.MeterID
            LEFT JOIN Contract c ON cwm.ContractID = c.ContractID
            LEFT JOIN Merchant m ON c.MerchantID = m.MerchantID
            WHERE 1=1
        """
        params = []
        
        if merchant_id:
            query += " AND m.MerchantID = ?"
            params.append(merchant_id)
        
        if meter_type:
            query += " AND wm.MeterType = ?"
            params.append(meter_type)
        
        query += " ORDER BY wm.MeterNumber"
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()
        
        return [{
            'meter_id': r.MeterID,
            'meter_number': r.MeterNumber,
            'meter_type': r.MeterType,
            'meter_multiplier': float(r.MeterMultiplier) if r.MeterMultiplier else 1,
            'installation_location': r.InstallationLocation or '',
            'unit_price': float(r.UnitPrice) if r.UnitPrice else 0,
            'current_reading': float(r.CurrentReading) if r.CurrentReading else 0,
            'status': r.Status or '正常',
            'create_time': r.CreateTime.strftime('%Y-%m-%d %H:%M:%S') if r.CreateTime else '',
            'update_time': r.UpdateTime.strftime('%Y-%m-%d %H:%M:%S') if r.UpdateTime else '',
            'contract_id': r.ContractID,
            'merchant_name': r.MerchantName or '',
            'merchant_id': r.MerchantID
        } for r in rows]
    
    @staticmethod
    def get_by_id(meter_id):
        """
        根据 ID 获取水表
        
        Args:
            meter_id: 水表 ID
            
        Returns:
            dict: 水表信息
        """
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT 
                wm.MeterID,
                wm.MeterNumber,
                wm.MeterType,
                wm.MeterMultiplier,
                wm.InstallationLocation,
                wm.UnitPrice,
                wm.LastReading,
                wm.CurrentReading,
                wm.Status,
                wm.CreateTime,
                wm.UpdateTime,
                cwm.ContractID,
                m.MerchantName,
                m.MerchantID
            FROM WaterMeter wm
            LEFT JOIN ContractWaterMeter cwm ON wm.MeterID = cwm.MeterID
            LEFT JOIN Contract c ON cwm.ContractID = c.ContractID
            LEFT JOIN Merchant m ON c.MerchantID = m.MerchantID
            WHERE wm.MeterID = ?
        """, (meter_id,))
        
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return {
                'meter_id': row.MeterID,
                'meter_number': row.MeterNumber,
                'meter_type': row.MeterType,
                'meter_multiplier': float(row.MeterMultiplier) if row.MeterMultiplier else 1,
                'installation_location': row.InstallationLocation or '',
                'unit_price': float(row.UnitPrice) if row.UnitPrice else 0,
                'last_reading': float(row.LastReading) if row.LastReading else 0,
                'current_reading': float(row.CurrentReading) if row.CurrentReading else 0,
                'status': row.Status or '正常',
                'contract_id': row.ContractID,
                'merchant_name': row.MerchantName or '',
                'merchant_id': row.MerchantID
            }
        return None
    
    @staticmethod
    def create(data):
        """
        创建水表

        Args:
            data: 水表数据字典

        Returns:
            int: 新创建的水表 ID
        """
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO WaterMeter (
                MeterNumber, MeterType, MeterMultiplier, InstallationLocation,
                UnitPrice, LastReading, CurrentReading, Status, InstallationDate
            ) OUTPUT INSERTED.MeterID
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            data['meter_number'],
            data['meter_type'],
            data.get('meter_multiplier', 1),
            data.get('installation_location', ''),
            data.get('unit_price', 0),
            data.get('last_reading', 0),
            data.get('current_reading', 0),
            data.get('status', '正常'),
            data.get('installation_date')
        ))

        meter_id = cursor.fetchone()[0]
        conn.commit()
        conn.close()

        return meter_id
    
    @staticmethod
    def update(meter_id, data):
        """
        更新水表
        
        Args:
            meter_id: 水表 ID
            data: 水表数据字典
            
        Returns:
            bool: 是否成功
        """
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE WaterMeter SET
                MeterMultiplier = ?,
                InstallationLocation = ?,
                UnitPrice = ?,
                Status = ?,
                UpdateTime = GETDATE()
            WHERE MeterID = ?
        """, (
            data.get('meter_multiplier', 1),
            data.get('installation_location', ''),
            data['unit_price'],
            data.get('status', '正常'),
            meter_id
        ))
        
        conn.commit()
        conn.close()
        
        return True
    
    @staticmethod
    def delete(meter_id):
        """
        删除水表
        
        Args:
            meter_id: 水表 ID
            
        Returns:
            bool: 是否成功
        """
        conn = get_connection()
        cursor = conn.cursor()
        
        # 先删除关联关系
        cursor.execute("DELETE FROM ContractWaterMeter WHERE MeterID = ?", (meter_id,))
        
        # 再删除水表
        cursor.execute("DELETE FROM WaterMeter WHERE MeterID = ?", (meter_id,))
        
        conn.commit()
        conn.close()
        
        return True
    
    @staticmethod
    def link_to_contract(meter_id, contract_id, start_reading=0):
        """
        关联水表到合同
        
        Args:
            meter_id: 水表 ID
            contract_id: 合同 ID
            start_reading: 起始读数
            
        Returns:
            bool: 是否成功
        """
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO ContractWaterMeter (ContractID, MeterID, StartReading)
            VALUES (?, ?, ?)
        """, (contract_id, meter_id, start_reading))
        
        conn.commit()
        conn.close()
        
        return True
    
    @staticmethod
    def unlink_from_contract(meter_id):
        """
        解除水表与合同的关联
        
        Args:
            meter_id: 水表 ID
            
        Returns:
            bool: 是否成功
        """
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute("DELETE FROM ContractWaterMeter WHERE MeterID = ?", (meter_id,))
        
        conn.commit()
        conn.close()
        
        return True
    
    @staticmethod
    def check_contract_link(meter_id):
        """
        检查水表是否关联了未完成的合同
        
        Args:
            meter_id: 水表 ID
            
        Returns:
            bool: 是否有关联
        """
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT COUNT(*) 
            FROM ContractWaterMeter cwm
            INNER JOIN Contract c ON cwm.ContractID = c.ContractID
            WHERE cwm.MeterID = ? AND c.Status = N'有效'
        """, (meter_id,))
        
        count = cursor.fetchone()[0]
        conn.close()
        
        return count > 0


class ElectricityMeterModel:
    """电表模型"""
    
    @staticmethod
    def get_all(merchant_id=None, meter_type=None):
        """
        获取所有电表（可筛选）
        
        Args:
            merchant_id: 商户 ID（可选）
            meter_type: 表类型（可选）
            
        Returns:
            list: 电表列表
        """
        conn = get_connection()
        cursor = conn.cursor()
        
        query = """
            SELECT 
                em.MeterID,
                em.MeterNumber,
                em.MeterType,
                em.MeterMultiplier,
                em.InstallationLocation,
                em.UnitPrice,
                em.CurrentReading,
                em.Status,
                em.CreateTime,
                em.UpdateTime,
                cm.ContractID,
                m.MerchantName,
                m.MerchantID
            FROM ElectricityMeter em
            LEFT JOIN ContractElectricityMeter cem ON em.MeterID = cem.MeterID
            LEFT JOIN Contract c ON cem.ContractID = c.ContractID
            LEFT JOIN Merchant m ON c.MerchantID = m.MerchantID
            WHERE 1=1
        """
        params = []
        
        if merchant_id:
            query += " AND m.MerchantID = ?"
            params.append(merchant_id)
        
        if meter_type:
            query += " AND em.MeterType = ?"
            params.append(meter_type)
        
        query += " ORDER BY em.MeterNumber"
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()
        
        return [{
            'meter_id': r.MeterID,
            'meter_number': r.MeterNumber,
            'meter_type': r.MeterType,
            'meter_multiplier': float(r.MeterMultiplier) if r.MeterMultiplier else 1,
            'installation_location': r.InstallationLocation or '',
            'unit_price': float(r.UnitPrice) if r.UnitPrice else 0,
            'current_reading': float(r.CurrentReading) if r.CurrentReading else 0,
            'status': r.Status or '正常',
            'create_time': r.CreateTime.strftime('%Y-%m-%d %H:%M:%S') if r.CreateTime else '',
            'update_time': r.UpdateTime.strftime('%Y-%m-%d %H:%M:%S') if r.UpdateTime else '',
            'contract_id': r.ContractID,
            'merchant_name': r.MerchantName or '',
            'merchant_id': r.MerchantID
        } for r in rows]
    
    @staticmethod
    def get_by_id(meter_id):
        """
        根据 ID 获取电表
        
        Args:
            meter_id: 电表 ID
            
        Returns:
            dict: 电表信息
        """
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT 
                em.MeterID,
                em.MeterNumber,
                em.MeterType,
                em.MeterMultiplier,
                em.InstallationLocation,
                em.UnitPrice,
                em.LastReading,
                em.CurrentReading,
                em.Status,
                em.CreateTime,
                em.UpdateTime,
                cem.ContractID,
                m.MerchantName,
                m.MerchantID
            FROM ElectricityMeter em
            LEFT JOIN ContractElectricityMeter cem ON em.MeterID = cem.MeterID
            LEFT JOIN Contract c ON cem.ContractID = c.ContractID
            LEFT JOIN Merchant m ON c.MerchantID = m.MerchantID
            WHERE em.MeterID = ?
        """, (meter_id,))
        
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return {
                'meter_id': row.MeterID,
                'meter_number': row.MeterNumber,
                'meter_type': row.MeterType,
                'meter_multiplier': float(row.MeterMultiplier) if row.MeterMultiplier else 1,
                'installation_location': row.InstallationLocation or '',
                'unit_price': float(row.UnitPrice) if row.UnitPrice else 0,
                'last_reading': float(row.LastReading) if row.LastReading else 0,
                'current_reading': float(row.CurrentReading) if row.CurrentReading else 0,
                'status': row.Status or '正常',
                'contract_id': row.ContractID,
                'merchant_name': row.MerchantName or '',
                'merchant_id': row.MerchantID
            }
        return None
    
    @staticmethod
    def create(data):
        """
        创建电表

        Args:
            data: 电表数据字典

        Returns:
            int: 新创建的电表 ID
        """
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO ElectricityMeter (
                MeterNumber, MeterType, MeterMultiplier, InstallationLocation,
                UnitPrice, LastReading, CurrentReading, Status, InstallationDate
            ) OUTPUT INSERTED.MeterID
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            data['meter_number'],
            data['meter_type'],
            data.get('meter_multiplier', 1),
            data.get('installation_location', ''),
            data.get('unit_price', 0),
            data.get('last_reading', 0),
            data.get('current_reading', 0),
            data.get('status', '正常'),
            data.get('installation_date')
        ))

        meter_id = cursor.fetchone()[0]
        conn.commit()
        conn.close()

        return meter_id
    
    @staticmethod
    def update(meter_id, data):
        """
        更新电表
        
        Args:
            meter_id: 电表 ID
            data: 电表数据字典
            
        Returns:
            bool: 是否成功
        """
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE ElectricityMeter SET
                MeterMultiplier = ?,
                InstallationLocation = ?,
                UnitPrice = ?,
                Status = ?,
                UpdateTime = GETDATE()
            WHERE MeterID = ?
        """, (
            data.get('meter_multiplier', 1),
            data.get('installation_location', ''),
            data['unit_price'],
            data.get('status', '正常'),
            meter_id
        ))
        
        conn.commit()
        conn.close()
        
        return True
    
    @staticmethod
    def delete(meter_id):
        """
        删除电表
        
        Args:
            meter_id: 电表 ID
            
        Returns:
            bool: 是否成功
        """
        conn = get_connection()
        cursor = conn.cursor()
        
        # 先删除关联关系
        cursor.execute("DELETE FROM ContractElectricityMeter WHERE MeterID = ?", (meter_id,))
        
        # 再删除电表
        cursor.execute("DELETE FROM ElectricityMeter WHERE MeterID = ?", (meter_id,))
        
        conn.commit()
        conn.close()
        
        return True
    
    @staticmethod
    def link_to_contract(meter_id, contract_id, start_reading=0):
        """
        关联电表到合同
        
        Args:
            meter_id: 电表 ID
            contract_id: 合同 ID
            start_reading: 起始读数
            
        Returns:
            bool: 是否成功
        """
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO ContractElectricityMeter (ContractID, MeterID, StartReading)
            VALUES (?, ?, ?)
        """, (contract_id, meter_id, start_reading))
        
        conn.commit()
        conn.close()
        
        return True
    
    @staticmethod
    def unlink_from_contract(meter_id):
        """
        解除电表与合同的关联
        
        Args:
            meter_id: 电表 ID
            
        Returns:
            bool: 是否成功
        """
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute("DELETE FROM ContractElectricityMeter WHERE MeterID = ?", (meter_id,))
        
        conn.commit()
        conn.close()
        
        return True
    
    @staticmethod
    def check_contract_link(meter_id):
        """
        检查电表是否关联了未完成的合同
        
        Args:
            meter_id: 电表 ID
            
        Returns:
            bool: 是否有关联
        """
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT COUNT(*) 
            FROM ContractElectricityMeter cem
            INNER JOIN Contract c ON cem.ContractID = c.ContractID
            WHERE cem.MeterID = ? AND c.Status = N'有效'
        """, (meter_id,))
        
        count = cursor.fetchone()[0]
        conn.close()
        
        return count > 0
