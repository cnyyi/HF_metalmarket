# 应收账款模块 — 改进提案（Proposal）

## 文档信息

| 项目名称 | 宏发金属交易市场管理系统 |
| ---- | ---- |
| 模块名称 | 应收账款 |
| 文档版本 | V1.0 |
| 编写日期 | 2026-04-15 |

---

## 1. 改进目标

将应收账款模块从"基本可用"提升到"生产就绪"，补齐缺失功能、修复架构问题、提升用户体验。

---

## 2. 改进项总览

| 编号 | 改进项 | 类型 | 优先级 | 影响范围 |
|------|--------|------|--------|---------|
| P-01 | 清理废弃代码 | 技术债 | P1 | receivable_service.py |
| P-02 | 修复详情路由架构违规 | 技术债 | P2 | finance.py, receivable_service.py |
| P-03 | 实现编辑应收功能 | 新功能 | P1 | finance.py, receivable_repo.py, receivable.html |
| P-04 | 实现删除应收功能 | 新功能 | P1 | finance.py, receivable_repo.py, receivable.html |
| P-05 | 增强列表筛选（费用类型+日期范围） | 体验优化 | P2 | finance.py, receivable_repo.py, receivable.html |
| P-06 | 实现导出Excel | 新功能 | P2 | finance.py, receivable.html |
| P-07 | 实现逾期自动检查 | 新功能 | P2 | finance.py, finance_service.py |
| P-08 | 修复MerchantID外键约束问题 | 数据库 | P2 | 数据库迁移脚本 |

---

## 3. 改进项详细方案

### P-01：清理废弃代码

**现状**：
- `ReceivableService.pay()` 方法已废弃，路由层已改用 `FinanceService.collect_receivable()`
- `ReceivableService.get_expense_types()` 已废弃，路由层已改用 `DictService.get_expense_items()`

**方案**：
1. 删除 `ReceivableService.pay()` 方法
2. 删除 `ReceivableService.get_expense_types()` 方法
3. 全局搜索确认无其他调用点

**风险**：低。两个方法均无外部调用。

---

### P-02：修复详情路由架构违规

**现状**：
`finance.py` 的 `receivable_detail` 路由直接访问 `receivable_svc.repo` 和 `finance_svc.collection_repo`，绕过 Service 层。

**方案**：
1. 在 `ReceivableService` 中新增 `get_receivable_detail(receivable_id)` 方法
2. 方法内部调用 repo 获取基本信息 + collection_repo 获取收款历史
3. 修改路由层调用新方法

**风险**：低。纯重构，不改变业务逻辑。

---

### P-03：实现编辑应收功能

**现状**：编辑功能完全缺失。

**方案**：

后端：
1. `receivable_repo.py` 新增 `update()` 方法
2. `receivable_service.py` 新增 `update_receivable()` 方法，包含业务规则校验
3. `finance.py` 新增 `/receivable/update/<id>` POST 路由

前端：
1. 在列表操作列添加"编辑"按钮
2. 点击后弹出模态窗口，加载现有数据
3. 表单字段：金额、到期日期、费用类型、备注
4. 提交时校验业务规则（仅未付款状态可编辑）

**业务规则**：
- 仅 `未付款` 状态可编辑全部字段
- `部分付款` 状态仅可编辑到期日期和备注
- `已付款` 状态不允许编辑
- 系统自动生成的应收编辑时显示提示

---

### P-04：实现删除应收功能

**现状**：删除功能完全缺失。

**方案**：

后端：
1. `receivable_repo.py` 已有 `delete()` 方法
2. `receivable_service.py` 新增 `delete_receivable()` 方法，包含业务规则校验
3. `finance.py` 新增 `/receivable/delete/<id>` POST 路由

前端：
1. 在列表操作列添加"删除"按钮
2. 点击后弹出确认对话框
3. 系统自动生成的应收显示额外提示

**业务规则**：
- 仅 `未付款` 状态可删除
- 已有收款记录（CollectionRecord）的不允许删除
- 删除时同步删除 ReceivableDetail 关联记录

---

### P-05：增强列表筛选

**现状**：仅支持搜索关键词和状态筛选。

**方案**：

后端：
1. `receivable_repo.py` 的 `get_list()` 方法新增 `expense_type_id`、`date_from`、`date_to` 参数
2. SQL WHERE 条件动态追加

前端：
1. 筛选区新增费用类型下拉（数据来源字典表）
2. 新增到期日期范围选择器
3. 筛选条件变更时自动刷新列表

---

### P-06：实现导出Excel

**现状**：按钮存在但功能未实现。

**方案**：

后端：
1. `finance.py` 新增 `/receivable/export` GET 路由
2. 使用 Python `openpyxl` 库生成 Excel
3. 支持与列表相同的筛选参数
4. 返回文件流下载

前端：
1. 修改导出按钮，点击时携带当前筛选条件请求导出接口
2. 使用 `window.location.href` 触发下载

**导出字段**：客户名称、客户类型、费用类型、应收金额、已付金额、剩余金额、到期日期、状态、备注、创建时间

---

### P-07：实现逾期自动检查

**现状**：`check_overdue()` 方法存在但无调用入口。

**方案**：

后端：
1. `finance_service.py` 新增 `check_and_update_overdue()` 方法
2. 批量更新：`UPDATE Receivable SET Status=N'逾期' WHERE DueDate < GETDATE() AND Status=N'未付款'`
3. `finance.py` 新增 `/receivable/overdue_check` POST 路由（手动触发）

前端：
1. 在列表页添加"逾期检查"按钮
2. 点击后调用接口，返回更新的记录数
3. 刷新列表

**暂不实现**：定时任务（需引入 APScheduler 等调度框架，作为独立改进项）

---

### P-08：修复MerchantID外键约束问题

**现状**：
- `Receivable.MerchantID` 为 `NOT NULL FK→Merchant`
- `CollectionRecord.MerchantID` 为 `NOT NULL FK→Merchant`
- 当 CustomerType='Customer' 时，MerchantID 应为 NULL，但 NOT NULL 约束不允许

**方案**：

数据库迁移：
1. `ALTER TABLE Receivable ALTER COLUMN MerchantID INT NULL`
2. `ALTER TABLE CollectionRecord ALTER COLUMN MerchantID INT NULL`
3. 删除并重建外键约束（允许 NULL）

代码调整：
1. `receivable_repo.py` 的 `create()` 方法：CustomerType='Customer' 时 MerchantID 设为 NULL
2. `finance_service.py` 的 `collect_receivable()` 方法：处理 MerchantID 为 NULL 的情况
3. 所有查询 MerchantID 的 SQL 改用 LEFT JOIN

**风险**：中。需确保所有关联代码兼容 NULL 值。

---

## 4. 实施优先级

```
第一阶段（P1 - 核心功能补齐）：
  P-01 清理废弃代码
  P-03 实现编辑应收
  P-04 实现删除应收

第二阶段（P2 - 体验优化与健壮性）：
  P-02 修复详情路由架构违规
  P-05 增强列表筛选
  P-06 实现导出Excel
  P-07 实现逾期自动检查
  P-08 修复MerchantID外键约束
```

---

## 5. 不在本次改进范围内

| 项目 | 原因 |
|------|------|
| 定时任务调度 | 需引入新依赖（APScheduler），作为独立改进项 |
| 逾期邮件/短信提醒 | 需要消息服务基础设施 |
| 应收审批流程 | 业务需求未明确 |
| 批量收款核销 | 当前业务场景不需要 |
| 应收冲抵 | 业务需求未明确 |
