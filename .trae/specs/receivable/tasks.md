# 应收账款模块 — 任务清单（Tasks）

## 文档信息

| 项目名称 | 宏发金属交易市场管理系统 |
| ---- | ---- |
| 模块名称 | 应收账款 |
| 文档版本 | V1.0 |
| 编写日期 | 2026-04-15 |

---

## 第一阶段：核心功能补齐（P1）

### Task 1.1：清理废弃代码

**改进项**：P-01
**预估复杂度**：低
**涉及文件**：
- `app/services/receivable_service.py`

**具体步骤**：
1. [ ] 删除 `ReceivableService.pay()` 方法
2. [ ] 删除 `ReceivableService.get_expense_types()` 静态方法
3. [ ] 全局搜索 `pay(` 和 `get_expense_types(` 确认无其他调用
4. [ ] 运行语法检查

**验收标准**：
- 代码中不再包含 `pay()` 和 `get_expense_types()` 方法
- 应用启动无报错
- 应收列表页正常加载

---

### Task 1.2：实现编辑应收功能 — 后端

**改进项**：P-03
**预估复杂度**：中
**涉及文件**：
- `app/repositories/receivable_repo.py`
- `app/services/receivable_service.py`
- `app/routes/finance.py`

**具体步骤**：
1. [ ] `receivable_repo.py` 新增 `update()` 方法：
   ```python
   def update(self, receivable_id, amount=None, due_date=None,
              description=None, expense_type_id=None):
       # UPDATE Receivable SET ... WHERE ReceivableID = ?
       # 仅更新非None字段
   ```
2. [ ] `receivable_service.py` 新增 `update_receivable()` 方法：
   - 查询现有应收记录
   - 校验状态：未付款可编辑全部字段，部分付款仅可编辑到期日期和备注
   - 调用 repo.update()
3. [ ] `finance.py` 新增路由：
   ```python
   @finance_bp.route('/receivable/update/<int:receivable_id>', methods=['POST'])
   @login_required
   def receivable_update(receivable_id):
       data = request.json
       result = receivable_svc.update_receivable(receivable_id, **data)
       return jsonify(result)
   ```

**验收标准**：
- POST `/finance/receivable/update/<id>` 可正常更新未付款应收
- 部分付款状态仅允许修改到期日期和备注
- 已付款状态返回错误提示
- 参数化查询，无SQL注入风险

---

### Task 1.3：实现编辑应收功能 — 前端

**改进项**：P-03
**预估复杂度**：中
**涉及文件**：
- `templates/finance/receivable.html`

**具体步骤**：
1. [ ] 在列表操作列添加"编辑"按钮（`<button class="btn btn-sm btn-warning" onclick="openEditModal(id)">`）
2. [ ] 创建编辑模态窗口（复用新增弹窗结构，修改标题和提交逻辑）
3. [ ] 实现 `openEditModal(receivableId)` 函数：
   - 调用 `/finance/receivable/detail/<id>` 加载数据
   - 填充表单字段
   - 根据状态禁用不可编辑字段
4. [ ] 实现 `submitEdit()` 函数：
   - 收集表单数据
   - POST 到 `/finance/receivable/update/<id>`
   - 成功后刷新列表

**验收标准**：
- 点击编辑按钮弹出模态窗口，数据正确填充
- 未付款状态所有字段可编辑
- 部分付款状态仅到期日期和备注可编辑
- 保存成功后列表自动刷新

---

### Task 1.4：实现删除应收功能 — 后端

**改进项**：P-04
**预估复杂度**：中
**涉及文件**：
- `app/services/receivable_service.py`
- `app/routes/finance.py`

**具体步骤**：
1. [ ] `receivable_service.py` 新增 `delete_receivable()` 方法：
   - 查询应收记录，校验状态
   - 检查是否有关联的 CollectionRecord
   - 删除 ReceivableDetail 关联记录
   - 删除 Receivable 记录
   - 在同一事务内完成
2. [ ] `finance.py` 新增路由：
   ```python
   @finance_bp.route('/receivable/delete/<int:receivable_id>', methods=['POST'])
   @login_required
   def receivable_delete(receivable_id):
       result = receivable_svc.delete_receivable(receivable_id)
       return jsonify(result)
   ```

**验收标准**：
- 仅未付款且无收款记录的应收可删除
- 有收款记录的返回明确错误提示
- 部分付款/已付款状态返回明确错误提示
- 删除时同步清理 ReceivableDetail
- 事务内执行，失败自动回滚

---

### Task 1.5：实现删除应收功能 — 前端

**改进项**：P-04
**预估复杂度**：低
**涉及文件**：
- `templates/finance/receivable.html`

**具体步骤**：
1. [ ] 在列表操作列添加"删除"按钮（`<button class="btn btn-sm btn-danger" onclick="deleteReceivable(id, refType)">`）
2. [ ] 实现 `deleteReceivable(receivableId, referenceType)` 函数：
   - 弹出确认对话框
   - 如果 referenceType 不为空，显示额外提示"该应收由系统自动生成"
   - POST 到 `/finance/receivable/delete/<id>`
   - 成功后刷新列表

**验收标准**：
- 点击删除按钮弹出确认对话框
- 系统自动生成的应收显示额外提示
- 删除成功后列表自动刷新
- 删除失败显示错误提示

---

## 第二阶段：体验优化与健壮性（P2）

### Task 2.1：修复详情路由架构违规

**改进项**：P-02
**预估复杂度**：低
**涉及文件**：
- `app/services/receivable_service.py`
- `app/routes/finance.py`

**具体步骤**：
1. [ ] `receivable_service.py` 新增 `get_receivable_detail()` 方法：
   - 调用 `self.repo.get_by_id()` 获取基本信息
   - 调用 `collection_repo.get_by_receivable_id()` 获取收款历史
   - 组装返回数据
2. [ ] 修改 `finance.py` 的 `receivable_detail` 路由，改用 Service 方法

**验收标准**：
- 路由层不再直接访问 repo
- 详情接口返回数据与修改前一致

---

### Task 2.2：增强列表筛选 — 后端

**改进项**：P-05
**预估复杂度**：中
**涉及文件**：
- `app/repositories/receivable_repo.py`
- `app/services/receivable_service.py`
- `app/routes/finance.py`

**具体步骤**：
1. [ ] `receivable_repo.py` 的 `get_list()` 方法新增参数：
   - `expense_type_id`：费用类型ID筛选
   - `date_from`：到期日期起始
   - `date_to`：到期日期结束
2. [ ] SQL WHERE 条件动态追加对应筛选
3. [ ] `receivable_service.py` 的 `get_receivables()` 透传新参数
4. [ ] `finance.py` 的 `receivable_list()` 从 request.args 提取新参数

**验收标准**：
- 支持按费用类型筛选
- 支持按到期日期范围筛选
- 多个筛选条件可组合使用
- 不传筛选参数时行为与修改前一致

---

### Task 2.3：增强列表筛选 — 前端

**改进项**：P-05
**预估复杂度**：中
**涉及文件**：
- `templates/finance/receivable.html`

**具体步骤**：
1. [ ] 筛选区新增费用类型下拉（页面加载时从 `/finance/receivable/expense_types` 获取）
2. [ ] 新增到期日期范围选择器（两个 date input）
3. [ ] 修改 `loadReceivables()` 函数，携带新筛选参数
4. [ ] 筛选条件变更时自动刷新列表

**验收标准**：
- 费用类型下拉正确显示字典数据
- 日期范围筛选正常工作
- 多个筛选条件可组合使用
- 清空筛选条件后显示全部数据

---

### Task 2.4：实现导出Excel

**改进项**：P-06
**预估复杂度**：中
**涉及文件**：
- `app/routes/finance.py`
- `templates/finance/receivable.html`

**前置条件**：确认 openpyxl 已安装或安装依赖

**具体步骤**：
1. [ ] `finance.py` 新增 `/receivable/export` GET 路由：
   - 接收与 list 相同的筛选参数
   - 查询全量数据（不分页）
   - 使用 openpyxl 生成 Excel
   - 返回文件流
2. [ ] 修改前端导出按钮：
   - 携带当前筛选条件
   - `window.location.href = '/finance/receivable/export?...'`

**验收标准**：
- 点击导出按钮下载 Excel 文件
- Excel 包含所有筛选后的数据
- 表头正确：客户名称、客户类型、费用类型、应收金额、已付金额、剩余金额、到期日期、状态、备注、创建时间
- 文件名包含导出日期

---

### Task 2.5：实现逾期自动检查

**改进项**：P-07
**预估复杂度**：低
**涉及文件**：
- `app/services/finance_service.py`
- `app/routes/finance.py`
- `templates/finance/receivable.html`

**具体步骤**：
1. [ ] `finance_service.py` 新增 `check_and_update_overdue()` 方法：
   ```python
   def check_and_update_overdue(self):
       with DBConnection() as conn:
           cursor = conn.cursor()
           cursor.execute("""
               UPDATE Receivable
               SET Status = N'逾期', UpdateTime = GETDATE()
               WHERE DueDate < GETDATE() AND Status = N'未付款'
           """)
           count = cursor.rowcount
           conn.commit()
           return count
   ```
2. [ ] `finance.py` 新增 `/receivable/overdue_check` POST 路由
3. [ ] 前端列表页添加"逾期检查"按钮，点击调用接口

**验收标准**：
- 点击逾期检查按钮后，过期的未付款应收状态变为"逾期"
- 返回更新的记录数
- 列表自动刷新

---

### Task 2.6：修复MerchantID外键约束问题

**改进项**：P-08
**预估复杂度**：中
**涉及文件**：
- 数据库迁移脚本
- `app/repositories/receivable_repo.py`
- `app/services/finance_service.py`
- 所有查询 MerchantID 的 SQL

**具体步骤**：
1. [ ] 创建迁移脚本：
   ```sql
   ALTER TABLE Receivable ALTER COLUMN MerchantID INT NULL;
   ALTER TABLE CollectionRecord ALTER COLUMN MerchantID INT NULL;
   ```
2. [ ] 修改 `receivable_repo.py` 的 `create()` 方法：CustomerType='Customer' 时 MerchantID 设为 NULL
3. [ ] 修改 `finance_service.py` 的 `collect_receivable()` 方法：处理 MerchantID 为 NULL
4. [ ] 修改所有 LEFT JOIN Merchant 的 SQL，确保兼容 MerchantID=NULL

**验收标准**：
- CustomerType='Customer' 的应收可正常创建（MerchantID=NULL）
- 收款核销兼容 MerchantID=NULL
- 列表查询正确显示客户名称

---

## 任务依赖关系

```
Task 1.1 (清理废弃代码)
  ↓
Task 1.2 (编辑后端) → Task 1.3 (编辑前端)
Task 1.4 (删除后端) → Task 1.5 (删除前端)

Task 2.1 (修复架构违规) — 独立
Task 2.2 (筛选后端) → Task 2.3 (筛选前端)
Task 2.4 (导出Excel) — 独立
Task 2.5 (逾期检查) — 独立
Task 2.6 (外键约束) — 独立
```

---

## 验收检查清单

### 功能验收

- [ ] 应收列表正常加载，分页正确
- [ ] 搜索和状态筛选正常
- [ ] 新增应收（商户/客户双模式）正常
- [ ] 编辑未付款应收正常
- [ ] 编辑部分付款应收（仅日期/备注）正常
- [ ] 已付款应收不可编辑
- [ ] 删除未付款应收正常
- [ ] 有收款记录的应收不可删除
- [ ] 收款核销正常（四步联动）
- [ ] 收款后状态自动更新
- [ ] 费用类型筛选正常
- [ ] 日期范围筛选正常
- [ ] 导出Excel正常
- [ ] 逾期检查正常

### 技术验收

- [ ] 所有 SQL 使用参数化查询
- [ ] 中文使用 N'...' 前缀
- [ ] 收款核销在事务内执行
- [ ] 路由层不直接访问 repo
- [ ] 无废弃代码残留
- [ ] 应用启动无报错
