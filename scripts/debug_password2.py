"""直接验证密码"""
import sys
sys.path.insert(0, '.')

from app import create_app
from config import DevelopmentConfig
app = create_app(DevelopmentConfig)

with app.app_context():
    from utils.database import DBConnection
    from passlib.hash import pbkdf2_sha256
    
    with DBConnection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT UserID, Username, Password FROM [User] WHERE Username = 'yyi'")
        row = cursor.fetchone()
        if row:
            stored_hash = row[2]
            print(f"用户: {row[1]}")
            print(f"完整哈希: {stored_hash}")
            print(f"哈希长度: {len(stored_hash)}")
            
            # 测试多种密码
            for pwd in ['123456', 'yyi', 'password', 'admin']:
                try:
                    result = pbkdf2_sha256.verify(pwd, stored_hash)
                    print(f"  verify('{pwd}') = {result}")
                except Exception as e:
                    print(f"  verify('{pwd}') ERROR: {e}")
            
            # 用已知正确的哈希对比
            new_hash = pbkdf2_sha256.hash('123456')
            print(f"\n新哈希(123456): {new_hash}")
            print(f"验证新哈希: {pbkdf2_sha256.verify('123456', new_hash)}")
