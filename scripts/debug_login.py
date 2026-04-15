"""调试登录问题"""
import sys
sys.path.insert(0, '.')

from app import create_app
from config import DevelopmentConfig

app = create_app(DevelopmentConfig)

with app.app_context():
    from app.services.auth_service import AuthService
    
    # 尝试获取最近注册的用户
    from utils.database import DBConnection
    with DBConnection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT TOP 5 UserID, Username, IsActive, UserType, Password
            FROM [User] 
            ORDER BY UserID DESC
        """)
        print("=== 最近用户 ===")
        for r in cursor.fetchall():
            print(f"  ID={r[0]}, Username={r[1]}, IsActive={r[2]}, UserType={r[3]}, HasPassword={bool(r[4])}")
    
    # 模拟登录
    print("\n=== 模拟登录测试 ===")
    
    # 用第一个非admin用户测试
    with DBConnection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT TOP 1 Username FROM [User] WHERE Username != 'admin' ORDER BY UserID DESC")
        test_user = cursor.fetchone()
    
    if test_user:
        test_username = test_user[0]
        print(f"测试用户: {test_username}")
        
        user = AuthService.get_user_by_username(test_username)
        if user:
            print(f"  user_id={user.user_id}")
            print(f"  is_active={user.is_active}")
            print(f"  user_type={user.user_type}")
            print(f"  is_merchant={user.is_merchant}")
            print(f"  has_roles={len(user.roles)}")
            print(f"  has_permissions={len(user.permissions)}")
            print(f"  get_id={user.get_id()}")
            print(f"  is_authenticated={user.is_authenticated}")
            
            # 测试密码验证
            # 用 123456 测试
            from passlib.hash import pbkdf2_sha256
            test_result = AuthService.verify_password('123456', user.password)
            print(f"  verify_password('123456')={test_result}")
        else:
            print("  用户查询返回 None!")
