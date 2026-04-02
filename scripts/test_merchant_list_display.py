# 测试商户列表页面的商户类型显示

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app
from app.services.merchant_service import MerchantService


def test_merchant_list_display():
    """
    测试商户列表页面的商户类型显示
    """
    
    print("测试商户列表页面的商户类型显示...")
    
    app = create_app()
    
    with app.app_context():
        # 获取商户列表
        merchants, total_count, total_pages = MerchantService.get_merchants(page=1, per_page=10)
        
        print(f"\n获取到 {len(merchants)} 条商户记录")
        print("-" * 100)
        print(f"{'ID':<5} {'商户名称':<30} {'商户类型代码':<15} {'商户类型名称':<20}")
        print("-" * 100)
        
        for merchant in merchants[:10]:  # 只显示前10条
            print(f"{merchant.merchant_id:<5} {merchant.merchant_name:<30} {merchant.merchant_type:<15} {merchant.merchant_type_name:<20}")
        
        print("-" * 100)
        
        # 验证类型名称映射
        print("\n验证商户类型名称映射：")
        type_mapping = MerchantService.get_merchant_type_name_mapping()
        print(f"类型映射字典: {type_mapping}")
        
        # 检查是否有商户类型名称为代码值的情况（说明映射失败）
        failed_merchants = [m for m in merchants if m.merchant_type_name == m.merchant_type]
        if failed_merchants:
            print(f"\n⚠ 有 {len(failed_merchants)} 条商户的类型名称映射失败")
            for m in failed_merchants[:5]:
                print(f"  商户ID: {m.merchant_id}, 类型代码: {m.merchant_type}")
        else:
            print("\n✓ 所有商户的类型名称映射成功！")
        
        return True


if __name__ == "__main__":
    success = test_merchant_list_display()
    sys.exit(0 if success else 1)