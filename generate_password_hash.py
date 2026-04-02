# 生成密码哈希值的脚本
from passlib.hash import pbkdf2_sha256
from app import create_app
from config import DevelopmentConfig
from utils.database import execute_update

# 创建应用实例
app = create_app(DevelopmentConfig)

# 要生成哈希的密码
password = 'admin123'

# 生成哈希值
hashed_password = pbkdf2_sha256.hash(password)
print(f"密码: {password}")
print(f"哈希值: {hashed_password}")

# 在应用程序上下文中更新数据库中的管理员密码
with app.app_context():
    try:
        update_query = """
            UPDATE [User]
            SET Password = ?
            WHERE Username = 'admin'
        """
        execute_update(update_query, (hashed_password,))
        print("数据库中的管理员密码已更新")
    except Exception as e:
        print(f"更新密码失败: {e}")

