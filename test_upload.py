# -*- coding: utf-8 -*-
"""
测试文件上传API
"""
import requests
import os

BASE_URL = 'http://127.0.0.1:5000'

session = requests.Session()

print("1. 测试获取首页...")
try:
    response = session.get(f'{BASE_URL}/')
    print(f"   状态码: {response.status_code}")
    print(f"   Cookies: {session.cookies.get_dict()}")
except Exception as e:
    print(f"   错误: {e}")

print("\n2. 测试获取登录页面...")
try:
    response = session.get(f'{BASE_URL}/auth/login')
    print(f"   状态码: {response.status_code}")
    print(f"   Cookies: {session.cookies.get_dict()}")
except Exception as e:
    print(f"   错误: {e}")

print("\n3. 测试获取添加地块页面...")
try:
    response = session.get(f'{BASE_URL}/plot/add')
    print(f"   状态码: {response.status_code}")
    
    if 'csrf-token' in response.text:
        print("   ✓ CSRF token存在")
    else:
        print("   ✗ CSRF token不存在")
    
    if 'uploadArea' in response.text:
        print("   ✓ 上传区域存在")
    else:
        print("   ✗ 上传区域不存在")
        
    if 'fileInput' in response.text:
        print("   ✓ 文件输入控件存在")
    else:
        print("   ✗ 文件输入控件不存在")
        
except Exception as e:
    print(f"   错误: {e}")

print("\n4. 创建测试图片文件...")
test_image_path = 'test_image.jpg'
try:
    from PIL import Image
    img = Image.new('RGB', (100, 100), color='red')
    img.save(test_image_path)
    print(f"   ✓ 测试图片已创建: {test_image_path}")
except ImportError:
    print("   ! PIL未安装，创建简单文件")
    with open(test_image_path, 'wb') as f:
        f.write(b'\xff\xd8\xff\xe0\x00\x10JFIF')
    print(f"   ✓ 测试文件已创建: {test_image_path}")

print("\n5. 测试文件上传API（需要登录）...")
try:
    with open(test_image_path, 'rb') as f:
        files = {'file': ('test.jpg', f, 'image/jpeg')}
        data = {'biz_type': 'Plot'}
        
        response = session.post(
            f'{BASE_URL}/file/upload',
            files=files,
            data=data
        )
        
        print(f"   状态码: {response.status_code}")
        print(f"   响应: {response.text[:200]}")
        
        if response.status_code == 401:
            print("   ! 需要登录才能上传文件")
        elif response.status_code == 400:
            print("   ! CSRF token验证失败")
            
except Exception as e:
    print(f"   错误: {e}")

print("\n6. 清理测试文件...")
try:
    if os.path.exists(test_image_path):
        os.remove(test_image_path)
        print(f"   ✓ 测试文件已删除")
except Exception as e:
    print(f"   错误: {e}")

print("\n测试完成!")
