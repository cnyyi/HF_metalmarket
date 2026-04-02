from flask import Flask, Blueprint

# 创建蓝图
test_bp = Blueprint('test', __name__)

# 添加路由
@test_bp.route('/list')
def test_list():
    return 'Hello, Blueprint List!'

# 创建应用实例
app = Flask(__name__)

# 注册蓝图
app.register_blueprint(test_bp, url_prefix='/test')

# 打印所有路由
print("\n===== ALL ROUTES ======")
for rule in app.url_map.iter_rules():
    print(f"{rule.rule} -> {rule.endpoint}")
print("=====================\n")

if __name__ == '__main__':
    app.run(debug=True, port=5002)