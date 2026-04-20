# -*- coding: utf-8 -*-
"""
商户数据迁移脚本 - 非交互版本
从源表 [metalmarket].[dbo].[merchants] 迁移到目标表 [HF_MetalMarket].[dbo].[Merchant]
"""
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pyodbc
from config import Config


def get_source_connection():
    """获取源数据库连接 (metalmarket)"""
    conn_str = (
        'DRIVER={ODBC Driver 17 for SQL Server};'
        f"SERVER={os.environ.get('SOURCE_DB_SERVER', 'localhost')};"
        f"DATABASE={os.environ.get('SOURCE_DB_DATABASE', 'metalmarket')};"
        f"UID={os.environ.get('SOURCE_DB_UID', 'sa')};"
        f"PWD={os.environ.get('SOURCE_DB_PWD', '')};"
        'Encrypt=no;'
        'TrustServerCertificate=yes;'
        'charset=utf-8;'
    )
    return pyodbc.connect(conn_str)


def get_target_connection():
    """获取目标数据库连接 (HF_MetalMarket)"""
    return pyodbc.connect(Config.ODBC_CONNECTION_STRING)


def check_source_table():
    """检查源表结构和数据"""
    print("=" * 60)
    print("1. 检查源表 [metalmarket].[dbo].[merchants]")
    print("=" * 60)
    
    conn = get_source_connection()
    cursor = conn.cursor()
    
    # 查看表结构
    print("\n源表字段结构:")
    cursor.execute("""
        SELECT COLUMN_NAME, DATA_TYPE, CHARACTER_MAXIMUM_LENGTH, IS_NULLABLE, COLUMN_DEFAULT
        FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_NAME = 'merchants'
        ORDER BY ORDINAL_POSITION
    """)
    columns = cursor.fetchall()
    for col in columns:
        print(f"  {col.COLUMN_NAME}: {col.DATA_TYPE}({col.CHARACTER_MAXIMUM_LENGTH}), Nullable={col.IS_NULLABLE}, Default={col.COLUMN_DEFAULT}")
    
    # 查看数据量
    cursor.execute("SELECT COUNT(*) FROM merchants")
    count = cursor.fetchone()[0]
    print(f"\n源表数据量: {count} 条")
    
    # 查看样例数据
    print("\n源表样例数据 (前5条):")
    cursor.execute("SELECT TOP 5 * FROM merchants")
    rows = cursor.fetchall()
    for row in rows:
        print(f"  {row}")
    
    # 检查必填字段是否有空值
    print("\n检查数据完整性:")
    cursor.execute("SELECT COUNT(*) FROM merchants WHERE company_name IS NULL OR company_name = ''")
    null_name = cursor.fetchone()[0]
    print(f"  商户名称(company_name)为空的记录: {null_name} 条")
    
    # 查看业态类型
    print("\n业态类型分布:")
    cursor.execute("""
        SELECT business_type_id, COUNT(*) as cnt 
        FROM merchants 
        GROUP BY business_type_id
    """)
    type_dist = cursor.fetchall()
    for t in type_dist:
        print(f"  business_type_id={t.business_type_id}: {t.cnt} 条")
    
    conn.close()
    
    return columns, count


def check_target_table():
    """检查目标表结构和数据"""
    print("\n" + "=" * 60)
    print("2. 检查目标表 [HF_MetalMarket].[dbo].[Merchant]")
    print("=" * 60)
    
    conn = get_target_connection()
    cursor = conn.cursor()
    
    # 查看表结构
    print("\n目标表字段结构:")
    cursor.execute("""
        SELECT COLUMN_NAME, DATA_TYPE, CHARACTER_MAXIMUM_LENGTH, IS_NULLABLE, COLUMN_DEFAULT
        FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_NAME = 'Merchant'
        ORDER BY ORDINAL_POSITION
    """)
    columns = cursor.fetchall()
    for col in columns:
        print(f"  {col.COLUMN_NAME}: {col.DATA_TYPE}({col.CHARACTER_MAXIMUM_LENGTH}), Nullable={col.IS_NULLABLE}, Default={col.COLUMN_DEFAULT}")
    
    # 查看现有数据量
    cursor.execute("SELECT COUNT(*) FROM Merchant")
    count = cursor.fetchone()[0]
    print(f"\n目标表现有数据量: {count} 条")
    
    conn.close()
    
    return columns, count


def migrate_data():
    """执行数据迁移"""
    print("\n" + "=" * 60)
    print("3. 执行数据迁移")
    print("=" * 60)
    
    # 连接源数据库
    source_conn = get_source_connection()
    source_cursor = source_conn.cursor()
    
    # 连接目标数据库
    target_conn = get_target_connection()
    target_cursor = target_conn.cursor()
    
    # 获取目标表现有的商户名称（避免重复）
    target_cursor.execute("SELECT MerchantName FROM Merchant")
    existing_names = set(row[0] for row in target_cursor.fetchall())
    print(f"目标表现有商户: {len(existing_names)} 个")
    
    # 获取源数据
    source_cursor.execute("""
        SELECT 
            id,
            company_name,
            legal_person,
            contact_person,
            contact_phone,
            business_type_id
        FROM merchants
        ORDER BY id
    """)
    source_rows = source_cursor.fetchall()
    print(f"源表总数据: {len(source_rows)} 条")
    
    # 数据转换和插入
    insert_count = 0
    skip_count = 0
    error_count = 0
    
    for row in source_rows:
        merchant_name = row.company_name.strip() if row.company_name else None
        
        # 检查商户名称
        if not merchant_name:
            skip_count += 1
            print(f"  跳过空名称记录: id={row.id}")
            continue
        
        # 检查是否已存在
        if merchant_name in existing_names:
            skip_count += 1
            continue
        
        # 数据清洗
        legal_person = row.legal_person.strip() if row.legal_person else None
        contact_person = row.contact_person.strip() if row.contact_person else None
        phone = row.contact_phone.strip() if row.contact_phone else None
        
        # 商户类型转换 (business_type_id -> merchant_type)
        business_type_id = row.business_type_id
        if business_type_id == 5:
            merchant_type = 'recycling'
        elif business_type_id == 6:
            merchant_type = 'trading'
        elif business_type_id == 8:
            merchant_type = 'scrap'
        else:
            merchant_type = 'other'
        
        # 字段长度截断
        if merchant_name and len(merchant_name) > 100:
            merchant_name = merchant_name[:100]
        if legal_person and len(legal_person) > 50:
            legal_person = legal_person[:50]
        if contact_person and len(contact_person) > 50:
            contact_person = contact_person[:50]
        if phone and len(phone) > 20:
            phone = phone[:20]
        
        # 实际插入
        try:
            target_cursor.execute("""
                INSERT INTO Merchant (
                    MerchantName, LegalPerson, ContactPerson, Phone, Address,
                    MerchantType, BusinessLicense, TaxRegistration, Description, Status
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                merchant_name, legal_person, contact_person, phone, None,
                merchant_type, None, None, None, '正常'
            ))
            insert_count += 1
            print(f"  插入成功: {merchant_name}")
        except Exception as e:
            error_count += 1
            print(f"  插入失败: {merchant_name}, 错误: {e}")
    
    target_conn.commit()
    
    print(f"\n迁移结果:")
    print(f"  成功插入: {insert_count} 条")
    print(f"  跳过: {skip_count} 条")
    print(f"  错误: {error_count} 条")
    
    source_conn.close()
    target_conn.close()
    
    return insert_count, skip_count, error_count


def verify_migration():
    """验证迁移结果"""
    print("\n" + "=" * 60)
    print("4. 迁移验证")
    print("=" * 60)
    
    # 源表数据量
    source_conn = get_source_connection()
    source_cursor = source_conn.cursor()
    source_cursor.execute("SELECT COUNT(*) FROM merchants WHERE company_name IS NOT NULL AND company_name != ''")
    source_count = source_cursor.fetchone()[0]
    source_conn.close()
    
    # 目标表数据量
    target_conn = get_target_connection()
    target_cursor = target_conn.cursor()
    target_cursor.execute("SELECT COUNT(*) FROM Merchant")
    target_count = target_cursor.fetchone()[0]
    
    print(f"源表有效数据: {source_count} 条")
    print(f"目标表总数据: {target_count} 条")
    
    # 检查数据一致性
    print("\n检查数据一致性...")
    target_cursor.execute("SELECT MerchantName FROM Merchant ORDER BY MerchantName")
    target_names = [row[0] for row in target_cursor.fetchall()]
    
    source_conn = get_source_connection()
    source_cursor = source_conn.cursor()
    source_cursor.execute("SELECT DISTINCT company_name FROM merchants WHERE company_name IS NOT NULL AND company_name != '' ORDER BY company_name")
    source_names = [row[0].strip() for row in source_cursor.fetchall()]
    
    # 比较差异
    target_set = set(target_names)
    source_set = set(source_names)
    
    missing = source_set - target_set
    extra = target_set - source_set
    
    if missing:
        print(f"目标表缺失的商户: {len(missing)} 个")
        for name in list(missing)[:10]:
            print(f"  - {name}")
    
    if extra:
        print(f"目标表多余的商户: {len(extra)} 个")
    
    if not missing and not extra:
        print("数据一致性检查通过!")
    
    source_conn.close()
    target_conn.close()


def main():
    """主函数"""
    print("=" * 60)
    print("商户数据迁移工具 (非交互版本)")
    print("源表: [metalmarket].[dbo].[merchants]")
    print("目标表: [HF_MetalMarket].[dbo].[Merchant]")
    print("=" * 60)
    
    # 1. 检查源表
    check_source_table()
    
    # 2. 检查目标表
    check_target_table()
    
    # 3. 执行迁移
    migrate_data()
    
    # 4. 验证迁移
    verify_migration()
    
    print("\n迁移流程完成!")


if __name__ == '__main__':
    main()
