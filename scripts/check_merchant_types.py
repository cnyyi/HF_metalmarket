# 检查 Sys_Dictionary 表中的商户类型数据

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app
from utils.database import execute_query


def check_merchant_types():
    """
    检查 Sys_Dictionary 表中的商户类型数据
    """
    
    print("检查 Sys_Dictionary 表中的商户类型数据...")
    
    # 查询 Sys_Dictionary 表中的商户类型
    query = """
        SELECT DictType, DictCode, DictName, Description, SortOrder 
        FROM Sys_Dictionary 
        WHERE DictType = 'merchant_type' 
        ORDER BY SortOrder
    """
    
    results = execute_query(query, fetch_type='all')
    
    if not results:
        print("✗ Sys_Dictionary 表中没有商户类型数据！")
        print("需要初始化商户类型数据。")
        return False
    
    print(f"\n找到 {len(results)} 条商户类型记录：")
    print("-" * 80)
    print(f"{'DictCode':<15} {'DictName':<20} {'Description':<30} {'SortOrder':<10}")
    print("-" * 80)
    
    for result in results:
        print(f"{result.DictCode:<15} {result.DictName:<20} {result.Description:<30} {result.SortOrder:<10}")
    
    print("-" * 80)
    
    # 检查是否有预期的商户类型
    expected_codes = ['individual', 'company', 'intent', 'business']
    actual_codes = [result.DictCode for result in results]
    
    missing_codes = set(expected_codes) - set(actual_codes)
    if missing_codes:
        print(f"\n⚠ 缺少预期的商户类型: {missing_codes}")
        return False
    
    print("\n✓ 商户类型数据完整！")
    return True


if __name__ == "__main__":
    app = create_app()
    with app.app_context():
        success = check_merchant_types()
        sys.exit(0 if success else 1)