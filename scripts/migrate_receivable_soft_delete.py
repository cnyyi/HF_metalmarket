# -*- coding: utf-8 -*-
"""迁移脚本：Receivable表新增软删除字段"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.database import DBConnection

def run():
    with DBConnection() as conn:
        cursor = conn.cursor()

        # 检查现有列
        cursor.execute("""
            SELECT name FROM sys.columns 
            WHERE object_id = OBJECT_ID('Receivable')
        """)
        existing = [row[0] for row in cursor.fetchall()]
        print(f"Receivable 现有列: {existing}")

        # IsActive
        if 'IsActive' not in existing:
            cursor.execute("ALTER TABLE Receivable ADD IsActive BIT NOT NULL DEFAULT 1")
            print("Added IsActive")
        else:
            print("IsActive already exists")

        # DeletedBy
        if 'DeletedBy' not in existing:
            cursor.execute("ALTER TABLE Receivable ADD DeletedBy INT NULL")
            print("Added DeletedBy")
        else:
            print("DeletedBy already exists")

        # DeletedAt
        if 'DeletedAt' not in existing:
            cursor.execute("ALTER TABLE Receivable ADD DeletedAt DATETIME NULL")
            print("Added DeletedAt")
        else:
            print("DeletedAt already exists")

        # DeleteReason
        if 'DeleteReason' not in existing:
            cursor.execute("ALTER TABLE Receivable ADD DeleteReason NVARCHAR(500) NULL")
            print("Added DeleteReason")
        else:
            print("DeleteReason already exists")

        conn.commit()
        print("Migration complete!")

if __name__ == '__main__':
    import os
    from dotenv import load_dotenv
    load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env'))
    from app import create_app
    from config import DevelopmentConfig
    app = create_app(DevelopmentConfig)
    with app.app_context():
        run()
