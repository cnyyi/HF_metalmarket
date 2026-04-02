# 修复商户类型数据
# 将已有的商户类型从 recycling/trading/scrap/other 转换为 individual/company/intent/business

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app
from utils.database import execute_update, execute_query


def fix_merchant_types():
    """
    修复商户类型数据，统一使用 individual/company/intent/business 体系
    """
    
    print("开始修复商户类型数据...")
    
    # 检查需要更新的数据量
    check_query = """
        SELECT MerchantType, COUNT(*) as count 
        FROM Merchant 
        WHERE MerchantType IN ('recycling', 'trading', 'scrap', 'other')
        GROUP BY MerchantType
    """
    
    results = execute_query(check_query, fetch_type='all')
    
    if not results:
        print("✓ 没有需要修复的商户类型数据")
        return True
    
    print("当前需要修复的商户类型分布：")
    total_count = 0
    for result in results:
        print(f"  {result.MerchantType}: {result.count} 条")
        total_count += result.count
    
    print(f"总计需要修复: {total_count} 条记录")
    
    # 执行类型转换
    update_query = """
        UPDATE Merchant
        SET MerchantType = CASE 
            WHEN MerchantType = 'recycling' THEN 'individual'
            WHEN MerchantType = 'trading' THEN 'company'
            WHEN MerchantType = 'scrap' THEN 'intent'
            WHEN MerchantType = 'other' THEN 'business'
            ELSE MerchantType
        END
        WHERE MerchantType IN ('recycling', 'trading', 'scrap', 'other')
    """
    
    try:
        affected_rows = execute_update(update_query)
        print(f"✓ 成功更新了 {affected_rows} 条商户记录")
        
        # 验证修复结果
        verify_query = """
            SELECT MerchantType, COUNT(*) as count 
            FROM Merchant 
            GROUP BY MerchantType
            ORDER BY count DESC
        """
        
        verify_results = execute_query(verify_query, fetch_type='all')
        print("\n修复后的商户类型分布：")
        for result in verify_results:
            print(f"  {result.MerchantType}: {result.count} 条")
        
        print("\n✓ 商户类型修复完成！")
        return True
        
    except Exception as e:
        print(f"✗ 修复失败: {e}")
        return False


if __name__ == "__main__":
    app = create_app()
    with app.app_context():
        success = fix_merchant_types()
        sys.exit(0 if success else 1)