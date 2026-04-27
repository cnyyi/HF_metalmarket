# 前端页面优化设计：CSS/JS 封装与控件风格统一

日期：2026-04-21
范围：后台管理页面（admin_base.html 继承的页面）
方案：渐进式提取（方案 A）

---

## 1. 背景与问题

当前后台管理页面存在以下前端问题：

### 1.1 CSS 问题

- **暗色模式覆盖样式大量重复**：`finance/payable.html`、`garbage/list.html`、`garbage/detail.html`、`garbage/add.html`、`garbage/edit.html`、`admin/index.html` 等多个页面各自重复定义了几乎相同的 `[data-theme="dark"]` 覆盖样式（badge、btn-outline、alert 等）
- **页面特定 CSS 分散在模板 `<style>` 标签中**：`detail-section`/`detail-field`、`summary-row`/`table-summary-row`、`sortable`、`filter-form`、`summary-card`、`summary-amount-cell` 等样式在多个页面重复出现
- **admin.css 已有设计令牌系统**，但对 Bootstrap 组件的暗色模式覆盖不完整，导致各页面自行补充

### 1.2 JS 问题

- **分页渲染逻辑大量重复**：26 个列表页面中几乎都有相同的分页 HTML 生成代码
- **搜索+回车触发逻辑重复**：每个页面都重复写搜索按钮点击 + Enter 键触发
- **删除确认模态框+AJAX 删除逻辑重复**：每个页面都有类似的删除确认流程
- **AJAX 请求封装缺失**：每个页面都手动写 `$.ajax` + CSRF Token + 错误处理
- **状态徽章渲染逻辑重复**：getStatusClass / getStatusBadge 在多页面重复
- **空状态/加载状态 HTML 重复**：每个页面都写类似的空数据/加载中/错误 HTML

### 1.3 控件风格不一致

- 搜索栏布局不统一（input-group vs form vs 独立 input+button）
- 筛选区域有的有背景框，有的裸放
- 操作按钮大小和样式不统一（btn-outline vs btn 实心，btn-sm vs 默认大小）
- 模态框头部样式不统一（默认 vs bg-success vs 渐变背景 vs bg-danger）
- 表格合计行 class 不统一（table-info vs table-summary-row vs summary-row）
- 状态显示方式不统一（badge vs status-badge vs 纯文字+颜色）

---

## 2. 设计方案

### 2.1 CSS 暗色模式统一

在 `admin.css` 的 `[data-theme="dark"]` 区块中补充完整的 Bootstrap 暗色模式覆盖，形成统一的暗色模式补丁。

**新增样式**：

```css
/* Bootstrap Badge 暗色模式 */
[data-theme="dark"] .badge.bg-warning { background-color: rgba(251,191,36,0.18)!important; color: #FBBF24!important; }
[data-theme="dark"] .badge.bg-success { background-color: rgba(52,211,153,0.18)!important; color: #34D399!important; }
[data-theme="dark"] .badge.bg-info { background-color: rgba(96,165,250,0.18)!important; color: #60A5FA!important; }
[data-theme="dark"] .badge.bg-primary { background-color: rgba(129,140,248,0.18)!important; color: #818CF8!important; }
[data-theme="dark"] .badge.bg-secondary { background-color: rgba(156,163,175,0.18)!important; color: #9CA3AF!important; }
[data-theme="dark"] .badge.bg-danger { background-color: rgba(248,113,113,0.18)!important; color: #F87171!important; }

/* Bootstrap Button Outline 暗色模式 */
[data-theme="dark"] .btn-outline-danger { color: var(--color-danger); border-color: var(--color-danger); }
[data-theme="dark"] .btn-outline-danger:hover { background-color: rgba(248,113,113,0.15); color: var(--color-danger); }
[data-theme="dark"] .btn-outline-info { color: var(--color-info); border-color: var(--color-info); }
[data-theme="dark"] .btn-outline-info:hover { background-color: rgba(96,165,250,0.15); color: var(--color-info); }
[data-theme="dark"] .btn-outline-primary { color: var(--color-primary); border-color: var(--color-primary); }
[data-theme="dark"] .btn-outline-primary:hover { background-color: rgba(129,140,248,0.15); color: var(--color-primary); }
[data-theme="dark"] .btn-outline-warning { color: var(--color-warning); border-color: var(--color-warning); }
[data-theme="dark"] .btn-outline-warning:hover { background-color: rgba(251,191,36,0.15); color: var(--color-warning); }
[data-theme="dark"] .btn-outline-success { color: var(--color-success); border-color: var(--color-success); }
[data-theme="dark"] .btn-outline-success:hover { background-color: rgba(52,211,153,0.15); color: var(--color-success); }

/* Bootstrap Button Solid 暗色模式 */
[data-theme="dark"] .btn-success { background-color: rgba(52,211,153,0.18); border-color: #34D399; color: #34D399; }
[data-theme="dark"] .btn-success:hover { background-color: rgba(52,211,153,0.28); color: #34D399; }
[data-theme="dark"] .btn-warning { background-color: rgba(251,191,36,0.18); border-color: #FBBF24; color: #1A1F2E; }

/* Bootstrap Alert 暗色模式 */
[data-theme="dark"] .alert-info { background-color: rgba(96,165,250,0.1); border-color: rgba(96,165,250,0.2); color: var(--color-info); }
[data-theme="dark"] .alert-warning { background-color: rgba(251,191,36,0.1); border-color: rgba(251,191,36,0.2); color: var(--color-warning); }
[data-theme="dark"] .alert-danger { background-color: rgba(248,113,113,0.1); border-color: rgba(248,113,113,0.2); color: var(--color-danger); }
[data-theme="dark"] .alert-success { background-color: rgba(52,211,153,0.1); border-color: rgba(52,211,153,0.2); color: var(--color-success); }

/* 其他 Bootstrap 暗色模式补丁 */
[data-theme="dark"] .text-muted { color: var(--color-text-muted)!important; }
[data-theme="dark"] .bg-light { background-color: var(--color-bg-light)!important; }
[data-theme="dark"] .table-light { background-color: var(--color-bg-light)!important; color: var(--color-text); }
```

**需删除重复暗色模式样式的页面**：

| 页面 | 删除内容 |
|------|---------|
| `finance/payable.html` | `[data-theme="dark"] .badge.*`、`.btn-outline-*`、`.btn-success`、`.alert-*`、`.btn-outline-danger` |
| `garbage/list.html` | `[data-theme="dark"] .badge.*`、`.btn-outline-*`、`.btn-success`、`.alert-info`、`.text-muted` |
| `garbage/detail.html` | `[data-theme="dark"] .status-badge.bg-warning`、`.bg-success` |
| `garbage/add.html` | 暗色模式覆盖样式 |
| `garbage/edit.html` | 暗色模式覆盖样式 |
| `admin/index.html` | 暗色模式覆盖样式 |

### 2.2 CSS 公共组件样式提取

将多个页面重复的组件样式统一提取到 `admin.css` 中，新增"公共组件"区块。

**新增样式**：

```css
/* ========== 公共组件：详情区 ========== */
.detail-section { margin-bottom: 16px; }
.detail-section h6 { border-bottom: 1px solid var(--color-border); padding-bottom: 6px; margin-bottom: 10px; }
.detail-field { margin-bottom: 6px; }
.detail-field .label { color: var(--color-text-muted); font-size: 13px; }
.detail-field .value { font-weight: 500; }

/* ========== 公共组件：汇总行 ========== */
.table-summary-row,
.summary-row td {
    background: var(--color-bg-card, #f8f9fa);
    border-top: 2px solid var(--color-primary);
    font-size: 0.88rem;
    font-weight: 700;
}
.table-summary-row td,
.summary-row td {
    padding: 12px 8px;
    vertical-align: middle;
    border-bottom: none;
}
[data-theme="dark"] .table-summary-row,
[data-theme="dark"] .summary-row td {
    background: rgba(22, 93, 255, 0.06);
}

/* ========== 公共组件：排序表头 ========== */
.sortable { cursor: pointer; user-select: none; white-space: nowrap; }
.sortable:hover { color: var(--color-primary); }
.sortable .sort-icon { margin-left: 4px; font-size: 0.7em; opacity: 0.4; }
.sortable.asc .sort-icon, .sortable.desc .sort-icon { opacity: 1; color: var(--color-primary); }
.sortable.asc .sort-icon::after { content: ' \25B2'; }
.sortable.desc .sort-icon::after { content: ' \25BC'; }
.sortable:not(.asc):not(.desc) .sort-icon::after { content: ' \25B2'; }

/* ========== 公共组件：筛选表单 ========== */
.filter-form {
    background: var(--color-bg-light);
    border-radius: 8px;
    padding: 16px;
    border: 1px solid var(--color-border);
}

/* ========== 公共组件：汇总卡片 ========== */
.summary-card { border-radius: var(--radius-xl); border: none; overflow: hidden; }
.summary-card .card-body { padding: var(--space-4) var(--space-6); }
.summary-label { font-size: var(--font-size-sm); color: var(--color-text-muted); margin-bottom: var(--space-1); }
.summary-amount { font-size: var(--font-size-2xl); font-weight: 700; font-family: var(--font-mono); }
.summary-income { border-left: 4px solid var(--color-success); }
.summary-expense { border-left: 4px solid var(--color-danger); }
.summary-net { border-left: 4px solid var(--color-primary); }

/* ========== 公共组件：金额高亮 ========== */
.summary-amount-cell {
    font-family: var(--font-mono);
    font-variant-numeric: tabular-nums;
    font-weight: 600;
    letter-spacing: -0.02em;
}
.amount-unpaid { color: var(--color-danger); }
.amount-paid { color: var(--color-success); }
.amount-total { color: var(--color-text); }

/* ========== 公共组件：链接样式 ========== */
.summary-link,
.detail-link {
    color: var(--color-primary);
    text-decoration: none;
    cursor: pointer;
    border-bottom: 1px dashed var(--color-primary);
    transition: all var(--transition-fast);
}
.summary-link:hover,
.detail-link:hover {
    color: var(--color-primary-hover);
    border-bottom-style: solid;
    text-decoration: none;
}

/* ========== 公共组件：方向标签 ========== */
.direction-income { color: var(--color-success); font-weight: 500; }
.direction-expense { color: var(--color-danger); font-weight: 500; }

/* ========== 公共组件：可点击行 ========== */
.customer-row {
    cursor: pointer;
    transition: background-color var(--transition-fast);
}
.customer-row:hover {
    background-color: var(--table-hover-bg) !important;
}

/* ========== 公共组件：Tab 增强 ========== */
.enhanced-tabs .nav-link {
    font-weight: 600;
    font-size: 0.9rem;
    padding: 10px 24px;
    border-radius: var(--radius-lg) var(--radius-lg) 0 0;
    color: var(--color-text-muted);
    transition: all var(--transition-fast);
}
.enhanced-tabs .nav-link:hover {
    color: var(--color-primary);
    background: var(--color-primary-light);
}
.enhanced-tabs .nav-link.active {
    color: var(--color-primary);
    background: var(--color-bg-card);
    border-color: var(--color-border) var(--color-border) var(--color-bg-card);
}
```

**类名统一映射**：

| 旧类名 | 新类名 | 说明 |
|--------|--------|------|
| `contract-number-link` | `detail-link` | 语义更通用 |
| `payable-tabs` | `enhanced-tabs` | 可复用于其他 Tab 场景 |

**需删除重复组件样式的页面**：

| 页面 | 删除内容 |
|------|---------|
| `finance/payable.html` | `detail-section`/`detail-field`、`summary-amount-cell`/`amount-*`、`customer-row`、`payable-tabs` |
| `finance/cash_flow.html` | `detail-section`/`detail-field`、`summary-link`、`direction-income`/`direction-expense` |
| `finance/receivable.html` | `table-summary-row` |
| `garbage/list.html` | `summary-row`、`filter-form`、`badge` 覆盖 |
| `plot/list.html` | `sortable` |
| `contract/list.html` | `contract-number-link` → 改用 `detail-link` |
| `admin/index.html` | `summary-card`/`summary-amount`/`summary-label` |

### 2.3 JS 工具函数封装

在 `admin.js` 中新增以下工具函数：

#### 2.3.1 renderPagination(container, data, onPageClick)

统一的分页 HTML 生成器。

- `container`：分页容器选择器（如 `'#pagination'`）
- `data`：`{ current_page, total_pages, total }`
- `onPageClick`：`function(pageNumber)` 点击页码时的回调

功能：生成包含上一页/下一页/页码/省略号的分页 HTML，自动处理边界情况。

#### 2.3.2 bindSearch(inputId, btnId, callback)

统一绑定搜索按钮点击 + 输入框回车键。

- `inputId`：搜索输入框 ID
- `btnId`：搜索按钮 ID
- `callback`：`function()` 搜索时调用

#### 2.3.3 confirmDelete(options)

统一的删除确认流程。

- `options.url`：删除接口 URL
- `options.id`：要删除的记录 ID
- `options.modalId`：确认模态框 ID（默认 `'deleteModal'`）
- `options.onSuccess`：删除成功回调
- `options.message`：成功提示消息（默认 `'删除成功'`）

自动处理：显示模态框 → 确认按钮点击 → AJAX POST（带 CSRF Token）→ 成功后关闭模态框 + 刷新 + Toast 提示。

#### 2.3.4 ajaxPost(url, data, onSuccess, onError)

AJAX POST 封装，自动携带 CSRF Token。

- `url`：请求 URL
- `data`：请求数据（对象）
- `onSuccess`：`function(resp)` 成功回调
- `onError`：`function(xhr)` 失败回调（可选，默认 Toast 错误提示）

#### 2.3.5 ajaxGet(url, params, onSuccess, onError)

AJAX GET 封装。

- `url`：请求 URL
- `params`：查询参数（对象）
- `onSuccess`：`function(resp)` 成功回调
- `onError`：`function(xhr)` 失败回调（可选，默认 Toast 错误提示）

#### 2.3.6 statusBadge(status)

统一的状态徽章 HTML 生成。

- `status`：状态文本
- 返回：`<span class="status-badge status-xxx">状态文本</span>`

支持的状态映射：

| 状态 | CSS class |
|------|-----------|
| 未付款/未缴费 | `status-unpaid` |
| 部分付款/部分缴费 | `status-partial` |
| 已付款/已缴费 | `status-paid` |
| 逾期 | `status-overdue` |
| 有效/正常/活跃 | `status-active` |
| 无效/停用 | `status-inactive` |

#### 2.3.7 表格状态占位函数

- `tableLoadingHtml(colspan)`：加载中占位
- `tableEmptyHtml(colspan, message)`：空数据占位（message 默认 `'暂无数据'`）
- `tableErrorHtml(colspan, message)`：错误占位（message 默认 `'加载失败'`）

### 2.4 统一同类控件风格

| 控件 | 统一规范 | 说明 |
|------|---------|------|
| 搜索栏 | `input-group` + 搜索图标 + 搜索按钮 | 所有列表页搜索栏统一结构 |
| 筛选区域 | `.filter-form` 包裹 | 统一浅色背景框+圆角+边框 |
| 操作按钮 | `btn-sm btn-outline-*` | 列表行内操作统一用小号描边按钮 |
| 模态框头部 | 使用 admin.css 定义的 `modal-header` 默认样式（主题色背景） | 特殊场景（危险操作）用 `bg-danger text-white` |
| 表格合计行 | `.table-summary-row` | 统一使用 `table-summary-row` class |
| 状态显示 | `statusBadge()` 函数 | 统一使用 JS 函数生成，或使用 `.status-badge .status-*` class |

**具体页面改动**：

| 页面 | 改动内容 |
|------|---------|
| `merchant/list.html` | 搜索栏从 `<form>` 改为 `input-group` 结构；操作按钮统一为 `btn-sm btn-outline-*` |
| `finance/receivable.html` | 筛选区域加 `.filter-form` 包裹；合计行统一为 `.table-summary-row` |
| `finance/payable.html` | `payable-tabs` → `enhanced-tabs`；筛选区域加 `.filter-form` |
| `finance/cash_flow.html` | 筛选区域加 `.filter-form` |
| `contract/list.html` | `contract-number-link` → `detail-link`；操作按钮统一为 `btn-sm btn-outline-*` |
| `utility/reading_data.html` | 模态框头部从内联渐变样式改为标准 `modal-header` |
| `expense/list.html` | 合计行从 `table-info fw-bold` 改为 `.table-summary-row` |
| `garbage/list.html` | 合计行统一为 `.summary-row` → `.table-summary-row` |
| `plot/list.html` | 操作按钮统一为 `btn-sm btn-outline-*` |

---

## 3. 实施策略

采用分批实施，每批完成后验证：

1. **第一批**：CSS 暗色模式统一 + 公共组件样式提取 → 修改 admin.css，清理各页面重复样式
2. **第二批**：JS 工具函数封装 → 在 admin.js 中新增函数，逐页面替换
3. **第三批**：控件风格统一 → 逐页面调整控件结构和 class

每批完成后在浏览器中验证亮色/暗色模式下的显示效果。

---

## 4. 不做的事

- 不引入前端构建工具（Vite/Webpack）
- 不修改微信端页面（wx_base.html 继承的）
- 不修改公共页面（public_base.html 继承的）
- 不改变现有页面功能逻辑
- 不重构页面 HTML 结构（仅调整 class 和样式引用方式）
