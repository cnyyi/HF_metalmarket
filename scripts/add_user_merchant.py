import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from config import DevelopmentConfig

app = create_app(DevelopmentConfig)

with app.app_context():
    from utils.database import DBConnection

    with DBConnection() as conn:
        cursor = conn.cursor()

        cursor.execute("""
            SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS
            WHERE TABLE_NAME = 'User'
            ORDER BY ORDINAL_POSITION
        """)
        cols = [r.COLUMN_NAME for r in cursor.fetchall()]
        print('User table columns:', cols)

        if 'MerchantID' not in cols:
            print('\nAdding MerchantID column to User table...')
            cursor.execute("""
                ALTER TABLE [User]
                ADD MerchantID INT NULL
            """)
            conn.commit()
            print('MerchantID column added successfully!')
        else:
            print('\nMerchantID column already exists.')
