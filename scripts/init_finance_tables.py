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

        tables_to_check = ['ExpenseType', 'Receivable', 'Payable', 'CashFlow', 'CollectionRecord', 'PaymentRecord']

        for table in tables_to_check:
            cursor.execute("""
                SELECT COUNT(*) FROM INFORMATION_SCHEMA.TABLES
                WHERE TABLE_NAME = ?
            """, table)
            exists = cursor.fetchone()[0]
            print(f'{table}: {"EXISTS" if exists else "NOT FOUND"}')

        if not cursor.execute("SELECT COUNT(*) FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME = ?", 'Receivable').fetchone()[0]:
            print('\nCreating Receivable table...')
            cursor.execute("""
                CREATE TABLE Receivable (
                    ReceivableID INT PRIMARY KEY IDENTITY(1,1),
                    MerchantID INT NOT NULL FOREIGN KEY REFERENCES Merchant(MerchantID),
                    ExpenseTypeID INT NOT NULL FOREIGN KEY REFERENCES ExpenseType(ExpenseTypeID),
                    Amount DECIMAL(12,2) NOT NULL,
                    Description NVARCHAR(500) NULL,
                    DueDate DATETIME NOT NULL,
                    Status NVARCHAR(50) DEFAULT N'未付款',
                    PaidAmount DECIMAL(12,2) DEFAULT 0,
                    RemainingAmount DECIMAL(12,2) NOT NULL,
                    ReferenceID INT NULL,
                    ReferenceType NVARCHAR(50) NULL,
                    CreateTime DATETIME DEFAULT GETDATE(),
                    UpdateTime DATETIME NULL
                );
            """)
            conn.commit()
            print('Receivable table created successfully!')
        else:
            print('\nReceivable table already exists.')

        if not cursor.execute("SELECT COUNT(*) FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME = ?", 'Payable').fetchone()[0]:
            print('\nCreating Payable table...')
            cursor.execute("""
                CREATE TABLE Payable (
                    PayableID INT PRIMARY KEY IDENTITY(1,1),
                    VendorName NVARCHAR(100) NOT NULL,
                    ExpenseTypeID INT NOT NULL FOREIGN KEY REFERENCES ExpenseType(ExpenseTypeID),
                    Amount DECIMAL(12,2) NOT NULL,
                    Description NVARCHAR(500) NULL,
                    DueDate DATETIME NOT NULL,
                    Status NVARCHAR(50) DEFAULT N'未付款',
                    PaidAmount DECIMAL(12,2) DEFAULT 0,
                    RemainingAmount DECIMAL(12,2) NOT NULL,
                    ReferenceID INT NULL,
                    ReferenceType NVARCHAR(50) NULL,
                    CreateTime DATETIME DEFAULT GETDATE(),
                    UpdateTime DATETIME NULL
                );
            """)
            conn.commit()
            print('Payable table created successfully!')
        else:
            print('\nPayable table already exists.')

        if not cursor.execute("SELECT COUNT(*) FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME = ?", 'CashFlow').fetchone()[0]:
            print('\nCreating CashFlow table...')
            cursor.execute("""
                CREATE TABLE CashFlow (
                    CashFlowID INT PRIMARY KEY IDENTITY(1,1),
                    Amount DECIMAL(12,2) NOT NULL,
                    Direction NVARCHAR(20) NOT NULL,
                    ExpenseTypeID INT NOT NULL FOREIGN KEY REFERENCES ExpenseType(ExpenseTypeID),
                    Description NVARCHAR(500) NULL,
                    TransactionDate DATETIME DEFAULT GETDATE(),
                    ReferenceID INT NULL,
                    ReferenceType NVARCHAR(50) NULL,
                    CreatedBy INT NOT NULL FOREIGN KEY REFERENCES [User](UserID),
                    CreateTime DATETIME DEFAULT GETDATE()
                );
            """)
            conn.commit()
            print('CashFlow table created successfully!')
        else:
            print('\nCashFlow table already exists.')

        print('\nAll finance tables checked/created.')
