# -*- coding: utf-8 -*-
"""
测试商户编辑功能修改
"""
import requests
import re

BASE_URL = 'http://127.0.0.1:5000'

session = requests.Session()

print("=" * 60)
print("商户编辑功能测试")
print("=" * 60)

print("\n1. 测试获取商户编辑页面...")
try:
    response = session.get(f'{BASE_URL}/merchant/edit/28')
    print(f"   状态码: {response.status_code}")
    
    if response.status_code == 200:
        print("   ✓ 页面加载成功")
        
        if '营业执照号' in response.text:
            print("   ✓ 营业执照字段存在")
            
            if 'required="required"' in response.text and 'business_license' in response.text:
                license_section = response.text[response.text.find('business_license'):response.text.find('business_license') + 500]
                if 'required="required"' in license_section:
                    print("   ✗ 营业执照字段仍然是必填项")
                else:
                    print("   ✓ 营业执照字段已改为非必填")
            else:
                print("   ✓ 营业执照字段已改为非必填")
        else:
            print("   ✗ 营业执照字段不存在")
        
        if 'merchant_type' in response.text:
            print("   ✓ 商户类型字段存在")
            
            if '个体工商户' in response.text and '公司' in response.text:
                print("   ✓ 商户类型选项已加载")
            else:
                print("   ✗ 商户类型选项未加载")
        else:
            print("   ✗ 商户类型字段不存在")
            
        if '可选' in response.text:
            print("   ✓ 营业执照字段提示已更新为可选")
    elif response.status_code == 302:
        print("   ! 需要登录才能访问")
    else:
        print(f"   ✗ 意外的状态码: {response.status_code}")
        
except Exception as e:
    print(f"   错误: {e}")

print("\n" + "=" * 60)
print("测试完成")
print("=" * 60)
