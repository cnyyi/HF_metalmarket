# 宿舍管理模块实施计划

## 概述

基于设计文档 `docs/plans/2026-04-15-dormitory-design.md`，实施宿舍管理模块。

## 实施步骤

### 阶段一：基础设施（数据库 + 服务层骨架）

- [ ] 1.1 编写数据库迁移脚本 `scripts/add_dorm_tables.sql`
  - 创建4张表：DormRoom / DormOccupancy / DormReading / DormBill
  - 插入字典数据（dorm_room_type / dorm_room_status / dorm_tenant_type / dorm_occupancy_status / dorm_bill_status）
  - 插入费用项（expense_item_income 新增宿舍租金/宿舍水费/宿舍电费）
  - 插入客户类型（customer_type 新增宿舍个人）
  - 插入权限 dorm_manage 并赋权 admin + staff
  - 所有插入加 IF NOT EXISTS 幂等处理

- [ ] 1.2 创建服务层 `app/services/dorm_service.py`
  - DormService 类，严格遵循 Routes→Services→DBConnection 架构
  - 房间CRUD方法
  - 入住/退房方法（含房间状态联动）
  - 电表读数方法
  - 账单生成/确认/开账方法
  - 财务联动方法（创建Receivable，复用 FinanceService）
  - 身份证照片上传方法

### 阶段二：路由层 + 页面模板

- [ ] 2.1 创建路由蓝图 `app/routes/dorm.py`
  - dorm_bp → /dorm/
  - 4组路由：房间管理 / 入住管理 / 电表抄表 / 月度账单
  - 身份证上传接口
  - 所有接口加 @login_required + @check_permission('dorm_manage')

- [ ] 2.2 创建页面模板
  - `templates/dorm/rooms.html` — 房间管理
  - `templates/dorm/occupancy.html` — 入住管理
  - `templates/dorm/reading.html` — 电表抄表
  - `templates/dorm/bill.html` — 月度账单

### 阶段三：系统集成

- [ ] 3.1 注册蓝图到 `app/__init__.py`
- [ ] 3.2 更新导航菜单 `templates/admin_base.html`
  - 市场管理下拉内，磅秤数据下方加分隔线
  - 新增4项：宿舍房间/入住管理/电表抄表/宿舍账单
- [ ] 3.3 创建 uploads/dorm_idcard/ 目录（身份证照片存储）

### 阶段四：数据库迁移 + 测试

- [ ] 4.1 执行迁移脚本
- [ ] 4.2 功能测试：房间CRUD / 入住退房 / 抄表 / 生成账单 / 联动应收

## 文件清单

| 操作 | 文件路径 |
|---|---|
| 新增 | scripts/add_dorm_tables.sql |
| 新增 | app/services/dorm_service.py |
| 新增 | app/routes/dorm.py |
| 新增 | templates/dorm/rooms.html |
| 新增 | templates/dorm/occupancy.html |
| 新增 | templates/dorm/reading.html |
| 新增 | templates/dorm/bill.html |
| 修改 | app/__init__.py（注册 dorm_bp） |
| 修改 | templates/admin_base.html（导航菜单） |

## 依赖关系

- 阶段二依赖阶段一（服务层方法）
- 阶段三依赖阶段二（路由函数名）
- 阶段四依赖全部完成
