# 水电表列表页面重构设计文档

**创建日期：** 2026-04-03
**作者：** AI Assistant
**状态：** 待审核

---

## 一、概述

### 1.1 项目背景

当前水电表列表页面功能较为基础，缺少便捷的查询筛选功能，用户体验有待提升。本次重构旨在优化页面功能，提升用户操作效率，同时保持与现有系统UI风格的一致性。

### 1.2 设计目标

- ✅ 实现实时查询筛选功能（表编号模糊查询 + 表类型筛选）
- ✅ 实现无刷新分页功能（每页20条数据）
- ✅ 完善绑定/解绑功能（根据合同有效期判断）
- ✅ 保持与现有系统UI风格一致
- ✅ 提升用户体验和操作效率

### 1.3 技术栈

- **前端：** jQuery 4.0.0 + Bootstrap 5 + Font Awesome
- **后端：** Flask + pyodbc
- **数据库：** SQL Server
- **交互方式：** AJAX + JSON

---

## 二、需求分析

### 2.1 功能需求

#### 2.1.1 查询功能

| 功能项 | 实现方式 | 触发方式 |
|--------|---------|---------|
| 表编号查询 | 模糊查询（LIKE %keyword%） | 输入后300ms自动触发 |
| 表类型筛选 | 单选按钮组（全部/电表/水表） | 点击立即触发 |

#### 2.1.2 列表展示

| 列名 | 数据来源 | 格式 | 说明 |
|------|---------|------|------|
| 序号 | 自动生成 | 数字 | 根据当前页自动计算 |
| 表编号 | MeterNumber | 文本 | 完整显示 |
| 表类型 | MeterType | Badge | 电表(黄色)/水表(蓝色) |
| 创建时间 | CreateTime | YYYY-MM-DD | 使用CreateTime代替安装时间 |
| 初始表底 | CurrentReading | 数字(2位小数) | 右对齐 |
| 操作 | - | 按钮 | 绑定/解绑 + 修改 |

#### 2.1.3 绑定功能

**显示逻辑：**
- 未绑定：显示"绑定"按钮（绿色）
- 已绑定：显示"解绑"按钮（红色）

**合同有效期判断：**
```
起始日期 ≤ 今天 ≤ 结束日期 + 3个月
```

**绑定流程：**
1. 点击"绑定"按钮
2. 弹出模态框，选择有效合同
3. 确认绑定
4. 更新列表显示

**解绑流程：**
1. 点击"解绑"按钮
2. 弹出确认模态框
3. 确认解绑
4. 更新列表显示

#### 2.1.4 修改功能

**可修改字段：**
- 表编号（必填）
- 表类型（必填）
- 初始表底（可选）

**修改流程：**
1. 点击"修改"按钮
2. 加载水电表详情
3. 弹出编辑模态框
4. 保存修改

#### 2.1.5 分页功能

- **每页显示：** 20条数据
- **分页方式：** 后端分页，AJAX无刷新
- **分页控件：** Bootstrap分页组件
- **显示信息：** 显示 1-20 条，共 X 条

---

## 三、架构设计

### 3.1 页面结构

```
┌─────────────────────────────────────────────────────────┐
│  水电表管理                                    [+ 新增水电表] │
├─────────────────────────────────────────────────────────┤
│  ┌─────────────────────────────────────────────────┐   │
│  │ 查询区域                                          │   │
│  │ [表编号搜索框]  [○全部 ○电表 ○水表]             │   │
│  └─────────────────────────────────────────────────┘   │
│                                                          │
│  ┌─────────────────────────────────────────────────┐   │
│  │ 数据列表                                         │   │
│  │ 序号 | 表编号 | 表类型 | 创建时间 | 初始表底 | 操作 │   │
│  └─────────────────────────────────────────────────┘   │
│                                                          │
│  ┌─────────────────────────────────────────────────┐   │
│  │ 显示 1-20 条，共 45 条        [1][2][3]...      │   │
│  └─────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────┘
```

### 3.2 数据流程

```
用户操作 → JavaScript事件 → AJAX请求 → Flask路由 
    → UtilityService → Database → 返回JSON → 更新DOM
```

### 3.3 文件结构

```
templates/utility/list.html          # 前端页面（重构）
app/routes/utility.py                # 路由层（新增API）
app/services/utility_service.py      # 服务层（新增方法）
app/models/meter.py                  # 模型层（可能需要调整）
```

---

## 四、详细设计

### 4.1 前端设计

#### 4.1.1 查询区域

```html
<div class="row mb-3">
    <!-- 表编号搜索 -->
    <div class="col-md-4">
        <div class="input-group">
            <span class="input-group-text"><i class="fa fa-search"></i></span>
            <input type="text" 
                   class="form-control" 
                   id="searchMeterNumber" 
                   placeholder="输入表编号搜索">
        </div>
    </div>
    
    <!-- 表类型筛选 -->
    <div class="col-md-5">
        <div class="btn-group" role="group">
            <input type="radio" class="btn-check" name="meterType" id="typeAll" value="all" checked>
            <label class="btn btn-outline-primary" for="typeAll">全部</label>
            
            <input type="radio" class="btn-check" name="meterType" id="typeElectricity" value="electricity">
            <label class="btn btn-outline-primary" for="typeElectricity">电表</label>
            
            <input type="radio" class="btn-check" name="meterType" id="typeWater" value="water">
            <label class="btn btn-outline-primary" for="typeWater">水表</label>
        </div>
    </div>
    
    <!-- 新增按钮 -->
    <div class="col-md-3 text-end">
        <button type="button" class="btn btn-primary" data-bs-toggle="modal" data-bs-target="#addMeterModal">
            <i class="fa fa-plus"></i> 新增水电表
        </button>
    </div>
</div>
```

#### 4.1.2 数据表格

```html
<div class="table-responsive">
    <table class="table table-striped table-hover">
        <thead>
            <tr>
                <th style="width: 50px;">序号</th>
                <th style="width: 120px;">表编号</th>
                <th style="width: 80px;">表类型</th>
                <th style="width: 100px;">创建时间</th>
                <th style="width: 100px; text-align: right;">初始表底</th>
                <th style="width: 120px;">操作</th>
            </tr>
        </thead>
        <tbody id="meterTableBody">
            <tr>
                <td colspan="6" class="text-center text-muted">
                    <i class="fa fa-spinner fa-spin"></i> 加载中...
                </td>
            </tr>
        </tbody>
    </table>
</div>
```

#### 4.1.3 分页区域

```html
<div class="row mt-3">
    <div class="col-md-6">
        <div id="pageInfo" class="text-muted"></div>
    </div>
    <div class="col-md-6">
        <nav>
            <ul class="pagination justify-content-end mb-0" id="pagination"></ul>
        </nav>
    </div>
</div>
```

#### 4.1.4 绑定模态框

```html
<div class="modal fade" id="bindModal" tabindex="-1">
    <div class="modal-dialog">
        <div class="modal-content">
            <div class="modal-header bg-success text-white">
                <h5 class="modal-title"><i class="fa fa-link"></i> 绑定合同</h5>
                <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal"></button>
            </div>
            <div class="modal-body">
                <form id="bindForm">
                    <input type="hidden" id="bindMeterId">
                    <input type="hidden" id="bindMeterType">
                    
                    <div class="mb-3">
                        <label class="form-label fw-bold">当前表编号</label>
                        <input type="text" class="form-control" id="bindMeterNumber" readonly>
                    </div>
                    
                    <div class="mb-3">
                        <label class="form-label fw-bold">选择合同 <span class="text-danger">*</span></label>
                        <select class="form-select" id="bindContractId" required>
                            <option value="">-- 请选择合同 --</option>
                        </select>
                        <small class="text-muted">仅显示有效期内的合同</small>
                    </div>
                    
                    <div class="alert alert-info small">
                        <i class="fa fa-info-circle"></i>
                        合同有效期：起始日期 ≤ 今天 ≤ 结束日期+3个月
                    </div>
                </form>
            </div>
            <div class="modal-footer">
                <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">取消</button>
                <button type="button" class="btn btn-success" id="confirmBind">
                    <i class="fa fa-link"></i> 确认绑定
                </button>
            </div>
        </div>
    </div>
</div>
```

#### 4.1.5 解绑确认模态框

```html
<div class="modal fade" id="unbindModal" tabindex="-1">
    <div class="modal-dialog">
        <div class="modal-content">
            <div class="modal-header bg-danger text-white">
                <h5 class="modal-title"><i class="fa fa-unlink"></i> 确认解绑</h5>
                <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal"></button>
            </div>
            <div class="modal-body">
                <input type="hidden" id="unbindMeterId">
                <input type="hidden" id="unbindMeterType">
                
                <div class="text-center py-3">
                    <i class="fa fa-exclamation-triangle text-warning fa-3x mb-3"></i>
                    <p class="mb-2">确定要解除该水电表与合同的绑定关系吗？</p>
                    <p class="text-muted small mb-0">表编号：<strong id="unbindMeterNumber"></strong></p>
                </div>
            </div>
            <div class="modal-footer">
                <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">取消</button>
                <button type="button" class="btn btn-danger" id="confirmUnbind">
                    <i class="fa fa-unlink"></i> 确认解绑
                </button>
            </div>
        </div>
    </div>
</div>
```

#### 4.1.6 修改模态框

```html
<div class="modal fade" id="editModal" tabindex="-1">
    <div class="modal-dialog">
        <div class="modal-content">
            <div class="modal-header bg-primary text-white">
                <h5 class="modal-title"><i class="fa fa-edit"></i> 修改水电表</h5>
                <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal"></button>
            </div>
            <div class="modal-body">
                <form id="editForm">
                    <input type="hidden" id="editMeterId">
                    <input type="hidden" id="editMeterType">
                    
                    <div class="mb-3">
                        <label for="edit_meter_number" class="form-label fw-bold">
                            表编号 <span class="text-danger">*</span>
                        </label>
                        <input type="text" 
                               class="form-control" 
                               id="edit_meter_number" 
                               name="meter_number"
                               required
                               maxlength="50">
                        <div class="invalid-feedback">请输入表编号</div>
                    </div>
                    
                    <div class="mb-3">
                        <label for="edit_meter_type" class="form-label fw-bold">
                            表类型 <span class="text-danger">*</span>
                        </label>
                        <select class="form-select" 
                                id="edit_meter_type" 
                                name="meter_type"
                                required>
                            <option value="water">水表</option>
                            <option value="electricity">电表</option>
                        </select>
                    </div>
                    
                    <div class="mb-3">
                        <label for="edit_current_reading" class="form-label fw-bold">初始表底</label>
                        <input type="number" 
                               class="form-control" 
                               id="edit_current_reading" 
                               name="current_reading"
                               step="0.01"
                               min="0"
                               value="0">
                        <small class="text-muted">默认值为 0</small>
                    </div>
                </form>
            </div>
            <div class="modal-footer">
                <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">取消</button>
                <button type="button" class="btn btn-primary" id="confirmEdit">
                    <i class="fa fa-save"></i> 保存修改
                </button>
            </div>
        </div>
    </div>
</div>
```

### 4.2 JavaScript设计

#### 4.2.1 全局变量

```javascript
// 查询参数
let searchParams = {
    meter_number: '',
    meter_type: 'all',
    page: 1,
    page_size: 20
};

// 分页参数
let currentPage = 1;
let pageSize = 20;
let totalCount = 0;
let totalPages = 0;

// 防抖定时器
let searchTimer = null;
```

#### 4.2.2 核心函数

**表编号搜索（防抖300ms）：**
```javascript
$('#searchMeterNumber').on('input', function() {
    const value = $(this).val().trim();
    
    if (searchTimer) {
        clearTimeout(searchTimer);
    }
    
    searchTimer = setTimeout(function() {
        searchParams.meter_number = value;
        searchParams.page = 1;
        loadMeterList();
    }, 300);
});
```

**表类型筛选（立即触发）：**
```javascript
$('input[name="meterType"]').on('change', function() {
    searchParams.meter_type = $(this).val();
    searchParams.page = 1;
    loadMeterList();
});
```

**加载数据列表：**
```javascript
function loadMeterList() {
    $('#meterTableBody').html(`
        <tr>
            <td colspan="6" class="text-center text-muted">
                <i class="fa fa-spinner fa-spin"></i> 加载中...
            </td>
        </tr>
    `);
    
    $.ajax({
        url: '/utility/list_data',
        method: 'GET',
        data: searchParams,
        success: function(response) {
            if (response.success) {
                totalCount = response.total;
                totalPages = Math.ceil(totalCount / pageSize);
                
                renderTable(response.data);
                renderPagination();
                updatePageInfo();
            } else {
                showError(response.message || '加载数据失败');
            }
        },
        error: function(xhr, status, error) {
            showError('网络错误，请稍后重试');
        }
    });
}
```

**渲染表格行：**
```javascript
function renderTableRow(item, index) {
    const rowNum = (currentPage - 1) * pageSize + index + 1;
    const typeBadge = item.meter_type === 'electricity' 
        ? '<span class="badge bg-warning">电表</span>'
        : '<span class="badge bg-info">水表</span>';
    
    const bindButton = item.is_bound 
        ? `<button class="btn btn-sm btn-outline-danger unbind-btn" data-id="${item.meter_id}" data-type="${item.meter_type}">
               <i class="fa fa-unlink"></i> 解绑
           </button>`
        : `<button class="btn btn-sm btn-outline-success bind-btn" data-id="${item.meter_id}" data-type="${item.meter_type}">
               <i class="fa fa-link"></i> 绑定
           </button>`;
    
    return `
        <tr>
            <td class="text-center">${rowNum}</td>
            <td>${item.meter_number}</td>
            <td class="text-center">${typeBadge}</td>
            <td class="text-center">${item.create_time}</td>
            <td class="text-end">${item.current_reading.toFixed(2)}</td>
            <td class="text-center">
                ${bindButton}
                <button class="btn btn-sm btn-outline-primary edit-btn ms-1" data-id="${item.meter_id}" data-type="${item.meter_type}">
                    <i class="fa fa-edit"></i> 修改
                </button>
            </td>
        </tr>
    `;
}
```

### 4.3 后端API设计

#### 4.3.1 API接口列表

| 接口路径 | 方法 | 功能 | 参数 |
|---------|------|------|------|
| `/utility/list_data` | GET | 获取水电表列表（分页+筛选） | meter_number, meter_type, page, page_size |
| `/utility/valid_contracts` | GET | 获取有效合同列表 | 无 |
| `/utility/bind` | POST | 绑定水电表到合同 | meter_id, meter_type, contract_id |
| `/utility/unbind` | POST | 解绑水电表 | meter_id, meter_type |
| `/utility/detail/<id>` | GET | 获取水电表详情 | meter_type |
| `/utility/edit/<id>` | POST | 修改水电表 | meter_number, meter_type, current_reading |

#### 4.3.2 路由实现示例

**获取水电表列表：**
```python
@utility_bp.route('/list_data')
@login_required
def list_data():
    """
    获取水电表列表（分页+筛选）
    """
    try:
        meter_number = request.args.get('meter_number', '').strip()
        meter_type = request.args.get('meter_type', 'all')
        page = int(request.args.get('page', 1))
        page_size = int(request.args.get('page_size', 20))
        
        result = utility_service.get_meter_list(
            meter_number=meter_number,
            meter_type=meter_type,
            page=page,
            page_size=page_size
        )
        
        return jsonify(result)
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'获取数据失败：{str(e)}'
        }), 500
```

**获取有效合同列表：**
```python
@utility_bp.route('/valid_contracts')
@login_required
def valid_contracts():
    """
    获取有效合同列表
    """
    try:
        result = utility_service.get_valid_contracts()
        return jsonify(result)
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'获取合同列表失败：{str(e)}'
        }), 500
```

**绑定水电表：**
```python
@utility_bp.route('/bind', methods=['POST'])
@login_required
def bind():
    """
    绑定水电表到合同
    """
    try:
        data = request.get_json()
        meter_id = data.get('meter_id')
        meter_type = data.get('meter_type')
        contract_id = data.get('contract_id')
        
        if not all([meter_id, meter_type, contract_id]):
            return jsonify({
                'success': False,
                'message': '缺少必要参数'
            }), 400
        
        result = utility_service.bind_meter_to_contract(
            meter_id=meter_id,
            meter_type=meter_type,
            contract_id=contract_id
        )
        
        return jsonify(result)
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'绑定失败：{str(e)}'
        }), 500
```

**解绑水电表：**
```python
@utility_bp.route('/unbind', methods=['POST'])
@login_required
def unbind():
    """
    解绑水电表
    """
    try:
        data = request.get_json()
        meter_id = data.get('meter_id')
        meter_type = data.get('meter_type')
        
        if not all([meter_id, meter_type]):
            return jsonify({
                'success': False,
                'message': '缺少必要参数'
            }), 400
        
        result = utility_service.unbind_meter_from_contract(
            meter_id=meter_id,
            meter_type=meter_type
        )
        
        return jsonify(result)
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'解绑失败：{str(e)}'
        }), 500
```

### 4.4 服务层设计

#### 4.4.1 获取水电表列表

```python
def get_meter_list(self, meter_number='', meter_type='all', page=1, page_size=20):
    """
    获取水电表列表（分页+筛选）
    
    Args:
        meter_number: 表编号（模糊查询）
        meter_type: 表类型（all/water/electricity）
        page: 页码
        page_size: 每页数量
        
    Returns:
        dict: {success, data, total, page, page_size}
    """
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        # 构建WHERE条件
        where_clauses = []
        params = []
        
        if meter_number:
            where_clauses.append("MeterNumber LIKE ?")
            params.append(f"%{meter_number}%")
        
        if meter_type != 'all':
            where_clauses.append("MeterType = ?")
            params.append(meter_type)
        
        where_sql = " AND ".join(where_clauses) if where_clauses else "1=1"
        
        # 查询总数
        count_sql = f"SELECT COUNT(*) FROM WaterMeter WHERE {where_sql}"
        cursor.execute(count_sql, params)
        total = cursor.fetchone()[0]
        
        # 分页查询
        offset = (page - 1) * page_size
        data_sql = f"""
            SELECT MeterID, MeterNumber, MeterType, CurrentReading, 
                   CreateTime, Status
            FROM WaterMeter
            WHERE {where_sql}
            ORDER BY CreateTime DESC
            OFFSET ? ROWS FETCH NEXT ? ROWS ONLY
        """
        params.extend([offset, page_size])
        
        cursor.execute(data_sql, params)
        rows = cursor.fetchall()
        conn.close()
        
        # 检查绑定状态
        data = []
        for row in rows:
            is_bound = self._check_meter_binding(row.MeterID, 'water')
            data.append({
                'meter_id': row.MeterID,
                'meter_number': row.MeterNumber,
                'meter_type': row.MeterType,
                'current_reading': float(row.CurrentReading) if row.CurrentReading else 0,
                'create_time': row.CreateTime.strftime('%Y-%m-%d') if row.CreateTime else '',
                'status': row.Status,
                'is_bound': is_bound
            })
        
        return {
            'success': True,
            'data': data,
            'total': total,
            'page': page,
            'page_size': page_size
        }
    except Exception as e:
        return {
            'success': False,
            'message': str(e)
        }
```

#### 4.4.2 获取有效合同列表

```python
def get_valid_contracts(self):
    """
    获取有效合同列表
    有效期：起始日期 ≤ 今天 ≤ 结束日期+3个月
    """
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT c.ContractID, c.ContractNumber, m.MerchantName,
                   c.StartDate, c.EndDate
            FROM Contract c
            INNER JOIN Merchant m ON c.MerchantID = m.MerchantID
            WHERE c.StartDate <= GETDATE()
              AND DATEADD(MONTH, 3, c.EndDate) >= GETDATE()
            ORDER BY c.ContractNumber
        """)
        
        rows = cursor.fetchall()
        conn.close()
        
        return {
            'success': True,
            'data': [{
                'contract_id': r.ContractID,
                'contract_number': r.ContractNumber,
                'merchant_name': r.MerchantName,
                'start_date': r.StartDate.strftime('%Y-%m-%d'),
                'end_date': r.EndDate.strftime('%Y-%m-%d')
            } for r in rows]
        }
    except Exception as e:
        return {
            'success': False,
            'message': str(e)
        }
```

#### 4.4.3 检查绑定状态

```python
def _check_meter_binding(self, meter_id, meter_type):
    """
    检查水电表是否已绑定合同
    
    Args:
        meter_id: 水电表ID
        meter_type: 表类型（water/electricity）
        
    Returns:
        bool: 是否已绑定
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    if meter_type == 'water':
        cursor.execute("""
            SELECT COUNT(*) FROM ContractWaterMeter
            WHERE MeterID = ?
        """, (meter_id,))
    else:
        cursor.execute("""
            SELECT COUNT(*) FROM ContractElectricityMeter
            WHERE MeterID = ?
        """, (meter_id,))
    
    count = cursor.fetchone()[0]
    conn.close()
    
    return count > 0
```

#### 4.4.4 绑定水电表

```python
def bind_meter_to_contract(self, meter_id, meter_type, contract_id):
    """
    绑定水电表到合同
    
    Args:
        meter_id: 水电表ID
        meter_type: 表类型（water/electricity）
        contract_id: 合同ID
        
    Returns:
        dict: {success, message}
    """
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        if meter_type == 'water':
            cursor.execute("""
                INSERT INTO ContractWaterMeter (ContractID, MeterID, InitialReading)
                VALUES (?, ?, 
                    (SELECT CurrentReading FROM WaterMeter WHERE MeterID = ?))
            """, (contract_id, meter_id, meter_id))
        else:
            cursor.execute("""
                INSERT INTO ContractElectricityMeter (ContractID, MeterID, InitialReading)
                VALUES (?, ?, 
                    (SELECT CurrentReading FROM ElectricityMeter WHERE MeterID = ?))
            """, (contract_id, meter_id, meter_id))
        
        conn.commit()
        conn.close()
        
        return {
            'success': True,
            'message': '绑定成功'
        }
    except Exception as e:
        return {
            'success': False,
            'message': str(e)
        }
```

#### 4.4.5 解绑水电表

```python
def unbind_meter_from_contract(self, meter_id, meter_type):
    """
    解绑水电表
    
    Args:
        meter_id: 水电表ID
        meter_type: 表类型（water/electricity）
        
    Returns:
        dict: {success, message}
    """
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        if meter_type == 'water':
            cursor.execute("""
                DELETE FROM ContractWaterMeter WHERE MeterID = ?
            """, (meter_id,))
        else:
            cursor.execute("""
                DELETE FROM ContractElectricityMeter WHERE MeterID = ?
            """, (meter_id,))
        
        conn.commit()
        conn.close()
        
        return {
            'success': True,
            'message': '解绑成功'
        }
    except Exception as e:
        return {
            'success': False,
            'message': str(e)
        }
```

---

## 五、数据库设计

### 5.1 现有表结构

本次重构不需要修改数据库表结构，使用现有表：

- **WaterMeter** - 水表信息表
- **ElectricityMeter** - 电表信息表
- **ContractWaterMeter** - 合同-水表关联表
- **ContractElectricityMeter** - 合同-电表关联表
- **Contract** - 合同信息表
- **Merchant** - 商户信息表

### 5.2 字段使用说明

| 字段名 | 表名 | 用途 |
|--------|------|------|
| MeterID | WaterMeter/ElectricityMeter | 主键 |
| MeterNumber | WaterMeter/ElectricityMeter | 表编号（模糊查询） |
| MeterType | WaterMeter/ElectricityMeter | 表类型（筛选） |
| CurrentReading | WaterMeter/ElectricityMeter | 当前读数/初始表底 |
| CreateTime | WaterMeter/ElectricityMeter | 创建时间（代替安装时间） |
| Status | WaterMeter/ElectricityMeter | 状态 |

---

## 六、错误处理

### 6.1 前端错误处理

```javascript
// 显示错误信息
function showError(message) {
    $('#meterTableBody').html(`
        <tr>
            <td colspan="6" class="text-center text-danger py-5">
                <i class="fa fa-exclamation-triangle fa-3x mb-3"></i>
                <p>${message}</p>
                <button class="btn btn-sm btn-outline-primary" onclick="loadMeterList()">
                    <i class="fa fa-refresh"></i> 重试
                </button>
            </td>
        </tr>
    `);
}

// 空数据显示
function showEmpty() {
    $('#meterTableBody').html(`
        <tr>
            <td colspan="6" class="text-center text-muted py-5">
                <i class="fa fa-inbox fa-3x mb-3"></i>
                <p>暂无数据</p>
            </td>
        </tr>
    `);
}
```

### 6.2 后端错误处理

所有API接口统一返回格式：

```python
# 成功响应
{
    'success': True,
    'data': [...],
    'total': 100,
    'page': 1,
    'page_size': 20
}

# 失败响应
{
    'success': False,
    'message': '错误信息'
}
```

---

## 七、性能优化

### 7.1 前端优化

1. **防抖处理** - 表编号搜索使用300ms防抖，减少请求次数
2. **按需加载** - 分页加载，每次只请求20条数据
3. **缓存机制** - 有效合同列表缓存（可选）

### 7.2 后端优化

1. **索引优化** - MeterNumber、MeterType字段建议添加索引
2. **分页查询** - 使用 OFFSET-FETCH 分页，避免全表扫描
3. **连接池** - 使用数据库连接池（已有）

### 7.3 数据库优化建议

```sql
-- 建议添加索引（如果不存在）
CREATE INDEX IX_WaterMeter_MeterNumber ON WaterMeter(MeterNumber);
CREATE INDEX IX_WaterMeter_MeterType ON WaterMeter(MeterType);
CREATE INDEX IX_ElectricityMeter_MeterNumber ON ElectricityMeter(MeterNumber);
CREATE INDEX IX_ElectricityMeter_MeterType ON ElectricityMeter(MeterType);
```

---

## 八、测试计划

### 8.1 功能测试

| 测试项 | 测试内容 | 预期结果 |
|--------|---------|---------|
| 表编号搜索 | 输入表编号关键字 | 显示匹配的记录 |
| 表类型筛选 | 点击单选按钮 | 立即筛选对应类型 |
| 分页功能 | 点击页码 | 无刷新切换页面 |
| 绑定功能 | 点击绑定按钮 | 弹出模态框，可选择有效合同 |
| 解绑功能 | 点击解绑按钮 | 弹出确认框，确认后解绑 |
| 修改功能 | 点击修改按钮 | 弹出编辑框，可修改信息 |

### 8.2 性能测试

| 测试项 | 测试条件 | 预期结果 |
|--------|---------|---------|
| 页面加载 | 首次加载 | < 2秒 |
| 查询响应 | 输入搜索关键字 | < 500ms |
| 分页切换 | 点击页码 | < 500ms |

### 8.3 兼容性测试

- ✅ Chrome 最新版
- ✅ Firefox 最新版
- ✅ Edge 最新版

---

## 九、实施计划

### 9.1 开发任务

| 任务 | 预计时间 | 优先级 |
|------|---------|--------|
| 重构前端页面（list.html） | 2小时 | 高 |
| 实现后端API（utility.py） | 1.5小时 | 高 |
| 实现服务层方法（utility_service.py） | 1.5小时 | 高 |
| 测试功能 | 1小时 | 高 |
| 优化和修复bug | 1小时 | 中 |

**总计：** 约7小时

### 9.2 部署步骤

1. 备份现有文件
2. 部署新代码
3. 重启服务
4. 功能测试
5. 性能监控

---

## 十、风险与应对

### 10.1 潜在风险

| 风险 | 影响 | 应对措施 |
|------|------|---------|
| 数据量大导致查询慢 | 用户体验差 | 添加索引，优化查询 |
| 并发请求过多 | 服务器压力大 | 使用缓存，限制请求频率 |
| 浏览器兼容性问题 | 部分用户无法使用 | 充分测试，提供降级方案 |

### 10.2 回滚方案

如果出现严重问题，可以快速回滚到旧版本：

1. 恢复备份文件
2. 重启服务
3. 验证功能正常

---

## 十一、后续优化

### 11.1 短期优化（1个月内）

- 添加导出功能（Excel）
- 批量操作功能
- 高级筛选（按商户、状态等）

### 11.2 长期优化（3个月内）

- 数据可视化（图表展示）
- 移动端适配
- 性能监控和告警

---

## 十二、附录

### 12.1 参考文档

- Bootstrap 5 文档：https://getbootstrap.com/docs/5.1/
- jQuery 文档：https://api.jquery.com/
- Flask 文档：https://flask.palletsprojects.com/

### 12.2 相关文件

- 现有页面：`templates/utility/list.html`
- 路由文件：`app/routes/utility.py`
- 服务文件：`app/services/utility_service.py`
- 模型文件：`app/models/meter.py`

---

**文档版本：** 1.0
**最后更新：** 2026-04-03
