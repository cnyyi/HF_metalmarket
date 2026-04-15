# Phase 1 设计文档：商户门户

## 1. 目标

让市场商户能够登录系统，查看自己的合同、缴费、过磅等数据，为后续进销存功能奠定基础。

## 2. 用户类型设计

### 2.1 UserType 区分

在 `[User]` 表新增 `UserType` 字段，区分管理端用户和商户端用户：

| UserType | 说明 | 登录后默认页 |
|----------|------|-------------|
| `Admin` | 市场管理方用户 | `/admin/` |
| `Merchant` | 商户端用户 | `/portal/` |

### 2.2 商户用户与商户的关联

- 商户用户通过 `MerchantID` 字段关联到 `Merchant` 表
- 一个商户可以有多个用户（老板+店员）
- 商户用户只能查看自己商户的数据

### 2.3 商户用户角色

新增 `merchant` 角色，权限范围仅限门户功能：

| 权限编码 | 权限名称 | 说明 |
|---------|---------|------|
| `portal_view` | 门户访问 | 登录商户门户 |
| `portal_contract` | 合同查看 | 查看本商户合同 |
| `portal_finance` | 财务查看 | 查看本商户应收/缴费 |
| `portal_scale` | 过磅查看 | 查看本商户过磅记录 |
| `portal_utility` | 水电查看 | 查看本商户水电抄表 |

## 3. 数据库变更

### 3.1 User 表新增字段

```sql
ALTER TABLE [User] ADD UserType NVARCHAR(20) DEFAULT N'Admin';
-- 更新现有数据
UPDATE [User] SET UserType = N'Admin' WHERE UserType IS NULL OR UserType = '';
```

### 3.2 Merchant 表新增字段（可选）

```sql
-- 商户账户状态：是否已开通门户
ALTER TABLE Merchant ADD PortalEnabled BIT DEFAULT 0;
-- 商户门户开通时间
ALTER TABLE Merchant ADD PortalOpenTime DATETIME NULL;
```

## 4. 路由设计

### 4.1 商户门户蓝图 `portal_bp`

| 路由 | 方法 | 功能 | 权限 |
|------|------|------|------|
| `/portal/` | GET | 商户首页（数据概览） | portal_view |
| `/portal/contracts` | GET | 我的合同列表 | portal_contract |
| `/portal/contracts/<id>` | GET | 合同详情 | portal_contract |
| `/portal/receivables` | GET | 我的应收/缴费 | portal_finance |
| `/portal/scale-records` | GET | 过磅记录 | portal_scale |
| `/portal/utility-readings` | GET | 水电抄表 | portal_utility |
| `/portal/profile` | GET | 商户信息 | portal_view |

### 4.2 API 路由

| 路由 | 方法 | 功能 |
|------|------|------|
| `/portal/api/contracts` | GET | 合同列表数据 |
| `/portal/api/receivables` | GET | 应收/缴费数据 |
| `/portal/api/scale-records` | GET | 过磅记录数据 |
| `/portal/api/utility-readings` | GET | 水电抄表数据 |
| `/portal/api/dashboard` | GET | 首页统计数据 |

### 4.3 登录分流

修改 `auth.login` 路由，根据 UserType 登录后重定向：

```python
# 登录成功后
if user.user_type == 'Merchant':
    return redirect(url_for('portal.index'))
else:
    return redirect(url_for('admin.index'))
```

## 5. 数据隔离策略

### 5.1 核心原则

商户用户只能查询 `MerchantID = 当前用户.MerchantID` 的数据。

### 5.2 实现方式

在 `portal_bp` 的每个路由中，通过 `current_user.merchant_id` 过滤：

```python
@portal_bp.route('/api/contracts')
@login_required
def api_contracts():
    merchant_id = current_user.merchant_id
    # 只查该商户的合同
    result = contract_svc.get_contracts(merchant_id=merchant_id, ...)
    return jsonify(result)
```

### 5.3 安全装饰器

```python
def merchant_required(f):
    """确保是商户用户"""
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('auth.login'))
        if current_user.user_type != 'Merchant':
            return redirect(url_for('admin.index'))
        if not current_user.merchant_id:
            abort(403, description='未关联商户')
        return f(*args, **kwargs)
    return decorated
```

## 6. 商户首页设计

### 6.1 数据概览卡片

| 卡片 | 数据源 |
|------|--------|
| 当前合同数 | Contract WHERE MerchantID=? AND Status=N'有效' |
| 待缴金额 | Receivable WHERE MerchantID=? AND Status!=N'已付款' |
| 本月水电 | UtilityReading WHERE MerchantID=? AND 本月 |
| 本月过磅 | ScaleRecord WHERE MerchantID=? AND 本月 |

### 6.2 快捷入口

- 查看合同
- 缴费记录
- 水电抄表
- 过磅记录

### 6.3 待办提醒

- 即将到期合同
- 逾期未缴账单
- 水电异常提醒

## 7. 商户账户管理

### 7.1 创建商户账户

管理端在"商户管理"中增加"开通门户"按钮：

1. 自动生成用户名（如 `m_{MerchantID}` 或商户名拼音）
2. 生成初始密码
3. 设置 UserType='Merchant'
4. 关联 MerchantID
5. 分配 merchant 角色
6. 更新 Merchant.PortalEnabled = 1

### 7.2 管理端界面

在商户详情/编辑页面增加：
- 开通门户按钮
- 重置密码按钮
- 门户状态显示

## 8. 文件变更清单

### 新增文件

| 文件 | 说明 |
|------|------|
| `app/routes/portal.py` | 商户门户路由 |
| `app/services/portal_service.py` | 商户门户服务层 |
| `templates/portal/index.html` | 商户首页 |
| `templates/portal/contracts.html` | 合同列表 |
| `templates/portal/receivables.html` | 缴费记录 |
| `templates/portal/scale_records.html` | 过磅记录 |
| `templates/portal/utility_readings.html` | 水电抄表 |
| `templates/portal/profile.html` | 商户信息 |
| `scripts/migrate_add_user_type.py` | 数据库迁移脚本 |

### 修改文件

| 文件 | 变更 |
|------|------|
| `app/models/user.py` | 新增 user_type 属性 |
| `app/services/auth_service.py` | 查询增加 UserType 字段，登录分流 |
| `app/routes/auth.py` | 登录后按 UserType 重定向 |
| `app/__init__.py` | 注册 portal_bp 蓝图 |
| `templates/merchant_base.html` | 补全导航链接 |
| `app/routes/merchant.py` | 增加"开通门户"功能 |
| `app/services/merchant_service.py` | 增加门户账户管理方法 |

## 9. 实施顺序

1. **数据库迁移**：User 表加 UserType，Merchant 表加 PortalEnabled
2. **User 模型更新**：增加 user_type 属性
3. **AuthService 更新**：查询加 UserType，登录分流
4. **Portal 蓝图+路由**：骨架搭建
5. **Portal Service**：数据查询（带商户隔离）
6. **商户首页**：数据概览
7. **合同查询页**
8. **缴费记录页**
9. **过磅记录页**
10. **水电抄表页**
11. **管理端开通门户功能**
12. **商户信息页**
