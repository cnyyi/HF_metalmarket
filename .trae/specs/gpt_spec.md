
# 🧠 一、系统总体定位（最终统一认知）

```text
系统类型：多租户园区/交易市场综合管理系统
核心能力：
- 资源管理（地块）
- 合同管理
- 计费系统（价格规则）
- 财务系统（应收 + 收款）
- 水电系统
- 用户与权限系统（多组织绑定）
- 信息发布系统（外部访问）
```

---

# 👥 二、用户体系（完整）

---

## 2.1 用户类型（逻辑角色）

```text
1、市场管理方（公司管理员/员工）
2、市场商户（租户及员工）
3、往来商户（客户，按商户隔离）
4、外部用户（未绑定用户）
```

---

## 2.2 用户实体（User）

```yaml
entity: User

fields:
  - id
  - username
  - password_hash
  - phone
  - status [active, inactive]
  - is_admin (平台管理员)
```

---

## 2.3 用户绑定关系（核心 ⭐）

```yaml
entity: UserBinding

fields:
  - id
  - user_id
  - target_type [company, merchant]
  - target_id
  - role [owner, finance, staff]
  - status [pending, approved, rejected]
```

---

## 2.4 用户绑定流程

```text
注册 → 外部用户
↓
申请绑定（选择商户 + 角色）
↓
生成 UserBinding（pending）
↓
管理员审批
↓
生效权限
```

---

## 2.5 权限模型（三层）

```text
User → UserBinding → Role → 权限
```

---

## 2.6 数据隔离规则

```text
用户只能访问：
- 自己绑定商户的数据
- 管理员可访问全部
```

---

# 🏢 三、商户体系（多租户核心）

---

## 3.1 商户实体（Merchant）

```yaml
entity: Merchant

fields:
  - id
  - name
  - type [tenant, partner]
  - parent_id
  - owner_user_id
  - contact_phone
  - status
```

---

## 3.2 商户类型

```text
tenant：市场租户
partner：往来商户
```

---

## 3.3 数据归属规则

```text
所有业务数据必须绑定 merchant_id：
- 合同
- 应收
- 收款
- 水电
```

---

# 🏗 四、地块系统（资源管理）

---

## 4.1 地块实体（Plot）

```yaml
entity: Plot

fields:
  - id
  - code（唯一编号）
  - type [混凝土土地、钢结构厂房等]
  - area
  - map_path

derived:
  - current_status（occupied / vacant）
```

---

## 4.2 核心规则

```text
同一时间：
一个地块只能被一个合同占用
```

---

# 📄 五、合同系统（核心业务）

---
***合同提前解除的处理***
```text
如果合同提前解除，
- 合同状态变更为 inactive
- 合同关联的地块占用状态变更为 vacant
```





## 5.1 合同实体（Contract）

```yaml
entity: Contract

fields:
  - id
  - merchant_id
  - contract_number
  - start_date
  - end_date
  - billing_cycle [月/季/半年/年]
  - deposit_amount
  - status
```

---

## 5.2 合同地块绑定（核心 ⭐）

```yaml
entity: ContractPlot

fields:
  - contract_id
  - plot_id

  - unit_price（锁定价格）
  - area
  - monthly_rent
  - yearly_rent
```

---

## 5.3 关键规则

```text
1. 一个合同可以绑定多个地块
2. 地块不能重复出租（时间不可重叠）
3. 合同签订时锁定价格（不能动态查）
```

---

## 5.4 地块占用约束（关键）

```text
如果：
新合同时间 与 现有合同时间重叠
且地块相同
→ 禁止绑定
```

---

# 💰 六、价格体系（计费核心）

---

## 6.1 价格规则（PriceRule）

```yaml
entity: PriceRule

fields:
  - id
  - plot_type
  - billing_cycle
  - unit_price
  - effective_date
  - expire_date
```

---

## 6.2 核心能力

```text
- 不同周期不同价格
- 支持历史价格
- 支持调价
```

---

## 6.3 使用规则

```text
创建合同时：
从 PriceRule 获取价格
→ 写入 ContractPlot（锁定）
```

---

# 🧾 七、应收系统（Receivable）

---

## 7.1 应收实体

```yaml
entity: Receivable

fields:
  - id
  - contract_id
  - merchant_id
  - period_start
  - period_end
  - amount
  - paid_amount
```

---

## 7.2 派生字段

```yaml
remaining_amount = amount - paid_amount

status:
  pending / partial / paid
```

---

## 7.3 生成规则

```text
根据合同自动生成：
- 月付 → 每月
- 季付 → 每3个月
- 年付 → 每年
```

---

# 💳 八、收款系统（Payment）

---

## 8.1 收款主表

```yaml
entity: Payment

fields:
  - id
  - merchant_id
  - total_amount
  - payment_date
  - type [rent, deposit]
  - status
```

---

## 8.2 收款分摊（核心 ⭐）

```yaml
entity: PaymentAllocation

fields:
  - payment_id
  - receivable_id
  - allocated_amount
```

---

## 8.3 核心规则

```text
1. 一笔收款可以对应多笔应收
2. 不允许预收款
3. 分摊总额必须等于收款金额
```

---

## 8.4 联动逻辑

```text
Payment → Allocation → 更新 Receivable.paid_amount
```

---

# 💧 九、水电系统（Meter）

---

## 9.1 抄表记录

```yaml
entity: MeterRecord

fields:
  - contract_id
  - type [water, electricity]
  - previous_reading
  - current_reading
  - usage
  - unit_price
```

---

## 9.2 派生

```text
usage = 当前 - 上次
amount = usage × 单价
```

---

## 9.3 联动

```text
MeterRecord → 生成 Receivable
```

---

# 🔗 十、完整业务链路（最重要）

---

## 主链路（租金）

```text
PriceRule
   ↓
Contract
   ↓
ContractPlot（锁定价格）
   ↓
Receivable（自动生成）
   ↓
Payment
   ↓
PaymentAllocation
```

---

## 水电链路

```text
MeterRecord
   ↓
Receivable
   ↓
Payment
```

---

# 🔐 十一、权限系统（完整）

---

## 11.1 权限结构

```text
用户 → 绑定 → 角色 → 权限 → 数据范围
```

---

## 11.2 角色

```text
admin（平台）
owner（负责人）
finance（财务）
staff（员工）
external（外部）
```

---

## 11.3 权限控制

```text
操作权限：
- create / read / update / delete

数据权限：
- 仅自己商户
- 或全部（管理员）
```

---

# 🌐 十二、外部用户系统

---

## 功能

```text
- 浏览公告
- 查看空置地块
- 注册账号
- 申请绑定商户
```

---

# 🧩 十三、系统模块总览

---

## 13.1 市场管理系统

* 地块管理
* 商户管理
* 用户管理
* 日志管理

---

## 13.2 财务系统

* 应收管理
* 收款管理
* 对账

---

## 13.3 合同系统

* 合同管理
* 地块绑定
* 收费规则

---

## 13.4 水电系统

* 抄表
* 费用计算

---

## 13.5 信息发布系统

* 公告
* 对外展示

---

## 13.6 系统管理

* 权限
* 配置
* 字典（价格规则）

---

# ⚠️ 十四、关键设计原则（必须遵守）

---

## ❗1：价格必须锁定

```text
合同创建时写入价格
不能动态查
```

---

## ❗2：金额必须可推导

```text
remaining = amount - paid
```

---

## ❗3：收款必须分摊

```text
不能直接改应收
```

---

## ❗4：数据必须归属商户

```text
所有核心表必须有 merchant_id
```

---

## ❗5：禁止时间重叠出租

```text
地块同一时间只能一个合同
```

---

# 📢 十五、信息发布系统

---

## 15.1 公告实体（Announcement）

```yaml
entity: Announcement

fields:
  - id (INT, PK, 自增)
  - title (NVARCHAR(200), 公告标题)
  - content (NVARCHAR(MAX), 公告内容，支持富文本)
  - category (NVARCHAR(50), 分类：通知/政策/招商/其他)
  - priority (NVARCHAR(20), 优先级：置顶/普通)
  - is_published (BIT, 是否已发布，默认0)
  - publish_time (DATETIME, 发布时间，可为空)
  - expire_time (DATETIME, 过期时间，可为空)
  - author_id (INT, 发布人，关联User.UserID)
  - view_count (INT, 浏览次数，默认0)
  - create_time (DATETIME, 创建时间)
  - update_time (DATETIME, 更新时间)
```

---

## 15.2 公告分类规则

```text
分类由 Sys_Dictionary 管理（DictType = 'announcement_category'）
默认分类：
  - 通知：日常通知、停水停电通知
  - 政策：市场管理政策、规章制度
  - 招商：空置地块招商信息
  - 其他：其他公告
```

---

## 15.3 公告状态流转

```text
草稿(is_published=0)
  ↓ 发布操作
已发布(is_published=1, publish_time=当前时间)
  ↓ 到达expire_time 或 手动下架
已过期/已下架(is_published=0)
```

---

## 15.4 公告访问规则

```text
管理员：
  - 创建/编辑/删除/发布/下架公告
  - 查看所有公告（含草稿）

商户用户：
  - 只能查看已发布且未过期的公告
  - 浏览时自动增加 view_count

外部用户：
  - 只能查看分类为"招商"的已发布公告
  - 无需登录即可浏览
```

---

## 15.5 公告管理页面

```text
路由前缀：/announcement

页面列表：
  /announcement/list          - 公告列表（管理端）
  /announcement/create        - 创建公告
  /announcement/edit/<id>     - 编辑公告
  /announcement/delete/<id>   - 删除公告（Ajax）
  /announcement/publish/<id>  - 发布公告（Ajax）
  /announcement/unpublish/<id> - 下架公告（Ajax）

API列表：
  GET  /announcement/data     - 获取公告列表数据
  POST /announcement/create   - 创建公告
  POST /announcement/edit/<id> - 编辑公告
  POST /announcement/delete/<id> - 删除公告

对外展示：
  /public/announcements       - 公开公告列表（外部用户）
  /public/announcement/<id>   - 公告详情（外部用户）
```

---

## 15.6 公告与现有系统集成

```text
1. 公告创建时记录 author_id（关联User表）
2. 公告分类使用 Sys_Dictionary 管理
3. 权限控制：announcement_manage（新增权限项）
4. admin/staff 角色拥有公告管理权限
5. merchant 角色仅可查看
```

---

# 📝 十六、日志管理系统

---

## 16.1 操作日志实体（OperationLog）

```yaml
entity: OperationLog

fields:
  - id (INT, PK, 自增)
  - user_id (INT, 操作人，关联User.UserID)
  - username (NVARCHAR(50), 操作人用户名，冗余存储)
  - module (NVARCHAR(50), 操作模块：商户/合同/地块/水电/财务/用户/公告)
  - action (NVARCHAR(50), 操作类型：create/update/delete/login/logout/export/import)
  - target_type (NVARCHAR(50), 操作对象类型：Merchant/Contract/Plot等)
  - target_id (NVARCHAR(50), 操作对象ID)
  - target_name (NVARCHAR(200), 操作对象名称/编号，冗余存储)
  - detail (NVARCHAR(MAX), 操作详情，JSON格式记录变更内容)
  - ip_address (NVARCHAR(50), 操作IP地址)
  - user_agent (NVARCHAR(500), 浏览器UA)
  - create_time (DATETIME, 操作时间)
```

---

## 16.2 日志记录规则

```text
自动记录以下操作：

1. 数据变更（create/update/delete）
   - 记录变更前后的值（JSON格式）
   - update操作记录修改了哪些字段

2. 用户登录/登出
   - 记录登录IP和时间
   - 记录登出时间

3. 敏感操作
   - 删除操作（不可逆）
   - 权限变更
   - 角色分配
   - 数据导出

4. 财务操作
   - 收款/付款
   - 应收/应付变更
   - 现金流水
```

---

## 16.3 日志记录方式

```text
采用装饰器模式，在路由层自动记录：

@log_operation(module='商户管理', action='create', target_type='Merchant')
def create_merchant():
    ...

装饰器自动获取：
  - 当前登录用户（from session）
  - 请求IP地址
  - 操作时间
  - 请求参数

detail字段格式：
{
  "before": {"field1": "old_value", "field2": "old_value"},
  "after": {"field1": "new_value", "field2": "new_value"},
  "changes": ["field1", "field2"]
}
```

---

## 16.4 日志查询规则

```text
管理员：
  - 查看所有日志
  - 按模块/操作类型/时间范围/操作人筛选
  - 导出日志

商户用户：
  - 不可查看操作日志

日志保留策略：
  - 默认保留180天
  - 超期日志自动归档（可配置）
```

---

## 16.5 日志管理页面

```text
路由前缀：/log

页面列表：
  /log/list                   - 日志列表

API列表：
  GET /log/data               - 获取日志列表数据（支持分页和筛选）
  GET /log/detail/<id>        - 获取日志详情
  GET /log/export             - 导出日志（Excel）

筛选参数：
  - module：操作模块
  - action：操作类型
  - user_id：操作人
  - start_date / end_date：时间范围
  - keyword：关键词搜索（target_name）
```

---

## 16.6 日志与现有系统集成

```text
1. 日志记录时关联 user_id（User表）
2. 冗余存储 username，避免用户删除后无法追溯
3. module 字段与现有权限模块对应
4. 权限控制：log_manage（新增权限项）
5. 仅 admin 角色拥有日志查看权限
```

---

# 🌐 十七、外部用户系统

---

## 17.1 外部用户定义

```text
外部用户 = 未绑定商户的注册用户

与内部用户的区别：
  - 无 UserBinding 关系
  - 无 UserRole 分配
  - 只能访问公开资源
  - 可申请绑定商户（升级为内部用户）
```

---

## 17.2 外部用户可访问功能

```text
无需登录：
  - 浏览招商公告（/public/announcements，分类=招商）
  - 查看空置地块列表（/public/plots，Status=空闲）
  - 注册账号（/auth/register）

需要登录：
  - 查看所有已发布公告
  - 申请绑定商户（/user/bind_request）
  - 查看自己的绑定申请状态
  - 修改个人资料
```

---

## 17.3 用户绑定申请实体（UserBindingRequest）

```yaml
entity: UserBindingRequest

fields:
  - id (INT, PK, 自增)
  - user_id (INT, 申请人，关联User.UserID)
  - merchant_id (INT, 申请绑定的商户，关联Merchant.MerchantID)
  - requested_role (NVARCHAR(50), 申请角色：owner/finance/staff)
  - status (NVARCHAR(20), 状态：pending/approved/rejected)
  - request_note (NVARCHAR(500), 申请备注)
  - review_note (NVARCHAR(500), 审批备注)
  - reviewer_id (INT, 审批人，关联User.UserID)
  - review_time (DATETIME, 审批时间)
  - create_time (DATETIME, 申请时间)
  - update_time (DATETIME, 更新时间)
```

---

## 17.4 绑定申请流程

```text
1. 外部用户注册账号
   ↓
2. 登录后，在"我的绑定"页面点击"申请绑定"
   ↓
3. 选择商户 + 申请角色 + 填写备注
   ↓
4. 生成 UserBindingRequest（status=pending）
   ↓
5. 管理员在"绑定审批"页面查看待审批列表
   ↓
6a. 审批通过：
    - 创建 UserRole 记录（分配对应角色）
    - 更新 User.MerchantID（绑定商户）
    - 更新 UserBindingRequest.status = approved
    - 记录操作日志
   ↓
6b. 审批拒绝：
    - 更新 UserBindingRequest.status = rejected
    - 填写拒绝原因
    - 通知申请人
```

---

## 17.5 绑定申请规则

```text
1. 一个用户同一时间只能绑定一个商户
2. 一个用户同时只能有一条 pending 状态的申请
3. 申请被拒绝后可以重新申请
4. 已绑定商户的用户可以申请更换绑定（需先解绑）
5. admin 角色可以直接为用户分配商户和角色（无需审批）
```

---

## 17.6 外部用户权限矩阵

```text
功能                    | 外部用户(未登录) | 外部用户(已登录) | 商户用户 | 管理员
------------------------|-----------------|-----------------|---------|--------
浏览招商公告             | ✅              | ✅              | ✅      | ✅
查看空置地块             | ✅              | ✅              | ✅      | ✅
注册账号                 | ✅              | -               | -       | -
登录系统                 | -               | ✅              | ✅      | ✅
查看所有公告             | -               | ✅              | ✅      | ✅
申请绑定商户             | -               | ✅              | -       | -
查看绑定状态             | -               | ✅              | ✅      | ✅
修改个人资料             | -               | ✅              | ✅      | ✅
商户管理                 | -               | -               | 🔒自己  | ✅
合同管理                 | -               | -               | 🔒自己  | ✅
水电查看                 | -               | -               | 🔒自己  | ✅
财务查看                 | -               | -               | 🔒自己  | ✅
用户管理                 | -               | -               | -       | ✅
日志管理                 | -               | -               | -       | ✅
公告管理                 | -               | -               | -       | ✅
绑定审批                 | -               | -               | -       | ✅
```

---

## 17.7 外部用户系统页面

```text
公开页面（无需登录）：
  /public/announcements       - 招商公告列表
  /public/announcement/<id>   - 公告详情
  /public/plots               - 空置地块列表
  /auth/register              - 注册页面

外部用户页面（需登录）：
  /user/my_binding            - 我的绑定状态
  /user/bind_request          - 申请绑定商户
  /user/profile               - 个人资料

管理员页面：
  /user/binding_requests      - 绑定审批列表
  /user/binding_approve/<id>  - 审批绑定申请
```

---

## 17.8 外部用户系统与现有系统集成

```text
1. 注册流程复用现有 auth.register 路由
2. 注册后默认无角色、无商户绑定
3. 绑定审批通过后：
   - 创建 UserRole 记录（角色=申请的requested_role）
   - 更新 User.MerchantID
4. 权限控制：binding_manage（新增权限项）
5. admin 角色拥有绑定审批权限
6. 操作日志记录绑定审批操作
```

---

# 🔗 十八、新增模块与现有系统的关系

---

## 18.1 新增数据库表

```text
1. Announcement        - 公告表
2. OperationLog        - 操作日志表
3. UserBindingRequest  - 用户绑定申请表
```

---

## 18.2 新增路由蓝图

```text
1. announcement_bp  - /announcement  - 公告管理
2. log_bp           - /log           - 日志管理
3. public_bp        - /public        - 公开访问（外部用户）
```

---

## 18.3 新增权限项

```text
1. announcement_manage - 公告管理 - 模块：公告管理
2. log_manage          - 日志管理 - 模块：日志管理
3. binding_manage      - 绑定审批 - 模块：用户管理
```

---

## 18.4 角色权限分配（更新后）

```text
admin（管理员）：
  - 所有权限（10项）
  - 新增：announcement_manage, log_manage, binding_manage

staff（工作人员）：
  - 除用户管理、日志管理外的所有权限
  - 新增：announcement_manage

merchant（商户）：
  - contract_manage, utility_manage, scale_manage
  - 新增：无（仅可查看公告，无需管理权限）
```

---

## 18.5 新增模板目录

```text
templates/
  announcement/        - 公告管理页面
    list.html
    create.html
    edit.html
  log/                 - 日志管理页面
    list.html
    detail.html
  public/              - 公开访问页面
    announcements.html
    announcement_detail.html
    plots.html
  user/                - 新增页面
    my_binding.html
    bind_request.html
    binding_requests.html
```

---

## 18.6 新增服务文件

```text
app/services/
  announcement_service.py  - 公告管理服务
  log_service.py           - 日志管理服务
```

---

## 18.7 新增模型文件

```text
app/models/
  announcement.py          - 公告模型
  operation_log.py         - 操作日志模型
  user_binding.py          - 用户绑定申请模型
```

---

# ⚠️ 十九、补充设计原则

---

## ❗6：日志必须可追溯

```text
所有数据变更操作必须记录日志
日志不可修改、不可删除（仅管理员可归档）
冗余存储关键信息（username、target_name），避免关联数据删除后无法追溯
```

---

## ❗7：外部访问必须隔离

```text
公开页面不暴露内部数据结构
外部用户只能访问明确允许的资源
API接口必须做权限校验，不能仅靠前端隐藏
```

---

## ❗8：公告发布必须审核

```text
公告创建后为草稿状态
仅管理员可发布公告
已发布的公告不可删除，只能下架
```