"""
迁移脚本：给 ContractElectricityMeter 和 ContractWaterMeter 表添加 Status 字段
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.database import DBConnection


def run_migration():
    with DBConnection() as conn:
        cursor = conn.cursor()

        # 1. ContractElectricityMeter 添加 Status 字段
        cursor.execute("""
            IF NOT EXISTS (SELECT * FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = 'ContractElectricityMeter' AND COLUMN_NAME = 'Status')
            ALTER TABLE [ContractElectricityMeter] ADD [Status] NVARCHAR(20) DEFAULT N'启用'
        """)
        print('[OK] ContractElectricityMeter.Status 字段检查/添加完成')

        # 2. ContractWaterMeter 添加 Status 字段
        cursor.execute("""
            IF NOT EXISTS (SELECT * FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = 'ContractWaterMeter' AND COLUMN_NAME = 'Status')
            ALTER TABLE [ContractWaterMeter] ADD [Status] NVARCHAR(20) DEFAULT N'启用'
        """)
        print('[OK] ContractWaterMeter.Status 字段检查/添加完成')

        # 3. 回填历史数据
        cursor.execute("UPDATE [ContractElectricityMeter] SET [Status] = N'启用' WHERE [Status] IS NULL")
        cursor.execute("UPDATE [ContractWaterMeter] SET [Status] = N'启用' WHERE [Status] IS NULL")
        print('[OK] 历史数据回填完成')

        conn.commit()
        print('\n迁移完成！')


if __name__ == '__main__':
    from app import create_app
    from config.development import DevelopmentConfig
    app = create_app(DevelopmentConfig)
    with app.app_context():
        run_migration()
