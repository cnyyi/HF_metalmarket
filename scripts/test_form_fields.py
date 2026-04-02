# 测试表单类是否包含business_type字段

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app
from app.forms.merchant_form import MerchantAddForm, MerchantEditForm


def test_form_fields():
    """
    测试表单字段
    """
    print("=" * 80)
    print("测试表单字段")
    print("=" * 80)
    
    # 测试 MerchantAddForm
    print("\nMerchantAddForm 字段：")
    add_form = MerchantAddForm()
    for field_name in dir(add_form):
        field = getattr(add_form, field_name, None)
        if hasattr(field, 'label') and not field_name.startswith('_'):
            print(f"  - {field_name}: {field.label.text}")
    
    # 检查是否有 business_type 字段
    if hasattr(add_form, 'business_type'):
        print("\n✓ MerchantAddForm 包含 business_type 字段")
    else:
        print("\n✗ MerchantAddForm 不包含 business_type 字段")
    
    # 测试 MerchantEditForm
    print("\nMerchantEditForm 字段：")
    edit_form = MerchantEditForm()
    for field_name in dir(edit_form):
        field = getattr(edit_form, field_name, None)
        if hasattr(field, 'label') and not field_name.startswith('_'):
            print(f"  - {field_name}: {field.label.text}")
    
    # 检查是否有 business_type 字段
    if hasattr(edit_form, 'business_type'):
        print("\n✓ MerchantEditForm 包含 business_type 字段")
    else:
        print("\n✗ MerchantEditForm 不包含 business_type 字段")


if __name__ == "__main__":
    app = create_app()
    
    with app.app_context():
        # 在应用请求上下文中测试
        with app.test_request_context():
            test_form_fields()