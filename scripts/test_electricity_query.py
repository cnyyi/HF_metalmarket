# -*- coding: utf-8 -*-
"""验证 dashboard_stats API 中 electricity 部分"""
import os, sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

env_path = os.path.join(PROJECT_ROOT, '.env')
with open(env_path, 'r', encoding='utf-8') as f:
    for line in f:
        line = line.strip()
        if line and not line.startswith('#') and '=' in line:
            k, v = line.split('=', 1)
            os.environ[k.strip()] = v.strip()

from app import create_app
app = create_app()
with app.app_context():
    with app.test_client() as client:
        # 先登录
        client.post('/auth/login', data={'username': 'admin', 'password': '123456'})
        # 请求 dashboard
        resp = client.get('/admin/api/dashboard/stats')
        import json
        data = json.loads(resp.data)
        if data.get('success'):
            elec = data['data'].get('electricity', {})
            print(f'latest_month: {elec.get("latest_month")}')
            print(f'total_usage: {elec.get("total_usage")} kWh')
            print(f'total_amount: {elec.get("total_amount")}')
        else:
            print(f'API error: {data}')
