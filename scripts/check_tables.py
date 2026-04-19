# -*- coding: utf-8 -*-
"""检查数据库表是否存在"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env'))

from app import create_app
from config import DevelopmentConfig
app = create_app(DevelopmentConfig)

with app.app_context():
    from utils.database import DBConnection
    with DBConnection() as conn:
        cursor = conn.cursor()
        
        # 检查关键表是否存在
        tables_to_check = ['CollectionRecord', 'PrepaymentApply', 'DepositTransfer', 'Receivable']
        for t in tables_to_check:
            cursor.execute("""
                SELECT COUNT(*) FROM INFORMATION_SCHEMA.TABLES 
                WHERE TABLE_NAME = ?
            """, (t,))
            exists = cursor.fetchone()[0]
            print(f"Table {t}: {'EXISTS' if exists else 'NOT FOUND'}")
        
        # 检查 Receivable 表的 IsActive 字段值
        cursor.execute("SELECT TOP 3 ReceivableID, Status, IsActive FROM Receivable ORDER BY ReceivableID DESC")
        rows = cursor.fetchall()
        for r in rows:
            print(f"  ReceivableID={r.ReceivableID}, Status={r.Status}, IsActive={r.IsActive} (type={type(r.IsActive).__name__})")
        
        # 检查 PrepaymentApply 表的列
        cursor.execute("""
            SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS 
            WHERE TABLE_NAME = 'PrepaymentApply'
        """)
        cols = [r[0] for r in cursor.fetchall()]
        print(f"PrepaymentApply columns: {cols}")
