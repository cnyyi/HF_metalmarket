# 前端 CSS/JS 封装与控件风格统一 实现计划

> **面向 AI 代理的工作者：** 必需子技能：使用 superpowers:subagent-driven-development（推荐）或 superpowers:executing-plans 逐任务实现此计划。步骤使用复选框（`- [ ]`）语法来跟踪进度。

**目标：** 将后台管理页面中重复的 CSS 暗色模式样式和公共组件样式提取到 admin.css，将重复的 JS 逻辑封装为 admin.js 工具函数，并统一同类控件的风格。

**架构：** 渐进式提取——先在 admin.css/admin.js 中新增统一样式和函数，再逐页面清理重复代码并替换为公共版本，最后统一控件风格。每批完成后浏览器验证。

**技术栈：** Bootstrap 5 + jQuery + 自定义 CSS 变量系统

---

## 文件结构

| 文件 | 操作 | 职责 |
|------|------|------|
| `app/static/css/admin.css` | 修改 | 新增暗色模式覆盖 + 公共组件样式 |
| `app/static/js/admin.js` | 修改 | 新增工具函数（renderPagination, bindSearch, confirmDelete, ajaxPost, ajaxGet, statusBadge, tableLoadingHtml, tableEmptyHtml, tableErrorHtml） |
| `templates/finance/payable.html` | 修改 | 删除重复暗色模式样式 + 删除重复组件样式 + 替换类名 + 加 filter-form |
| `templates/finance/receivable.html` | 修改 | 删除重复组件样式 + 加 filter-form + 合计行改 class |
| `templates/finance/cash_flow.html` | 修改 | 删除重复组件样式 + 加 filter-form |
| `templates/garbage/list.html` | 修改 | 删除重复暗色模式样式 + 删除重复组件样式 + 合计行改 class |
| `templates/garbage/detail.html` | 修改 | 删除重复暗色模式样式 |
| `templates/garbage/add.html` | 修改 | 删除重复暗色模式样式 |
| `templates/garbage/edit.html` | 修改 | 删除重复暗色模式样式 |
| `templates/contract/list.html` | 修改 | 删除重复组件样式 + 替换类名 + 操作按钮统一 |
| `templates/merchant/list.html` | 修改 | 搜索栏改结构 + 操作按钮统一 |
| `templates/plot/list.html` | 修改 | 删除重复组件样式 + 操作按钮统一 |
| `templates/expense/list.html` | 修改 | 合计行改 class |
| `templates/utility/reading_data.html` | 修改 | 模态框头部改样式 |
| `templates/admin/index.html` | 修改 | 删除重复组件样式（summary-card 等） |

---

## 第一批：CSS 暗色模式统一 + 公共组件样式提取

### 任务 1：admin.css 新增暗色模式覆盖样式

**文件：**
- 修改：`app/static/css/admin.css`（在文件末尾 `面包屑` 区块之前，约第 1310 行附近插入）

- [ ] **步骤 1：在 admin.css 的暗色模式区块末尾（Nav Tabs 暗色区块之后）追加以下样式**

在 `/* ========== Nav Tabs 暗色 ========== */` 区块之后、`/* ========== 面包屑 — 保持兼容但样式更新 ========== */` 之前插入：

```css
/* ========== Bootstrap Badge 暗色模式 ========== */
[data-theme="dark"] .badge.bg-warning { background-color: rgba(251,191,36,0.18)!important; color: #FBBF24!important; }
[data-theme="dark"] .badge.bg-success { background-color: rgba(52,211,153,0.18)!important; color: #34D399!important; }
[data-theme="dark"] .badge.bg-info { background-color: rgba(96,165,250,0.18)!important; color: #60A5FA!important; }
[data-theme="dark"] .badge.bg-primary { background-color: rgba(129,140,248,0.18)!important; color: #818CF8!important; }
[data-theme="dark"] .badge.bg-secondary { background-color: rgba(156,163,175,0.18)!important; color: #9CA3AF!important; }
[data-theme="dark"] .badge.bg-danger { background-color: rgba(248,113,113,0.18)!important; color: #F87171!important; }

/* ========== Bootstrap Button Outline 暗色模式 ========== */
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

/* ========== Bootstrap Button Solid 暗色模式 ========== */
[data-theme="dark"] .btn-success { background-color: rgba(52,211,153,0.18); border-color: #34D399; color: #34D399; }
[data-theme="dark"] .btn-success:hover { background-color: rgba(52,211,153,0.28); color: #34D399; }
[data-theme="dark"] .btn-warning { background-color: rgba(251,191,36,0.18); border-color: #FBBF24; color: #1A1F2E; }

/* ========== Bootstrap Alert 暗色模式 ========== */
[data-theme="dark"] .alert-info { background-color: rgba(96,165,250,0.1); border-color: rgba(96,165,250,0.2); color: var(--color-info); }
[data-theme="dark"] .alert-info a { color: var(--color-info); }
[data-theme="dark"] .alert-warning { background-color: rgba(251,191,36,0.1); border-color: rgba(251,191,36,0.2); color: var(--color-warning); }
[data-theme="dark"] .alert-danger { background-color: rgba(248,113,113,0.1); border-color: rgba(248,113,113,0.2); color: var(--color-danger); }
[data-theme="dark"] .alert-success { background-color: rgba(52,211,153,0.1); border-color: rgba(52,211,153,0.2); color: var(--color-success); }

/* ========== 其他 Bootstrap 暗色模式补丁 ========== */
[data-theme="dark"] .text-muted { color: var(--color-text-muted)!important; }
[data-theme="dark"] .text-primary { color: var(--color-primary)!important; }
[data-theme="dark"] .bg-light { background-color: var(--color-bg-light)!important; }
[data-theme="dark"] .table-light { background-color: var(--color-bg-light)!important; color: var(--color-text); }
```

- [ ] **步骤 2：浏览器验证**

打开以下页面，切换亮色/暗色模式，确认 badge、btn-outline、alert、text-muted 等组件在暗色模式下显示正常：
- `/finance/payable` — 验证 badge 和 btn-outline
- `/garbage/` — 验证 badge 和 btn-outline
- `/garbage/add` — 验证 alert-info

- [ ] **步骤 3：Commit**

```bash
git add app/static/css/admin.css
git commit -m "feat(css): 新增 Bootstrap 组件暗色模式覆盖样式到 admin.css"
```

---

### 任务 2：admin.css 新增公共组件样式

**文件：**
- 修改：`app/static/css/admin.css`（在任务 1 新增的暗色模式覆盖之后、面包屑区块之前插入）

- [ ] **步骤 1：在 admin.css 中追加公共组件样式**

在任务 1 新增的暗色模式补丁之后、`/* ========== 面包屑 — 保持兼容但样式更新 ========== */` 之前插入：

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

/* ========== 公共组件：状态徽章 ========== */
.status-badge {
    font-size: var(--badge-font-size);
    padding: var(--badge-padding);
    border-radius: var(--badge-radius);
    display: inline-block;
}
.status-badge.status-unpaid { background-color: rgba(248,113,113,0.15); color: var(--color-danger); }
.status-badge.status-partial { background-color: rgba(251,191,36,0.15); color: var(--color-warning); }
.status-badge.status-paid { background-color: rgba(52,211,153,0.15); color: var(--color-success); }
.status-badge.status-overdue { background-color: rgba(239,68,68,0.15); color: #EF4444; }
.status-badge.status-active { background-color: rgba(52,211,153,0.15); color: var(--color-success); }
.status-badge.status-inactive { background-color: rgba(156,163,175,0.15); color: var(--color-secondary); }
```

- [ ] **步骤 2：浏览器验证**

打开 `/finance/payable` 和 `/finance/cash_flow`，确认详情区、汇总行、Tab 等组件样式正常。

- [ ] **步骤 3：Commit**

```bash
git add app/static/css/admin.css
git commit -m "feat(css): 新增公共组件样式到 admin.css（详情区/汇总行/排序/筛选/卡片/链接/Tab/状态徽章）"
```

---

### 任务 3：清理 finance/payable.html 重复样式

**文件：**
- 修改：`templates/finance/payable.html`

- [ ] **步骤 1：删除 payable.html 中重复的暗色模式覆盖样式**

删除 `{% block extra_css %}` 内以下行（约第 53-103 行）：

```css
[data-theme="dark"] .badge.bg-info { ... }
[data-theme="dark"] .badge.bg-primary { ... }
[data-theme="dark"] .badge.bg-warning { ... }
[data-theme="dark"] .badge.bg-success { ... }
[data-theme="dark"] .btn-outline-warning { ... }
[data-theme="dark"] .btn-outline-warning:hover { ... }
[data-theme="dark"] .btn-outline-info { ... }
[data-theme="dark"] .btn-outline-info:hover { ... }
[data-theme="dark"] .alert-warning { ... }
[data-theme="dark"] .alert-info { ... }
[data-theme="dark"] .btn-outline-danger { ... }
[data-theme="dark"] .btn-outline-danger:hover { ... }
[data-theme="dark"] #deleteInfo { ... }
```

- [ ] **步骤 2：删除 payable.html 中重复的公共组件样式**

删除 `{% block extra_css %}` 内以下样式（这些已移入 admin.css）：
- `detail-section` / `detail-field` 样式
- `summary-amount-cell` / `amount-unpaid` / `amount-paid` / `amount-total` 样式
- `customer-row` 样式
- `payable-tabs` 样式

- [ ] **步骤 3：替换类名**

在 payable.html 的 HTML 和 JS 中：
- `payable-tabs` → `enhanced-tabs`
- 筛选区域外层加 `.filter-form` 包裹

- [ ] **步骤 4：浏览器验证**

打开 `/finance/payable`，切换亮色/暗色模式，确认：
- badge 颜色正常
- btn-outline 颜色正常
- alert 颜色正常
- 详情区样式正常
- Tab 样式正常
- 筛选区域有背景框

- [ ] **步骤 5：Commit**

```bash
git add templates/finance/payable.html
git commit -m "refactor(payable): 删除重复样式，替换为 admin.css 公共组件"
```

---

### 任务 4：清理 garbage/ 页面重复样式

**文件：**
- 修改：`templates/garbage/list.html`
- 修改：`templates/garbage/detail.html`
- 修改：`templates/garbage/add.html`
- 修改：`templates/garbage/edit.html`

- [ ] **步骤 1：清理 garbage/list.html**

删除 `{% block extra_css %}` 内以下重复样式（约第 31-88 行）：
```css
[data-theme="dark"] .summary-row td { ... }
[data-theme="dark"] .badge.bg-warning { ... }
[data-theme="dark"] .badge.bg-success { ... }
[data-theme="dark"] .badge.bg-secondary { ... }
[data-theme="dark"] .btn-outline-info { ... }
[data-theme="dark"] .btn-outline-info:hover { ... }
[data-theme="dark"] .btn-outline-primary { ... }
[data-theme="dark"] .btn-outline-primary:hover { ... }
[data-theme="dark"] .btn-outline-danger { ... }
[data-theme="dark"] .btn-outline-danger:hover { ... }
[data-theme="dark"] .btn-success { ... }
[data-theme="dark"] .btn-success:hover { ... }
[data-theme="dark"] .text-muted { ... }
[data-theme="dark"] .alert-info { ... }
[data-theme="dark"] .alert-info a { ... }
```

同时删除重复的公共组件样式：
- `summary-row` 样式（已移入 admin.css 的 `.summary-row td`）
- `filter-form` 样式（已移入 admin.css）

- [ ] **步骤 2：清理 garbage/detail.html**

删除 `{% block extra_css %}` 内以下重复样式（约第 31-49 行）：
```css
[data-theme="dark"] .status-badge.bg-warning { ... }
[data-theme="dark"] .status-badge.bg-success { ... }
[data-theme="dark"] .status-badge.bg-secondary { ... }
[data-theme="dark"] .detail-value.text-primary { ... }
[data-theme="dark"] .text-primary { ... }
[data-theme="dark"] .text-muted { ... }
```

同时删除重复的 `.status-badge` 样式（已移入 admin.css）。

- [ ] **步骤 3：清理 garbage/add.html**

删除 `{% block extra_css %}` 内以下重复样式（约第 25-30 行）：
```css
[data-theme="dark"] .alert-info { ... }
[data-theme="dark"] .alert-info a { ... }
```

- [ ] **步骤 4：清理 garbage/edit.html**

删除 `{% block extra_css %}` 内以下重复样式（约第 21 行）：
```css
[data-theme="dark"] .text-muted { ... }
```

- [ ] **步骤 5：浏览器验证**

打开 `/garbage/`、`/garbage/detail/1`、`/garbage/add`、`/garbage/edit/1`，切换亮色/暗色模式，确认样式正常。

- [ ] **步骤 6：Commit**

```bash
git add templates/garbage/list.html templates/garbage/detail.html templates/garbage/add.html templates/garbage/edit.html
git commit -m "refactor(garbage): 删除重复暗色模式样式和公共组件样式"
```

---

### 任务 5：清理 finance/receivable.html 重复样式

**文件：**
- 修改：`templates/finance/receivable.html`

- [ ] **步骤 1：删除 receivable.html 中重复的组件样式**

删除 `{% block extra_css %}` 内以下样式：
```css
[data-theme="dark"] .table-summary-row { ... }
```
以及 `table-summary-row` 的亮色样式定义（已移入 admin.css）。

- [ ] **步骤 2：浏览器验证**

打开 `/finance/receivable`，确认合计行样式正常。

- [ ] **步骤 3：Commit**

```bash
git add templates/finance/receivable.html
git commit -m "refactor(receivable): 删除重复汇总行样式"
```

---

### 任务 6：清理 finance/cash_flow.html 重复样式

**文件：**
- 修改：`templates/finance/cash_flow.html`

- [ ] **步骤 1：删除 cash_flow.html 中重复的组件样式**

删除 `{% block extra_css %}` 内以下样式（已移入 admin.css）：
- `detail-section` / `detail-field` 样式
- `summary-link` 样式
- `direction-income` / `direction-expense` 样式

- [ ] **步骤 2：浏览器验证**

打开 `/finance/cash_flow`，确认详情区和方向标签样式正常。

- [ ] **步骤 3：Commit**

```bash
git add templates/finance/cash_flow.html
git commit -m "refactor(cash_flow): 删除重复组件样式"
```

---

### 任务 7：清理 contract/list.html 和 plot/list.html 重复样式

**文件：**
- 修改：`templates/contract/list.html`
- 修改：`templates/plot/list.html`

- [ ] **步骤 1：清理 contract/list.html**

删除 `{% block extra_css %}` 内 `contract-number-link` 样式（已移入 admin.css 为 `detail-link`）。

在 HTML 和 JS 中将 `contract-number-link` 类名替换为 `detail-link`。

- [ ] **步骤 2：清理 plot/list.html**

删除 `{% block extra_css %}` 内 `sortable` 样式（已移入 admin.css）。

- [ ] **步骤 3：浏览器验证**

打开 `/contract/` 和 `/plot/`，确认链接和排序表头样式正常。

- [ ] **步骤 4：Commit**

```bash
git add templates/contract/list.html templates/plot/list.html
git commit -m "refactor(contract,plot): 删除重复组件样式，替换类名"
```

---

### 任务 8：清理 admin/index.html 重复样式

**文件：**
- 修改：`templates/admin/index.html`

- [ ] **步骤 1：检查 admin/index.html 中是否有可提取的公共组件样式**

admin/index.html 的样式主要是仪表盘专属的（kpi-card、pie-card、panel-card 等），这些样式高度页面特定，不应提取到 admin.css。但需检查是否有 `summary-card`/`summary-amount`/`summary-label` 等重复样式。

根据 grep 结果，admin/index.html 中没有 `summary-card`/`summary-amount`/`summary-label`，因此此页面无需修改。

- [ ] **步骤 2：确认无需修改，跳过此任务**

---

## 第二批：JS 工具函数封装

### 任务 9：admin.js 新增工具函数

**文件：**
- 修改：`app/static/js/admin.js`（在文件末尾追加）

- [ ] **步骤 1：在 admin.js 末尾追加以下工具函数**

```javascript
/**
 * 统一分页 HTML 生成器
 * @param {string} container - 分页容器选择器（如 '#pagination'）
 * @param {object} data - { current_page, total_pages, total }
 * @param {function} onPageClick - function(pageNumber) 点击页码回调
 */
function renderPagination(container, data, onPageClick) {
    var el = $(container);
    if (!el.length) return;
    el.empty();

    var totalPages = data.total_pages;
    var curPage = data.current_page;

    if (totalPages <= 1) {
        el.closest('#paginationArea').hide();
        return;
    }
    el.closest('#paginationArea').show();

    var html = '';
    html += '<li class="page-item ' + (curPage === 1 ? 'disabled' : '') + '">';
    html += '<a class="page-link" href="#" data-page="' + (curPage - 1) + '">上一页</a></li>';

    var startPage = Math.max(1, curPage - 2);
    var endPage = Math.min(totalPages, curPage + 2);

    if (startPage > 1) {
        html += '<li class="page-item"><a class="page-link" href="#" data-page="1">1</a></li>';
        if (startPage > 2) {
            html += '<li class="page-item disabled"><span class="page-link">...</span></li>';
        }
    }

    for (var i = startPage; i <= endPage; i++) {
        html += '<li class="page-item ' + (i === curPage ? 'active' : '') + '">';
        html += '<a class="page-link" href="#" data-page="' + i + '">' + i + '</a></li>';
    }

    if (endPage < totalPages) {
        if (endPage < totalPages - 1) {
            html += '<li class="page-item disabled"><span class="page-link">...</span></li>';
        }
        html += '<li class="page-item"><a class="page-link" href="#" data-page="' + totalPages + '">' + totalPages + '</a></li>';
    }

    html += '<li class="page-item ' + (curPage === totalPages ? 'disabled' : '') + '">';
    html += '<a class="page-link" href="#" data-page="' + (curPage + 1) + '">下一页</a></li>';

    el.html(html);

    el.off('click', '.page-link').on('click', '.page-link', function(e) {
        e.preventDefault();
        var page = $(this).data('page');
        if (page && !$(this).closest('.page-item').hasClass('disabled')) {
            if (typeof onPageClick === 'function') onPageClick(page);
        }
    });
}

/**
 * 统一搜索绑定（按钮点击 + 回车触发）
 * @param {string} inputId - 搜索输入框 ID
 * @param {string} btnId - 搜索按钮 ID
 * @param {function} callback - function() 搜索时调用
 */
function bindSearch(inputId, btnId, callback) {
    var input = $('#' + inputId);
    var btn = $('#' + btnId);

    btn.off('click').on('click', function() {
        if (typeof callback === 'function') callback();
    });

    input.off('keypress.search').on('keypress.search', function(e) {
        if (e.which === 13) {
            e.preventDefault();
            if (typeof callback === 'function') callback();
        }
    });
}

/**
 * 统一删除确认流程
 * @param {object} options
 * @param {string} options.url - 删除接口 URL
 * @param {string|number} options.id - 要删除的记录 ID
 * @param {string} [options.modalId='deleteModal'] - 确认模态框 ID
 * @param {function} [options.onSuccess] - 删除成功回调
 * @param {string} [options.message='删除成功'] - 成功提示消息
 */
function confirmDelete(options) {
    var modalId = options.modalId || 'deleteModal';
    var deleteId = options.id;
    var deleteUrl = options.url;
    var successMsg = options.message || '删除成功';

    $('#' + modalId).modal('show');
    $('#' + modalId + 'Confirm').off('click').on('click', function() {
        ajaxPost(deleteUrl, { id: deleteId }, function(resp) {
            $('#' + modalId).modal('hide');
            showToast('success', successMsg);
            if (typeof options.onSuccess === 'function') options.onSuccess(resp);
        });
    });
}

/**
 * AJAX POST 封装（自动携带 CSRF Token）
 * @param {string} url - 请求 URL
 * @param {object} data - 请求数据
 * @param {function} onSuccess - function(resp) 成功回调
 * @param {function} [onError] - function(xhr) 失败回调
 */
function ajaxPost(url, data, onSuccess, onError) {
    $.ajax({
        url: url,
        type: 'POST',
        data: data,
        headers: { 'X-CSRFToken': getCSRFToken() },
        success: function(resp) {
            if (typeof onSuccess === 'function') onSuccess(resp);
        },
        error: function(xhr) {
            if (typeof onError === 'function') {
                onError(xhr);
            } else {
                var msg = '操作失败';
                if (xhr.responseJSON && xhr.responseJSON.message) {
                    msg = xhr.responseJSON.message;
                }
                showToast('error', msg);
            }
        }
    });
}

/**
 * AJAX GET 封装
 * @param {string} url - 请求 URL
 * @param {object} params - 查询参数
 * @param {function} onSuccess - function(resp) 成功回调
 * @param {function} [onError] - function(xhr) 失败回调
 */
function ajaxGet(url, params, onSuccess, onError) {
    $.ajax({
        url: url,
        type: 'GET',
        data: params,
        success: function(resp) {
            if (typeof onSuccess === 'function') onSuccess(resp);
        },
        error: function(xhr) {
            if (typeof onError === 'function') {
                onError(xhr);
            } else {
                showToast('error', '请求失败，请刷新页面重试');
            }
        }
    });
}

/**
 * 统一状态徽章 HTML 生成
 * @param {string} status - 状态文本
 * @returns {string} HTML 字符串
 */
function statusBadge(status) {
    var statusMap = {
        '未付款': 'status-unpaid',
        '未缴费': 'status-unpaid',
        '部分付款': 'status-partial',
        '部分缴费': 'status-partial',
        '已付款': 'status-paid',
        '已缴费': 'status-paid',
        '逾期': 'status-overdue',
        '有效': 'status-active',
        '正常': 'status-active',
        '活跃': 'status-active',
        '无效': 'status-inactive',
        '停用': 'status-inactive'
    };
    var cls = statusMap[status] || 'status-inactive';
    return '<span class="status-badge ' + cls + '">' + escapeHtml(status) + '</span>';
}

/**
 * 表格加载中占位 HTML
 * @param {number} colspan - 列数
 * @returns {string} HTML 字符串
 */
function tableLoadingHtml(colspan) {
    return '<tr><td colspan="' + colspan + '" class="text-center py-4"><i class="fa fa-spinner fa-spin fa-2x text-muted"></i><p class="mt-2 text-muted">加载中...</p></td></tr>';
}

/**
 * 表格空数据占位 HTML
 * @param {number} colspan - 列数
 * @param {string} [message='暂无数据'] - 提示消息
 * @returns {string} HTML 字符串
 */
function tableEmptyHtml(colspan, message) {
    message = message || '暂无数据';
    return '<tr><td colspan="' + colspan + '" class="text-center py-4 text-muted"><i class="fa fa-inbox fa-2x mb-2"></i><p>' + escapeHtml(message) + '</p></td></tr>';
}

/**
 * 表格错误占位 HTML
 * @param {number} colspan - 列数
 * @param {string} [message='加载失败'] - 提示消息
 * @returns {string} HTML 字符串
 */
function tableErrorHtml(colspan, message) {
    message = message || '加载失败';
    return '<tr><td colspan="' + colspan + '" class="text-center py-4 text-danger"><i class="fa fa-exclamation-circle fa-2x mb-2"></i><p>' + escapeHtml(message) + '</p></td></tr>';
}
```

- [ ] **步骤 2：浏览器验证**

打开任意后台页面，按 F12 打开控制台，输入 `typeof renderPagination` 确认返回 `'function'`，确认工具函数已全局可用。

- [ ] **步骤 3：Commit**

```bash
git add app/static/js/admin.js
git commit -m "feat(js): 新增工具函数到 admin.js（分页/搜索/删除/AJAX/状态徽章/表格占位）"
```

---

### 任务 10：重构 finance/receivable.html JS

**文件：**
- 修改：`templates/finance/receivable.html`

- [ ] **步骤 1：替换 receivable.html 中的 renderPagination 函数**

将页面内自定义的 `renderPagination(data)` 函数（约第 481-501 行）替换为调用 admin.js 的公共函数：

```javascript
// 删除整个 renderPagination 函数定义
// 改为在 loadData 成功回调中调用：
renderPagination('#paginationList', data, function(page) {
    currentPage = page;
    loadData(currentTab, currentPage);
});
```

同时删除页面内分页点击事件绑定（约第 960 行的 `$(document).on('click', '#paginationList .page-link', ...)`），因为 `renderPagination` 已内置点击处理。

- [ ] **步骤 2：替换搜索逻辑**

将搜索按钮点击 + 回车绑定替换为 `bindSearch`：

```javascript
bindSearch('searchInput', 'searchBtn', function() {
    currentPage = 1;
    loadData(currentTab, currentPage);
});
```

- [ ] **步骤 3：浏览器验证**

打开 `/finance/receivable`，测试分页、搜索、筛选功能正常。

- [ ] **步骤 4：Commit**

```bash
git add templates/finance/receivable.html
git commit -m "refactor(receivable): 使用 admin.js 公共工具函数替换重复 JS 逻辑"
```

---

### 任务 11：重构 contract/list.html JS

**文件：**
- 修改：`templates/contract/list.html`

- [ ] **步骤 1：替换 contract/list.html 中的分页逻辑**

将 `loadContracts` 函数中的分页 HTML 生成代码（约第 300-317 行）替换为：

```javascript
renderPagination('#pagination', response.data, function(page) {
    loadContracts(page);
});
```

同时删除页面内的 `.page-link` 点击事件绑定（约第 325 行），因为 `renderPagination` 已内置。

- [ ] **步骤 2：替换搜索逻辑**

将搜索按钮点击 + 回车绑定替换为 `bindSearch`。

- [ ] **步骤 3：浏览器验证**

打开 `/contract/`，测试分页、搜索功能正常。

- [ ] **步骤 4：Commit**

```bash
git add templates/contract/list.html
git commit -m "refactor(contract): 使用 admin.js 公共工具函数替换重复 JS 逻辑"
```

---

### 任务 12：重构 plot/list.html JS

**文件：**
- 修改：`templates/plot/list.html`

- [ ] **步骤 1：替换 plot/list.html 中的分页逻辑和搜索逻辑**

同任务 10/11 的模式：
- 分页 → `renderPagination`
- 搜索 → `bindSearch`

- [ ] **步骤 2：浏览器验证**

打开 `/plot/`，测试分页、搜索、排序功能正常。

- [ ] **步骤 3：Commit**

```bash
git add templates/plot/list.html
git commit -m "refactor(plot): 使用 admin.js 公共工具函数替换重复 JS 逻辑"
```

---

### 任务 13：重构 garbage/list.html JS

**文件：**
- 修改：`templates/garbage/list.html`

- [ ] **步骤 1：替换 garbage/list.html 中的分页逻辑和搜索逻辑**

同上模式：
- 分页 → `renderPagination`
- 搜索 → `bindSearch`
- 删除确认 → `confirmDelete`

- [ ] **步骤 2：浏览器验证**

打开 `/garbage/`，测试分页、搜索、删除功能正常。

- [ ] **步骤 3：Commit**

```bash
git add templates/garbage/list.html
git commit -m "refactor(garbage): 使用 admin.js 公共工具函数替换重复 JS 逻辑"
```

---

### 任务 14：重构其余列表页 JS

**文件：**
- 修改：`templates/finance/payable.html`
- 修改：`templates/finance/cash_flow.html`
- 修改：`templates/merchant/list.html`
- 修改：`templates/expense/list.html`
- 修改：`templates/dorm/rooms.html`

- [ ] **步骤 1：逐页面替换分页/搜索/删除逻辑**

每个页面按相同模式替换：
- 分页 → `renderPagination`
- 搜索 → `bindSearch`
- 删除确认 → `confirmDelete`
- AJAX POST → `ajaxPost`
- AJAX GET → `ajaxGet`

- [ ] **步骤 2：浏览器验证**

逐页面测试分页、搜索、删除功能正常。

- [ ] **步骤 3：Commit**

```bash
git add templates/finance/payable.html templates/finance/cash_flow.html templates/merchant/list.html templates/expense/list.html templates/dorm/rooms.html
git commit -m "refactor: 使用 admin.js 公共工具函数替换多页面重复 JS 逻辑"
```

---

## 第三批：控件风格统一

### 任务 15：统一 merchant/list.html 控件风格

**文件：**
- 修改：`templates/merchant/list.html`

- [ ] **步骤 1：搜索栏改为 input-group 结构**

将搜索栏从 `<form>` 结构改为 `input-group` 结构：

```html
<div class="input-group" style="max-width: 360px;">
    <input type="text" class="form-control" id="searchInput" placeholder="搜索商户名称...">
    <button class="btn btn-outline-primary" type="button" id="searchBtn">
        <i class="fa fa-search"></i> 搜索
    </button>
</div>
```

- [ ] **步骤 2：操作按钮统一为 btn-sm btn-outline-\***

将列表行内操作按钮统一为 `btn-sm btn-outline-*` 样式。

- [ ] **步骤 3：浏览器验证**

打开 `/merchant/list`，确认搜索栏和操作按钮风格统一。

- [ ] **步骤 4：Commit**

```bash
git add templates/merchant/list.html
git commit -m "style(merchant): 统一搜索栏和操作按钮风格"
```

---

### 任务 16：统一 finance/receivable.html 控件风格

**文件：**
- 修改：`templates/finance/receivable.html`

- [ ] **步骤 1：筛选区域加 .filter-form 包裹**

在筛选区域外层添加 `<div class="filter-form">` 包裹。

- [ ] **步骤 2：合计行统一为 .table-summary-row**

将合计行的 class 从其他变体改为 `table-summary-row`。

- [ ] **步骤 3：浏览器验证**

打开 `/finance/receivable`，确认筛选区域有背景框，合计行样式统一。

- [ ] **步骤 4：Commit**

```bash
git add templates/finance/receivable.html
git commit -m "style(receivable): 统一筛选区域和合计行风格"
```

---

### 任务 17：统一 finance/payable.html 控件风格

**文件：**
- 修改：`templates/finance/payable.html`

- [ ] **步骤 1：筛选区域加 .filter-form 包裹**

在筛选区域外层添加 `<div class="filter-form">` 包裹。

- [ ] **步骤 2：浏览器验证**

打开 `/finance/payable`，确认筛选区域有背景框。

- [ ] **步骤 3：Commit**

```bash
git add templates/finance/payable.html
git commit -m "style(payable): 统一筛选区域风格"
```

---

### 任务 18：统一 finance/cash_flow.html 控件风格

**文件：**
- 修改：`templates/finance/cash_flow.html`

- [ ] **步骤 1：筛选区域加 .filter-form 包裹**

- [ ] **步骤 2：浏览器验证**

- [ ] **步骤 3：Commit**

```bash
git add templates/finance/cash_flow.html
git commit -m "style(cash_flow): 统一筛选区域风格"
```

---

### 任务 19：统一 utility/reading_data.html 模态框头部

**文件：**
- 修改：`templates/utility/reading_data.html`

- [ ] **步骤 1：模态框头部从内联渐变样式改为标准 modal-header**

将模态框头部的内联渐变背景样式移除，改为使用 admin.css 定义的默认 `modal-header` 样式。危险操作模态框使用 `bg-danger text-white`。

- [ ] **步骤 2：浏览器验证**

打开抄表页面，确认模态框头部样式统一。

- [ ] **步骤 3：Commit**

```bash
git add templates/utility/reading_data.html
git commit -m "style(reading_data): 统一模态框头部风格"
```

---

### 任务 20：统一 expense/list.html 和 garbage/list.html 合计行

**文件：**
- 修改：`templates/expense/list.html`
- 修改：`templates/garbage/list.html`

- [ ] **步骤 1：expense/list.html 合计行改 class**

将合计行从 `table-info fw-bold` 改为 `table-summary-row`。

- [ ] **步骤 2：garbage/list.html 合计行改 class**

将合计行从 `summary-row` 改为 `table-summary-row`。

- [ ] **步骤 3：浏览器验证**

打开 `/expense/` 和 `/garbage/`，确认合计行样式统一。

- [ ] **步骤 4：Commit**

```bash
git add templates/expense/list.html templates/garbage/list.html
git commit -m "style(expense,garbage): 统一合计行 class 为 table-summary-row"
```

---

### 任务 21：统一 contract/list.html 和 plot/list.html 操作按钮

**文件：**
- 修改：`templates/contract/list.html`
- 修改：`templates/plot/list.html`

- [ ] **步骤 1：操作按钮统一为 btn-sm btn-outline-\***

将列表行内操作按钮统一为 `btn-sm btn-outline-*` 样式。

- [ ] **步骤 2：浏览器验证**

打开 `/contract/` 和 `/plot/`，确认操作按钮风格统一。

- [ ] **步骤 3：Commit**

```bash
git add templates/contract/list.html templates/plot/list.html
git commit -m "style(contract,plot): 统一操作按钮为 btn-sm btn-outline-*"
```

---

### 任务 22：最终全面验证

- [ ] **步骤 1：逐页面验证亮色/暗色模式**

依次打开以下页面，切换亮色/暗色模式，确认所有样式正常：

| 页面 | 验证重点 |
|------|---------|
| `/admin/` | 仪表盘 KPI 卡片、饼图、面板 |
| `/merchant/list` | 搜索栏 input-group、操作按钮 btn-sm btn-outline |
| `/contract/` | detail-link、操作按钮、分页 |
| `/finance/receivable` | filter-form、table-summary-row、分页、搜索 |
| `/finance/payable` | enhanced-tabs、filter-form、badge、btn-outline |
| `/finance/cash_flow` | filter-form、detail-section、direction 标签 |
| `/garbage/` | badge、btn-outline、table-summary-row、分页 |
| `/garbage/detail` | status-badge |
| `/garbage/add` | alert-info |
| `/garbage/edit` | text-muted |
| `/plot/` | sortable、操作按钮 btn-sm btn-outline |
| `/expense/` | table-summary-row |
| `/utility/reading_data` | modal-header |

- [ ] **步骤 2：确认无 JS 控制台错误**

按 F12 打开控制台，确认无 JS 报错。

- [ ] **步骤 3：最终 Commit（如有修复）**

```bash
git add -A
git commit -m "fix: 修复最终验证中发现的问题"
```
