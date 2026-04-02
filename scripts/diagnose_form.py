# 全面诊断脚本：检查运行时表单实例

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app
from app.forms.merchant_form import MerchantEditForm
import inspect


def diagnose_form():
    """
    全面诊断表单实例
    """
    print("=" * 80)
    print("全面诊断 MerchantEditForm")
    print("=" * 80)
    
    # 1. 检查类定义源文件
    print("\n1. 检查类定义源文件：")
    print(f"   文件路径: {inspect.getfile(MerchantEditForm)}")
    print(f"   模块: {MerchantEditForm.__module__}")
    
    # 2. 检查类属性
    print("\n2. 检查类属性：")
    class_attrs = dir(MerchantEditForm)
    business_type_in_class = 'business_type' in class_attrs
    print(f"   business_type 在类属性中: {business_type_in_class}")
    
    # 3. 检查实例属性
    app = create_app()
    with app.app_context():
        with app.test_request_context():
            print("\n3. 创建表单实例：")
            form = MerchantEditForm()
            
            print(f"   实例类型: {type(form)}")
            print(f"   实例模块: {type(form).__module__}")
            
            # 检查实例属性
            instance_attrs = dir(form)
            business_type_in_instance = 'business_type' in instance_attrs
            print(f"   business_type 在实例属性中: {business_type_in_instance}")
            
            # 尝试访问 business_type
            print("\n4. 尝试访问 business_type：")
            try:
                business_type_field = getattr(form, 'business_type', None)
                if business_type_field:
                    print(f"   ✓ 成功访问 business_type")
                    print(f"   字段类型: {type(business_type_field)}")
                    print(f"   字段标签: {business_type_field.label.text if hasattr(business_type_field, 'label') else 'N/A'}")
                else:
                    print(f"   ✗ business_type 为 None")
            except AttributeError as e:
                print(f"   ✗ 访问失败: {e}")
            
            # 列出所有表单字段
            print("\n5. 所有表单字段：")
            for attr_name in dir(form):
                if not attr_name.startswith('_'):
                    attr = getattr(form, attr_name, None)
                    if hasattr(attr, 'label'):
                        print(f"   - {attr_name}: {attr.label.text}")
    
    print("\n" + "=" * 80)
    print("诊断完成")
    print("=" * 80)


if __name__ == "__main__":
    diagnose_form()