# 商户类型数据转换脚本
# 将Merchant表中的MerchantType字段从dictcode转换为dictname

import sys
import os
import datetime
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app
from utils.database import execute_query, execute_update


def backup_merchant_data():
    """
    备份商户数据
    """
    print("=" * 80)
    print("步骤1: 备份商户数据")
    print("=" * 80)
    
    # 创建备份表
    backup_table_name = f"Merchant_Backup_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    create_backup_table_query = f"""
        SELECT * INTO {backup_table_name}
        FROM Merchant
    """
    
    try:
        execute_update(create_backup_table_query)
        print(f"✓ 成功创建备份表: {backup_table_name}")
        
        # 验证备份数据
        count_query = f"SELECT COUNT(*) as count FROM {backup_table_name}"
        result = execute_query(count_query, fetch_type='one')
        print(f"✓ 备份表包含 {result.count} 条记录")
        
        return backup_table_name
    except Exception as e:
        print(f"✗ 备份失败: {e}")
        return None


def get_merchant_type_mapping():
    """
    获取商户类型的字典映射
    """
    print("\n" + "=" * 80)
    print("步骤2: 获取商户类型字典映射")
    print("=" * 80)
    
    query = """
        SELECT DictCode, DictName 
        FROM Sys_Dictionary 
        WHERE DictType = 'merchant_type'
        ORDER BY SortOrder
    """
    
    results = execute_query(query, fetch_type='all')
    
    mapping = {}
    print(f"\n找到 {len(results)} 条商户类型映射：")
    print("-" * 60)
    print(f"{'DictCode':<20} {'DictName':<20}")
    print("-" * 60)
    
    for result in results:
        mapping[result.DictCode] = result.DictName
        print(f"{result.DictCode:<20} {result.DictName:<20}")
    
    print("-" * 60)
    
    return mapping


def analyze_current_data(mapping):
    """
    分析当前数据状态
    """
    print("\n" + "=" * 80)
    print("步骤3: 分析当前数据状态")
    print("=" * 80)
    
    # 查询当前商户类型分布
    query = """
        SELECT MerchantType, COUNT(*) as count 
        FROM Merchant 
        GROUP BY MerchantType 
        ORDER BY count DESC
    """
    
    results = execute_query(query, fetch_type='all')
    
    print(f"\n当前商户类型分布：")
    print("-" * 80)
    print(f"{'当前值':<20} {'记录数':<10} {'是否在字典中':<15} {'对应字典名称':<20}")
    print("-" * 80)
    
    total_records = 0
    unmapped_values = []
    
    for result in results:
        total_records += result.count
        is_in_dict = result.MerchantType in mapping
        dict_name = mapping.get(result.MerchantType, 'N/A')
        
        status = "✓" if is_in_dict else "✗"
        print(f"{result.MerchantType:<20} {result.count:<10} {status:<15} {dict_name:<20}")
        
        if not is_in_dict:
            unmapped_values.append(result.MerchantType)
    
    print("-" * 80)
    print(f"总计: {total_records} 条记录")
    
    if unmapped_values:
        print(f"\n⚠ 警告: 发现 {len(unmapped_values)} 个未映射的值: {unmapped_values}")
        return False, unmapped_values
    else:
        print("\n✓ 所有商户类型值都能找到对应的字典名称")
        return True, []


def convert_merchant_types(mapping):
    """
    执行商户类型数据转换
    """
    print("\n" + "=" * 80)
    print("步骤4: 执行数据转换")
    print("=" * 80)
    
    # 构建CASE语句
    case_statements = []
    for dict_code, dict_name in mapping.items():
        case_statements.append(f"WHEN MerchantType = '{dict_code}' THEN N'{dict_name}'")
    
    case_statement = "\n        ".join(case_statements)
    
    update_query = f"""
        UPDATE Merchant
        SET MerchantType = CASE
            {case_statement}
            ELSE MerchantType
        END
        WHERE MerchantType IN ({', '.join([f"'{code}'" for code in mapping.keys()])})
    """
    
    try:
        affected_rows = execute_update(update_query)
        print(f"✓ 成功更新了 {affected_rows} 条记录")
        return True
    except Exception as e:
        print(f"✗ 更新失败: {e}")
        return False


def verify_conversion(mapping):
    """
    验证转换结果
    """
    print("\n" + "=" * 80)
    print("步骤5: 验证转换结果")
    print("=" * 80)
    
    # 查询转换后的商户类型分布
    query = """
        SELECT MerchantType, COUNT(*) as count 
        FROM Merchant 
        GROUP BY MerchantType 
        ORDER BY count DESC
    """
    
    results = execute_query(query, fetch_type='all')
    
    print(f"\n转换后的商户类型分布：")
    print("-" * 80)
    print(f"{'商户类型':<30} {'记录数':<10} {'是否为字典名称':<15}")
    print("-" * 80)
    
    total_records = 0
    all_correct = True
    
    for result in results:
        total_records += result.count
        is_dict_name = result.MerchantType in mapping.values()
        status = "✓" if is_dict_name else "✗"
        
        print(f"{result.MerchantType:<30} {result.count:<10} {status:<15}")
        
        if not is_dict_name:
            all_correct = False
    
    print("-" * 80)
    print(f"总计: {total_records} 条记录")
    
    if all_correct:
        print("\n✓ 所有商户类型都已成功转换为字典名称！")
        return True
    else:
        print("\n✗ 部分商户类型转换失败或存在异常值")
        return False


def main():
    """
    主函数
    """
    print("\n" + "=" * 80)
    print("商户类型数据转换工具")
    print("=" * 80)
    print(f"开始时间: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    app = create_app()
    
    with app.app_context():
        # 步骤1: 备份数据
        backup_table = backup_merchant_data()
        if not backup_table:
            print("\n✗ 数据备份失败，终止操作")
            return False
        
        # 步骤2: 获取字典映射
        mapping = get_merchant_type_mapping()
        if not mapping:
            print("\n✗ 无法获取字典映射，终止操作")
            return False
        
        # 步骤3: 分析当前数据
        all_mapped, unmapped = analyze_current_data(mapping)
        if not all_mapped:
            print(f"\n⚠ 存在未映射的值，请先处理这些值后再执行转换")
            print(f"未映射的值: {unmapped}")
            response = input("\n是否继续执行转换？(y/n): ")
            if response.lower() != 'y':
                print("操作已取消")
                return False
        
        # 步骤4: 执行转换
        if not convert_merchant_types(mapping):
            print("\n✗ 数据转换失败")
            return False
        
        # 步骤5: 验证结果
        if not verify_conversion(mapping):
            print("\n✗ 数据验证失败")
            return False
        
        print("\n" + "=" * 80)
        print("✓ 数据转换完成！")
        print("=" * 80)
        print(f"备份表名: {backup_table}")
        print(f"完成时间: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("\n如需回滚，请执行以下SQL：")
        print(f"  DROP TABLE Merchant;")
        print(f"  SELECT * INTO Merchant FROM {backup_table};")
        
        return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)