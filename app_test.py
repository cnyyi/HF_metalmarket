import os
import sys
from app import create_app
from config import DevelopmentConfig

# 设置Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 创建应用实例
app = create_app(DevelopmentConfig)

# 打印应用实例的id
print(f"[DEBUG] App instance id: {id(app)}")

# 打印所有路由
print("\n===== ALL ROUTES IN APP_TEST.PY =====")
for rule in app.url_map.iter_rules():
    print(f"{rule.rule} -> {rule.endpoint}")
print("==============================\n")

# 测试路由
with app.test_client() as client:
    print("\n===== TESTING ROUTES =====")
    # 测试 /test 路由
    response = client.get('/test')
    print(f"/test: {response.status_code} - {response.data.decode('utf-8')}")
    
    # 测试 /auth/ 路由
    response = client.get('/auth/')
    print(f"/auth/: {response.status_code}")
    
    # 测试 /user/list 路由
    response = client.get('/user/list')
    print(f"/user/list: {response.status_code} - {response.data.decode('utf-8')}")
    
    # 测试 /merchant/list 路由
    response = client.get('/merchant/list')
    print(f"/merchant/list: {response.status_code} - {response.data.decode('utf-8')}")
print("==============================\n")