# -*- coding: utf-8 -*-
"""精确测试垃圾清运 API"""
import sys
sys.stdout.reconfigure(encoding='utf-8')

from app import create_app
from flask import url_for

app = create_app()

with app.test_client() as client:
    with app.test_request_context():
        # 1. 登录（用正确的 form-data 格式）
        login_resp = client.post('/auth/login', data={
            'username': 'admin',
            'password': 'admin123'
        }, follow_redirects=True)
        print("登录后状态:", login_resp.status_code)

        # 2. 测试 vendors API（带 session）
        r1 = client.get('/garbage/vendors')
        print("GET /garbage/vendors:", r1.status_code)
        try:
            import json
            d = json.loads(r1.data)
            print("vendors:", d)
        except:
            print("非JSON:", r1.data[:100])

        # 3. 测试 garbage-types
        r2 = client.get('/garbage/garbage-types')
        print("\nGET /garbage/garbage-types:", r2.status_code)
        try:
            d2 = json.loads(r2.data)
            print("garbage-types:", d2)
        except:
            print("非JSON:", r2.data[:100])

        # 4. 完整测试 POST create（先用 /garbage/create GET 拿 token）
        r3 = client.get('/garbage/create')
        print("\nGET /garbage/create:", r3.status_code)

        # 从 response 里提取 CSRF token
        csrf_token = None
        try:
            import re
            m = re.search(r'name="csrf-token"\s+content="([^"]+)"', r3.data.decode('utf-8'))
            if m:
                csrf_token = m.group(1)
                print("页面 CSRF token:", csrf_token[:30])
        except Exception as e:
            print("提取 token 失败:", e)

        # 5. 用页面拿到的 token POST create
        if csrf_token:
            payload = {
                'collection_date': '2026-04-20',
                'customer_id': '2',
                'garbage_type': '生活垃圾',
                'amount': '1',
                'unit': '车',
                'unit_price': '100',
                'total_amount': '100',
                'description': '测试'
            }
            r4 = client.post('/garbage/create',
                json=payload,
                headers={'X-CSRFToken': csrf_token}
            )
            print("\nPOST /garbage/create:", r4.status_code)
            try:
                d4 = json.loads(r4.data)
                print("返回:", d4)
            except:
                print("返回内容:", r4.data[:300])

        # 6. 查数据库
        print("\n\n=== 数据库状态 ===")
        from utils.database import DBConnection
        with app.app_context():
            with DBConnection() as conn:
                cur = conn.cursor()
                cur.execute("SELECT CollectionID, CollectionDate, CustomerID, GarbageType, TotalAmount, Status FROM GarbageCollection")
                rows = cur.fetchall()
                print("GarbageCollection:", len(rows), "条")
                for r in rows:
                    print(f"  ID={r.CollectionID}, Date={r.CollectionDate}, CustomerID={r.CustomerID}, Type={r.GarbageType}, Amount={r.TotalAmount}, Status={r.Status}")

                cur.execute("SELECT PayableID, VendorName, Amount, Status, ReferenceType FROM Payable WHERE ReferenceType='garbage_collection'")
                rows2 = cur.fetchall()
                print("\nPayable (垃圾):", len(rows2), "条")
                for r in rows2:
                    print(f"  ID={r.PayableID}, Vendor={r.VendorName}, Amount={r.Amount}, Status={r.Status}")
