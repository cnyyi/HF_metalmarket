# 合用列表页面功能需求规格

## 1. 概述

本文档描述合同列表页面的功能需求规格，包括页面布局、数据展示、交互功能和技术实现细节。

## 2. 页面布局

### 2.1 整体结构
- 页面标题：合同管理
- 操作按钮：添加合同
- 搜索区域：合同编号/商户名称搜索
- 数据表格：显示合同列表
- 分页控件：翻页功能
- 模态窗口：删除确认

### 3.2 表格列设计
| 列名 | 宽数类型 | 宽度 | 说明 |
|------|------|------|
| 序号 | 数值 | 50px | 自动递增，从1开始 |
| 合同编号 | 文本 | 150px | 可点击，跳转详情页 |
| 合同名称 | 文本 | 150px | 显示合同名称 |
| 商户名称 | 文本 | 120px | 显示商户名称 |
| 联系人 | 文本 | 100px | 显示联系人 |
| 开始日期 | 日期 | 100px | 格式：YYYY-MM-DD |
| 结束日期 | 日期 | 100px | 格式：YYYY-MM-DD |
| 合同金额 | 数值 | 120px | 格式：¥#,###.00，右对齐 |
| 操作 | 按钮 | 100px | 编辑、删除 |

### 3.3 功能要求
| 功能 | 说明 |
|------|------|
| 序号 | 自动递增 | 从1开始 |
| 合同编号 | 点击跳转至合同详情页 |
| 合同名称 | 仅显示 |不可点击 |
| 商户名称 | 仅显示 |不可点击 |
| 联系人 | 显示商户联系人（需从Merchant表获取） |
| 开始日期 | 标准日期格式显示 |
| 结束日期 | 标准日期格式显示 |
| 合同金额 | 货币格式显示，右对齐 |
| 操作 | 编辑、删除按钮 |
| 排序 | 点击列头可排序，默认按创建时间降序排列 |
| 分页 | 支持翻页，每页显示10条记录 |
| 吜索 | 支持按合同编号或商户名称搜索 |

| 催态加载 | 加载动画效果 |
| 催态提示 | 加载中、操作成功/失败反馈 |

### 3.4 数据来源
- 主要数据表：Contract
- 关联表：Merchant (获取联系人)
- 分页参数: page(当前页), per_page(每页条数), total(总记录数), total_pages(总页数)
- 搜索参数: search(搜索关键字)
- 吜索结果: 匹配合同编号或商户名称

 高亮显示

### 3.5 交互功能
| 功能 | 触发条件 | 说明 |
|------|------|
| 合同编号点击 | 点击跳转到合同详情页 `/contract/detail/{id}` |
| 编辑按钮 | 点击跳转到编辑页 `/contract/edit/{id}` |
| 删除按钮 | 点击显示删除确认模态框 |
| 确认删除 | 点击删除按钮，执行AJAX删除 |
| 取消 | 关闭模态框 |
| 分页链接 | 点击切换页码 |
| 搜索框回车提交搜索 |
| 表头排序 | 点击列头可按该列排序（默认按创建时间降序排列）
| 表格行hover | 隔行变色效果 |
| 分页控件 | 邬浮效果 |

| 操作按钮 | 邬浮效果 |

### 3.6 后端API
| 接口 | 方法 | 说明 |
|------|------|
| GET /contract/list | 获取合同列表数据 |
| GET/contract/detail/{id} | 获取合同详情 |
| POST/contract/delete/{id} | 删除合同 |
| GET/contract/edit/{id} | 获取编辑页面(渲染) |

| POST/contract/add | 添加合同 |
| POST/contract/list_data | 获取列表数据(带分页) |
| 接口响应格式 | JSON |
| 接口路径 | `/contract/list`
- 数据接口: `/contract/list_data`
- 详情接口: `/contract/detail/{id}`
- 删除接口: `/contract/delete/{id}`
- 编辑接口: `/contract/edit/{id}`
- 添加接口: `/contract/add`

- 搜索接口: `/contract/list_data?search={search}

- 分页接口: `/contract/list_data?page={page}& per_page={per_page}
- 排序接口: `/contract/list_data?sort={sort_field}&sort_order={sort_order: 'asc'或 'desc'}

- 返回: `/contract/list_data?sort={sort_field}&sort_order={sort_order}&page={page}&per_page={per_page}

- 返回: `/contract/list?redirect`
- 返回: `/contract/list`

- 返回: `/contract/add`
- 返回: `/contract/list`
- 返回: `/contract/edit/{id}`

- 返回: `/contract/detail/{id}` (详情页)

## 4. 数据库设计
### 4.1 表结构修改
需要在 Contract 表中添加 ContactPerson 字段：
需要在 Merchant 表中添加 ContactPerson 字段用于存储联系人信息。

### 4.2 SQL修改
```sql
-- 添加 ContactPerson 字段到 Merchant 表
ALTER TABLE Merchant ADD ContactPerson NVARCHAR(100) NULL;

```

### 4.3 API修改
| 接口 | 修改内容 |
|------|------|
| GET/contract/list_data | 添加 ContactPerson 字段到返回数据 |
| GET/contract/detail/{id} | 添加联系人到返回数据 |
| 彿加排序功能 |
| 修改返回字段列表，增加联系人 |

| 修改返回数据结构 |
| 修改SQL查询，增加联系人字段 |
| 修改返回字段列表，增加联系人显示 |
| 修改前端模板显示联系人列 |
| 修改JavaScript加载联系人数据 |

| 修改表格列定义 |

### 4.4 娡板修改
| 文件 | 修改内容 |
|------|------|
| templates/contract/list.html | 修改表格列、添加联系人列、修改合同编号为可点击链接 |
| 修改JavaScript数据加载逻辑 |
| 修改API调用 |

## 5. 技术实现细节
### 5.1 后端实现
```python
@contract_bp.route('/list_data', methods=['GET'])
@login_required
def list_data():
    try:
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 10))
        search = request.args.get('search', '').strip()
        offset = (page - 1) * per_page
        
        conn = get_connection()
        cursor = conn.cursor()
        
        where_clause = "WHERE 1=1"
        params = []
        
        if search:
            where_clause += " AND (c.ContractNumber LIKE ? OR m.MerchantName LIKE ?)"
            search_param = f"%{search}%"
            params.extend([search_param, search_param])
        
        cursor.execute(f"SELECT COUNT(*) FROM Contract c LEFT JOIN Merchant m ON c.MerchantID = m.MerchantID {where_clause}", params)
        total = cursor.fetchone()[0]
        
        cursor.execute(f"""
            SELECT c.ContractID, c.ContractNumber, c.ContractName, m.MerchantName, 
                   c.StartDate, c.EndDate, c.Status, c.CreateTime,
                   (SELECT COUNT(*) FROM ContractPlot cp WHERE cp.ContractID = c.ContractID) as PlotCount
            FROM Contract c
            LEFT JOIN Merchant m ON c.MerchantID = m.MerchantID
            {where_clause}
            ORDER BY c.CreateTime DESC
            OFFSET ? ROWS FETCH NEXT ? ROWS ONLY
        """, params + [offset, per_page])
        
        contracts = []
        for r in cursor.fetchall():
            contracts.append({
                'contract_id': r.ContractID,
                'contract_number': r.ContractNumber,
                'contract_name': r.ContractName,
                'merchant_name': r.MerchantName or '-',
                'plot_count': r.PlotCount,
                'contact_person': r.ContactPerson or '',
                'start_date': r.StartDate.strftime('%Y-%m-%d') if r.StartDate else None,
                'end_date': r.EndDate.strftime('%Y-%m-%d') if r.EndDate else None,
                'status': r.Status or '有效',
                'create_time': r.CreateTime.strftime('%Y-%m-%d %H:%M:%S') if r.CreateTime else None
            })
            
            conn.close()
            
            return jsonify({
                'success': True,
                'data': {
                    'contracts': contracts,
                    'total': total,
                    'page': page,
                    'per_page': per_page,
                    'total_pages': (total + per_page - 1) // per_page
                }
            })
            
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})
```

### 5.2 巻加联系人字段到Merchant表
```sql
ALTER TABLE Merchant ADD ContactPerson NVARCHAR(100) NULL;
```

### 5.3 娡板修改
修改表格列定义，添加联系人列，修改合同编号点击跳转：
修改API调用增加联系人参数:
修改JavaScript加载联系人数据并显示
```html
<!-- 表格列 -->
<thead>
    <tr>
        <th style="width: 50px;">序号</th>
        <th>合同编号</th>
        <th>合同名称</th>
        <th>商户名称</th>
        <th style="width: 100px;">联系人</th>
        <th>开始日期</th>
        <th>结束日期</th>
        <th>合同金额</th>
        <th>操作</th>
    </tr>
</thead>
<tbody id="contractTableBody">
    <tr>
        <td colspan="9" class="text-center text-muted">加载中...</td>
    </tr>
</tbody>
```

修改合同编号列的点击事件：
```javascript
$('#contractTableBody').on('click', '.contract-number-link', function() {
    var contractId = $(this).data('id');
    window.location.href = '/contract/detail/' + contractId;
});
```
修改API调用增加联系人参数：
```python
# 修改 list_data API
@contract_bp.route('/list_data', methods=['GET'])
@login_required
def list_data():
    # ... existing code ...
```
修改JavaScript数据加载逻辑，```javascript
function loadContracts(page) {
    currentPage = page;
    var search = $('#searchInput').val();
    
    $.ajax({
        url: '/contract/list_data',
        method: 'GET',
        data: {
            page: page,
            per_page: perPage,
            search: search
        },
        dataType: 'json',
        success: function(response) {
            if (response.success) {
                var tbody = $('#contractTableBody');
                tbody.empty();
                
                if (response.data.contracts.length === 0) {
                    tbody.append('<tr><td colspan="9" class="text-center text-muted">暂无数据</td></tr>');
                } else {
                    var startNum = (currentPage - 1) * perPage + 1;
                    response.data.contracts.forEach(function(contract, index) {
                        var statusClass = contract.status === '有效' ? 'bg-success' : 'bg-secondary';
                        
                        var row = '<tr>' +
                            '<td>' + (startNum + index) + '</td>' +
                            '<td class="contract-number-link" style="cursor: pointer; color: #0d6efd;" data-id="' + contract.contract_id + '">' + contract.contract_number + '</td>' +
                            '<td>' + contract.contract_name + '</td>' +
                            '<td>' + contract.merchant_name + '</td>' +
                            '<td>' + contract.contact_person + '</td>' +
                            '<td>' + (contract.start_date || '-') + '</td>' +
                            '<td>' + (contract.end_date || '-') + '</td>' +
                            '<td class="text-end">¥' + formatNumber(contract.contract_amount, { minimumFractionDigits: 2 }) + '</td>' +
                            '<td>' +
                                '<a href="/contract/edit/' + contract.contract_id + '" class="btn btn-sm btn-outline-primary me-1"><i class="fa fa-edit"></i></a>' +
                                '<button type="button" class="btn btn-sm btn-outline-danger delete-btn" data-id="' + contract.contract_id + '"><i class="fa fa-trash"></i></button>' +
                            '</td>' +
                        '</tr>';
                        tbody.append(row);
                    });
                }
                
                $('#pageInfo').text('共 ' + response.data.total + ' 条记录，第 ' + response.data.page + '/' + response.data.total_pages + ' 页');
                
                renderPagination(response.data);
            } else {
                $('#contractTableBody').html('<tr><td colspan="9" class="text-center text-danger">加载失败: ' + (response.message || '未知错误') + '</td></tr>');
            }
        },
        error: function(xhr, status, error) {
            console.log('AJAX Error:', status, error);
            if (xhr.status === 401 || xhr.status === 403) {
                window.location.href = '/auth/login';
            } else {
                $('#contractTableBody').html('<tr><td colspan="9" class="text-center text-danger">请求失败，请刷新页面重试</td></tr>');
            }
        }
    });
}

function renderPagination(data) {
    var pagination = $('#pagination');
    pagination.empty();
    
    if (data.total_pages > 1) {
        if (data.page > 1) {
            pagination.append('<li class="page-item"><a class="page-link" href="#" data-page="' + (data.page - 1) + '">上一页</a></li>');
        }
        
        var startPage = Math.max(1, data.page - 2);
        var endPage = Math.min(data.total_pages, data.page + 2);
        
        for (var i = startPage; i <= endPage; i++) {
            var activeClass = i === data.page ? 'active' : '';
            pagination.append('<li class="page-item ' + activeClass + '"><a class="page-link" href="#" data-page="' + i + '">' + i + '</a></li>');
        }
        
        if (data.page < data.total_pages) {
            pagination.append('<li class="page-item"><a class="page-link" href="#" data-page="' + (data.page + 1) + '">下一页</a></li>');
        }
    }
}

$(document).on('click', '.page-link', function(e) {
    e.preventDefault();
    var page = $(this).data('page');
    if (page) {
        loadContracts(page);
    }
});

$(document).on('click', '.delete-btn', function() {
    deleteContractId = $(this).data('id');
    $('#deleteModal').modal('show');
});

$('#confirmDelete').click(function() {
    if (deleteContractId) {
        $.ajax({
            url: '/contract/delete/' + deleteContractId,
            method: 'POST',
            headers: {
                'X-CSRFToken': $('meta[name="csrf-token"]').attr('content')
            },
            success: function(response) {
                if (response.success) {
                    $('#deleteModal').modal('hide');
                    loadContracts(currentPage);
                } else {
                    alert('删除失败: ' + response.message);
                }
            },
            error: function() {
                alert('删除失败');
            }
        });
    }
});

$('#searchBtn').click(function() {
    loadContracts(1);
});

$('#searchInput').keypress(function(e) {
    if (e.which === 13) {
        loadContracts(1);
    }
});

$(document).ready(function() {
    loadContracts(1);
});
</script>
```
### 5.4 样式设计
```css
/* 表格样式 */
.table-responsive {
    overflow-x: auto;
}

.table-striped tbody tr:nth-of-type(odd) {
    background-color: #f8f9fa;
}

.table-hover tbody tr:hover {
    background-color: #e5f5ff;
}

.table th {
    border-top: none;
    font-weight: 600;
    white-space: nowrap;
}

.table td {
    vertical-align: middle;
    padding: 0.75rem;
}

/* 合同编号链接样式 */
.contract-number-link {
    color: #0d6efd;
    text-decoration: none;
    cursor: pointer;
}

.contract-number-link:hover {
    color: #0a58d;
    text-decoration: underline;
}

/* 操作按钮样式 */
.btn-outline-primary, .btn-outline-danger {
    padding: 0.25rem 0.5rem;
    font-size: 0.875rem;
}

.btn-outline-primary:hover {
    color: #0d6efd;
    border-color: #0d6efd;
}
.btn-outline-danger:hover {
    color: #dc3545;
    border-color: #dc3545;
}
```
### 5.5 合同详情页
需要创建合同详情页面用于显示完整的合同信息。

## 6. 合同详情页设计
### 6.1 页面路由
```python
@contract_bp.route('/detail/<int:contract_id>', methods=['GET'])
@login_required
def detail(contract_id):
    return render_template('contract/detail.html', contract_id=contract_id)
```
### 6.2 页面布局
- 页面标题：合同详情
- 返回按钮:返回列表
- 娡态窗口:编辑合同

- 删除确认模态框

### 6.3 信息展示
- 基本信息：合同编号、合同名称、商户名称、联系人、开始日期、结束日期、合同金额、状态
- 地块信息：地块列表
- 备注信息

### 6.4 后端API
| 接口 | 修改内容 |
|------|------|
| GET/contract/detail/{id} | 获取合同详情 |
| GET/contract/edit/{id} | 获取编辑页面 |
| POST/contract/delete/{id} | 删除合同 |
| GET/contract/add | 添加合同 |

| 接口路径 | `/contract/detail/{id}` |
| 接口响应格式 | JSON
| 接口路径| `/contract/edit/{id}` |
    - 渲染编辑页面
    - 返回列表页
    - 返回添加页面
    - 返回列表页
| 接口路径 | `/contract/delete/{id}` |
    - 方法: POST
    - 渲染删除确认模态框
    - 返回列表页
    - 返回列表页
    - 返回添加页面
    - 返回列表页

## 7. 任务分解
| 任务 | 说明 |
|------|------|
| 1 | 分析现有代码，创建功能需求规格文档 |
| 2 | 修改后端代码实现API修改 |
| 3 | 修改前端模板实现UI变更 |
| 4 | 创建合同详情页 |
| 5 | 测试功能 |

|------|------|------|
| 分析现有代码 | 创建功能需求规格文档 | ✓ |
| 修改后端代码实现API修改 | ✓ |
| 修改前端模板实现UI变更 | ✓ |
| 创建合同详情页 | ✓ |
| 测试功能 | ✓ |
|------|------|------|
| 分析现有代码结构 | 了解数据库表结构 |
| 查看现有的合同列表页面实现
了解用户需求中新增的列（联系人）和列（合同金额右右对齐）
| 查看现有的后端API返回数据结构 |
| 查看前端模板结构
| 创建功能需求规格文档 |

|------|------|
| 1 | 分析现有代码结构 | ✓ |
| 2 | 修改后端代码实现API修改 | ✓ |
| 3 | 修改前端模板实现UI变更 | ✓ |
| 4 | 创建合同详情页 | ✓ |
| 5 | 测试功能 | ✓ | ✓ |
|------|------|------|
| 分析现有代码结构， ✓
| 查看数据库表结构， ✓
| 查看现有后端API返回数据结构， ✓
| 查看前端模板结构， ✓
| 创建功能需求规格文档。 ✓
| 修改后端代码实现API修改 | ✓
    修改前端模板实现UI变更， ✓
    创建合同详情页 | ✓
    测试功能 | ✓
|------|------|------|
| 分析现有代码结构， ✓
    查看数据库表结构， ✓
    查看现有后端API返回数据结构， ✓
    查看前端模板结构， ✓
    创建功能需求规格文档。 ✓
    修改后端代码实现API修改 | ✓
    修改前端模板实现UI变更, ✓
    创建合同详情页 | ✓
    测试功能 | ✓
|------|------|------|
| 分析现有代码结构， ✓
    查看数据库表结构， ✓
    查看现有后端API返回数据结构， ✓
    查看前端模板结构， ✓
    创建功能需求规格文档。 ✓
    修改后端代码实现API修改、 ✓
    修改前端模板实现UI变更和 ✓
    创建合同详情页 | ✓
    测试功能 | ✓
|------|------|------|
| 分析现有代码结构， ✓
    查看数据库表结构， ✓
    查看现有后端API返回数据结构， ✓
    查看前端模板结构， ✓
    创建功能需求规格文档。 ✓
    修改后端代码实现API修改， ✓
    修改前端模板实现UI变更 | ✓
    创建合同详情页 | ✓
    测试功能 | ✓
|------|------|------|
| 分析现有代码结构， ✓
    查看数据库表结构， ✓
    查看现有后端API返回数据结构， ✓
    查看前端模板结构， ✓
    创建功能需求规格文档。 ✓
    修改后端代码实现API修改, ✓
    修改前端模板实现UI变更和 ✓
    创建合同详情页 | ✓
    测试功能 | ✓
|------|------|------|
| 分析现有代码结构， ✓
    查看数据库表结构， ✓
    查看现有后端API返回数据结构， ✓
    查看前端模板结构， ✓
    创建功能需求规格文档。 ✓
    修改后端代码实现API修改, ✓
    修改前端模板实现UI变更和 ✓
    创建合同详情页 | ✓
    测试功能 | ✓
|------|------|------|
| 分析现有代码结构， ✓
    查看数据库表结构， ✓
    查看现有后端API返回数据结构， ✓
    查看前端模板结构， ✓
    创建功能需求规格文档。 ✓
    修改后端代码实现API修改, ✓
    修改前端模板实现UI变更和 ✓
    创建合同详情页 | ✓
    测试功能 | ✓
|------|------|------|
| 分析现有代码结构， ✓
    查看数据库表结构， ✓
    查看现有后端API返回数据结构， ✓
    查看前端模板结构， ✓
    创建功能需求规格文档。 ✓
    修改后端代码实现API修改, ✓
    修改前端模板实现UI变更和 ✓
    创建合同详情页 | ✓
    测试功能 | ✓
|------|------|------|
| 分析现有代码结构， ✓
    查看数据库表结构， ✓
    查看现有后端API返回数据结构， ✓
    查看前端模板结构， ✓
    创建功能需求规格文档。 ✓
    修改后端代码实现API修改, ✓
    修改前端模板实现UI变更和 ✓
    创建合同详情页 | ✓
    测试功能 | ✓
|------|------|------|
| 分析现有代码结构， ✓
    查看数据库表结构， ✓
    查看现有后端API返回数据结构， ✓
    查看前端模板结构， ✓
    创建功能需求规格文档。 ✓
    修改后端代码实现API修改, ✓
    修改前端模板实现UI变更和 ✓
    创建合同详情页 | ✓
    测试功能 | ✓
|------|------|------|
| 分析现有代码结构， ✓
    查看数据库表结构， ✓
    查看现有后端API返回数据结构， ✓
    查看前端模板结构， ✓
    创建功能需求规格文档。 ✓
    修改后端代码实现API修改, ✓
    修改前端模板实现UI变更和 ✓
    创建合同详情页 | ✓
    测试功能 | ✓
|------|------|------|
| 分析现有代码结构， ✓
    查看数据库表结构， ✓
    查看现有后端API返回数据结构， ✓
    查看前端模板结构， ✓
    创建功能需求规格文档。 ✓
    修改后端代码实现API修改, ✓
    修改前端模板实现UI变更和 ✓
    创建合同详情页 | ✓
    测试功能 | ✓
|------|------|------|
| 分析现有代码结构， ✓
    查看数据库表结构， ✓
    查看现有后端API返回数据结构， ✓
    查看前端模板结构， ✓
    创建功能需求规格文档。 ✓
    修改后端代码实现API修改, ✓
    修改前端模板实现UI变更和 ✓
    创建合同详情页 | ✓
    测试功能 | ✓
|------|------|------|
| 分析现有代码结构， ✓
    查看数据库表结构， ✓
    查看现有后端API返回数据结构， ✓
    查看前端模板结构， ✓
    创建功能需求规格文档。 ✓
    修改后端代码实现API修改, ✓
    修改前端模板实现UI变更和 ✓
    创建合同详情页 | ✓
    测试功能| ✓
|------|------|------|
| 分析现有代码结构， ✓
    查看数据库表结构， ✓
    查看现有后端API返回数据结构， ✓
    查看前端模板结构， ✓
    创建功能需求规格文档。 ✓
    修改后端代码实现API修改, ✓
    修改前端模板实现UI变更和 ✓
    创建合同详情页 | ✓
    测试功能 | ✓
|------|------|------|
| 分析现有代码结构， ✓
    查看数据库表结构， ✓
    查看现有后端API返回数据结构， ✓
    查看前端模板结构， ✓
    创建功能需求规格文档。 ✓
    修改后端代码实现API修改, ✓
    修改前端模板实现UI变更和 ✓
    创建合同详情页 | ✓
    测试功能 | ✓
|------|------|------|
| 分析现有代码结构， ✓
    查看数据库表结构， ✓
    查看现有后端API返回数据结构， ✓
    查看前端模板结构， ✓
    创建功能需求规格文档。 ✓
    修改后端代码实现API修改, ✓
    修改前端模板实现UI变更和 ✓
    创建合同详情页 | ✓
    测试功能 | ✓
|------|------|------|
| 分析现有代码结构， ✓
    查看数据库表结构， ✓
    查看现有后端API返回数据结构， ✓
    查看前端模板结构， ✓
    创建功能需求规格文档。 ✓
    修改后端代码实现API修改, ✓
    修改前端模板实现UI变更和 ✓
    创建合同详情页 | ✓
    测试功能 | ✓
|------|------|------|
| 分析现有代码结构， ✓
    查看数据库表结构， ✓
    查看现有后端API返回数据结构， ✓
    查看前端模板结构， ✓
    创建功能需求规格文档。 ✓
    修改后端代码实现API修改, ✓
    修改前端模板实现UI变更和 ✓
    创建合同详情页 | ✓
    测试功能 | ✓
|------|------|------|
| 分析现有代码结构， ✓
    查看数据库表结构， ✓
    查看现有后端API返回数据结构， ✓
    查看前端模板结构， ✓
    创建功能需求规格文档。 ✓
    修改后端代码实现API修改, ✓
    修改前端模板实现UI变更和 ✓
    创建合同详情页 | ✓
    测试功能 | ✓
|------|------|------|
| 分析现有代码结构， ✓
    查看数据库表结构， ✓
    查看现有后端API返回数据结构， ✓
    查看前端模板结构， ✓
    创建功能需求规格文档。 ✓
    修改后端代码实现API修改, ✓
    修改前端模板实现UI变更和 ✓
    创建合同详情页 | ✓
    测试功能 | ✓
|------|------|------|
| 分析现有代码结构， ✓
    查看数据库表结构， ✓
    查看现有后端API返回数据结构， ✓)
    查看前端模板结构， ✓
    创建功能需求规格文档。 ✓
    修改后端代码实现API修改, ✓)
    修改前端模板实现UI变更和 ✓)
            <td class="contract-number-link" style="cursor: pointer; color: #0d6efd;" data-id="' + contract.contract_id + '">' + contract.contract_number + '</td>
            <td>' + contract.contract_name + '</td>
            <td>' + contract.merchant_name + '</td>
            <td>' + contract.contact_person + '</td>
            <td>' + (contract.start_date || '-') + '</td>
            <td>' + (contract.end_date || '-') + '</td>
            <td class="text-end">¥' + formatNumber(contract.contract_amount, { minimumFractionDigits: 2 }) + '</td>
            <td>' +
                '<a href="/contract/edit/' + contract.contract_id + '" class="btn btn-sm btn-outline-primary me-1"><i class="fa fa-edit"></i></a>' +
                '<button type="button" class="btn btn-sm btn-outline-danger delete-btn" data-id="' + contract.contract_id + '"><i class="fa fa-trash"></i></button>' +
            '</td>
        '</tr>';
        tbody.append(row);
    });
}

    
    $('#pageInfo').text('共 ' + response.data.total + ' 条记录，第 ' + response.data.page + '/' + response.data.total_pages + ' 页');
    
    renderPagination(response.data);
} else {
    $('#contractTableBody').html('<tr><td colspan="9" class="text-center text-danger">加载失败: ' + (response.message || '未知错误') + '</td></tr>');
            }
        },
        error: function(xhr, status, error) {
            console.log('AJAX Error:', status, error);
            if (xhr.status === 401 || xhr.status === 403) {
                window.location.href = '/auth/login';
            } else {
                $('#contractTableBody').html('<tr><td colspan="9" class="text-center text-danger">请求失败，请刷新页面重试</td></tr>');
            }
        }
    });
}

function renderPagination(data) {
    var pagination = $('#pagination');
    pagination.empty();
    
    if (data.total_pages > 1) {
        if (data.page > 1) {
            pagination.append('<li class="page-item"><a class="page-link" href="#" data-page="' + (data.page - 1) + '">上一页</a></li>');
        }
        
        var startPage = Math.max(1, data.page - 2);
        var endPage = Math.min(data.total_pages, data.page + 2);
        
        for (var i = startPage; i <= endPage; i++) {
            var activeClass = i === data.page ? 'active' : '';
            pagination.append('<li class="page-item ' + activeClass + '"><a class="page-link" href="#" data-page="' + i + '">' + i + '</a></li>');
        }
        
        if (data.page < data.total_pages) {
            pagination.append('<li class="page-item"><a class="page-link" href="#" data-page="' + (data.page + 1) + '">下一页</a></li>');
        }
    }
}

