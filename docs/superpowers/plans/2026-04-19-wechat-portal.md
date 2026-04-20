# 微信门户 实现计划

> **面向 AI 代理的工作者：** 必需子技能：使用 superpowers:subagent-driven-development（推荐）或 superpowers:executing-plans 逐任务实现此计划。步骤使用复选框（`- [ ]`）语法来跟踪进度。

**目标：** 为宏发金属交易市场新增微信门户，商户通过微信公众号H5登录、注册、申请绑定商户，审批通过后按身份权限查看电费/水费/合同/过磅/磅费数据。

**架构：** 新增 `wx_bp` 蓝图（`/wx` 前缀），独立移动端模板，复用现有 PortalService 数据查询逻辑。新增 WxAuthService 处理微信OAuth登录，WxBindService 处理商户绑定申请与审批，WxNotifyService 处理微信模板消息通知。

**技术栈：** Flask Blueprint + Jinja2 + jQuery + Bootstrap 5 + wechatpy + SQL Server (pyodbc)

**设计规格：** `docs/superpowers/specs/2026-04-19-wechat-portal-design.md`

---

## 文件结构

### 新增文件

| 文件 | 职责 |
|------|------|
| `scripts/migrate_wx_tables.sql` | 数据库迁移：创建 WxUser + MerchantBinding 表 |
| `config/wx_config.py` | 微信配置类（AppID/Secret/Token等） |
| `app/models/wx_user.py` | WxUser 模型（纯POJO） |
| `app/models/merchant_binding.py` | MerchantBinding 模型（纯POJO） |
| `app/services/wx_auth_service.py` | 微信OAuth登录 + 手机号绑定 |
| `app/services/wx_bind_service.py` | 商户绑定申请/审批/切换 |
| `app/services/wx_notify_service.py` | 微信模板消息通知 |
| `app/routes/wx.py` | 微信门户蓝图 + 装饰器 |
| `templates/wx_base.html` | 微信端移动端母版 |
| `templates/wx/auth/login.html` | 微信授权登录页 |
| `templates/wx/auth/phone.html` | 手机号绑定页 |
| `templates/wx/bind/apply.html` | 申请绑定商户页 |
| `templates/wx/bind/status.html` | 绑定状态查看页 |
| `templates/wx/index.html` | 微信门户首页 |
| `templates/wx/contracts.html` | 合同列表页 |
| `templates/wx/utility.html` | 水电费页 |
| `templates/wx/scale.html` | 过磅数据页 |
| `templates/wx/finance.html` | 缴费记录页 |
| `templates/wx/profile.html` | 个人信息页 |
| `templates/wx/switch.html` | 切换商户页 |
| `templates/merchant/bind_requests.html` | 管理端绑定审批页 |

### 修改文件

| 文件 | 变更内容 |
|------|---------|
| `config/base.py` | 增加 WX_ 前缀微信配置项 |
| `app/__init__.py` | 注册 wx_bp 蓝图 |
| `app/services/portal_service.py` | 增加 bind_role 参数做权限过滤 |
| `app/routes/merchant.py` | 增加绑定审批路由 |
| `templates/merchant/list.html` | 增加绑定审批入口按钮 |

---

## 任务 1：数据库迁移 — 创建 WxUser 和 MerchantBinding 表

**文件：**
- 创建：`scripts/migrate_wx_tables.sql`

- [ ] **步骤 1：编写迁移SQL脚本**

```sql
-- =============================================
-- 微信门户数据库迁移脚本
-- 创建 WxUser 和 MerchantBinding 表
-- =============================================

-- 1. 微信用户关联表
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'WxUser')
BEGIN
    CREATE TABLE WxUser (
        WxUserID      INT IDENTITY(1,1) PRIMARY KEY,
        OpenID        NVARCHAR(100) NOT NULL,
        UnionID       NVARCHAR(100) NULL,
        UserID        INT NULL FOREIGN KEY REFERENCES [User](UserID),
        Nickname      NVARCHAR(50) NULL,
        HeadImgUrl    NVARCHAR(500) NULL,
        PhoneNumber   NVARCHAR(20) NULL,
        CurrentMerchantID INT NULL FOREIGN KEY REFERENCES Merchant(MerchantID),
        CreateTime    DATETIME DEFAULT GETDATE(),
        UpdateTime    DATETIME NULL
    );

    -- OpenID 唯一索引
    CREATE UNIQUE INDEX IX_WxUser_OpenID ON WxUser(OpenID);

    -- UnionID 索引（可选，用于跨公众号/小程序关联）
    CREATE INDEX IX_WxUser_UnionID ON WxUser(UnionID) WHERE UnionID IS NOT NULL;

    -- UserID 索引
    CREATE INDEX IX_WxUser_UserID ON WxUser(UserID) WHERE UserID IS NOT NULL;
END
GO

-- 2. 商户绑定申请表
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'MerchantBinding')
BEGIN
    CREATE TABLE MerchantBinding (
        BindingID     INT IDENTITY(1,1) PRIMARY KEY,
        UserID        INT NOT NULL FOREIGN KEY REFERENCES [User](UserID),
        MerchantID    INT NOT NULL FOREIGN KEY REFERENCES Merchant(MerchantID),
        BindRole      NVARCHAR(20) NOT NULL,
        Status        NVARCHAR(20) NOT NULL DEFAULT N'Pending',
        ApplyTime     DATETIME DEFAULT GETDATE(),
        ApproveTime   DATETIME NULL,
        ApproverID    INT NULL FOREIGN KEY REFERENCES [User](UserID),
        RejectReason  NVARCHAR(200) NULL,
        Remark        NVARCHAR(200) NULL,
        IsActive      BIT DEFAULT 1
    );

    -- 用户+商户+状态 复合索引
    CREATE INDEX IX_MerchantBinding_UserMerchant
        ON MerchantBinding(UserID, MerchantID, Status);

    -- 状态索引（管理端查询待审批）
    CREATE INDEX IX_MerchantBinding_Status
        ON MerchantBinding(Status) WHERE Status = N'Pending';
END
GO

-- 3. 新增 UserType 枚举值 'WeChatUser'（如果不存在）
-- 注意：UserType 字段已在 Phase 1 迁移中添加
-- WeChatUser 类型用于通过微信自动注册的用户
GO

PRINT N'微信门户数据库迁移完成';
```

- [ ] **步骤 2：在数据库中执行迁移脚本**

运行：`python -c "from utils.database import execute_query; execute_query(open('scripts/migrate_wx_tables.sql', encoding='utf-8').read(), fetch_type='none'); print('迁移完成')"`
预期：输出"微信门户数据库迁移完成"

- [ ] **步骤 3：验证表已创建**

运行：`python -c "from utils.database import execute_query; r1=execute_query('SELECT COUNT(*) as cnt FROM WxUser',fetch_type='one'); r2=execute_query('SELECT COUNT(*) as cnt FROM MerchantBinding',fetch_type='one'); print(f'WxUser: {r1.cnt}, MerchantBinding: {r2.cnt}')"`
预期：两张表计数为0，无报错

- [ ] **步骤 4：Commit**

```bash
git add scripts/migrate_wx_tables.sql
git commit -m "feat(wx): 添加微信门户数据库迁移脚本"
```

---

## 任务 2：微信配置 + 模型层

**文件：**
- 创建：`config/wx_config.py`
- 创建：`app/models/wx_user.py`
- 创建：`app/models/merchant_binding.py`
- 修改：`config/base.py`

- [ ] **步骤 1：创建微信配置类**

创建 `config/wx_config.py`：

```python
import os


class WxConfig:
    WX_APP_ID = os.environ.get('WX_APP_ID', '')
    WX_APP_SECRET = os.environ.get('WX_APP_SECRET', '')
    WX_TOKEN = os.environ.get('WX_TOKEN', '')
    WX_ENCODING_AES_KEY = os.environ.get('WX_ENCODING_AES_KEY', '')
    WX_TEMPLATE_BIND_RESULT = os.environ.get('WX_TEMPLATE_BIND_RESULT', '')
```

- [ ] **步骤 2：在 base.py 中引入微信配置**

在 `config/base.py` 的 `Config` 类末尾添加：

```python
    WX_APP_ID = os.environ.get('WX_APP_ID', '')
    WX_APP_SECRET = os.environ.get('WX_APP_SECRET', '')
    WX_TOKEN = os.environ.get('WX_TOKEN', '')
    WX_ENCODING_AES_KEY = os.environ.get('WX_ENCODING_AES_KEY', '')
    WX_TEMPLATE_BIND_RESULT = os.environ.get('WX_TEMPLATE_BIND_RESULT', '')
```

- [ ] **步骤 3：创建 WxUser 模型**

创建 `app/models/wx_user.py`：

```python
import datetime


class WxUser:
    def __init__(self, wx_user_id=None, openid=None, unionid=None,
                 user_id=None, nickname=None, head_img_url=None,
                 phone_number=None, current_merchant_id=None,
                 create_time=None, update_time=None):
        self.wx_user_id = wx_user_id
        self.openid = openid
        self.unionid = unionid
        self.user_id = user_id
        self.nickname = nickname
        self.head_img_url = head_img_url
        self.phone_number = phone_number
        self.current_merchant_id = current_merchant_id
        self.create_time = create_time or datetime.datetime.now()
        self.update_time = update_time
```

- [ ] **步骤 4：创建 MerchantBinding 模型**

创建 `app/models/merchant_binding.py`：

```python
import datetime


class MerchantBinding:
    STATUS_PENDING = 'Pending'
    STATUS_APPROVED = 'Approved'
    STATUS_REJECTED = 'Rejected'
    STATUS_CANCELLED = 'Cancelled'

    ROLE_BOSS = 'Boss'
    ROLE_STAFF = 'Staff'
    ROLE_FINANCE = 'Finance'

    ROLE_CHOICES = [
        (ROLE_BOSS, '老板'),
        (ROLE_STAFF, '员工'),
        (ROLE_FINANCE, '财务'),
    ]

    def __init__(self, binding_id=None, user_id=None, merchant_id=None,
                 bind_role=None, status=None, apply_time=None,
                 approve_time=None, approver_id=None, reject_reason=None,
                 remark=None, is_active=True,
                 merchant_name=None, user_real_name=None):
        self.binding_id = binding_id
        self.user_id = user_id
        self.merchant_id = merchant_id
        self.bind_role = bind_role
        self.status = status or self.STATUS_PENDING
        self.apply_time = apply_time or datetime.datetime.now()
        self.approve_time = approve_time
        self.approver_id = approver_id
        self.reject_reason = reject_reason
        self.remark = remark
        self.is_active = is_active
        self.merchant_name = merchant_name
        self.user_real_name = user_real_name

    @property
    def bind_role_display(self):
        role_map = {self.ROLE_BOSS: '老板', self.ROLE_STAFF: '员工', self.ROLE_FINANCE: '财务'}
        return role_map.get(self.bind_role, self.bind_role)

    @property
    def status_display(self):
        status_map = {
            self.STATUS_PENDING: '待审批',
            self.STATUS_APPROVED: '已通过',
            self.STATUS_REJECTED: '已驳回',
            self.STATUS_CANCELLED: '已取消',
        }
        return status_map.get(self.status, self.status)
```

- [ ] **步骤 5：验证模型可导入**

运行：`python -c "from app.models.wx_user import WxUser; from app.models.merchant_binding import MerchantBinding; print('模型导入成功')"`
预期：输出"模型导入成功"

- [ ] **步骤 6：Commit**

```bash
git add config/wx_config.py config/base.py app/models/wx_user.py app/models/merchant_binding.py
git commit -m "feat(wx): 添加微信配置和模型层"
```

---

## 任务 3：WxAuthService — 微信OAuth登录 + 手机号绑定

**文件：**
- 创建：`app/services/wx_auth_service.py`

- [ ] **步骤 1：编写 WxAuthService**

创建 `app/services/wx_auth_service.py`：

```python
import datetime
import logging
import uuid
from flask import current_app
from wechatpy import WeChatOAuth
from wechatpy.exceptions import WeChatClientException
from utils.database import execute_query, execute_update
from app.models.wx_user import WxUser
from app.models.user import User
from app.services.auth_service import AuthService

logger = logging.getLogger(__name__)


class WxAuthService:

    @staticmethod
    def get_oauth_client():
        return WeChatOAuth(
            app_id=current_app.config.get('WX_APP_ID', ''),
            secret=current_app.config.get('WX_APP_SECRET', ''),
            redirect_uri='',
            scope='snsapi_userinfo',
        )

    @staticmethod
    def get_auth_url(redirect_uri, state=None):
        oauth = WxAuthService.get_oauth_client()
        oauth.redirect_uri = redirect_uri
        if not state:
            state = uuid.uuid4().hex[:16]
        return oauth.authorize_url(state=state), state

    @staticmethod
    def handle_callback(code):
        oauth = WxAuthService.get_oauth_client()
        try:
            token_data = oauth.fetch_access_token(code)
            openid = token_data.get('openid', '')
            access_token = token_data.get('access_token', '')
            unionid = token_data.get('unionid', '')
        except WeChatClientException as e:
            logger.error(f'微信OAuth回调失败: {e}')
            return None

        if not openid:
            return None

        wx_user = WxAuthService.get_wx_user(openid)
        if wx_user:
            user = AuthService.get_user_by_id(wx_user.user_id) if wx_user.user_id else None
            if user and user.is_active:
                return user
            return None

        nickname = ''
        head_img_url = ''
        try:
            user_info = oauth.get_user_info(access_token, openid)
            nickname = user_info.get('nickname', '')
            head_img_url = user_info.get('headimgurl', '')
        except WeChatClientException:
            pass

        user, wx_user = WxAuthService.create_wx_user(openid, unionid, nickname, head_img_url)
        return user

    @staticmethod
    def get_wx_user(openid):
        query = """
            SELECT WxUserID, OpenID, UnionID, UserID, Nickname, HeadImgUrl,
                   PhoneNumber, CurrentMerchantID, CreateTime, UpdateTime
            FROM WxUser WHERE OpenID = ?
        """
        result = execute_query(query, (openid,), fetch_type='one')
        if not result:
            return None
        return WxUser(
            wx_user_id=result.WxUserID,
            openid=result.OpenID,
            unionid=result.UnionID,
            user_id=result.UserID,
            nickname=result.Nickname,
            head_img_url=result.HeadImgUrl,
            phone_number=result.PhoneNumber,
            current_merchant_id=result.CurrentMerchantID,
            create_time=result.CreateTime,
            update_time=result.UpdateTime,
        )

    @staticmethod
    def get_wx_user_by_user_id(user_id):
        query = """
            SELECT WxUserID, OpenID, UnionID, UserID, Nickname, HeadImgUrl,
                   PhoneNumber, CurrentMerchantID, CreateTime, UpdateTime
            FROM WxUser WHERE UserID = ?
        """
        result = execute_query(query, (user_id,), fetch_type='one')
        if not result:
            return None
        return WxUser(
            wx_user_id=result.WxUserID,
            openid=result.OpenID,
            unionid=result.UnionID,
            user_id=result.UserID,
            nickname=result.Nickname,
            head_img_url=result.HeadImgUrl,
            phone_number=result.PhoneNumber,
            current_merchant_id=result.CurrentMerchantID,
            create_time=result.CreateTime,
            update_time=result.UpdateTime,
        )

    @staticmethod
    def create_wx_user(openid, unionid, nickname, head_img_url):
        from utils.database import DBConnection
        username = f'wx_{uuid.uuid4().hex[:12]}'
        hashed_password = AuthService.hash_password(uuid.uuid4().hex)

        insert_user_query = """
            INSERT INTO [User] (Username, Password, RealName, Phone, Email, IsActive, CreateTime, UserType)
            VALUES (?, ?, ?, '', '', 1, ?, N'WeChatUser')
        """
        execute_update(insert_user_query, (username, hashed_password, nickname or '微信用户', datetime.datetime.now()))

        with DBConnection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT CAST(SCOPE_IDENTITY() AS INT)")
            row = cursor.fetchone()
            new_user_id = row[0] if row else None

        if not new_user_id:
            return None, None

        role = execute_query("SELECT RoleID FROM Role WHERE RoleCode = 'merchant'", fetch_type='one')
        if role:
            execute_update(
                "INSERT INTO UserRole (UserID, RoleID, CreateTime) VALUES (?, ?, ?)",
                (new_user_id, role.RoleID, datetime.datetime.now()),
            )

        insert_wx_query = """
            INSERT INTO WxUser (OpenID, UnionID, UserID, Nickname, HeadImgUrl, CreateTime)
            VALUES (?, ?, ?, ?, ?, ?)
        """
        execute_update(insert_wx_query, (openid, unionid or '', new_user_id, nickname, head_img_url, datetime.datetime.now()))

        user = AuthService.get_user_by_id(new_user_id)
        wx_user = WxAuthService.get_wx_user(openid)
        return user, wx_user

    @staticmethod
    def bind_phone(wx_user_id, phone, sms_code):
        stored_code = WxAuthService._get_sms_code(phone)
        if not stored_code or stored_code != sms_code:
            return {'success': False, 'message': '验证码错误或已过期'}

        execute_update("""
            UPDATE WxUser SET PhoneNumber = ?, UpdateTime = ? WHERE WxUserID = ?
        """, (phone, datetime.datetime.now(), wx_user_id))

        existing_user = execute_query(
            "SELECT UserID, Username FROM [User] WHERE Phone = ? AND UserType != N'WeChatUser'",
            (phone,), fetch_type='one',
        )
        if existing_user:
            return {'success': True, 'message': '手机号绑定成功', 'has_existing_account': True, 'existing_user_id': existing_user.UserID}

        return {'success': True, 'message': '手机号绑定成功', 'has_existing_account': False}

    @staticmethod
    def send_sms_code(phone):
        import random
        code = str(random.randint(100000, 999999))
        WxAuthService._store_sms_code(phone, code)
        logger.info(f'短信验证码已生成: phone={phone}, code={code}')
        return {'success': True, 'message': '验证码已发送'}

    @staticmethod
    def _store_sms_code(phone, code):
        from flask import session
        session_key = f'sms_code_{phone}'
        session_data = {'code': code, 'expire': (datetime.datetime.now() + datetime.timedelta(minutes=5)).isoformat()}
        session = __import__('flask').session
        session[session_key] = session_data

    @staticmethod
    def _get_sms_code(phone):
        from flask import session as flask_session
        session_key = f'sms_code_{phone}'
        data = flask_session.get(session_key)
        if not data:
            return None
        expire_str = data.get('expire', '')
        if not expire_str:
            return None
        expire_time = datetime.datetime.fromisoformat(expire_str)
        if datetime.datetime.now() > expire_time:
            flask_session.pop(session_key, None)
            return None
        return data.get('code')
```

- [ ] **步骤 2：验证服务可导入**

运行：`python -c "from app.services.wx_auth_service import WxAuthService; print('WxAuthService 导入成功')"`
预期：输出"WxAuthService 导入成功"

- [ ] **步骤 3：Commit**

```bash
git add app/services/wx_auth_service.py
git commit -m "feat(wx): 添加微信OAuth登录和手机号绑定服务"
```

---

## 任务 4：WxBindService — 商户绑定申请/审批/切换

**文件：**
- 创建：`app/services/wx_bind_service.py`

- [ ] **步骤 1：编写 WxBindService**

创建 `app/services/wx_bind_service.py`：

```python
import datetime
import logging
from utils.database import execute_query, execute_update, DBConnection
from app.models.merchant_binding import MerchantBinding

logger = logging.getLogger(__name__)


class WxBindService:

    @staticmethod
    def apply_binding(user_id, merchant_id, bind_role, remark=None):
        existing = execute_query("""
            SELECT BindingID FROM MerchantBinding
            WHERE UserID = ? AND MerchantID = ? AND Status = N'Pending' AND IsActive = 1
        """, (user_id, merchant_id), fetch_type='one')
        if existing:
            return {'success': False, 'message': '您已提交过该商户的绑定申请，请等待审批'}

        approved = execute_query("""
            SELECT BindingID FROM MerchantBinding
            WHERE UserID = ? AND MerchantID = ? AND Status = N'Approved' AND IsActive = 1
        """, (user_id, merchant_id), fetch_type='one')
        if approved:
            return {'success': False, 'message': '您已绑定该商户'}

        insert_query = """
            INSERT INTO MerchantBinding (UserID, MerchantID, BindRole, Status, ApplyTime, Remark, IsActive)
            VALUES (?, ?, ?, N'Pending', ?, ?, 1)
        """
        execute_update(insert_query, (user_id, merchant_id, bind_role, datetime.datetime.now(), remark or ''))

        return {'success': True, 'message': '绑定申请已提交，请等待管理员审批'}

    @staticmethod
    def cancel_binding(binding_id, user_id):
        binding = execute_query(
            "SELECT BindingID, Status FROM MerchantBinding WHERE BindingID = ? AND UserID = ?",
            (binding_id, user_id), fetch_type='one',
        )
        if not binding:
            return {'success': False, 'message': '绑定记录不存在'}
        if binding.Status != 'Pending':
            return {'success': False, 'message': '只能取消待审批的申请'}

        execute_update("""
            UPDATE MerchantBinding SET Status = N'Cancelled', IsActive = 0 WHERE BindingID = ?
        """, (binding_id,))
        return {'success': True, 'message': '已取消绑定申请'}

    @staticmethod
    def get_user_bindings(user_id):
        query = """
            SELECT mb.BindingID, mb.UserID, mb.MerchantID, mb.BindRole, mb.Status,
                   mb.ApplyTime, mb.ApproveTime, mb.RejectReason, mb.Remark,
                   m.MerchantName
            FROM MerchantBinding mb
            LEFT JOIN Merchant m ON mb.MerchantID = m.MerchantID
            WHERE mb.UserID = ? AND mb.IsActive = 1
            ORDER BY mb.ApplyTime DESC
        """
        results = execute_query(query, (user_id,), fetch_type='all')
        bindings = []
        for r in results:
            bindings.append(MerchantBinding(
                binding_id=r.BindingID,
                user_id=r.UserID,
                merchant_id=r.MerchantID,
                bind_role=r.BindRole,
                status=r.Status,
                apply_time=r.ApplyTime,
                approve_time=r.ApproveTime,
                reject_reason=r.RejectReason,
                remark=r.Remark,
                merchant_name=r.MerchantName,
            ))
        return bindings

    @staticmethod
    def get_approved_bindings(user_id):
        query = """
            SELECT mb.BindingID, mb.UserID, mb.MerchantID, mb.BindRole, mb.Status,
                   m.MerchantName
            FROM MerchantBinding mb
            LEFT JOIN Merchant m ON mb.MerchantID = m.MerchantID
            WHERE mb.UserID = ? AND mb.Status = N'Approved' AND mb.IsActive = 1
            ORDER BY mb.ApplyTime DESC
        """
        results = execute_query(query, (user_id,), fetch_type='all')
        bindings = []
        for r in results:
            bindings.append(MerchantBinding(
                binding_id=r.BindingID,
                user_id=r.UserID,
                merchant_id=r.MerchantID,
                bind_role=r.BindRole,
                status=r.Status,
                merchant_name=r.MerchantName,
            ))
        return bindings

    @staticmethod
    def get_pending_requests(merchant_id=None):
        conditions = ["mb.Status = N'Pending'", "mb.IsActive = 1"]
        params = []
        if merchant_id:
            conditions.append("mb.MerchantID = ?")
            params.append(merchant_id)

        where = " AND ".join(conditions)
        query = f"""
            SELECT mb.BindingID, mb.UserID, mb.MerchantID, mb.BindRole, mb.Status,
                   mb.ApplyTime, mb.Remark,
                   m.MerchantName, u.RealName AS UserRealName, u.Phone
            FROM MerchantBinding mb
            LEFT JOIN Merchant m ON mb.MerchantID = m.MerchantID
            LEFT JOIN [User] u ON mb.UserID = u.UserID
            WHERE {where}
            ORDER BY mb.ApplyTime DESC
        """
        results = execute_query(query, tuple(params), fetch_type='all')
        items = []
        for r in results:
            items.append({
                'binding_id': r.BindingID,
                'user_id': r.UserID,
                'merchant_id': r.MerchantID,
                'bind_role': r.BindRole,
                'status': r.Status,
                'apply_time': r.ApplyTime.strftime('%Y-%m-%d %H:%M') if r.ApplyTime else '',
                'remark': r.Remark or '',
                'merchant_name': r.MerchantName or '',
                'user_real_name': r.UserRealName or '',
                'phone': r.Phone or '',
            })
        return items

    @staticmethod
    def approve_binding(binding_id, approver_id):
        binding = execute_query(
            "SELECT BindingID, UserID, MerchantID, BindRole FROM MerchantBinding WHERE BindingID = ? AND Status = N'Pending'",
            (binding_id,), fetch_type='one',
        )
        if not binding:
            return {'success': False, 'message': '绑定申请不存在或已处理'}

        execute_update("""
            UPDATE MerchantBinding
            SET Status = N'Approved', ApproveTime = ?, ApproverID = ?
            WHERE BindingID = ?
        """, (datetime.datetime.now(), approver_id, binding_id))

        user_approved = execute_query("""
            SELECT BindingID FROM MerchantBinding
            WHERE UserID = ? AND MerchantID = ? AND Status = N'Approved' AND IsActive = 1
        """, (binding.UserID, binding.MerchantID), fetch_type='one')

        if not user_approved or user_approved.BindingID == binding_id:
            execute_update("""
                UPDATE [User] SET MerchantID = ? WHERE UserID = ? AND (MerchantID IS NULL OR MerchantID = 0)
            """, (binding.MerchantID, binding.UserID))

        wx_user = execute_query(
            "SELECT WxUserID FROM WxUser WHERE UserID = ?", (binding.UserID,), fetch_type='one',
        )
        if wx_user:
            execute_update("""
                UPDATE WxUser SET CurrentMerchantID = ? WHERE WxUserID = ? AND (CurrentMerchantID IS NULL OR CurrentMerchantID = 0)
            """, (binding.MerchantID, wx_user.WxUserID))

        merchant = execute_query(
            "SELECT MerchantName FROM Merchant WHERE MerchantID = ?",
            (binding.MerchantID,), fetch_type='one',
        )
        merchant_name = merchant.MerchantName if merchant else ''

        return {'success': True, 'message': f'已通过 {merchant_name} 的绑定申请', 'openid': '', 'merchant_name': merchant_name, 'bind_role': binding.BindRole}

    @staticmethod
    def reject_binding(binding_id, approver_id, reason):
        binding = execute_query(
            "SELECT BindingID, UserID, MerchantID FROM MerchantBinding WHERE BindingID = ? AND Status = N'Pending'",
            (binding_id,), fetch_type='one',
        )
        if not binding:
            return {'success': False, 'message': '绑定申请不存在或已处理'}

        execute_update("""
            UPDATE MerchantBinding
            SET Status = N'Rejected', ApproveTime = ?, ApproverID = ?, RejectReason = ?
            WHERE BindingID = ?
        """, (datetime.datetime.now(), approver_id, reason or '', binding_id))

        merchant = execute_query(
            "SELECT MerchantName FROM Merchant WHERE MerchantID = ?",
            (binding.MerchantID,), fetch_type='one',
        )
        merchant_name = merchant.MerchantName if merchant else ''

        return {'success': True, 'message': f'已驳回 {merchant_name} 的绑定申请', 'openid': '', 'merchant_name': merchant_name, 'reason': reason or ''}

    @staticmethod
    def get_user_current_merchant(user_id):
        wx_user = execute_query(
            "SELECT CurrentMerchantID FROM WxUser WHERE UserID = ?",
            (user_id,), fetch_type='one',
        )
        merchant_id = None
        if wx_user and wx_user.CurrentMerchantID:
            merchant_id = wx_user.CurrentMerchantID
        else:
            user = execute_query(
                "SELECT MerchantID FROM [User] WHERE UserID = ?",
                (user_id,), fetch_type='one',
            )
            if user and user.MerchantID:
                merchant_id = user.MerchantID

        if not merchant_id:
            return None

        merchant = execute_query(
            "SELECT MerchantID, MerchantName FROM Merchant WHERE MerchantID = ?",
            (merchant_id,), fetch_type='one',
        )
        if not merchant:
            return None
        return {'merchant_id': merchant.MerchantID, 'merchant_name': merchant.MerchantName}

    @staticmethod
    def get_user_bind_role(user_id, merchant_id):
        binding = execute_query("""
            SELECT BindRole FROM MerchantBinding
            WHERE UserID = ? AND MerchantID = ? AND Status = N'Approved' AND IsActive = 1
        """, (user_id, merchant_id), fetch_type='one')
        if binding:
            return binding.BindRole
        return None

    @staticmethod
    def switch_merchant(user_id, merchant_id):
        approved = execute_query("""
            SELECT BindingID FROM MerchantBinding
            WHERE UserID = ? AND MerchantID = ? AND Status = N'Approved' AND IsActive = 1
        """, (user_id, merchant_id), fetch_type='one')
        if not approved:
            return {'success': False, 'message': '您未绑定该商户'}

        execute_update("""
            UPDATE WxUser SET CurrentMerchantID = ?, UpdateTime = ? WHERE UserID = ?
        """, (merchant_id, datetime.datetime.now(), user_id))

        execute_update("""
            UPDATE [User] SET MerchantID = ? WHERE UserID = ?
        """, (merchant_id, user_id))

        return {'success': True, 'message': '已切换商户'}
```

- [ ] **步骤 2：验证服务可导入**

运行：`python -c "from app.services.wx_bind_service import WxBindService; print('WxBindService 导入成功')"`
预期：输出"WxBindService 导入成功"

- [ ] **步骤 3：Commit**

```bash
git add app/services/wx_bind_service.py
git commit -m "feat(wx): 添加商户绑定申请/审批/切换服务"
```

---

## 任务 5：WxNotifyService — 微信模板消息通知

**文件：**
- 创建：`app/services/wx_notify_service.py`

- [ ] **步骤 1：编写 WxNotifyService**

创建 `app/services/wx_notify_service.py`：

```python
import logging
from flask import current_app
from utils.database import execute_query

logger = logging.getLogger(__name__)


class WxNotifyService:

    @staticmethod
    def _get_wechat_client():
        from wechatpy import WeChatClient
        app_id = current_app.config.get('WX_APP_ID', '')
        secret = current_app.config.get('WX_APP_SECRET', '')
        return WeChatClient(app_id, secret)

    @staticmethod
    def send_bind_approved(openid, merchant_name, bind_role):
        template_id = current_app.config.get('WX_TEMPLATE_BIND_RESULT', '')
        if not template_id or not openid:
            logger.warning('微信模板消息配置缺失或openid为空，跳过通知')
            return False

        role_map = {'Boss': '老板', 'Staff': '员工', 'Finance': '财务'}
        try:
            client = WxNotifyService._get_wechat_client()
            client.message.send_template(
                user_id=openid,
                template_id=template_id,
                data={
                    'first': {'value': '您的商户绑定申请已通过'},
                    'keyword1': {'value': merchant_name},
                    'keyword2': {'value': role_map.get(bind_role, bind_role)},
                    'keyword3': {'value': '已通过'},
                    'remark': {'value': '您现在可以登录查看商户数据了'},
                },
            )
            logger.info(f'绑定通过通知已发送: openid={openid}, merchant={merchant_name}')
            return True
        except Exception as e:
            logger.error(f'发送微信模板消息失败: {e}')
            return False

    @staticmethod
    def send_bind_rejected(openid, merchant_name, reason):
        template_id = current_app.config.get('WX_TEMPLATE_BIND_RESULT', '')
        if not template_id or not openid:
            logger.warning('微信模板消息配置缺失或openid为空，跳过通知')
            return False

        try:
            client = WxNotifyService._get_wechat_client()
            client.message.send_template(
                user_id=openid,
                template_id=template_id,
                data={
                    'first': {'value': '您的商户绑定申请已被驳回'},
                    'keyword1': {'value': merchant_name},
                    'keyword2': {'value': '-'},
                    'keyword3': {'value': '已驳回'},
                    'remark': {'value': f'驳回原因：{reason or "无"}'},
                },
            )
            logger.info(f'绑定驳回通知已发送: openid={openid}, merchant={merchant_name}')
            return True
        except Exception as e:
            logger.error(f'发送微信模板消息失败: {e}')
            return False

    @staticmethod
    def send_new_bind_request(admin_openids, merchant_name, user_name):
        template_id = current_app.config.get('WX_TEMPLATE_BIND_RESULT', '')
        if not template_id:
            logger.warning('微信模板消息配置缺失，跳过管理员通知')
            return False

        for openid in admin_openids:
            if not openid:
                continue
            try:
                client = WxNotifyService._get_wechat_client()
                client.message.send_template(
                    user_id=openid,
                    template_id=template_id,
                    data={
                        'first': {'value': '收到新的商户绑定申请'},
                        'keyword1': {'value': merchant_name},
                        'keyword2': {'value': user_name},
                        'keyword3': {'value': '待审批'},
                        'remark': {'value': '请登录管理后台进行审批'},
                    },
                )
            except Exception as e:
                logger.error(f'发送管理员通知失败: openid={openid}, error={e}')
        return True
```

- [ ] **步骤 2：验证服务可导入**

运行：`python -c "from app.services.wx_notify_service import WxNotifyService; print('WxNotifyService 导入成功')"`
预期：输出"WxNotifyService 导入成功"

- [ ] **步骤 3：Commit**

```bash
git add app/services/wx_notify_service.py
git commit -m "feat(wx): 添加微信模板消息通知服务"
```

---

## 任务 6：wx_bp 蓝图 — 微信门户路由 + 装饰器

**文件：**
- 创建：`app/routes/wx.py`
- 修改：`app/__init__.py`

- [ ] **步骤 1：编写 wx_bp 蓝图**

创建 `app/routes/wx.py`：

```python
from functools import wraps
from flask import Blueprint, render_template, redirect, url_for, request, jsonify, session, current_app
from flask_login import login_required, current_user, login_user
from app.services.wx_auth_service import WxAuthService
from app.services.wx_bind_service import WxBindService
from app.services.portal_service import PortalService

wx_bp = Blueprint('wx', __name__, url_prefix='/wx')


def wx_login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('wx.login'))
        return f(*args, **kwargs)
    return decorated


def wx_bound_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('wx.login'))
        merchant = WxBindService.get_user_current_merchant(current_user.user_id)
        if not merchant:
            return redirect(url_for('wx.bind_apply'))
        return f(*args, **kwargs)
    return decorated


def wx_role_allowed(*allowed_roles):
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            if not current_user.is_authenticated:
                return redirect(url_for('wx.login'))
            merchant = WxBindService.get_user_current_merchant(current_user.user_id)
            if not merchant:
                return redirect(url_for('wx.bind_apply'))
            bind_role = WxBindService.get_user_bind_role(current_user.user_id, merchant['merchant_id'])
            if bind_role not in allowed_roles and bind_role != 'Boss':
                return jsonify({'success': False, 'message': '您没有权限查看此数据'}), 403
            return f(*args, **kwargs)
        return decorated
    return decorator


def _get_current_merchant_id():
    merchant = WxBindService.get_user_current_merchant(current_user.user_id)
    return merchant['merchant_id'] if merchant else None


def _get_current_bind_role():
    merchant_id = _get_current_merchant_id()
    if not merchant_id:
        return None
    return WxBindService.get_user_bind_role(current_user.user_id, merchant_id)


@wx_bp.route('/auth/login')
def login():
    redirect_uri = request.host_url.rstrip('/') + url_for('wx.callback')
    auth_url, state = WxAuthService.get_auth_url(redirect_uri, state=None)
    session['wx_oauth_state'] = state
    return redirect(auth_url)


@wx_bp.route('/auth/callback')
def callback():
    code = request.args.get('code', '')
    state = request.args.get('state', '')
    if not code:
        return redirect(url_for('wx.login'))

    user = WxAuthService.handle_callback(code)
    if not user:
        return render_template('wx/auth/login.html', error='微信授权登录失败，请重试')

    login_user(user)
    merchant = WxBindService.get_user_current_merchant(user.user_id)
    if merchant:
        return redirect(url_for('wx.index'))
    return redirect(url_for('wx.bind_apply'))


@wx_bp.route('/auth/phone', methods=['GET'])
@wx_login_required
def phone_page():
    return render_template('wx/auth/phone.html')


@wx_bp.route('/auth/phone', methods=['POST'])
@wx_login_required
def phone_bind():
    data = request.get_json() or {}
    phone = data.get('phone', '').strip()
    sms_code = data.get('code', '').strip()
    if not phone or not sms_code:
        return jsonify({'success': False, 'message': '请输入手机号和验证码'})

    wx_user = WxAuthService.get_wx_user_by_user_id(current_user.user_id)
    if not wx_user:
        return jsonify({'success': False, 'message': '微信用户信息不存在'})

    result = WxAuthService.bind_phone(wx_user.wx_user_id, phone, sms_code)
    return jsonify(result)


@wx_bp.route('/auth/send-sms', methods=['POST'])
def send_sms():
    data = request.get_json() or {}
    phone = data.get('phone', '').strip()
    if not phone:
        return jsonify({'success': False, 'message': '请输入手机号'})
    result = WxAuthService.send_sms_code(phone)
    return jsonify(result)


@wx_bp.route('/bind/apply', methods=['GET'])
@wx_login_required
def bind_apply():
    return render_template('wx/bind/apply.html')


@wx_bp.route('/bind/status', methods=['GET'])
@wx_login_required
def bind_status():
    return render_template('wx/bind/status.html')


@wx_bp.route('/api/bind/apply', methods=['POST'])
@wx_login_required
def api_bind_apply():
    data = request.get_json() or {}
    merchant_id = data.get('merchant_id')
    bind_role = data.get('bind_role', '').strip()
    remark = data.get('remark', '').strip()
    if not merchant_id or not bind_role:
        return jsonify({'success': False, 'message': '请选择商户和身份'})
    if bind_role not in ('Boss', 'Staff', 'Finance'):
        return jsonify({'success': False, 'message': '无效的身份类型'})

    result = WxBindService.apply_binding(current_user.user_id, merchant_id, bind_role, remark)
    return jsonify(result)


@wx_bp.route('/api/bind/cancel', methods=['POST'])
@wx_login_required
def api_bind_cancel():
    data = request.get_json() or {}
    binding_id = data.get('binding_id')
    if not binding_id:
        return jsonify({'success': False, 'message': '参数错误'})
    result = WxBindService.cancel_binding(binding_id, current_user.user_id)
    return jsonify(result)


@wx_bp.route('/api/bindings', methods=['GET'])
@wx_login_required
def api_bindings():
    bindings = WxBindService.get_user_bindings(current_user.user_id)
    items = []
    for b in bindings:
        items.append({
            'binding_id': b.binding_id,
            'merchant_id': b.merchant_id,
            'merchant_name': b.merchant_name or '',
            'bind_role': b.bind_role,
            'bind_role_display': b.bind_role_display,
            'status': b.status,
            'status_display': b.status_display,
            'apply_time': b.apply_time.strftime('%Y-%m-%d %H:%M') if b.apply_time else '',
            'reject_reason': b.reject_reason or '',
        })
    return jsonify({'success': True, 'data': items})


@wx_bp.route('/api/merchants', methods=['GET'])
@wx_login_required
def api_merchants():
    search = request.args.get('search', '').strip()
    query = """
        SELECT TOP 20 MerchantID, MerchantName, ContactPerson, Phone
        FROM Merchant WHERE Status = N'正常'
    """
    params = []
    if search:
        query += " AND MerchantName LIKE ?"
        params.append(f'%{search}%')
    query += " ORDER BY MerchantName"
    results = execute_query(query, tuple(params), fetch_type='all') if params else execute_query(query, fetch_type='all')
    items = [{'merchant_id': r.MerchantID, 'merchant_name': r.MerchantName, 'contact_person': r.ContactPerson or '', 'phone': r.Phone or ''} for r in results]
    return jsonify({'success': True, 'data': items})


@wx_bp.route('/')
@wx_login_required
@wx_bound_required
def index():
    return render_template('wx/index.html')


@wx_bp.route('/api/dashboard')
@wx_login_required
@wx_bound_required
def api_dashboard():
    merchant_id = _get_current_merchant_id()
    if not merchant_id:
        return jsonify({'success': False, 'message': '未绑定商户'}), 403
    try:
        stats = PortalService.get_dashboard(merchant_id)
        return jsonify({'success': True, 'data': stats})
    except Exception as e:
        return jsonify({'success': False, 'message': f'获取数据失败：{str(e)}'}), 500


@wx_bp.route('/contracts')
@wx_login_required
@wx_role_allowed('Staff')
def contracts():
    return render_template('wx/contracts.html')


@wx_bp.route('/api/contracts')
@wx_login_required
@wx_role_allowed('Staff')
def api_contracts():
    merchant_id = _get_current_merchant_id()
    if not merchant_id:
        return jsonify({'success': False, 'message': '未绑定商户'}), 403
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    try:
        result = PortalService.get_contracts(merchant_id, page=page, per_page=per_page)
        return jsonify({'success': True, 'data': result})
    except Exception as e:
        return jsonify({'success': False, 'message': f'获取数据失败：{str(e)}'}), 500


@wx_bp.route('/utility')
@wx_login_required
@wx_role_allowed('Finance')
def utility():
    return render_template('wx/utility.html')


@wx_bp.route('/api/utility')
@wx_login_required
@wx_role_allowed('Finance')
def api_utility():
    merchant_id = _get_current_merchant_id()
    if not merchant_id:
        return jsonify({'success': False, 'message': '未绑定商户'}), 403
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    try:
        result = PortalService.get_utility_readings(merchant_id, page=page, per_page=per_page)
        return jsonify({'success': True, 'data': result})
    except Exception as e:
        return jsonify({'success': False, 'message': f'获取数据失败：{str(e)}'}), 500


@wx_bp.route('/scale')
@wx_login_required
@wx_role_allowed('Staff')
def scale():
    return render_template('wx/scale.html')


@wx_bp.route('/api/scale-records')
@wx_login_required
@wx_role_allowed('Staff')
def api_scale_records():
    merchant_id = _get_current_merchant_id()
    if not merchant_id:
        return jsonify({'success': False, 'message': '未绑定商户'}), 403
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    try:
        result = PortalService.get_scale_records(merchant_id, page=page, per_page=per_page)
        return jsonify({'success': True, 'data': result})
    except Exception as e:
        return jsonify({'success': False, 'message': f'获取数据失败：{str(e)}'}), 500


@wx_bp.route('/finance')
@wx_login_required
@wx_role_allowed('Finance')
def finance():
    return render_template('wx/finance.html')


@wx_bp.route('/api/receivables')
@wx_login_required
@wx_role_allowed('Finance')
def api_receivables():
    merchant_id = _get_current_merchant_id()
    if not merchant_id:
        return jsonify({'success': False, 'message': '未绑定商户'}), 403
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    status = request.args.get('status', '').strip()
    try:
        result = PortalService.get_receivables(merchant_id, page=page, per_page=per_page, status=status or None)
        return jsonify({'success': True, 'data': result})
    except Exception as e:
        return jsonify({'success': False, 'message': f'获取数据失败：{str(e)}'}), 500


@wx_bp.route('/profile')
@wx_login_required
def profile():
    return render_template('wx/profile.html')


@wx_bp.route('/switch')
@wx_login_required
@wx_bound_required
def switch():
    return render_template('wx/switch.html')


@wx_bp.route('/api/switch', methods=['POST'])
@wx_login_required
@wx_bound_required
def api_switch():
    data = request.get_json() or {}
    merchant_id = data.get('merchant_id')
    if not merchant_id:
        return jsonify({'success': False, 'message': '请选择商户'})
    result = WxBindService.switch_merchant(current_user.user_id, merchant_id)
    return jsonify(result)


@wx_bp.route('/api/current-merchant')
@wx_login_required
def api_current_merchant():
    merchant = WxBindService.get_user_current_merchant(current_user.user_id)
    if not merchant:
        return jsonify({'success': True, 'data': None})
    bind_role = WxBindService.get_user_bind_role(current_user.user_id, merchant['merchant_id'])
    return jsonify({'success': True, 'data': {'merchant_id': merchant['merchant_id'], 'merchant_name': merchant['merchant_name'], 'bind_role': bind_role}})
```

- [ ] **步骤 2：修复 api_merchants 中的 execute_query 导入**

在 `app/routes/wx.py` 顶部添加导入：

```python
from utils.database import execute_query
```

- [ ] **步骤 3：在 app/__init__.py 中注册 wx_bp 蓝图**

在 `app/__init__.py` 的 `blueprints` 列表中添加一行：

```python
        ('app.routes.wx', 'wx_bp', '/wx', False),
```

添加在 `('app.routes.portal', 'portal_bp', None, False),` 之后。

- [ ] **步骤 4：验证蓝图注册**

运行：`python -c "from app import create_app; app = create_app(); print([r.rule for r in app.url_map.iter_rules() if r.rule.startswith('/wx')])"`
预期：输出包含 `/wx/`, `/wx/auth/login`, `/wx/bind/apply` 等路由

- [ ] **步骤 5：Commit**

```bash
git add app/routes/wx.py app/__init__.py
git commit -m "feat(wx): 添加微信门户蓝图和路由"
```

---

## 任务 7：wx_base.html — 微信端移动端母版

**文件：**
- 创建：`templates/wx_base.html`

- [ ] **步骤 1：编写移动端母版模板**

创建 `templates/wx_base.html`：

```html
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>{% block title %}首页{% endblock %} - 宏发金属交易市场</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdn.jsdelivr.net/npm/font-awesome@6.5.1/css/all.min.css" rel="stylesheet">
    <style>
        * { box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            background-color: #f5f5f5;
            padding-bottom: 60px;
            margin: 0;
        }
        .wx-header {
            background: linear-gradient(135deg, #27ae60, #2ecc71);
            color: white;
            padding: 12px 16px;
            position: sticky;
            top: 0;
            z-index: 100;
            display: flex;
            align-items: center;
            justify-content: space-between;
        }
        .wx-header .title {
            font-size: 17px;
            font-weight: 600;
        }
        .wx-header .back-btn {
            color: white;
            font-size: 18px;
            text-decoration: none;
            margin-right: 12px;
        }
        .wx-tab-bar {
            position: fixed;
            bottom: 0;
            left: 0;
            right: 0;
            background: white;
            border-top: 1px solid #e0e0e0;
            display: flex;
            z-index: 100;
            padding-bottom: env(safe-area-inset-bottom);
        }
        .wx-tab-bar .tab-item {
            flex: 1;
            text-align: center;
            padding: 8px 0 4px;
            color: #999;
            text-decoration: none;
            font-size: 11px;
        }
        .wx-tab-bar .tab-item i {
            font-size: 20px;
            display: block;
            margin-bottom: 2px;
        }
        .wx-tab-bar .tab-item.active {
            color: #27ae60;
        }
        .wx-card {
            background: white;
            border-radius: 8px;
            margin: 12px;
            padding: 16px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.08);
        }
        .wx-card-title {
            font-size: 15px;
            font-weight: 600;
            margin-bottom: 12px;
            color: #333;
        }
        .wx-empty {
            text-align: center;
            padding: 40px 20px;
            color: #999;
        }
        .wx-empty i {
            font-size: 48px;
            margin-bottom: 12px;
            display: block;
        }
        .wx-btn {
            display: block;
            width: 100%;
            padding: 12px;
            border-radius: 8px;
            font-size: 16px;
            font-weight: 500;
            text-align: center;
            border: none;
            cursor: pointer;
        }
        .wx-btn-primary {
            background: #27ae60;
            color: white;
        }
        .wx-btn-primary:active {
            background: #219a52;
        }
        .wx-btn-outline {
            background: white;
            color: #27ae60;
            border: 1px solid #27ae60;
        }
        .wx-form-group {
            margin-bottom: 16px;
        }
        .wx-form-group label {
            display: block;
            font-size: 14px;
            color: #666;
            margin-bottom: 6px;
        }
        .wx-form-group input,
        .wx-form-group select {
            width: 100%;
            padding: 10px 12px;
            border: 1px solid #ddd;
            border-radius: 6px;
            font-size: 15px;
        }
        .wx-form-group input:focus,
        .wx-form-group select:focus {
            border-color: #27ae60;
            outline: none;
            box-shadow: 0 0 0 2px rgba(39,174,96,0.15);
        }
        .wx-toast {
            position: fixed;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            background: rgba(0,0,0,0.7);
            color: white;
            padding: 12px 24px;
            border-radius: 6px;
            z-index: 9999;
            font-size: 14px;
        }
        .wx-badge {
            display: inline-block;
            padding: 2px 8px;
            border-radius: 10px;
            font-size: 12px;
        }
        .wx-badge-pending { background: #fff3e0; color: #f57c00; }
        .wx-badge-approved { background: #e8f5e9; color: #2e7d32; }
        .wx-badge-rejected { background: #ffebee; color: #c62828; }
        .wx-list-item {
            padding: 12px 0;
            border-bottom: 1px solid #f0f0f0;
        }
        .wx-list-item:last-child {
            border-bottom: none;
        }
        .wx-stat-card {
            background: white;
            border-radius: 8px;
            padding: 16px;
            text-align: center;
        }
        .wx-stat-card .stat-value {
            font-size: 24px;
            font-weight: 700;
            color: #333;
        }
        .wx-stat-card .stat-label {
            font-size: 12px;
            color: #999;
            margin-top: 4px;
        }
        .wx-merchant-tag {
            display: inline-flex;
            align-items: center;
            background: #e8f5e9;
            color: #2e7d32;
            padding: 4px 10px;
            border-radius: 12px;
            font-size: 13px;
        }
    </style>
    {% block extra_css %}{% endblock %}
</head>
<body>
    {% block header %}
    <div class="wx-header">
        <div>
            {% if request.endpoint != 'wx.index' %}
            <a class="back-btn" href="javascript:history.back()"><i class="fa fa-chevron-left"></i></a>
            {% endif %}
            <span class="title">{% block header_title %}宏发金属交易市场{% endblock %}</span>
        </div>
        <div>
            {% if current_user.is_authenticated %}
            <span style="font-size:13px;">{{ current_user.real_name or '用户' }}</span>
            {% endif %}
        </div>
    </div>
    {% endblock %}

    {% with messages = get_flashed_messages(with_categories=true) %}
        {% if messages %}
            {% for category, message in messages %}
            <div class="alert alert-{{ category }} alert-dismissible fade show m-2" role="alert">
                {{ message }}
                <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
            </div>
            {% endfor %}
        {% endif %}
    {% endwith %}

    <div class="wx-content">
        {% block content %}{% endblock %}
    </div>

    {% block tab_bar %}
    {% if current_user.is_authenticated %}
    <div class="wx-tab-bar">
        <a class="tab-item {% if request.endpoint == 'wx.index' %}active{% endif %}" href="{{ url_for('wx.index') }}">
            <i class="fa fa-home"></i>首页
        </a>
        <a class="tab-item {% if request.endpoint == 'wx.contracts' %}active{% endif %}" href="{{ url_for('wx.contracts') }}">
            <i class="fa fa-file-text"></i>合同
        </a>
        <a class="tab-item {% if request.endpoint == 'wx.finance' %}active{% endif %}" href="{{ url_for('wx.finance') }}">
            <i class="fa fa-money"></i>缴费
        </a>
        <a class="tab-item {% if request.endpoint == 'wx.profile' %}active{% endif %}" href="{{ url_for('wx.profile') }}">
            <i class="fa fa-user"></i>我的
        </a>
    </div>
    {% endif %}
    {% endblock %}

    <script src="https://cdn.jsdelivr.net/npm/jquery@3.7.1/dist/jquery.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
    <script>
    function wxToast(msg, duration) {
        duration = duration || 2000;
        var $t = $('<div class="wx-toast"></div>').text(msg);
        $('body').append($t);
        setTimeout(function() { $t.remove(); }, duration);
    }
    function wxGet(url, callback) {
        $.ajax({url: url, type: 'GET', success: function(resp) {
            if (resp.success) { callback(resp.data); } else { wxToast(resp.message || '请求失败'); }
        }, error: function() { wxToast('网络错误'); }});
    }
    function wxPost(url, data, callback) {
        $.ajax({url: url, type: 'POST', contentType: 'application/json',
            data: JSON.stringify(data), success: function(resp) {
                if (resp.success) { callback(resp); } else { wxToast(resp.message || '操作失败'); }
            }, error: function() { wxToast('网络错误'); }});
    }
    function escapeHtml(str) {
        if (!str) return '';
        return str.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
    }
    </script>
    {% block extra_js %}{% endblock %}
</body>
</html>
```

- [ ] **步骤 2：Commit**

```bash
git add templates/wx_base.html
git commit -m "feat(wx): 添加微信端移动端母版模板"
```

---

## 任务 8：微信登录 + 手机号绑定页面

**文件：**
- 创建：`templates/wx/auth/login.html`
- 创建：`templates/wx/auth/phone.html`

- [ ] **步骤 1：创建微信登录页**

创建 `templates/wx/auth/login.html`：

```html
{% extends "wx_base.html" %}

{% block title %}登录{% endblock %}
{% block header_title %}登录{% endblock %}

{% block tab_bar %}{% endblock %}

{% block content %}
<div style="padding: 40px 24px; text-align: center;">
    <div style="margin-bottom: 32px;">
        <i class="fa fa-industry" style="font-size: 64px; color: #27ae60;"></i>
        <h4 style="margin-top: 16px; color: #333;">宏发金属交易市场</h4>
        <p style="color: #999; font-size: 14px;">商户服务平台</p>
    </div>

    {% if error %}
    <div class="alert alert-danger" role="alert">{{ error }}</div>
    {% endif %}

    <a href="{{ url_for('wx.login') }}" class="wx-btn wx-btn-primary" style="margin-bottom: 16px;">
        <i class="fa fa-wechat"></i> 微信授权登录
    </a>

    <p style="color: #999; font-size: 12px; margin-top: 24px;">
        登录即表示同意《用户协议》和《隐私政策》
    </p>
</div>
{% endblock %}
```

- [ ] **步骤 2：创建手机号绑定页**

创建 `templates/wx/auth/phone.html`：

```html
{% extends "wx_base.html" %}

{% block title %}绑定手机号{% endblock %}
{% block header_title %}绑定手机号{% endblock %}

{% block content %}
<div class="wx-card">
    <div class="wx-card-title">绑定手机号</div>
    <p style="color: #666; font-size: 14px; margin-bottom: 20px;">绑定手机号后可使用手机号登录，也便于接收重要通知</p>

    <div class="wx-form-group">
        <label>手机号</label>
        <input type="tel" id="phone" placeholder="请输入手机号" maxlength="11">
    </div>

    <div class="wx-form-group">
        <label>验证码</label>
        <div style="display: flex; gap: 10px;">
            <input type="text" id="smsCode" placeholder="请输入验证码" maxlength="6" style="flex: 1;">
            <button class="wx-btn wx-btn-outline" id="sendCodeBtn" style="width: auto; padding: 10px 16px; font-size: 14px; white-space: nowrap;" onclick="sendCode()">获取验证码</button>
        </div>
    </div>

    <button class="wx-btn wx-btn-primary" onclick="bindPhone()">确认绑定</button>
</div>
{% endblock %}

{% block extra_js %}
<script>
var countdown = 0;

function sendCode() {
    var phone = $('#phone').val().trim();
    if (!phone || phone.length !== 11) {
        wxToast('请输入正确的手机号');
        return;
    }
    wxPost('{{ url_for("wx.send_sms") }}', {phone: phone}, function(resp) {
        wxToast('验证码已发送');
        countdown = 60;
        var btn = $('#sendCodeBtn');
        btn.prop('disabled', true);
        var timer = setInterval(function() {
            countdown--;
            if (countdown <= 0) {
                clearInterval(timer);
                btn.prop('disabled', false).text('获取验证码');
            } else {
                btn.text(countdown + 's');
            }
        }, 1000);
    });
}

function bindPhone() {
    var phone = $('#phone').val().trim();
    var code = $('#smsCode').val().trim();
    if (!phone || !code) {
        wxToast('请输入手机号和验证码');
        return;
    }
    wxPost('{{ url_for("wx.phone_bind") }}', {phone: phone, code: code}, function(resp) {
        wxToast('绑定成功');
        setTimeout(function() {
            window.location.href = '{{ url_for("wx.bind_apply") }}';
        }, 1000);
    });
}
</script>
{% endblock %}
```

- [ ] **步骤 3：Commit**

```bash
git add templates/wx/auth/login.html templates/wx/auth/phone.html
git commit -m "feat(wx): 添加微信登录和手机号绑定页面"
```

---

## 任务 9：商户绑定申请 + 状态查看页面

**文件：**
- 创建：`templates/wx/bind/apply.html`
- 创建：`templates/wx/bind/status.html`

- [ ] **步骤 1：创建绑定申请页**

创建 `templates/wx/bind/apply.html`：

```html
{% extends "wx_base.html" %}

{% block title %}申请绑定商户{% endblock %}
{% block header_title %}申请绑定商户{% endblock %}

{% block content %}
<div class="wx-card">
    <div class="wx-card-title">选择商户</div>
    <div class="wx-form-group">
        <label>搜索商户</label>
        <input type="text" id="merchantSearch" placeholder="输入商户名称搜索">
    </div>
    <div id="merchantList" style="max-height: 200px; overflow-y: auto;"></div>
    <div id="selectedMerchant" style="display:none; margin-top: 12px; padding: 10px; background: #e8f5e9; border-radius: 6px;">
        <span id="selectedMerchantName" style="font-weight: 500;"></span>
        <input type="hidden" id="selectedMerchantId">
    </div>
</div>

<div class="wx-card">
    <div class="wx-card-title">选择身份</div>
    <div style="display: flex; gap: 10px;">
        <div class="role-option" data-role="Boss" onclick="selectRole(this)" style="flex:1; text-align:center; padding: 12px; border: 2px solid #ddd; border-radius: 8px; cursor: pointer;">
            <i class="fa fa-user-tie" style="font-size: 24px; color: #f39c12;"></i>
            <div style="margin-top: 6px; font-size: 14px;">老板</div>
        </div>
        <div class="role-option" data-role="Staff" onclick="selectRole(this)" style="flex:1; text-align:center; padding: 12px; border: 2px solid #ddd; border-radius: 8px; cursor: pointer;">
            <i class="fa fa-user" style="font-size: 24px; color: #3498db;"></i>
            <div style="margin-top: 6px; font-size: 14px;">员工</div>
        </div>
        <div class="role-option" data-role="Finance" onclick="selectRole(this)" style="flex:1; text-align:center; padding: 12px; border: 2px solid #ddd; border-radius: 8px; cursor: pointer;">
            <i class="fa fa-calculator" style="font-size: 24px; color: #e74c3c;"></i>
            <div style="margin-top: 6px; font-size: 14px;">财务</div>
        </div>
    </div>
    <input type="hidden" id="selectedRole">
</div>

<div class="wx-card">
    <div class="wx-form-group">
        <label>申请说明（选填）</label>
        <input type="text" id="remark" placeholder="例如：我是该商户的法人代表">
    </div>
    <button class="wx-btn wx-btn-primary" onclick="submitApply()">提交申请</button>
</div>

<div style="text-align: center; padding: 16px;">
    <a href="{{ url_for('wx.bind_status') }}" style="color: #27ae60; font-size: 14px;">查看我的绑定状态 →</a>
</div>
{% endblock %}

{% block extra_js %}
<script>
var selectedMerchantId = null;
var selectedRole = null;

function selectRole(el) {
    $('.role-option').css('border-color', '#ddd');
    $(el).css('border-color', '#27ae60');
    selectedRole = $(el).data('role');
    $('#selectedRole').val(selectedRole);
}

$('#merchantSearch').on('input', function() {
    var search = $(this).val().trim();
    if (search.length < 1) { $('#merchantList').empty(); return; }
    wxGet('{{ url_for("wx.api_merchants") }}?search=' + encodeURIComponent(search), function(data) {
        var html = '';
        for (var i = 0; i < data.length; i++) {
            html += '<div class="wx-list-item" style="cursor:pointer;" onclick="selectMerchant(' + data[i].merchant_id + ', \'' + escapeHtml(data[i].merchant_name) + '\')">';
            html += '<div style="font-weight:500;">' + escapeHtml(data[i].merchant_name) + '</div>';
            html += '<div style="font-size:12px;color:#999;">' + escapeHtml(data[i].contact_person || '') + ' ' + escapeHtml(data[i].phone || '') + '</div>';
            html += '</div>';
        }
        if (!html) html = '<div class="wx-empty"><p>未找到商户</p></div>';
        $('#merchantList').html(html);
    });
});

function selectMerchant(id, name) {
    selectedMerchantId = id;
    $('#selectedMerchantId').val(id);
    $('#selectedMerchantName').text(name);
    $('#selectedMerchant').show();
    $('#merchantList').empty();
    $('#merchantSearch').val(name);
}

function submitApply() {
    if (!selectedMerchantId) { wxToast('请选择商户'); return; }
    if (!selectedRole) { wxToast('请选择身份'); return; }
    var remark = $('#remark').val().trim();
    wxPost('{{ url_for("wx.api_bind_apply") }}', {merchant_id: selectedMerchantId, bind_role: selectedRole, remark: remark}, function(resp) {
        wxToast(resp.message);
        if (resp.success) {
            setTimeout(function() { window.location.href = '{{ url_for("wx.bind_status") }}'; }, 1500);
        }
    });
}
</script>
{% endblock %}
```

- [ ] **步骤 2：创建绑定状态页**

创建 `templates/wx/bind/status.html`：

```html
{% extends "wx_base.html" %}

{% block title %}绑定状态{% endblock %}
{% block header_title %}绑定状态{% endblock %}

{% block content %}
<div id="bindingList"></div>

<div style="text-align: center; padding: 16px;">
    <a href="{{ url_for('wx.bind_apply') }}" class="wx-btn wx-btn-outline" style="display: inline-block; width: auto; padding: 10px 24px;">
        <i class="fa fa-plus"></i> 申请绑定新商户
    </a>
</div>
{% endblock %}

{% block extra_js %}
<script>
$(document).ready(function() {
    loadBindings();
});

function loadBindings() {
    wxGet('{{ url_for("wx.api_bindings") }}', function(data) {
        if (!data || data.length === 0) {
            $('#bindingList').html('<div class="wx-empty"><i class="fa fa-link"></i><p>暂无绑定记录</p></div>');
            return;
        }
        var html = '';
        for (var i = 0; i < data.length; i++) {
            var b = data[i];
            html += '<div class="wx-card">';
            html += '<div style="display:flex;justify-content:space-between;align-items:center;">';
            html += '<div><strong>' + escapeHtml(b.merchant_name) + '</strong></div>';
            html += '<span class="wx-badge wx-badge-' + b.status.toLowerCase() + '">' + b.status_display + '</span>';
            html += '</div>';
            html += '<div style="margin-top:8px;font-size:13px;color:#666;">';
            html += '身份：' + escapeHtml(b.bind_role_display) + '<br>';
            html += '申请时间：' + b.apply_time;
            if (b.reject_reason) {
                html += '<br><span style="color:#c62828;">驳回原因：' + escapeHtml(b.reject_reason) + '</span>';
            }
            html += '</div>';
            if (b.status === 'Pending') {
                html += '<button class="wx-btn wx-btn-outline" style="margin-top:10px;font-size:13px;padding:8px;" onclick="cancelBinding(' + b.binding_id + ')">取消申请</button>';
            }
            html += '</div>';
        }
        $('#bindingList').html(html);
    });
}

function cancelBinding(bindingId) {
    if (!confirm('确定取消此绑定申请？')) return;
    wxPost('{{ url_for("wx.api_bind_cancel") }}', {binding_id: bindingId}, function(resp) {
        wxToast(resp.message);
        if (resp.success) loadBindings();
    });
}
</script>
{% endblock %}
```

- [ ] **步骤 3：Commit**

```bash
git add templates/wx/bind/apply.html templates/wx/bind/status.html
git commit -m "feat(wx): 添加商户绑定申请和状态查看页面"
```

---

## 任务 10：微信门户首页 + 数据查看页面

**文件：**
- 创建：`templates/wx/index.html`
- 创建：`templates/wx/contracts.html`
- 创建：`templates/wx/utility.html`
- 创建：`templates/wx/scale.html`
- 创建：`templates/wx/finance.html`

- [ ] **步骤 1：创建微信门户首页**

创建 `templates/wx/index.html`：

```html
{% extends "wx_base.html" %}

{% block title %}首页{% endblock %}

{% block content %}
<div id="merchantInfo" style="padding: 16px; background: linear-gradient(135deg, #27ae60, #2ecc71); color: white; margin-bottom: 12px;">
    <div style="display: flex; justify-content: space-between; align-items: center;">
        <div>
            <h5 style="margin: 0;" id="merchantName">加载中...</h5>
            <span id="bindRoleTag" style="font-size: 12px; background: rgba(255,255,255,0.2); padding: 2px 8px; border-radius: 10px;"></span>
        </div>
        <a href="{{ url_for('wx.switch') }}" style="color: white; font-size: 13px;"><i class="fa fa-exchange-alt"></i> 切换</a>
    </div>
</div>

<div style="display: grid; grid-template-columns: 1fr 1fr; gap: 10px; padding: 0 12px;">
    <div class="wx-stat-card">
        <div class="stat-value" id="statContracts">-</div>
        <div class="stat-label">有效合同</div>
    </div>
    <div class="wx-stat-card">
        <div class="stat-value" id="statPending">-</div>
        <div class="stat-label">待缴金额</div>
    </div>
    <div class="wx-stat-card">
        <div class="stat-value" id="statUtility">-</div>
        <div class="stat-label">本月水电</div>
    </div>
    <div class="wx-stat-card">
        <div class="stat-value" id="statScale">-</div>
        <div class="stat-label">本月过磅</div>
    </div>
</div>

<div class="wx-card" style="margin-top: 12px;">
    <div class="wx-card-title">即将到期合同</div>
    <div id="expiringContracts"><p style="color:#999;">加载中...</p></div>
</div>

<div class="wx-card">
    <div class="wx-card-title">逾期未缴账单</div>
    <div id="overdueReceivables"><p style="color:#999;">加载中...</p></div>
</div>
{% endblock %}

{% block extra_js %}
<script>
$(document).ready(function() {
    wxGet('{{ url_for("wx.api_current_merchant") }}', function(data) {
        if (data) {
            $('#merchantName').text(data.merchant_name || '');
            var roleMap = {Boss:'老板', Staff:'员工', Finance:'财务'};
            $('#bindRoleTag').text(roleMap[data.bind_role] || '');
        }
    });

    wxGet('{{ url_for("wx.api_dashboard") }}', function(d) {
        $('#statContracts').text(d.active_contracts);
        $('#statPending').text('¥' + (d.pending_amount || 0).toFixed(0));
        $('#statUtility').text('¥' + (d.monthly_utility || 0).toFixed(0));
        $('#statScale').text(d.monthly_scale_count + '次');

        if (d.expiring_contracts && d.expiring_contracts.length > 0) {
            var html = '';
            for (var i = 0; i < d.expiring_contracts.length; i++) {
                var c = d.expiring_contracts[i];
                html += '<div class="wx-list-item"><div style="display:flex;justify-content:space-between;">';
                html += '<span>' + escapeHtml(c.contract_name) + '</span>';
                html += '<span class="wx-badge wx-badge-pending">' + c.end_date + '到期</span>';
                html += '</div></div>';
            }
            $('#expiringContracts').html(html);
        } else {
            $('#expiringContracts').html('<p style="color:#999;">暂无</p>');
        }

        if (d.overdue_receivables && d.overdue_receivables.length > 0) {
            var html = '';
            for (var i = 0; i < d.overdue_receivables.length; i++) {
                var r = d.overdue_receivables[i];
                html += '<div class="wx-list-item"><div style="display:flex;justify-content:space-between;">';
                html += '<span>' + escapeHtml(r.expense_type_name) + '</span>';
                html += '<span style="color:#c62828;font-weight:600;">¥' + (r.remaining_amount || 0).toFixed(0) + '</span>';
                html += '</div></div>';
            }
            $('#overdueReceivables').html(html);
        } else {
            $('#overdueReceivables').html('<p style="color:#999;">暂无</p>');
        }
    });
});
</script>
{% endblock %}
```

- [ ] **步骤 2：创建合同列表页**

创建 `templates/wx/contracts.html`：

```html
{% extends "wx_base.html" %}

{% block title %}我的合同{% endblock %}
{% block header_title %}我的合同{% endblock %}

{% block content %}
<div id="contractList"></div>
<div id="loadMore" style="text-align:center;padding:16px;display:none;">
    <button class="wx-btn wx-btn-outline" style="width:auto;padding:8px 24px;font-size:14px;" onclick="loadContracts()">加载更多</button>
</div>
{% endblock %}

{% block extra_js %}
<script>
var page = 1;
var hasMore = true;

$(document).ready(function() { loadContracts(); });

function loadContracts() {
    wxGet('{{ url_for("wx.api_contracts") }}?page=' + page + '&per_page=10', function(data) {
        var items = data.items || [];
        var html = '';
        for (var i = 0; i < items.length; i++) {
            var c = items[i];
            html += '<div class="wx-card">';
            html += '<div style="display:flex;justify-content:space-between;align-items:center;">';
            html += '<strong>' + escapeHtml(c.contract_name) + '</strong>';
            html += '<span class="wx-badge ' + (c.status === '有效' ? 'wx-badge-approved' : 'wx-badge-rejected') + '">' + escapeHtml(c.status) + '</span>';
            html += '</div>';
            html += '<div style="margin-top:8px;font-size:13px;color:#666;">';
            html += '编号：' + escapeHtml(c.contract_number) + '<br>';
            html += '期限：' + c.start_date + ' 至 ' + c.end_date + '<br>';
            html += '金额：¥' + (c.actual_amount || 0).toFixed(0);
            html += '</div></div>';
        }
        if (page === 1) { $('#contractList').html(html); } else { $('#contractList').append(html); }
        hasMore = data.current_page < data.total_pages;
        $('#loadMore').toggle(hasMore);
        if (hasMore) page++;
        if (!items.length && page === 1) {
            $('#contractList').html('<div class="wx-empty"><i class="fa fa-file-text"></i><p>暂无合同数据</p></div>');
        }
    });
}
</script>
{% endblock %}
```

- [ ] **步骤 3：创建水电费页**

创建 `templates/wx/utility.html`：

```html
{% extends "wx_base.html" %}

{% block title %}水电费{% endblock %}
{% block header_title %}水电费{% endblock %}

{% block content %}
<div id="utilityList"></div>
<div id="loadMore" style="text-align:center;padding:16px;display:none;">
    <button class="wx-btn wx-btn-outline" style="width:auto;padding:8px 24px;font-size:14px;" onclick="loadUtility()">加载更多</button>
</div>
{% endblock %}

{% block extra_js %}
<script>
var page = 1;
$(document).ready(function() { loadUtility(); });

function loadUtility() {
    wxGet('{{ url_for("wx.api_utility") }}?page=' + page + '&per_page=10', function(data) {
        var items = data.items || [];
        var html = '';
        for (var i = 0; i < items.length; i++) {
            var r = items[i];
            var typeIcon = r.reading_type === '电' ? 'fa-bolt' : 'fa-tint';
            var typeColor = r.reading_type === '电' ? '#f39c12' : '#3498db';
            html += '<div class="wx-card">';
            html += '<div style="display:flex;justify-content:space-between;align-items:center;">';
            html += '<span><i class="fa ' + typeIcon + '" style="color:' + typeColor + ';"></i> ' + escapeHtml(r.meter_number) + '</span>';
            html += '<span style="font-weight:600;">¥' + (r.total_amount || 0).toFixed(2) + '</span>';
            html += '</div>';
            html += '<div style="margin-top:6px;font-size:13px;color:#666;">';
            html += '抄表日期：' + r.reading_date + '<br>';
            html += '用量：' + (r.usage || 0).toFixed(1) + ' | 单价：¥' + (r.unit_price || 0).toFixed(2);
            html += '</div></div>';
        }
        if (page === 1) { $('#utilityList').html(html); } else { $('#utilityList').append(html); }
        var hasMore = data.current_page < data.total_pages;
        $('#loadMore').toggle(hasMore);
        if (hasMore) page++;
        if (!items.length && page === 1) {
            $('#utilityList').html('<div class="wx-empty"><i class="fa fa-tint"></i><p>暂无水电费数据</p></div>');
        }
    });
}
</script>
{% endblock %}
```

- [ ] **步骤 4：创建过磅数据页**

创建 `templates/wx/scale.html`：

```html
{% extends "wx_base.html" %}

{% block title %}过磅数据{% endblock %}
{% block header_title %}过磅数据{% endblock %}

{% block content %}
<div id="scaleList"></div>
<div id="loadMore" style="text-align:center;padding:16px;display:none;">
    <button class="wx-btn wx-btn-outline" style="width:auto;padding:8px 24px;font-size:14px;" onclick="loadScale()">加载更多</button>
</div>
{% endblock %}

{% block extra_js %}
<script>
var page = 1;
$(document).ready(function() { loadScale(); });

function loadScale() {
    wxGet('{{ url_for("wx.api_scale_records") }}?page=' + page + '&per_page=10', function(data) {
        var items = data.items || [];
        var html = '';
        for (var i = 0; i < items.length; i++) {
            var r = items[i];
            html += '<div class="wx-card">';
            html += '<div style="display:flex;justify-content:space-between;align-items:center;">';
            html += '<span>' + escapeHtml(r.product_name || '过磅记录') + '</span>';
            html += '<span style="font-weight:600;">¥' + (r.total_amount || 0).toFixed(2) + '</span>';
            html += '</div>';
            html += '<div style="margin-top:6px;font-size:13px;color:#666;">';
            html += '时间：' + r.scale_time + '<br>';
            html += '毛重：' + (r.gross_weight || 0) + ' | 皮重：' + (r.tare_weight || 0) + ' | 净重：' + (r.net_weight || 0);
            if (r.license_plate) html += '<br>车牌：' + escapeHtml(r.license_plate);
            html += '</div></div>';
        }
        if (page === 1) { $('#scaleList').html(html); } else { $('#scaleList').append(html); }
        var hasMore = data.current_page < data.total_pages;
        $('#loadMore').toggle(hasMore);
        if (hasMore) page++;
        if (!items.length && page === 1) {
            $('#scaleList').html('<div class="wx-empty"><i class="fa fa-balance-scale"></i><p>暂无过磅数据</p></div>');
        }
    });
}
</script>
{% endblock %}
```

- [ ] **步骤 5：创建缴费记录页**

创建 `templates/wx/finance.html`：

```html
{% extends "wx_base.html" %}

{% block title %}缴费记录{% endblock %}
{% block header_title %}缴费记录{% endblock %}

{% block content %}
<div style="padding: 12px; display: flex; gap: 8px;">
    <button class="wx-btn wx-btn-outline filter-btn active" data-status="" onclick="filterStatus(this)" style="flex:1;padding:8px;font-size:13px;">全部</button>
    <button class="wx-btn wx-btn-outline filter-btn" data-status="待付款" onclick="filterStatus(this)" style="flex:1;padding:8px;font-size:13px;">待付款</button>
    <button class="wx-btn wx-btn-outline filter-btn" data-status="已付款" onclick="filterStatus(this)" style="flex:1;padding:8px;font-size:13px;">已付款</button>
</div>
<div id="receivableList"></div>
<div id="loadMore" style="text-align:center;padding:16px;display:none;">
    <button class="wx-btn wx-btn-outline" style="width:auto;padding:8px 24px;font-size:14px;" onclick="loadReceivables()">加载更多</button>
</div>
{% endblock %}

{% block extra_js %}
<script>
var page = 1;
var currentStatus = '';

$(document).ready(function() { loadReceivables(); });

function filterStatus(el) {
    $('.filter-btn').removeClass('active').css({'background':'white','color':'#27ae60'});
    $(el).addClass('active').css({'background':'#27ae60','color':'white'});
    currentStatus = $(el).data('status');
    page = 1;
    loadReceivables();
}

function loadReceivables() {
    var url = '{{ url_for("wx.api_receivables") }}?page=' + page + '&per_page=10';
    if (currentStatus) url += '&status=' + encodeURIComponent(currentStatus);
    wxGet(url, function(data) {
        var items = data.items || [];
        var html = '';
        for (var i = 0; i < items.length; i++) {
            var r = items[i];
            var statusClass = r.status === '已付款' ? 'wx-badge-approved' : 'wx-badge-pending';
            html += '<div class="wx-card">';
            html += '<div style="display:flex;justify-content:space-between;align-items:center;">';
            html += '<span>' + escapeHtml(r.expense_type_name) + '</span>';
            html += '<span class="wx-badge ' + statusClass + '">' + escapeHtml(r.status) + '</span>';
            html += '</div>';
            html += '<div style="margin-top:6px;font-size:13px;color:#666;">';
            html += '金额：¥' + (r.amount || 0).toFixed(2);
            if (r.remaining_amount > 0) html += ' | 剩余：¥' + r.remaining_amount.toFixed(2);
            html += '<br>到期：' + r.due_date;
            html += '</div></div>';
        }
        if (page === 1) { $('#receivableList').html(html); } else { $('#receivableList').append(html); }
        var hasMore = data.current_page < data.total_pages;
        $('#loadMore').toggle(hasMore);
        if (hasMore) page++;
        if (!items.length && page === 1) {
            $('#receivableList').html('<div class="wx-empty"><i class="fa fa-money"></i><p>暂无缴费记录</p></div>');
        }
    });
}
</script>
{% endblock %}
```

- [ ] **步骤 6：Commit**

```bash
git add templates/wx/index.html templates/wx/contracts.html templates/wx/utility.html templates/wx/scale.html templates/wx/finance.html
git commit -m "feat(wx): 添加微信门户首页和数据查看页面"
```

---

## 任务 11：个人信息 + 商户切换页面

**文件：**
- 创建：`templates/wx/profile.html`
- 创建：`templates/wx/switch.html`

- [ ] **步骤 1：创建个人信息页**

创建 `templates/wx/profile.html`：

```html
{% extends "wx_base.html" %}

{% block title %}我的{% endblock %}
{% block header_title %}我的{% endblock %}

{% block content %}
<div style="text-align: center; padding: 24px; background: white; margin-bottom: 12px;">
    <div style="width: 64px; height: 64px; border-radius: 50%; background: #e8f5e9; margin: 0 auto 12px; display: flex; align-items: center; justify-content: center;">
        <i class="fa fa-user" style="font-size: 28px; color: #27ae60;"></i>
    </div>
    <h5>{{ current_user.real_name or '微信用户' }}</h5>
    <p style="color: #999; font-size: 13px; margin: 0;">{{ current_user.phone or '未绑定手机号' }}</p>
</div>

<div class="wx-card" style="padding: 0;">
    <a href="{{ url_for('wx.bind_status') }}" style="display:flex;justify-content:space-between;align-items:center;padding:14px 16px;text-decoration:none;color:#333;border-bottom:1px solid #f0f0f0;">
        <span><i class="fa fa-link" style="color:#27ae60;margin-right:10px;"></i>绑定状态</span>
        <i class="fa fa-chevron-right" style="color:#ccc;"></i>
    </a>
    <a href="{{ url_for('wx.switch') }}" style="display:flex;justify-content:space-between;align-items:center;padding:14px 16px;text-decoration:none;color:#333;border-bottom:1px solid #f0f0f0;">
        <span><i class="fa fa-exchange-alt" style="color:#3498db;margin-right:10px;"></i>切换商户</span>
        <i class="fa fa-chevron-right" style="color:#ccc;"></i>
    </a>
    <a href="{{ url_for('wx.phone_page') }}" style="display:flex;justify-content:space-between;align-items:center;padding:14px 16px;text-decoration:none;color:#333;border-bottom:1px solid #f0f0f0;">
        <span><i class="fa fa-phone" style="color:#f39c12;margin-right:10px;"></i>绑定手机号</span>
        <i class="fa fa-chevron-right" style="color:#ccc;"></i>
    </a>
</div>

<div style="padding: 16px;">
    <a href="{{ url_for('auth.logout') }}" class="wx-btn" style="background:#fff0f0;color:#c62828;border:1px solid #ffcdd2;">退出登录</a>
</div>
{% endblock %}
```

- [ ] **步骤 2：创建商户切换页**

创建 `templates/wx/switch.html`：

```html
{% extends "wx_base.html" %}

{% block title %}切换商户{% endblock %}
{% block header_title %}切换商户{% endblock %}

{% block content %}
<div id="merchantList" style="padding: 12px;"></div>
{% endblock %}

{% block extra_js %}
<script>
$(document).ready(function() {
    loadMerchants();
});

function loadMerchants() {
    wxGet('{{ url_for("wx.api_bindings") }}', function(data) {
        var approved = data.filter(function(b) { return b.status === 'Approved'; });
        if (!approved.length) {
            $('#merchantList').html('<div class="wx-empty"><i class="fa fa-store"></i><p>暂无已绑定的商户</p></div>');
            return;
        }
        wxGet('{{ url_for("wx.api_current_merchant") }}', function(current) {
            var html = '';
            for (var i = 0; i < approved.length; i++) {
                var b = approved[i];
                var isCurrent = current && current.merchant_id === b.merchant_id;
                html += '<div class="wx-card" style="' + (isCurrent ? 'border: 2px solid #27ae60;' : '') + '">';
                html += '<div style="display:flex;justify-content:space-between;align-items:center;">';
                html += '<div>';
                html += '<strong>' + escapeHtml(b.merchant_name) + '</strong>';
                if (isCurrent) html += ' <span class="wx-badge wx-badge-approved">当前</span>';
                html += '<div style="font-size:13px;color:#666;margin-top:4px;">身份：' + escapeHtml(b.bind_role_display) + '</div>';
                html += '</div>';
                if (!isCurrent) {
                    html += '<button class="wx-btn wx-btn-outline" style="width:auto;padding:8px 16px;font-size:13px;" onclick="switchTo(' + b.merchant_id + ')">切换</button>';
                }
                html += '</div></div>';
            }
            $('#merchantList').html(html);
        });
    });
}

function switchTo(merchantId) {
    wxPost('{{ url_for("wx.api_switch") }}', {merchant_id: merchantId}, function(resp) {
        wxToast(resp.message);
        if (resp.success) {
            setTimeout(function() { window.location.href = '{{ url_for("wx.index") }}'; }, 1000);
        }
    });
}
</script>
{% endblock %}
```

- [ ] **步骤 3：Commit**

```bash
git add templates/wx/profile.html templates/wx/switch.html
git commit -m "feat(wx): 添加个人信息和商户切换页面"
```

---

## 任务 12：管理端绑定审批功能

**文件：**
- 创建：`templates/merchant/bind_requests.html`
- 修改：`app/routes/merchant.py`
- 修改：`templates/merchant/list.html`

- [ ] **步骤 1：创建管理端绑定审批页**

创建 `templates/merchant/bind_requests.html`：

```html
{% extends "admin_base.html" %}

{% block title %}商户绑定审批{% endblock %}

{% block content %}
<div class="card">
    <div class="card-header">
        <h5 class="mb-0"><i class="fa fa-link"></i> 商户绑定审批</h5>
    </div>
    <div class="card-body">
        <div class="table-responsive">
            <table class="table table-hover">
                <thead>
                    <tr>
                        <th>申请人</th>
                        <th>手机号</th>
                        <th>商户</th>
                        <th>申请身份</th>
                        <th>申请时间</th>
                        <th>申请说明</th>
                        <th>操作</th>
                    </tr>
                </thead>
                <tbody id="requestList">
                    <tr><td colspan="7" class="text-center text-muted">加载中...</td></tr>
                </tbody>
            </table>
        </div>
    </div>
</div>

<div class="modal fade" id="rejectModal" tabindex="-1">
    <div class="modal-dialog">
        <div class="modal-content">
            <div class="modal-header">
                <h5 class="modal-title">驳回绑定申请</h5>
                <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
            </div>
            <div class="modal-body">
                <div class="mb-3">
                    <label class="form-label">驳回原因</label>
                    <textarea class="form-control" id="rejectReason" rows="3" placeholder="请输入驳回原因"></textarea>
                </div>
            </div>
            <div class="modal-footer">
                <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">取消</button>
                <button type="button" class="btn btn-danger" onclick="confirmReject()">确认驳回</button>
            </div>
        </div>
    </div>
</div>
{% endblock %}

{% block extra_js %}
<script>
var currentBindingId = null;

$(document).ready(function() { loadRequests(); });

function loadRequests() {
    $.ajax({
        url: '/merchant/api/bind-requests',
        type: 'GET',
        success: function(resp) {
            if (!resp.success) { showToast(resp.message, 'danger'); return; }
            var data = resp.data;
            if (!data.length) {
                $('#requestList').html('<tr><td colspan="7" class="text-center text-muted">暂无待审批申请</td></tr>');
                return;
            }
            var html = '';
            for (var i = 0; i < data.length; i++) {
                var r = data[i];
                var roleMap = {Boss:'老板', Staff:'员工', Finance:'财务'};
                html += '<tr>';
                html += '<td>' + escapeHtml(r.user_real_name) + '</td>';
                html += '<td>' + escapeHtml(r.phone) + '</td>';
                html += '<td>' + escapeHtml(r.merchant_name) + '</td>';
                html += '<td><span class="badge bg-info">' + (roleMap[r.bind_role] || r.bind_role) + '</span></td>';
                html += '<td>' + r.apply_time + '</td>';
                html += '<td>' + escapeHtml(r.remark) + '</td>';
                html += '<td>';
                html += '<button class="btn btn-sm btn-success me-1" onclick="approveBinding(' + r.binding_id + ')"><i class="fa fa-check"></i> 通过</button>';
                html += '<button class="btn btn-sm btn-danger" onclick="showRejectModal(' + r.binding_id + ')"><i class="fa fa-times"></i> 驳回</button>';
                html += '</td>';
                html += '</tr>';
            }
            $('#requestList').html(html);
        }
    });
}

function approveBinding(bindingId) {
    if (!confirm('确定通过此绑定申请？')) return;
    $.ajax({
        url: '/merchant/api/bind-approve/' + bindingId,
        type: 'POST',
        contentType: 'application/json',
        data: JSON.stringify({csrf_token: getCSRFToken()}),
        success: function(resp) {
            showToast(resp.message, resp.success ? 'success' : 'danger');
            if (resp.success) loadRequests();
        }
    });
}

function showRejectModal(bindingId) {
    currentBindingId = bindingId;
    $('#rejectReason').val('');
    new bootstrap.Modal(document.getElementById('rejectModal')).show();
}

function confirmReject() {
    var reason = $('#rejectReason').val().trim();
    $.ajax({
        url: '/merchant/api/bind-reject/' + currentBindingId,
        type: 'POST',
        contentType: 'application/json',
        data: JSON.stringify({reason: reason, csrf_token: getCSRFToken()}),
        success: function(resp) {
            showToast(resp.message, resp.success ? 'success' : 'danger');
            if (resp.success) { loadRequests(); bootstrap.Modal.getInstance(document.getElementById('rejectModal')).hide(); }
        }
    });
}
</script>
{% endblock %}
```

- [ ] **步骤 2：在 merchant.py 中添加审批路由**

在 `app/routes/merchant.py` 中添加以下路由（在文件末尾，现有路由之后）：

```python
@merchant_bp.route('/bind-requests')
@login_required
@check_permission('merchant_manage')
def bind_requests():
    return render_template('merchant/bind_requests.html')


@merchant_bp.route('/api/bind-requests')
@login_required
@check_permission('merchant_manage')
def api_bind_requests():
    from app.services.wx_bind_service import WxBindService
    try:
        items = WxBindService.get_pending_requests()
        return jsonify({'success': True, 'data': items})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@merchant_bp.route('/api/bind-approve/<int:binding_id>', methods=['POST'])
@login_required
@check_permission('merchant_manage')
def api_bind_approve(binding_id):
    from app.services.wx_bind_service import WxBindService
    from app.services.wx_notify_service import WxNotifyService
    try:
        result = WxBindService.approve_binding(binding_id, current_user.user_id)
        if result.get('success') and result.get('openid'):
            WxNotifyService.send_bind_approved(result['openid'], result['merchant_name'], result['bind_role'])
        return jsonify(result)
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@merchant_bp.route('/api/bind-reject/<int:binding_id>', methods=['POST'])
@login_required
@check_permission('merchant_manage')
def api_bind_reject(binding_id):
    from app.services.wx_bind_service import WxBindService
    from app.services.wx_notify_service import WxNotifyService
    data = request.get_json() or {}
    reason = data.get('reason', '').strip()
    try:
        result = WxBindService.reject_binding(binding_id, current_user.user_id, reason)
        if result.get('success') and result.get('openid'):
            WxNotifyService.send_bind_rejected(result['openid'], result['merchant_name'], result.get('reason', ''))
        return jsonify(result)
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500
```

确保文件顶部有必要的导入：`from flask_login import login_required, current_user` 和 `from flask import request, jsonify`。

- [ ] **步骤 3：在商户列表页添加绑定审批入口**

在 `templates/merchant/list.html` 中找到操作按钮区域，添加一个"绑定审批"按钮：

```html
<a href="{{ url_for('merchant.bind_requests') }}" class="btn btn-outline-info btn-sm">
    <i class="fa fa-link"></i> 绑定审批
</a>
```

- [ ] **步骤 4：验证管理端审批路由可访问**

运行：`python -c "from app import create_app; app = create_app(); rules = [r.rule for r in app.url_map.iter_rules() if 'bind' in r.rule]; print(rules)"`
预期：输出包含 `/merchant/bind-requests`, `/merchant/api/bind-approve/<binding_id>`, `/merchant/api/bind-reject/<binding_id>`

- [ ] **步骤 5：Commit**

```bash
git add templates/merchant/bind_requests.html app/routes/merchant.py templates/merchant/list.html
git commit -m "feat(wx): 添加管理端商户绑定审批功能"
```

---

## 任务 13：集成测试 + 最终验证

**文件：**
- 修改：`app/routes/wx.py`（如有bug修复）
- 修改：`app/services/wx_auth_service.py`（如有bug修复）

- [ ] **步骤 1：启动应用验证所有蓝图注册成功**

运行：`python -c "from app import create_app; app = create_app(); print('应用创建成功'); wx_rules = [r.rule for r in app.url_map.iter_rules() if r.rule.startswith('/wx')]; print(f'微信路由数量: {len(wx_rules)}'); print('\n'.join(sorted(wx_rules)))"`
预期：输出所有 `/wx/` 前缀路由，无报错

- [ ] **步骤 2：验证所有模板文件存在**

运行：`python -c "import os; tdir='templates/wx'; files=[f for f in os.listdir(tdir) if f.endswith('.html')]; print(f'wx模板文件: {len(files)}个'); [print(f'  {f}') for f in sorted(files)]; auth_dir=os.path.join(tdir,'auth'); [print(f'  auth/{f}') for f in sorted(os.listdir(auth_dir)) if f.endswith('.html')]; bind_dir=os.path.join(tdir,'bind'); [print(f'  bind/{f}') for f in sorted(os.listdir(bind_dir)) if f.endswith('.html')]"`
预期：列出所有 wx 模板文件

- [ ] **步骤 3：验证所有服务层可正常导入**

运行：`python -c "from app.services.wx_auth_service import WxAuthService; from app.services.wx_bind_service import WxBindService; from app.services.wx_notify_service import WxNotifyService; from app.models.wx_user import WxUser; from app.models.merchant_binding import MerchantBinding; print('所有服务和模型导入成功')"`
预期：输出"所有服务和模型导入成功"

- [ ] **步骤 4：修复发现的任何问题**

如果上述步骤发现任何导入错误或路由问题，修复后重新验证。

- [ ] **步骤 5：最终 Commit**

```bash
git add -A
git commit -m "feat(wx): 微信门户Phase 2完整实现"
```
