# 客户名称超链接 + 可复用交易历史弹窗 设计

> **目标：** 在应收/应付页面的客户名称上添加超链接，点击后弹出可复用的模态窗口显示该客户的全维度财务交易记录。

---

## 1. 需求

1. 应收/应付页面的"客户名称"变为可点击超链接
2. 点击后弹出可复用模态窗口，显示该客户的**全维度财务记录**（应收+应付+预收+押金+现金流水）
3. 模态组件必须可复用，两个页面共享，避免代码重复
4. 弹窗支持按类型筛选Tab、分页
5. 支持关闭按钮、点击外部关闭、ESC键关闭

## 2. 技术方案

### 2.1 后端：新增客户交易历史 API

**路由**：`/finance/customer/transactions` (GET)

**参数**：
- `customer_type` — Merchant / Customer
- `customer_id` — 客户ID
- `type` — 可选，筛选类型：receivable/payable/prepayment/deposit/cashflow
- `page` / `per_page` — 分页

**返回**：5类财务记录的合并列表，按时间倒序排列：

```json
{
  "success": true,
  "data": {
    "items": [
      {
        "type": "receivable",
        "type_label": "应收",
        "id": 1,
        "amount": 1000.00,
        "status": "未付款",
        "expense_type_name": "宿舍租金",
        "description": "宿舍租金-A101-2026-04",
        "transaction_date": "2026-04-01",
        "create_time": "2026-04-01 10:00"
      }
    ],
    "total_count": 50,
    "total_pages": 5,
    "current_page": 1,
    "summary": {
      "total_receivable": 5000.00,
      "total_payable": 3000.00,
      "total_prepayment": 1000.00,
      "total_deposit": 2000.00,
      "total_cashflow": 8000.00
    }
  }
}
```

### 2.2 前端：可复用模态组件

**文件**：`static/js/customer-transaction-modal.js`

**接口**：
```javascript
CustomerTransactionModal.init();  // 页面加载时调用一次
CustomerTransactionModal.show(customerType, customerId, customerName);  // 打开弹窗
```

**模态内容**：
- 标题：`{客户名称} - 财务交易记录`
- 汇总卡片：应收总额、应付总额、预收总额、押金总额、净现金流
- 筛选Tab：全部 / 应收 / 应付 / 预收 / 押金 / 现金流水
- 表格列：类型、费用类型、金额、状态、日期
- 分页

### 2.3 页面修改

**receivable.html** 和 **payable.html**：
- 引入 `customer-transaction-modal.js`
- 客户名称渲染为超链接：`<a href="javascript:void(0)" class="customer-tx-link" data-type="Merchant" data-id="1" data-name="客户A">客户A</a>`
- 绑定点击事件调用 `CustomerTransactionModal.show()`

## 3. 文件变更

| 操作 | 文件 | 说明 |
|------|------|------|
| 创建 | `static/js/customer-transaction-modal.js` | 可复用模态组件 |
| 修改 | `app/routes/finance.py` | 新增路由 |
| 修改 | `app/services/finance_service.py` | 新增 get_customer_transactions 方法 |
| 修改 | `templates/finance/receivable.html` | 客户名称超链接 + 引入JS |
| 修改 | `templates/finance/payable.html` | 客户名称超链接 + 引入JS |
