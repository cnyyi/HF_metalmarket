"""快速测试商户门户功能"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from config import DevelopmentConfig
app = create_app(DevelopmentConfig)

with app.app_context():
    from app.services.merchant_service import MerchantService

    # 1. 查看现有商户
    from utils.database import execute_query
    merchants = execute_query("SELECT TOP 3 MerchantID, MerchantName FROM Merchant ORDER BY MerchantID", fetch_type='all')
    print('=== 现有商户 ===')
    for m in merchants:
        print(f'  ID={m[0]}, Name={m[1]}')

    if merchants:
        mid = merchants[0][0]
        mname = merchants[0][1]

        # 2. 开通门户
        print(f'\n=== 为 {mname}(ID={mid}) 开通门户 ===')
        result = MerchantService.open_portal(mid)
        print(f'  结果: {result}')

        # 3. 查看门户状态
        status = MerchantService.get_portal_status(mid)
        print(f'  门户状态: {status}')

        # 4. 测试重置密码
        if status.get('enabled'):
            reset = MerchantService.reset_portal_password(mid)
            print(f'  重置密码: {reset}')

        # 5. 测试商户用户登录
        from app.services.auth_service import AuthService
        if status.get('enabled'):
            user = AuthService.login(status['username'], '123456')
            if user:
                print(f'  登录测试: OK 用户={user.real_name}, 类型={user.user_type}, 商户ID={user.merchant_id}')
                print(f'  商户名称={user.merchant_name}')
                print(f'  is_merchant={user.is_merchant}')
            else:
                print('  登录测试: FAIL')

    print('\n测试完成!')
