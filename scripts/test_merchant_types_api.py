# 测试 get_merchant_types() 方法返回的数据

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app
from app.services.merchant_service import MerchantService


def test_get_merchant_types():
    """
    测试 get_merchant_types() 方法返回的数据
    """
    
    print("测试 get_merchant_types() 方法...")
    
    # 获取商户类型列表
    merchant_types = MerchantService.get_merchant_types()
    
    print(f"\n返回的商户类型数量: {len(merchant_types)}")
    print("-" * 60)
    print(f"{'DictCode':<20} {'DictName':<20}")
    print("-" * 60)
    
    for code, name in merchant_types:
        print(f"{code:<20} {name:<20}")
    
    print("-" * 60)
    
    # 验证数据
    expected_types = [
        ('individual', '个体工商户'),
        ('company', '公司'),
        ('intent', '意向客户'),
        ('business', '业务往来')
    ]
    
    if merchant_types == expected_types:
        print("\n✓ 商户类型数据正确！")
        return True
    else:
        print("\n✗ 商户类型数据不匹配！")
        print(f"预期: {expected_types}")
        print(f"实际: {merchant_types}")
        return False


if __name__ == "__main__":
    app = create_app()
    with app.app_context():
        success = test_get_merchant_types()
        sys.exit(0 if success else 1)