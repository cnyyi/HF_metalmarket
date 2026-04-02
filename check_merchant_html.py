# -*- coding: utf-8 -*-
"""
检查商户编辑页面的HTML内容
"""
import requests

BASE_URL = 'http://127.0.0.1:5000'

session = requests.Session()

print("获取商户编辑页面...")
response = session.get(f'{BASE_URL}/merchant/edit/28')

if response.status_code == 200:
    html = response.text
    
    print("\n查找表单字段...")
    
    import re
    
    fields = re.findall(r'<label[^>]*>([^<]+)</label>', html)
    print("\n找到的标签:")
    for field in fields:
        print(f"  - {field}")
    
    print("\n查找input字段...")
    inputs = re.findall(r'<input[^>]*>', html)
    for inp in inputs:
        if 'name=' in inp:
            name_match = re.search(r'name="([^"]+)"', inp)
            if name_match:
                print(f"  - {name_match.group(1)}")
    
    print("\n查找select字段...")
    selects = re.findall(r'<select[^>]*>', html)
    for sel in selects:
        if 'name=' in sel:
            name_match = re.search(r'name="([^"]+)"', sel)
            if name_match:
                print(f"  - {name_match.group(1)}")
    
    print("\n检查required属性...")
    if 'required' in html:
        print("  页面中存在required属性")
        required_fields = re.findall(r'<[^>]*required[^>]*>', html)
        print(f"  找到 {len(required_fields)} 个required字段")
    else:
        print("  页面中没有required属性")
    
    print("\n检查商户类型选项...")
    if '个体工商户' in html:
        print("  ✓ 找到'个体工商户'")
    if '公司' in html:
        print("  ✓ 找到'公司'")
    if '意向商户' in html:
        print("  ✓ 找到'意向商户'")
    if '业务往来' in html:
        print("  ✓ 找到'业务往来'")
        
else:
    print(f"状态码: {response.status_code}")
