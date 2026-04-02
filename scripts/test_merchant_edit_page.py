# 测试商户编辑页面的商户类型下拉框

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app


def test_merchant_edit_page():
    """
    测试商户编辑页面的商户类型下拉框
    """
    
    print("测试商户编辑页面的商户类型下拉框...")
    
    app = create_app()
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False  # 禁用 CSRF
    
    with app.test_client() as client:
        # 先登录
        response = client.post('/auth/login', data={
            'username': 'admin',
            'password': 'admin123'
        })
        
        if response.status_code != 302:
            print("✗ 登录失败")
            return False
        
        print("✓ 登录成功")
        
        # 访问商户编辑页面（使用商户ID=1）
        response = client.get('/merchant/edit/1')
        
        if response.status_code == 200:
            html_content = response.data.decode('utf-8')
            
            # 检查商户类型下拉框的内容
            print("\n检查商户类型下拉框内容：")
            print("-" * 80)
            
            # 查找商户类型的选项
            import re
            pattern = r'<select[^>]*id="merchant_type"[^>]*>(.*?)</select>'
            match = re.search(pattern, html_content, re.DOTALL)
            
            if match:
                select_content = match.group(1)
                print("找到商户类型下拉框：")
                print(select_content[:500])  # 只显示前500个字符
                
                # 检查是否包含正确的选项
                if '个体工商户' in select_content or 'individual' in select_content:
                    print("\n✓ 包含正确的商户类型选项")
                else:
                    print("\n✗ 未找到正确的商户类型选项")
                
                if '回收商' in select_content or 'recycling' in select_content:
                    print("✗ 仍然包含旧的商户类型选项")
                else:
                    print("✓ 不包含旧的商户类型选项")
            else:
                print("✗ 未找到商户类型下拉框")
            
            return True
        else:
            print(f"✗ 访问商户编辑页面失败，状态码: {response.status_code}")
            return False


if __name__ == "__main__":
    success = test_merchant_edit_page()
    sys.exit(0 if success else 1)