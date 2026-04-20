# -*- coding: utf-8 -*-
"""用 Flask 测试客户端直接调试垃圾清运 API"""
import sys
sys.stdout.reconfigure(encoding='utf-8')

from app import create_app
from utils.database import DBConnection

app = create_app()

with app.test_client() as client:
    # 1. 先登录获取 session
    login_resp = client.post('/auth/login', data={
        'username': 'admin',
        'password': 'admin123'
    }, follow_redirects=False)
    print("登录状态:", login_resp.status_code)
    print("Location:", login_resp.headers.get('Location', '无'))

    # 2. 测试 vendors API
    r = client.get('/garbage/vendors')
    print("\nGET /garbage/vendors:", r.status_code)
    try:
        import json
        data = json.loads(r.data)
        print("返回:", data)
    except:
        print("HTML 返回（可能未登录）:", r.data[:200])

    # 3. 测试 garbage-types API
    r2 = client.get('/garbage/garbage-types')
    print("\nGET /garbage/garbage-types:", r2.status_code)
    try:
        import json
        data2 = json.loads(r2.data)
        print("返回:", data2)
    except:
        print("HTML 返回:", r2.data[:200])

    # 4. 测试 POST create（带 CSRF token）
    with client.session_transaction() as sess:
        csrf_token = sess.get('_csrf_token', '')
    print("\nCSRF token:", csrf_token[:30] if csrf_token else '无')

    # 尝试用 CSRF token POST
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

    r3 = client.post('/garbage/create',
        json=payload,
        headers={'X-CSRFToken': csrf_token} if csrf_token else {}
    )
    print("\nPOST /garbage/create:", r3.status_code)
    try:
        import json
        data3 = json.loads(r3.data)
        print("返回:", data3)
    except:
        print("返回内容:", r3.data[:300])

    # 5. 也试试不带 CSRF token
    r4 = client.post('/garbage/create', json=payload)
    print("\nPOST /garbage/create (无CSRF):", r4.status_code)
    try:
        print("返回:", json.loads(r4.data))
    except:
        print("返回内容:", r4.data[:300])

# 6. 直接查数据库验证供应商
print("\n\n=== 数据库验证 ===")
with DBConnection() as conn:
    cur = conn.cursor()
    cur.execute("""
        SELECT CustomerID, CustomerName, CustomerType, Status
        FROM Customer
        WHERE CustomerType = N'服务商' AND Status = N'正常'
    """)
    rows = cur.fetchall()
    print("服务商客户:", len(rows), "条")
    for r in rows:
        print(f"  ID={r.CustomerID}, Name={r.CustomerName}, Type={r.CustomerType}, Status={r.Status}")
        # 检查字节
        print(f"  Status bytes: {r.Status.encode('utf-8').hex()}")

    # 检查 GarbageCollection 表是否为空
    cur.execute("SELECT COUNT(*) FROM GarbageCollection")
    cnt = cur.fetchone()[0]
    print(f"\nGarbageCollection 记录数: {cnt}")

    # 检查 Payable 表
    cur.execute("SELECT COUNT(*) FROM Payable WHERE ReferenceType='garbage_collection'")
    cnt2 = cur.fetchone()[0]
    print(f"垃圾相关 Payable 记录数: {cnt2}")
