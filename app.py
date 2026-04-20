import os
from dotenv import load_dotenv

# 加载 .env 环境变量（必须在导入配置之前）
env_path = os.path.join(os.path.dirname(__file__), '.env')
print(f"尝试加载 .env 文件: {env_path}")
print(f".env 文件是否存在: {os.path.exists(env_path)}")

load_dotenv(env_path)
print(f"加载后环境变量 DB_DRIVER: {os.environ.get('DB_DRIVER')}")
print(f"加载后环境变量 DB_SERVER: {os.environ.get('DB_SERVER')}")

# 现在才导入配置模块
from app import create_app
from config import DevelopmentConfig, ProductionConfig, TestingConfig


CONFIG_MAP = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
}


def get_config_class():
    """根据环境变量选择配置类，默认开发环境。"""
    config_name = os.environ.get('FLASK_CONFIG', 'development').lower()
    return CONFIG_MAP.get(config_name, DevelopmentConfig)


print("开始创建应用...")
app = create_app(get_config_class())
print("应用创建成功！")

if __name__ == '__main__':
    print("开始运行应用...")
    host = os.environ.get('FLASK_HOST', '127.0.0.1')
    port = int(os.environ.get('FLASK_PORT', '5000'))
    print(f"应用配置: host={host}, port={port}, debug={bool(app.config.get('DEBUG', False))}")
    app.run(
        host=host,
        port=port,
        debug=bool(app.config.get('DEBUG', False)),
        use_reloader=False
    )
    print("应用运行结束")
