# 微信门户设计文档

## 1. 概述

### 1.1 目标

为宏发金属交易市场管理系统新增微信门户，让商户通过微信公众号H5页面（后续扩展小程序）登录系统，自行注册账号、申请绑定商户，绑定审批通过后查看所属商户的电费、水费、合同、过磅数据、磅费等信息。

### 1.2 设计决策

| 决策项 | 选择 | 理由 |
|--------|------|------|
| 入口形式 | 微信公众号H5 + 后续小程序 | H5快速上线，小程序后续扩展 |
| 登录方式 | 微信授权为主 + 手机号备用 | 微信内体验流畅，微信外可用 |
| 多商户绑定 | 支持一个用户绑定多个商户 | 老板名下多家商户的实际场景 |
| 身份权限 | 身份决定可见数据 | 老板/员工/财务看到不同数据 |
| 审批方式 | 管理员后台审批 + 微信通知 | 管理集中，通知及时 |
| 架构方案 | 独立移动端路由（方案A） | 与现有架构一致，Service层复用 |

### 1.3 范围

本设计覆盖微信门户Phase 2的全部功能，包括：
- 微信OAuth2.0授权登录
- 手机号绑定（备用登录）
- 商户绑定申请（老板/员工/财务三种身份）
- 管理员审批绑定申请
- 微信消息通知
- 基于身份的数据权限控制
- 商户切换（多商户场景）
- 移动端数据查看页面

不包含：
- 微信小程序前端开发（后续独立项目）
- 微信支付集成
- 进销存功能

---

## 2. 架构设计

### 2.1 整体架构

```
微信公众号
  │
  ├─ 菜单/扫码 → H5页面（/wx/ 路由）
  │                │
  │                ├─ 服务端渲染（Jinja2模板）
  │                ├─ Ajax调用后端API
  │                │
  │                ↓
  │           Flask Blueprint (wx_bp)
  │                │
  │                ├─ WxAuthService（微信登录/注册/手机号绑定）
  │                ├─ WxBindService（商户绑定申请/审批）
  │                ├─ WxNotifyService（微信消息通知）
  │                └─ PortalService（复用现有，数据查询）
  │                │
  │                ↓
  │           DBConnection → SQL Server
  │
  └─ 微信服务器 ← OAuth2.0回调 / 消息推送
```

### 2.2 蓝图设计

新增蓝图 `wx_bp`，URL前缀 `/wx`：

| 路由 | 方法 | 功能 | 权限 |
|------|------|------|------|
| `/wx/` | GET | 微信门户首页 | wx_login |
| `/wx/auth/login` | GET | 微信授权登录入口 | 公开 |
| `/wx/auth/callback` | GET | 微信OAuth回调 | 公开 |
| `/wx/auth/phone` | GET/POST | 手机号绑定页面 | wx_login |
| `/wx/bind/apply` | GET/POST | 申请绑定商户 | wx_login |
| `/wx/bind/status` | GET | 绑定状态查看 | wx_login |
| `/wx/contracts` | GET | 我的合同 | wx_bound |
| `/wx/utility` | GET | 水电费 | wx_bound |
| `/wx/scale` | GET | 过磅数据 | wx_bound |
| `/wx/finance` | GET | 缴费记录 | wx_bound |
| `/wx/profile` | GET | 个人信息 | wx_login |
| `/wx/switch` | GET/POST | 切换商户 | wx_bound |

API路由：

| 路由 | 方法 | 功能 |
|------|------|------|
| `/wx/api/dashboard` | GET | 首页统计数据 |
| `/wx/api/contracts` | GET | 合同列表数据 |
| `/wx/api/utility` | GET | 水电费数据 |
| `/wx/api/scale-records` | GET | 过磅记录数据 |
| `/wx/api/receivables` | GET | 缴费记录数据 |
| `/wx/api/bind/apply` | POST | 提交绑定申请 |
| `/wx/api/bind/cancel` | POST | 取消绑定申请 |
| `/wx/api/switch` | POST | 切换当前商户 |

管理端新增路由（在现有管理蓝图中）：

| 路由 | 方法 | 功能 |
|------|------|------|
| `/merchant/bind-requests` | GET | 商户绑定申请列表 |
| `/merchant/api/bind-approve/<id>` | POST | 审批通过 |
| `/merchant/api/bind-reject/<id>` | POST | 审批驳回 |

### 2.3 模板结构

```
templates/
├── wx_base.html              # 微信端母版（移动端适配）
├── wx/
│   ├── index.html            # 首页
│   ├── auth/
│   │   ├── login.html        # 登录页
│   │   └── phone.html        # 手机号绑定
│   ├── bind/
│   │   ├── apply.html        # 申请绑定
│   │   └── status.html       # 绑定状态
│   ├── contracts.html        # 合同列表
│   ├── utility.html          # 水电费
│   ├── scale.html            # 过磅数据
│   ├── finance.html          # 缴费记录
│   ├── profile.html          # 个人信息
│   └── switch.html           # 切换商户
```

---

## 3. 数据库设计

### 3.1 新增表

#### MerchantBinding（商户绑定申请表）

| 字段 | 类型 | 说明 |
|------|------|------|
| BindingID | INT IDENTITY(1,1) PK | 绑定ID |
| UserID | INT FK → User.UserID | 申请用户 |
| MerchantID | INT FK → Merchant.MerchantID | 目标商户 |
| BindRole | NVARCHAR(20) | 绑定身份：Boss/Staff/Finance |
| Status | NVARCHAR(20) | 状态：Pending/Approved/Rejected/Cancelled |
| ApplyTime | DATETIME | 申请时间 |
| ApproveTime | DATETIME | 审批时间 |
| ApproverID | INT FK → User.UserID | 审批人 |
| RejectReason | NVARCHAR(200) | 驳回原因 |
| IsActive | BIT DEFAULT 1 | 是否有效 |

#### WxUser（微信用户关联表）

| 字段 | 类型 | 说明 |
|------|------|------|
| WxUserID | INT IDENTITY(1,1) PK | 微信用户ID |
| OpenID | NVARCHAR(100) | 微信OpenID |
| UnionID | NVARCHAR(100) | 微信UnionID（可选） |
| UserID | INT FK → User.UserID | 关联系统用户 |
| Nickname | NVARCHAR(50) | 微信昵称 |
| HeadImgUrl | NVARCHAR(500) | 微信头像URL |
| PhoneNumber | NVARCHAR(20) | 绑定手机号 |
| CurrentMerchantID | INT FK → Merchant.MerchantID | 当前选中的商户 |
| CreateTime | DATETIME | 创建时间 |
| UpdateTime | DATETIME | 更新时间 |

### 3.2 现有表变更

#### User 表

无需结构变更。`WeChatOpenID` 字段已存在，但实际关联通过 WxUser 表管理（一个User可关联多个OpenID，如H5和小程序不同OpenID）。

#### Merchant 表

无需结构变更。`PortalEnabled` 和 `PortalOpenTime` 字段已存在。

### 3.3 身份权限矩阵

| 数据模块 | 老板(Boss) | 员工(Staff) | 财务(Finance) |
|---------|-----------|------------|--------------|
| 合同列表 | ✅ | ✅ | ❌ |
| 合同详情 | ✅ | ✅ | ❌ |
| 电费 | ✅ | ❌ | ✅ |
| 水费 | ✅ | ❌ | ✅ |
| 过磅数据 | ✅ | ✅ | ❌ |
| 磅费 | ✅ | ❌ | ✅ |
| 缴费记录 | ✅ | ❌ | ✅ |
| 商户信息 | ✅ | ✅ | ✅ |
| 首页概览 | ✅ | ✅ | ✅ |

---

## 4. 核心流程设计

### 4.1 微信授权登录流程

```
1. 用户点击公众号菜单 → 访问 /wx/auth/login
2. 后端构造微信OAuth2.0授权URL，重定向到微信
3. 用户同意授权 → 微信回调 /wx/auth/callback?code=xxx
4. 后端用code换取access_token + openid
5. 查询WxUser表：
   a. OpenID已存在 → 获取关联User → login_user() → 重定向到/wx/
   b. OpenID不存在 → 创建User(WeChatUser类型) + WxUser记录 → login_user() → 重定向到/wx/bind/apply
6. 检查用户绑定状态：
   a. 已绑定商户 → 进入首页
   b. 未绑定 → 进入绑定申请页
```

### 4.2 手机号绑定流程

```
1. 用户在 /wx/auth/phone 页面输入手机号
2. 发送短信验证码（调用短信API）
3. 用户输入验证码 → 后端验证
4. 更新 WxUser.PhoneNumber
5. 如果该手机号已有系统账号 → 提示是否关联已有账号
```

### 4.3 商户绑定申请流程

```
1. 用户在 /wx/bind/apply 页面：
   a. 搜索/选择商户（从Merchant列表）
   b. 选择身份（老板/员工/财务）
   c. 填写申请说明（可选）
   d. 提交申请
2. 后端创建 MerchantBinding 记录（Status=Pending）
3. 管理员在后台 /merchant/bind-requests 看到 pending 申请
4. 管理员审批：
   a. 通过 → 更新 Status=Approved, 设置 User.MerchantID（主商户）
            → 发送微信模板消息通知用户
   b. 驳回 → 更新 Status=Rejected, 填写驳回原因
            → 发送微信模板消息通知用户
```

### 4.4 多商户切换流程

```
1. 用户在 /wx/switch 页面看到已绑定的商户列表
2. 当前商户高亮显示
3. 点击其他商户 → POST /wx/api/switch
4. 更新 WxUser.CurrentMerchantID
5. 刷新页面数据
```

---

## 5. 服务层设计

### 5.1 WxAuthService

```python
class WxAuthService:
    @staticmethod
    def get_auth_url(redirect_uri, state=None)  # 构造微信OAuth URL

    @staticmethod
    def handle_callback(code) -> User  # 处理OAuth回调，返回User对象

    @staticmethod
    def get_wx_user(openid) -> WxUser  # 根据OpenID查询微信用户

    @staticmethod
    def create_wx_user(openid, unionid, nickname, headimgurl) -> tuple[WxUser, User]  # 创建微信用户

    @staticmethod
    def bind_phone(wx_user_id, phone, code) -> bool  # 绑定手机号

    @staticmethod
    def send_sms_code(phone) -> bool  # 发送短信验证码
```

### 5.2 WxBindService

```python
class WxBindService:
    @staticmethod
    def apply_binding(user_id, merchant_id, bind_role, remark=None) -> MerchantBinding  # 提交绑定申请

    @staticmethod
    def cancel_binding(binding_id, user_id) -> bool  # 取消绑定申请

    @staticmethod
    def get_user_bindings(user_id) -> list  # 获取用户的绑定列表

    @staticmethod
    def get_pending_requests(merchant_id=None) -> list  # 获取待审批列表

    @staticmethod
    def approve_binding(binding_id, approver_id) -> bool  # 审批通过

    @staticmethod
    def reject_binding(binding_id, approver_id, reason) -> bool  # 审批驳回

    @staticmethod
    def get_user_current_merchant(user_id) -> Merchant  # 获取当前选中商户

    @staticmethod
    def switch_merchant(user_id, merchant_id) -> bool  # 切换商户
```

### 5.3 WxNotifyService

```python
class WxNotifyService:
    @staticmethod
    def send_bind_approved(openid, merchant_name, bind_role)  # 绑定通过通知

    @staticmethod
    def send_bind_rejected(openid, merchant_name, reason)  # 绑定驳回通知

    @staticmethod
    def send_new_bind_request(admin_openids, merchant_name, user_name)  # 新申请通知管理员
```

### 5.4 PortalService（复用）

现有 PortalService 的 `get_dashboard`, `get_contracts`, `get_receivables`, `get_scale_records`, `get_utility_readings` 方法直接复用，仅需在调用时传入当前选中的 merchant_id 和用户的 bind_role 做权限过滤。

---

## 6. 微信配置

### 6.1 所需微信能力

| 能力 | 用途 | 要求 |
|------|------|------|
| 网页授权(OAuth2.0) | 微信内H5登录 | 已认证服务号 |
| 模板消息 | 审批结果通知 | 已认证服务号 |
| JS-SDK | 微信内H5能力增强 | 已认证服务号 |
| 手机号获取 | 小程序端快速获取手机号 | 小程序 |

### 6.2 配置项

```python
WX_APP_ID = ''           # 公众号AppID
WX_APP_SECRET = ''       # 公众号AppSecret
WX_TOKEN = ''            # 公众号Token
WX_ENCODING_AES_KEY = '' # 公众号EncodingAESKey
WX_TEMPLATE_BIND_RESULT = ''  # 绑定结果通知模板ID
```

---

## 7. 前端设计

### 7.1 wx_base.html 母版

- 移动端优先，viewport meta标签
- 底部Tab导航：首页 / 合同 / 缴费 / 我的
- 顶部标题栏，带返回按钮
- 微信JS-SDK初始化
- 全局Toast提示（复用admin.js逻辑）

### 7.2 页面设计要点

- 所有列表页使用下拉刷新 + 上拉加载更多
- 卡片式布局，适配手机屏幕
- 数据为空时显示空状态图
- 绑定状态页显示申请进度（待审批/已通过/已驳回）

---

## 8. 安全设计

### 8.1 认证安全

- 微信OAuth2.0标准流程，code一次性使用
- OpenID与User关联，防止伪造
- 手机号绑定需短信验证码验证

### 8.2 数据隔离

- 所有数据查询必须通过 `current_merchant_id` 过滤
- `wx_bound` 装饰器确保用户已绑定商户
- 身份权限装饰器 `wx_role_required(['Boss', 'Finance'])` 控制数据可见性

### 8.3 CSRF保护

- 所有POST请求携带CSRF令牌
- 微信OAuth回调验证state参数

---

## 9. 文件变更清单

### 新增文件

| 文件 | 说明 |
|------|------|
| `app/routes/wx.py` | 微信门户路由 |
| `app/services/wx_auth_service.py` | 微信认证服务 |
| `app/services/wx_bind_service.py` | 商户绑定服务 |
| `app/services/wx_notify_service.py` | 微信通知服务 |
| `app/models/wx_user.py` | 微信用户模型 |
| `app/models/merchant_binding.py` | 商户绑定模型 |
| `templates/wx_base.html` | 微信端母版 |
| `templates/wx/index.html` | 首页 |
| `templates/wx/auth/login.html` | 登录页 |
| `templates/wx/auth/phone.html` | 手机号绑定 |
| `templates/wx/bind/apply.html` | 申请绑定 |
| `templates/wx/bind/status.html` | 绑定状态 |
| `templates/wx/contracts.html` | 合同列表 |
| `templates/wx/utility.html` | 水电费 |
| `templates/wx/scale.html` | 过磅数据 |
| `templates/wx/finance.html` | 缴费记录 |
| `templates/wx/profile.html` | 个人信息 |
| `templates/wx/switch.html` | 切换商户 |
| `templates/merchant/bind_requests.html` | 管理端绑定审批 |
| `scripts/migrate_wx_tables.sql` | 数据库迁移脚本 |
| `config/wx_config.py` | 微信配置 |

### 修改文件

| 文件 | 变更 |
|------|------|
| `app/__init__.py` | 注册 wx_bp 蓝图 |
| `app/services/portal_service.py` | 增加 bind_role 参数做权限过滤 |
| `app/routes/merchant.py` | 增加绑定审批路由 |
| `templates/merchant/list.html` | 增加绑定审批入口 |
| `config/base.py` | 增加微信配置项 |
| `requirements.txt` | 增加 wechatpy 依赖（已有但未使用） |

---

## 10. 实施阶段建议

### Phase 2A：基础框架 + 微信登录

1. 数据库迁移（WxUser + MerchantBinding表）
2. 微信配置
3. wx_bp 蓝图骨架
4. wx_base.html 母版
5. 微信OAuth2.0登录流程
6. 手机号绑定

### Phase 2B：商户绑定 + 审批

7. 商户绑定申请页面
8. 绑定状态查看
9. 管理端审批功能
10. 微信模板消息通知

### Phase 2C：数据查看 + 权限

11. 首页数据概览
12. 合同列表（身份权限过滤）
13. 水电费（身份权限过滤）
14. 过磅数据（身份权限过滤）
15. 缴费记录（身份权限过滤）
16. 商户切换功能

### Phase 2D：个人信息 + 优化

17. 个人信息页面
18. 体验优化（下拉刷新、空状态等）
19. 微信JS-SDK集成
