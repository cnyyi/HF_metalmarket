# 数据库初始化脚本
import os
import sys

# 将项目根目录添加到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pyodbc
from config import Config


class DatabaseInitializer:
    """
    数据库初始化类，用于创建数据库和表结构
    """
    
    def __init__(self):
        # 从配置中获取数据库连接信息
        self.connection_string = Config.ODBC_CONNECTION_STRING
        
        # 解析连接字符串，获取服务器、用户名、密码等信息
        self.server = None
        self.database = None
        self.username = None
        self.password = None
        self._parse_connection_string()
    
    def _parse_connection_string(self):
        """
        解析连接字符串，获取服务器、数据库、用户名、密码等信息
        """
        parts = self.connection_string.split(';')
        for part in parts:
            if not part:
                continue
                
            key, value = part.split('=', 1)
            key = key.strip().upper()
            value = value.strip()
            
            if key == 'SERVER':
                self.server = value
            elif key == 'DATABASE':
                self.database = value
            elif key == 'UID':
                self.username = value
            elif key == 'PWD':
                self.password = value
    
    def create_database(self):
        """
        创建数据库
        """
        # 连接到master数据库
        master_conn_str = (
            f'DRIVER={{ODBC Driver 17 for SQL Server}};'
            f'SERVER={self.server};'
            f'DATABASE=master;'
            f'UID={self.username};'
            f'PWD={self.password};'
            f'Encrypt=no;'
            f'TrustServerCertificate=yes;'
        )
        
        try:
            with pyodbc.connect(master_conn_str) as conn:
                conn.autocommit = True
                with conn.cursor() as cursor:
                    # 检查数据库是否已存在
                    cursor.execute(f"SELECT name FROM sys.databases WHERE name = '{self.database}'")
                    if not cursor.fetchone():
                        # 创建数据库
                        print(f"正在创建数据库: {self.database}")
                        cursor.execute(f"CREATE DATABASE {self.database}")
                        print(f"数据库 {self.database} 创建成功")
                    else:
                        print(f"数据库 {self.database} 已存在")
        except Exception as e:
            print(f"创建数据库失败: {e}")
            raise
    
    def _table_exists(self, cursor, table_name):
        """
        检查表是否存在
        
        Args:
            cursor: 数据库游标
            table_name: 表名
            
        Returns:
            布尔值，表示表是否存在
        """
        cursor.execute(
            "SELECT COUNT(*) FROM sys.objects WHERE object_id = OBJECT_ID(N'[dbo].[{}]') AND type IN (N'U')".format(table_name)
        )
        return cursor.fetchone()[0] > 0
    
    def create_tables(self):
        """
        创建表结构，仅创建不存在的表
        """
        try:
            with pyodbc.connect(self.connection_string) as conn:
                conn.autocommit = True
                with conn.cursor() as cursor:
                    # 系统字典表
                    if not self._table_exists(cursor, 'Sys_Dictionary'):
                        print("正在创建系统字典表 (Sys_Dictionary)...")
                        cursor.execute("""
                            CREATE TABLE Sys_Dictionary (
                                DictID INT PRIMARY KEY IDENTITY(1,1),
                                DictType NVARCHAR(50) NOT NULL,
                                DictCode NVARCHAR(50) NOT NULL,
                                DictName NVARCHAR(100) NOT NULL,
                                Description NVARCHAR(200) NULL,
                                SortOrder INT DEFAULT 0,
                                IsActive BIT DEFAULT 1,
                                CreateTime DATETIME DEFAULT GETDATE(),
                                UpdateTime DATETIME NULL
                            );
                        """)
                    else:
                        print("系统字典表 (Sys_Dictionary) 已存在")
                    
                    # 角色表
                    if not self._table_exists(cursor, 'Role'):
                        print("正在创建角色表 (Role)...")
                        cursor.execute("""
                            CREATE TABLE Role (
                                RoleID INT PRIMARY KEY IDENTITY(1,1),
                                RoleName NVARCHAR(50) NOT NULL UNIQUE,
                                RoleCode NVARCHAR(50) NOT NULL UNIQUE,
                                Description NVARCHAR(200) NULL,
                                IsActive BIT DEFAULT 1,
                                CreateTime DATETIME DEFAULT GETDATE(),
                                UpdateTime DATETIME NULL
                            );
                        """)
                    else:
                        print("角色表 (Role) 已存在")
                    
                    # 权限表
                    if not self._table_exists(cursor, 'Permission'):
                        print("正在创建权限表 (Permission)...")
                        cursor.execute("""
                            CREATE TABLE Permission (
                                PermissionID INT PRIMARY KEY IDENTITY(1,1),
                                PermissionName NVARCHAR(100) NOT NULL UNIQUE,
                                PermissionCode NVARCHAR(100) NOT NULL UNIQUE,
                                Description NVARCHAR(200) NULL,
                                ModuleName NVARCHAR(50) NOT NULL,
                                IsActive BIT DEFAULT 1,
                                CreateTime DATETIME DEFAULT GETDATE(),
                                UpdateTime DATETIME NULL
                            );
                        """)
                    else:
                        print("权限表 (Permission) 已存在")
                    
                    # 角色权限表
                    if not self._table_exists(cursor, 'RolePermission'):
                        print("正在创建角色权限表 (RolePermission)...")
                        cursor.execute("""
                            CREATE TABLE RolePermission (
                                RolePermissionID INT PRIMARY KEY IDENTITY(1,1),
                                RoleID INT NOT NULL FOREIGN KEY REFERENCES Role(RoleID),
                                PermissionID INT NOT NULL FOREIGN KEY REFERENCES Permission(PermissionID),
                                CreateTime DATETIME DEFAULT GETDATE()
                            );
                        """)
                    else:
                        print("角色权限表 (RolePermission) 已存在")
                    
                    # 用户表
                    if not self._table_exists(cursor, 'User'):
                        print("正在创建用户表 (User)...")
                        cursor.execute("""
                            CREATE TABLE [User] (
                                UserID INT PRIMARY KEY IDENTITY(1,1),
                                Username NVARCHAR(50) NOT NULL UNIQUE,
                                Password NVARCHAR(255) NOT NULL,
                                RealName NVARCHAR(50) NOT NULL,
                                Phone NVARCHAR(20) NULL,
                                Email NVARCHAR(100) NULL,
                                IsActive BIT DEFAULT 1,
                                CreateTime DATETIME DEFAULT GETDATE(),
                                UpdateTime DATETIME NULL,
                                LastLoginTime DATETIME NULL,
                                WeChatOpenID NVARCHAR(100) NULL,
                                MerchantID INT NULL
                            );
                        """)
                    else:
                        print("用户表 (User) 已存在")
                    
                    # 用户角色表
                    if not self._table_exists(cursor, 'UserRole'):
                        print("正在创建用户角色表 (UserRole)...")
                        cursor.execute("""
                            CREATE TABLE UserRole (
                                UserRoleID INT PRIMARY KEY IDENTITY(1,1),
                                UserID INT NOT NULL FOREIGN KEY REFERENCES [User](UserID),
                                RoleID INT NOT NULL FOREIGN KEY REFERENCES Role(RoleID),
                                CreateTime DATETIME DEFAULT GETDATE()
                            );
                        """)
                    else:
                        print("用户角色表 (UserRole) 已存在")
                    
                    # 商户表
                    if not self._table_exists(cursor, 'Merchant'):
                        print("正在创建商户表 (Merchant)...")
                        cursor.execute("""
                            CREATE TABLE Merchant (
                                MerchantID INT PRIMARY KEY IDENTITY(1,1),
                                MerchantName NVARCHAR(100) NOT NULL,
                                LegalPerson NVARCHAR(50) NOT NULL,
                                ContactPerson NVARCHAR(50) NOT NULL,
                                Phone NVARCHAR(20) NOT NULL,
                                Address NVARCHAR(200) NULL,
                                MerchantType NVARCHAR(50) NOT NULL,
                                BusinessLicense NVARCHAR(100) NULL,
                                TaxRegistration NVARCHAR(100) NULL,
                                Description NVARCHAR(500) NULL,
                                Status NVARCHAR(50) DEFAULT N'正常',
                                BusinessType NVARCHAR(100) NULL,
                                CreateTime DATETIME DEFAULT GETDATE(),
                                UpdateTime DATETIME NULL
                            );
                        """)
                    else:
                        print("商户表 (Merchant) 已存在")
                    
                    # 更新用户表的外键（如果存在）
                    if self._table_exists(cursor, 'User') and self._table_exists(cursor, 'Merchant'):
                        print("正在检查用户表外键...")
                        # 检查外键是否已存在
                        cursor.execute("""
                            SELECT COUNT(*) FROM sys.foreign_keys WHERE name = 'FK_User_Merchant'
                        """)
                        if cursor.fetchone()[0] == 0:
                            print("正在更新用户表外键...")
                            cursor.execute("""
                                ALTER TABLE [User] 
                                ADD CONSTRAINT FK_User_Merchant FOREIGN KEY (MerchantID) REFERENCES Merchant(MerchantID)
                            """)
                        else:
                            print("用户表外键已存在")
                    
                    # 地块表
                    if not self._table_exists(cursor, 'Plot'):
                        print("正在创建地块表 (Plot)...")
                        cursor.execute("""
                            CREATE TABLE Plot (
                                PlotID INT PRIMARY KEY IDENTITY(1,1),
                                PlotNumber NVARCHAR(50) NOT NULL UNIQUE,
                                PlotName NVARCHAR(100) NOT NULL,
                                Area DECIMAL(10,2) NOT NULL,
                                UnitPrice DECIMAL(10,2) NOT NULL,
                                TotalPrice DECIMAL(10,2) NOT NULL,
                                Location NVARCHAR(200) NULL,
                                Description NVARCHAR(500) NULL,
                                ImagePath NVARCHAR(255) NULL,
                                Status NVARCHAR(50) DEFAULT N'空闲',
                                PlotType NVARCHAR(50) NULL,
                                CreateTime DATETIME DEFAULT GETDATE(),
                                UpdateTime DATETIME NULL
                            );
                        """)
                    else:
                        print("地块表 (Plot) 已存在")
                    
                    # 合同表
                    if not self._table_exists(cursor, 'Contract'):
                        print("正在创建合同表 (Contract)...")
                        cursor.execute("""
                            CREATE TABLE Contract (
                                ContractID INT PRIMARY KEY IDENTITY(1,1),
                                ContractNumber NVARCHAR(50) NOT NULL UNIQUE,
                                MerchantID INT NOT NULL FOREIGN KEY REFERENCES Merchant(MerchantID),
                                ContractName NVARCHAR(100) NOT NULL,
                                StartDate DATETIME NOT NULL,
                                EndDate DATETIME NOT NULL,
                                ContractAmount DECIMAL(12,2) NOT NULL,
                                AmountReduction DECIMAL(12,2) DEFAULT 0,
                                ActualAmount DECIMAL(12,2) NOT NULL,
                                PaymentMethod NVARCHAR(50) NOT NULL,
                                ContractPeriodYear INT NOT NULL,
                                ContractPeriod NVARCHAR(50) NULL,
                                BusinessType NVARCHAR(50) NOT NULL,
                                Description NVARCHAR(500) NULL,
                                Status NVARCHAR(50) DEFAULT N'生效',
                                CreateTime DATETIME DEFAULT GETDATE(),
                                UpdateTime DATETIME NULL
                            );
                        """)
                    else:
                        print("合同表 (Contract) 已存在")
                    
                    # 合同地块关联表
                    if not self._table_exists(cursor, 'ContractPlot'):
                        print("正在创建合同地块关联表 (ContractPlot)...")
                        cursor.execute("""
                            CREATE TABLE ContractPlot (
                                ContractPlotID INT PRIMARY KEY IDENTITY(1,1),
                                ContractID INT NOT NULL FOREIGN KEY REFERENCES Contract(ContractID),
                                PlotID INT NOT NULL FOREIGN KEY REFERENCES Plot(PlotID),
                                UnitPrice DECIMAL(10,2) NOT NULL,
                                Area DECIMAL(10,2) NOT NULL,
                                MonthlyPrice DECIMAL(10,2) NOT NULL,
                                CreateTime DATETIME DEFAULT GETDATE()
                            );
                        """)
                    else:
                        print("合同地块关联表 (ContractPlot) 已存在")
                    
                    # 电表表
                    if not self._table_exists(cursor, 'ElectricityMeter'):
                        print("正在创建电表表 (ElectricityMeter)...")
                        cursor.execute("""
                            CREATE TABLE ElectricityMeter (
                                MeterID INT PRIMARY KEY IDENTITY(1,1),
                                MeterNumber NVARCHAR(50) NOT NULL UNIQUE,
                                MeterType NVARCHAR(50) NOT NULL DEFAULT N'electricity',
                                InstallationLocation NVARCHAR(200) NULL,
                                Status NVARCHAR(50) DEFAULT N'正常',
                                CreateTime DATETIME DEFAULT GETDATE(),
                                UpdateTime DATETIME NULL
                            );
                        """)
                    else:
                        print("电表表 (ElectricityMeter) 已存在")
                    
                    # 水表表
                    if not self._table_exists(cursor, 'WaterMeter'):
                        print("正在创建水表表 (WaterMeter)...")
                        cursor.execute("""
                            CREATE TABLE WaterMeter (
                                MeterID INT PRIMARY KEY IDENTITY(1,1),
                                MeterNumber NVARCHAR(50) NOT NULL UNIQUE,
                                MeterType NVARCHAR(50) NOT NULL DEFAULT N'water',
                                InstallationLocation NVARCHAR(200) NULL,
                                Status NVARCHAR(50) DEFAULT N'正常',
                                CreateTime DATETIME DEFAULT GETDATE(),
                                UpdateTime DATETIME NULL
                            );
                        """)
                    else:
                        print("水表表 (WaterMeter) 已存在")
                    
                    # 合同电表关联表
                    if not self._table_exists(cursor, 'ContractElectricityMeter'):
                        print("正在创建合同电表关联表 (ContractElectricityMeter)...")
                        cursor.execute("""
                            CREATE TABLE ContractElectricityMeter (
                                ContractMeterID INT PRIMARY KEY IDENTITY(1,1),
                                ContractID INT NOT NULL FOREIGN KEY REFERENCES Contract(ContractID),
                                MeterID INT NOT NULL FOREIGN KEY REFERENCES ElectricityMeter(MeterID),
                                StartReading DECIMAL(10,2) NOT NULL,
                                UnitPrice DECIMAL(10,4) DEFAULT 0,
                                CreateTime DATETIME DEFAULT GETDATE()
                            );
                        """)
                    else:
                        print("合同电表关联表 (ContractElectricityMeter) 已存在")
                    
                    # 合同水表关联表
                    if not self._table_exists(cursor, 'ContractWaterMeter'):
                        print("正在创建合同水表关联表 (ContractWaterMeter)...")
                        cursor.execute("""
                            CREATE TABLE ContractWaterMeter (
                                ContractMeterID INT PRIMARY KEY IDENTITY(1,1),
                                ContractID INT NOT NULL FOREIGN KEY REFERENCES Contract(ContractID),
                                MeterID INT NOT NULL FOREIGN KEY REFERENCES WaterMeter(MeterID),
                                StartReading DECIMAL(10,2) NOT NULL,
                                UnitPrice DECIMAL(10,4) DEFAULT 0,
                                CreateTime DATETIME DEFAULT GETDATE()
                            );
                        """)
                    else:
                        print("合同水表关联表 (ContractWaterMeter) 已存在")
                    
                    # 换表记录表
                    if not self._table_exists(cursor, 'MeterChangeRecord'):
                        print("正在创建换表记录表 (MeterChangeRecord)...")
                        cursor.execute("""
                            CREATE TABLE MeterChangeRecord (
                                ChangeRecordID INT PRIMARY KEY IDENTITY(1,1),
                                OldMeterID INT NOT NULL,
                                NewMeterID INT NOT NULL,
                                MeterType NVARCHAR(50) NOT NULL,
                                ContractID INT NOT NULL FOREIGN KEY REFERENCES Contract(ContractID),
                                MerchantID INT NOT NULL FOREIGN KEY REFERENCES Merchant(MerchantID),
                                OldMeterLastReading DECIMAL(10,2) NOT NULL,
                                NewMeterStartReading DECIMAL(10,2) NOT NULL,
                                ChangeDate DATETIME DEFAULT GETDATE(),
                                Reason NVARCHAR(500) NULL,
                                CreatedBy INT NOT NULL FOREIGN KEY REFERENCES [User](UserID),
                                CreateTime DATETIME DEFAULT GETDATE()
                            );
                        """)
                    else:
                        print("换表记录表 (MeterChangeRecord) 已存在")
                    
                    # 水电费抄表记录表
                    if not self._table_exists(cursor, 'UtilityReading'):
                        print("正在创建水电费抄表记录表 (UtilityReading)...")
                        cursor.execute("""
                            CREATE TABLE UtilityReading (
                                ReadingID INT PRIMARY KEY IDENTITY(1,1),
                                MeterID INT NOT NULL,
                                MeterType NVARCHAR(50) NOT NULL,
                                LastReading DECIMAL(10,2) NOT NULL,
                                CurrentReading DECIMAL(10,2) NOT NULL,
                                Usage DECIMAL(10,2) NOT NULL,
                                UnitPrice DECIMAL(10,2) NOT NULL,
                                TotalAmount DECIMAL(12,2) NOT NULL,
                                ReadingDate DATETIME DEFAULT GETDATE(),
                                ReadingMonth NVARCHAR(7) NOT NULL,
                                CreateTime DATETIME DEFAULT GETDATE()
                            );
                        """)
                    else:
                        print("水电费抄表记录表 (UtilityReading) 已存在")
                    
                    # 费用类型表
                    if not self._table_exists(cursor, 'ExpenseType'):
                        print("正在创建费用类型表 (ExpenseType)...")
                        cursor.execute("""
                            CREATE TABLE ExpenseType (
                                ExpenseTypeID INT PRIMARY KEY IDENTITY(1,1),
                                ExpenseTypeName NVARCHAR(100) NOT NULL UNIQUE,
                                ExpenseTypeCode NVARCHAR(50) NOT NULL UNIQUE,
                                ExpenseDirection NVARCHAR(20) NOT NULL,
                                Description NVARCHAR(200) NULL,
                                IsActive BIT DEFAULT 1,
                                CreateTime DATETIME DEFAULT GETDATE(),
                                UpdateTime DATETIME NULL
                            );
                        """)
                    else:
                        print("费用类型表 (ExpenseType) 已存在")
                    
                    # 应收账款表
                    if not self._table_exists(cursor, 'Receivable'):
                        print("正在创建应收账款表 (Receivable)...")
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
                    else:
                        print("应收账款表 (Receivable) 已存在")
                    
                    # 应付账款表
                    if not self._table_exists(cursor, 'Payable'):
                        print("正在创建应付账款表 (Payable)...")
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
                    else:
                        print("应付账款表 (Payable) 已存在")
                    
                    # 现金流水表
                    if not self._table_exists(cursor, 'CashFlow'):
                        print("正在创建现金流水表 (CashFlow)...")
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
                    else:
                        print("现金流水表 (CashFlow) 已存在")
                    
                    # 收款记录表
                    if not self._table_exists(cursor, 'CollectionRecord'):
                        print("正在创建收款记录表 (CollectionRecord)...")
                        cursor.execute("""
                            CREATE TABLE CollectionRecord (
                                CollectionRecordID INT PRIMARY KEY IDENTITY(1,1),
                                ReceivableID INT NOT NULL FOREIGN KEY REFERENCES Receivable(ReceivableID),
                                MerchantID INT NOT NULL FOREIGN KEY REFERENCES Merchant(MerchantID),
                                Amount DECIMAL(12,2) NOT NULL,
                                PaymentMethod NVARCHAR(50) NOT NULL,
                                TransactionDate DATETIME DEFAULT GETDATE(),
                                Description NVARCHAR(500) NULL,
                                CreatedBy INT NOT NULL FOREIGN KEY REFERENCES [User](UserID),
                                CreateTime DATETIME DEFAULT GETDATE()
                            );
                        """)
                    else:
                        print("收款记录表 (CollectionRecord) 已存在")
                    
                    # 付款记录表
                    if not self._table_exists(cursor, 'PaymentRecord'):
                        print("正在创建付款记录表 (PaymentRecord)...")
                        cursor.execute("""
                            CREATE TABLE PaymentRecord (
                                PaymentRecordID INT PRIMARY KEY IDENTITY(1,1),
                                PayableID INT NOT NULL FOREIGN KEY REFERENCES Payable(PayableID),
                                VendorName NVARCHAR(100) NOT NULL,
                                Amount DECIMAL(12,2) NOT NULL,
                                PaymentMethod NVARCHAR(50) NOT NULL,
                                TransactionDate DATETIME DEFAULT GETDATE(),
                                Description NVARCHAR(500) NULL,
                                CreatedBy INT NOT NULL FOREIGN KEY REFERENCES [User](UserID),
                                CreateTime DATETIME DEFAULT GETDATE()
                            );
                        """)
                    else:
                        print("付款记录表 (PaymentRecord) 已存在")
                    
                    # 磅秤表
                    if not self._table_exists(cursor, 'Scale'):
                        print("正在创建磅秤表 (Scale)...")
                        cursor.execute("""
                            CREATE TABLE Scale (
                                ScaleID INT PRIMARY KEY IDENTITY(1,1),
                                ScaleNumber NVARCHAR(50) NOT NULL UNIQUE,
                                ScaleName NVARCHAR(100) NOT NULL,
                                Location NVARCHAR(200) NOT NULL,
                                MaximumCapacity DECIMAL(10,2) NOT NULL,
                                Unit NVARCHAR(10) NOT NULL,
                                Status NVARCHAR(50) DEFAULT N'正常',
                                Description NVARCHAR(500) NULL,
                                CreateTime DATETIME DEFAULT GETDATE(),
                                UpdateTime DATETIME NULL
                            );
                        """)
                    else:
                        print("磅秤表 (Scale) 已存在")
                    
                    # 过磅记录表
                    if not self._table_exists(cursor, 'ScaleRecord'):
                        print("正在创建过磅记录表 (ScaleRecord)...")
                        cursor.execute("""
                            CREATE TABLE ScaleRecord (
                                ScaleRecordID INT PRIMARY KEY IDENTITY(1,1),
                                ScaleID INT NOT NULL FOREIGN KEY REFERENCES Scale(ScaleID),
                                MerchantID INT NOT NULL FOREIGN KEY REFERENCES Merchant(MerchantID),
                                GrossWeight DECIMAL(10,2) NOT NULL,
                                TareWeight DECIMAL(10,2) NOT NULL,
                                NetWeight DECIMAL(10,2) NOT NULL,
                                UnitPrice DECIMAL(10,2) NOT NULL,
                                TotalAmount DECIMAL(12,2) NOT NULL,
                                LicensePlate NVARCHAR(50) NULL,
                                ProductName NVARCHAR(100) NULL,
                                Operator NVARCHAR(50) NOT NULL,
                                ScaleTime DATETIME DEFAULT GETDATE(),
                                Description NVARCHAR(500) NULL,
                                CreateTime DATETIME DEFAULT GETDATE()
                            );
                        """)
                    else:
                        print("过磅记录表 (ScaleRecord) 已存在")
                    
                    print("所有表创建完成")
        except Exception as e:
            print(f"创建表失败: {e}")
            raise
    
    def _debug_permission_table(self, cursor):
        """
        调试权限表结构和数据
        """
        print("调试权限表结构...")
        # 检查表结构
        cursor.execute("""
            SELECT COLUMN_NAME, DATA_TYPE, IS_NULLABLE, COLUMN_DEFAULT
            FROM INFORMATION_SCHEMA.COLUMNS
            WHERE TABLE_NAME = 'Permission'
            ORDER BY ORDINAL_POSITION
        """)
        columns = cursor.fetchall()
        for column in columns:
            print(f"列名: {column.COLUMN_NAME}, 数据类型: {column.DATA_TYPE}, 是否可为空: {column.IS_NULLABLE}, 默认值: {column.COLUMN_DEFAULT}")
        
        # 检查主键
        cursor.execute("""
            SELECT kcu.COLUMN_NAME
            FROM INFORMATION_SCHEMA.TABLE_CONSTRAINTS tc
            INNER JOIN INFORMATION_SCHEMA.KEY_COLUMN_USAGE kcu ON tc.CONSTRAINT_NAME = kcu.CONSTRAINT_NAME
            WHERE tc.TABLE_NAME = 'Permission' AND tc.CONSTRAINT_TYPE = 'PRIMARY KEY'
        """)
        primary_keys = cursor.fetchall()
        print("\n主键:")
        for pk in primary_keys:
            print(f"列名: {pk.COLUMN_NAME}")
        
        # 检查唯一约束
        cursor.execute("""
            SELECT tc.CONSTRAINT_NAME, kcu.COLUMN_NAME
            FROM INFORMATION_SCHEMA.TABLE_CONSTRAINTS tc
            INNER JOIN INFORMATION_SCHEMA.KEY_COLUMN_USAGE kcu ON tc.CONSTRAINT_NAME = kcu.CONSTRAINT_NAME
            WHERE tc.TABLE_NAME = 'Permission' AND tc.CONSTRAINT_TYPE = 'UNIQUE'
        """)
        unique_constraints = cursor.fetchall()
        print("\n唯一约束:")
        for uc in unique_constraints:
            print(f"约束名称: {uc.CONSTRAINT_NAME}, 列名: {uc.COLUMN_NAME}")
        
        # 检查现有数据
        cursor.execute("SELECT * FROM Permission")
        rows = cursor.fetchall()
        print(f"\n现有权限数据 ({len(rows)} 条):")
        if rows:
            for row in rows:
                print(f"PermissionID: {row.PermissionID}, PermissionName: {row.PermissionName}, PermissionCode: {row.PermissionCode}, ModuleName: {row.ModuleName}")
        else:
            print("没有现有数据")
    
    def insert_initial_data(self):
        """
        插入初始数据，仅插入不存在的数据
        """
        try:
            with pyodbc.connect(self.connection_string) as conn:
                conn.autocommit = True
                with conn.cursor() as cursor:
                    # 调试权限表
                    self._debug_permission_table(cursor)
                    
                    # 插入系统字典数据
                    print("\n正在插入系统字典数据...")
                    
                    # 商户类型
                    self._insert_dict_data(cursor, 'merchant_type', [
                        ('individual', '个体工商户', '个体经营的商户', 1),
                        ('company', '公司', '企业法人经营的商户', 2),
                        ('intent', '意向商户', '有意向入驻的商户', 3),
                        ('business', '业务往来', '有业务往来的商户', 4)
                    ])
                    
                    # 费用项目
                    self._insert_dict_data(cursor, 'expense_item', [
                        ('rent', '租金', '地块租金', 1),
                        ('water', '水费', '自来水费用', 2),
                        ('electricity', '电费', '电力费用', 3),
                        ('scale_fee', '过磅费', '磅秤使用费用', 4),
                        ('management_fee', '管理费', '市场管理费用', 5)
                    ])
                    
                    # 地块状态
                    self._insert_dict_data(cursor, 'plot_status', [
                        ('idle', '空闲', '未出租的地块', 1),
                        ('rented', '已租', '已出租的地块', 2),
                        ('maintenance', '维修中', '正在维修的地块', 3)
                    ])
                    
                    # 业态类型
                    self._insert_dict_data(cursor, 'business_type', [
                        ('metal_material', '金属材料', '金属原材料销售', 1),
                        ('hardware', '五金工具', '五金工具销售', 2),
                        ('machinery', '机械配件', '机械配件销售', 3),
                        ('equipment', '设备租赁', '设备租赁业务', 4)
                    ])
                    
                    # 合同状态
                    self._insert_dict_data(cursor, 'contract_status', [
                        ('active', '生效', '当前生效的合同', 1),
                        ('expired', '已过期', '已到期的合同', 2),
                        ('terminated', '已终止', '提前终止的合同', 3)
                    ])
                    
                    # 付款方式
                    self._insert_dict_data(cursor, 'payment_method', [
                        ('cash', '现金', '现金支付', 1),
                        ('transfer', '转账', '银行转账', 2),
                        ('check', '支票', '支票支付', 3),
                        ('alipay', '支付宝', '支付宝支付', 4),
                        ('wechat', '微信', '微信支付', 5)
                    ])
                    
                    # 插入角色数据
                    print("正在插入角色数据...")
                    roles = [
                        ('管理员', 'admin', '系统管理员，拥有所有权限'),
                        ('工作人员', 'staff', '普通工作人员，拥有部分权限'),
                        ('商户', 'merchant', '商户用户，仅能查看自己的信息')
                    ]
                    
                    for role_name, role_code, description in roles:
                        cursor.execute("SELECT COUNT(*) FROM Role WHERE RoleCode = ?", (role_code,))
                        if cursor.fetchone()[0] == 0:
                            cursor.execute(
                                "INSERT INTO Role (RoleName, RoleCode, Description) VALUES (?, ?, ?)",
                                (role_name, role_code, description)
                            )
                    
                    # 插入权限数据
                    print("正在插入权限数据...")
                    permissions = [
                        ('用户管理', 'user_manage', '管理系统用户', '用户管理'),
                        ('商户管理', 'merchant_manage', '管理商户信息', '商户管理'),
                        ('地块管理', 'plot_manage', '管理地块信息', '地块管理'),
                        ('合同管理', 'contract_manage', '管理合同信息', '合同管理'),
                        ('水电计费', 'utility_manage', '管理水电计费', '水电计费'),
                        ('财务管理', 'finance_manage', '管理财务信息', '财务管理'),
                        ('磅秤管理', 'scale_manage', '管理磅秤信息', '磅秤管理')
                    ]
                    
                    # 直接使用TRUNCATE TABLE来清空权限表
                    try:
                        cursor.execute("TRUNCATE TABLE RolePermission")
                        cursor.execute("TRUNCATE TABLE Permission")
                        print("权限表和角色权限表已清空")
                    except Exception as e:
                        print(f"清空表失败: {e}")
                        # 如果TRUNCATE失败，尝试使用DELETE
                        cursor.execute("DELETE FROM RolePermission")
                        cursor.execute("DELETE FROM Permission")
                        print("使用DELETE清空表成功")
                    
                    # 重新插入所有权限
                    for permission_name, permission_code, description, module_name in permissions:
                        try:
                            cursor.execute(
                                "INSERT INTO Permission (PermissionName, PermissionCode, Description, ModuleName) VALUES (?, ?, ?, ?)",
                                (permission_name, permission_code, description, module_name)
                            )
                            print(f"插入权限成功: {permission_name} - {permission_code}")
                        except Exception as e:
                            print(f"插入权限失败: {permission_name} - {permission_code}, 错误: {e}")
                    
                    # 为管理员角色分配所有权限
                    print("正在分配角色权限...")
                    
                    # 为管理员角色分配所有权限
                    try:
                        cursor.execute("""
                            INSERT INTO RolePermission (RoleID, PermissionID) 
                            SELECT r.RoleID, p.PermissionID 
                            FROM Role r, Permission p 
                            WHERE r.RoleCode = 'admin';
                        """)
                        print("管理员角色权限分配成功")
                    except Exception as e:
                        print(f"管理员角色权限分配失败: {e}")
                    
                    # 为工作人员角色分配部分权限
                    try:
                        cursor.execute("""
                            INSERT INTO RolePermission (RoleID, PermissionID) 
                            SELECT r.RoleID, p.PermissionID 
                            FROM Role r, Permission p 
                            WHERE r.RoleCode = 'staff' AND p.ModuleName NOT IN ('用户管理');
                        """)
                        print("工作人员角色权限分配成功")
                    except Exception as e:
                        print(f"工作人员角色权限分配失败: {e}")
                    
                    # 为商户角色分配有限权限
                    try:
                        cursor.execute("""
                            INSERT INTO RolePermission (RoleID, PermissionID) 
                            SELECT r.RoleID, p.PermissionID 
                            FROM Role r, Permission p 
                            WHERE r.RoleCode = 'merchant' AND p.PermissionCode IN ('contract_manage', 'utility_manage', 'scale_manage');
                        """)
                        print("商户角色权限分配成功")
                    except Exception as e:
                        print(f"商户角色权限分配失败: {e}")
                    
                    # 插入初始用户（默认管理员密码：admin123）
                    print("正在插入初始用户...")
                    cursor.execute("SELECT COUNT(*) FROM [User] WHERE Username = ?", ('admin',))
                    if cursor.fetchone()[0] == 0:
                        try:
                            cursor.execute("""
                                INSERT INTO [User] (Username, Password, RealName, Phone, Email, IsActive) VALUES
                                ('admin', '$pbkdf2-sha256$29000$nPP.HwOAUGrN2TsnJETI.Q$Pm0jp5L2PsSp7mG2w37TZkLn0Y4mp3eSzDS0f69gIHo', '系统管理员', '13800138000', 'admin@example.com', 1);
                            """)
                            print("初始用户插入成功")
                        except Exception as e:
                            print(f"初始用户插入失败: {e}")
                    else:
                        print("初始用户已存在")
                    
                    # 为管理员用户分配管理员角色
                    try:
                        cursor.execute("DELETE FROM UserRole")
                        cursor.execute("""
                            INSERT INTO UserRole (UserID, RoleID) 
                            SELECT u.UserID, r.RoleID 
                            FROM [User] u, Role r 
                            WHERE u.Username = 'admin' AND r.RoleCode = 'admin';
                        """)
                        print("管理员用户角色分配成功")
                    except Exception as e:
                        print(f"管理员用户角色分配失败: {e}")
                    
                    print("初始数据插入完成")
        except Exception as e:
            print(f"插入初始数据失败: {e}")
            raise
    
    def _insert_dict_data(self, cursor, dict_type, data_list):
        """
        插入字典数据，仅插入不存在的数据
        
        Args:
            cursor: 数据库游标
            dict_type: 字典类型
            data_list: 数据列表，每个元素为(DictCode, DictName, Description, SortOrder)
        """
        for dict_code, dict_name, description, sort_order in data_list:
            cursor.execute(
                "SELECT COUNT(*) FROM Sys_Dictionary WHERE DictType = ? AND DictCode = ?",
                (dict_type, dict_code)
            )
            if cursor.fetchone()[0] == 0:
                cursor.execute(
                    "INSERT INTO Sys_Dictionary (DictType, DictCode, DictName, Description, SortOrder) VALUES (?, ?, ?, ?, ?)",
                    (dict_type, dict_code, dict_name, description, sort_order)
                )
    
    def init_database(self):
        """
        初始化数据库
        """
        print("开始初始化数据库...")
        
        try:
            # 创建数据库
            self.create_database()
            
            # 创建表结构
            self.create_tables()
            
            # 插入初始数据
            self.insert_initial_data()
            
            print("数据库初始化完成！")
        except Exception as e:
            print(f"数据库初始化失败: {e}")
            raise


if __name__ == '__main__':
    # 创建数据库初始化实例
    initializer = DatabaseInitializer()
    
    # 执行数据库初始化
    initializer.init_database()
