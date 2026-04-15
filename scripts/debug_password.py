"""检查密码哈希"""
import sys
sys.path.insert(0, '.')

from app import create_app
from config import DevelopmentConfig
app = create_app(DevelopmentConfig)

with app.app_context():
    from utils.database import DBConnection
    with DBConnection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT UserID, Username, Password FROM [User] ORDER BY UserID")
        for r in cursor.fetchall():
            pwd = r[2] or ''
            print(f"  ID={r[0]}, User={r[1]}, PwdLen={len(pwd)}, Starts={pwd[:20] if len(pwd)>20 else pwd}")
    
    # 测试 passlib 哈希
    from passlib.hash import pbkdf2_sha256
    test_hash = pbkdf2_sha256.hash('123456')
    print(f"\n新哈希测试: {test_hash[:30]}... 长度={len(test_hash)}")
    print(f"验证新哈希: {pbkdf2_sha256.verify('123456', test_hash)}")
