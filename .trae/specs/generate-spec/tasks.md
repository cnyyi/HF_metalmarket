# 任务列表

## 第一阶段：项目初始化 ✅ 已完成

- [x] 任务1：创建项目基础结构
  - [x] 创建项目目录结构（app/routes, app/services, app/models, app/forms, templates, utils, static）
  - [x] 配置 Flask 应用
  - [x] 配置数据库连接（utils/database.py）
  - [x] 创建基础模板（base.html, admin_base.html, public_base.html, merchant_base.html）
  - [x] 创建数据库初始化脚本（utils/init_database.py）

## 第二阶段：用户认证模块 ✅ 已完成

- [x] 任务2：实现用户登录功能
  - [x] 创建用户表
  - [x] 创建角色表
  - [x] 创建权限表
  - [x] 创建用户角色关联表
  - [x] 创建角色权限关联表
  - [x] 实现登录接口（GET/POST /auth/login）
  - [x] 实现登出接口（GET /auth/logout）
  - [x] 实现注册接口（GET/POST /auth/register）
  - [x] 实现首页接口（GET /auth/）
  - [x] 创建登录页面（templates/auth/login.html）
  - [x] 创建注册页面（templates/auth/register.html）
  - [x] 实现RBAC权限控制

## 第三阶段：用户管理模块 ✅ 已完成

- [x] 任务3：实现用户管理功能
  - [x] 实现用户列表接口（GET /user/list）
  - [x] 实现添加用户接口（GET/POST /user/add）
  - [x] 实现编辑用户接口（GET/POST /user/edit/<id>）
  - [x] 实现删除用户接口（GET /user/delete/<id>）
  - [x] 实现修改密码接口（GET/POST /user/change_password）
  - [x] 创建用户列表页面（templates/user/list.html）
  - [x] 创建添加用户页面（templates/user/add.html）
  - [x] 创建编辑用户页面（templates/user/edit.html）
  - [x] 创建修改密码页面（templates/user/change_password.html）
  - [x] 实现搜索和分页功能
  - [x] 实现权限控制（user_manage权限）

## 第四阶段：商户管理模块 ✅ 已完成

- [x] 任务4：实现商户管理功能
  - [x] 创建商户表
  - [x] 实现商户列表接口（GET /merchant/list）
  - [x] 实现添加商户接口（GET/POST /merchant/add）
  - [x] 实现编辑商户接口（GET/POST /merchant/edit/<id>）
  - [x] 创建商户列表页面（templates/merchant/list.html）
  - [x] 创建添加商户页面（templates/merchant/add.html）
  - [x] 创建编辑商户页面（templates/merchant/edit.html）
  - [x] 实现搜索和分页功能

## 第五阶段：地块管理模块 🔄 进行中

- [ ] 任务5：实现地块管理功能
  - [x] 创建地块表
  - [x] 创建地块列表页面（templates/plot/list.html）
  - [x] 创建添加地块页面（templates/plot/add.html）
  - [x] 创建编辑地块页面（templates/plot/edit.html）
  - [ ] 实现地块列表接口（GET /plot/list）
  - [ ] 实现新增地块接口（POST /plot/add）
  - [ ] 实现更新地块接口（POST /plot/edit/<id>）
  - [ ] 实现删除地块接口
  - [ ] 实现租金自动计算功能

## 第六阶段：合同管理模块 🔄 进行中

- [ ] 任务6：实现合同管理功能
  - [x] 创建合同表
  - [x] 创建合同列表页面（templates/contract/list.html）
  - [x] 创建添加合同页面（templates/contract/add.html）
  - [x] 创建编辑合同页面（templates/contract/edit.html）
  - [ ] 实现合同列表接口（GET /contract/list）
  - [ ] 实现创建合同接口（POST /contract/add）
  - [ ] 实现更新合同接口（POST /contract/edit/<id>）
  - [ ] 实现终止合同接口
  - [ ] 实现合同续签接口
  - [ ] 实现合同编号自动生成功能
  - [ ] 实现租金自动计算功能
  - [ ] 实现合同状态流转功能

## 第七阶段：水电计费模块 🔄 进行中

- [ ] 任务7：实现水电计费功能
  - [x] 创建水电表读数表
  - [x] 创建水电表列表页面（templates/utility/list.html）
  - [x] 创建添加水电表页面（templates/utility/add.html）
  - [x] 创建编辑水电表页面（templates/utility/edit.html）
  - [x] 创建水表抄表页面（templates/utility/water_meter.html）
  - [x] 创建电表抄表页面（templates/utility/electricity_meter.html）
  - [ ] 实现水电表列表接口（GET /utility/list）
  - [ ] 实现添加水电表接口（POST /utility/add）
  - [ ] 实现编辑水电表接口（POST /utility/edit/<id>）
  - [ ] 实现水表抄表接口（GET/POST /utility/water_meter）
  - [ ] 实现电表抄表接口（GET/POST /utility/electricity_meter）
  - [ ] 实现费用自动计算功能

## 第八阶段：财务管理模块 🔄 进行中

- [ ] 任务8：实现财务管理功能
  - [x] 创建应收账款表
  - [x] 创建应收账款页面（templates/finance/receivable.html）
  - [x] 创建应付账款页面（templates/finance/payable.html）
  - [x] 创建现金流水页面（templates/finance/cash_flow.html）
  - [ ] 实现应收账款列表接口（GET /finance/receivable）
  - [ ] 实现应付账款列表接口（GET /finance/payable）
  - [ ] 实现现金流水列表接口（GET /finance/cash_flow）
  - [ ] 实现生成应收账款接口
  - [ ] 实现收款记录接口

## 第九阶段：磅秤管理模块 🔄 进行中

- [ ] 任务9：实现磅秤管理功能
  - [x] 创建磅秤记录表
  - [x] 创建磅秤列表页面（templates/scale/list.html）
  - [x] 创建过磅记录页面（templates/scale/records.html）
  - [ ] 实现磅秤列表接口（GET /scale/list）
  - [ ] 实现过磅记录列表接口（GET /scale/records）
  - [ ] 实现记录过磅接口
  - [ ] 实现净重计算

## 第十阶段：仪表盘统计模块 ⬜ 待开始

- [ ] 任务10：实现仪表盘统计功能
  - [ ] 实现获取统计数据接口
  - [ ] 完善首页仪表盘
  - [ ] 实现数据可视化

## 第十一阶段：测试与部署 ⬜ 待开始

- [ ] 任务11：系统测试
  - [ ] 编写单元测试
  - [ ] 进行功能测试
  - [ ] 进行性能测试
  - [ ] 进行安全测试

- [ ] 任务12：系统部署
  - [ ] 准备生产环境
  - [ ] 部署系统到生产环境
  - [ ] 进行系统验收

## 任务依赖关系

- 任务2 依赖 任务1 ✅
- 任务3 依赖 任务2 ✅
- 任务4 依赖 任务2 ✅
- 任务5 依赖 任务4
- 任务6 依赖 任务4 和 任务5
- 任务7 依赖 任务6
- 任务8 依赖 任务6 和 任务7
- 任务9 依赖 任务4
- 任务10 依赖 任务4、任务5、任务6、任务7、任务8、任务9
- 任务11 依赖 任务1-10
- 任务12 依赖 任务11
