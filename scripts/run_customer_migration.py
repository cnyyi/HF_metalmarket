"""执行客户表迁移脚本"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.database import DBConnection


def run_migration():
    with DBConnection() as conn:
        cursor = conn.cursor()

        # 1. 创建 Customer 表
        cursor.execute("""
            IF NOT EXISTS (SELECT * FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME = 'Customer')
            CREATE TABLE [Customer] (
                CustomerID INT PRIMARY KEY IDENTITY(1,1),
                CustomerName NVARCHAR(100) NOT NULL,
                ShortName NVARCHAR(50) NULL,
                ContactPerson NVARCHAR(50) NULL,
                Phone NVARCHAR(20) NULL,
                Address NVARCHAR(200) NULL,
                CustomerType NVARCHAR(50) NULL,
                BusinessScope NVARCHAR(200) NULL,
                TaxNumber NVARCHAR(100) NULL,
                Description NVARCHAR(500) NULL,
                Status NVARCHAR(50) DEFAULT N'正常',
                CreateTime DATETIME DEFAULT GETDATE(),
                UpdateTime DATETIME NULL
            )
        """)
        print('[OK] Customer 表检查/创建完成')

        # 2. Receivable 新增字段
        cursor.execute("""
            IF NOT EXISTS (SELECT * FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = 'Receivable' AND COLUMN_NAME = 'CustomerType')
            ALTER TABLE [Receivable] ADD CustomerType NVARCHAR(20) NULL
        """)
        cursor.execute("""
            IF NOT EXISTS (SELECT * FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = 'Receivable' AND COLUMN_NAME = 'CustomerID')
            ALTER TABLE [Receivable] ADD CustomerID INT NULL
        """)
        print('[OK] Receivable 字段添加完成')

        # 3. Payable 新增字段
        cursor.execute("""
            IF NOT EXISTS (SELECT * FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = 'Payable' AND COLUMN_NAME = 'CustomerType')
            ALTER TABLE [Payable] ADD CustomerType NVARCHAR(20) NULL
        """)
        cursor.execute("""
            IF NOT EXISTS (SELECT * FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = 'Payable' AND COLUMN_NAME = 'CustomerID')
            ALTER TABLE [Payable] ADD CustomerID INT NULL
        """)
        print('[OK] Payable 字段添加完成')

        # 4. CollectionRecord 新增字段
        cursor.execute("""
            IF NOT EXISTS (SELECT * FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = 'CollectionRecord' AND COLUMN_NAME = 'CustomerType')
            ALTER TABLE [CollectionRecord] ADD CustomerType NVARCHAR(20) NULL
        """)
        print('[OK] CollectionRecord 字段添加完成')

        # 5. PaymentRecord 新增字段
        cursor.execute("""
            IF NOT EXISTS (SELECT * FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = 'PaymentRecord' AND COLUMN_NAME = 'CustomerType')
            ALTER TABLE [PaymentRecord] ADD CustomerType NVARCHAR(20) NULL
        """)
        print('[OK] PaymentRecord 字段添加完成')

        # 6. 回填历史数据
        cursor.execute("UPDATE [Receivable] SET CustomerType = 'Merchant', CustomerID = MerchantID WHERE CustomerType IS NULL AND MerchantID IS NOT NULL")
        cursor.execute("UPDATE [Payable] SET CustomerType = 'Merchant' WHERE CustomerType IS NULL AND VendorName IS NOT NULL")
        cursor.execute("UPDATE [CollectionRecord] SET CustomerType = 'Merchant' WHERE CustomerType IS NULL AND MerchantID IS NOT NULL")
        cursor.execute("UPDATE [PaymentRecord] SET CustomerType = 'Merchant' WHERE CustomerType IS NULL")
        print('[OK] 历史数据回填完成')

        conn.commit()
        print('\n迁移完成！')


if __name__ == '__main__':
    from app import create_app
    from config.development import DevelopmentConfig
    app = create_app(DevelopmentConfig)
    with app.app_context():
        run_migration()
