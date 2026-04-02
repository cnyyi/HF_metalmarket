# 字典管理功能设计文档

## 文档信息

| 项目名称 | 宏发金属交易市场管理系统 - 字典管理功能 |
| --- | --- |
| 文档版本 | V1.0 |
| 编写日期 | 2026-03-31 |
| 文档状态 | 设计阶段 |
| 编写人员 | 系统分析员 |

---

## 1. 功能概述

### 1.1 背景

当前系统中字典数据（如商户类型、业务类型等）分散在各个服务类中直接查询使用，缺少统一的字典管理界面，导致：
- 字典数据维护困难，需要直接操作数据库
- 无法快速添加或修改字典项
- 缺少操作审计和历史记录
- 无法批量导入导出字典数据

### 1.2 目标

实现一个轻量级的字典管理功能，为管理员提供：
- 统一的字典管理界面
- 按字典类型分类管理
- 字典项的增删改查操作
- 批量导入导出功能
- 操作日志记录

### 1.3 目标用户

- **系统管理员**：负责维护系统字典数据
- **工作人员**：查看和使用字典数据

---

## 2. 功能需求

### 2.1 核心功能

#### 2.1.1 字典分类管理

**功能描述**：
- 按DictType分组展示字典数据
- 支持字典类型的筛选和搜索
- 显示每个字典类型的字典项数量

**界面设计**：
- 左侧：字典类型树形菜单或标签页
- 右侧：选中类型的字典项列表

**数据来源**：
- 从Sys_Dictionary表查询不重复的DictType值
- 统计每个DictType的字典项数量

#### 2.1.2 字典项增删改查

**功能描述**：
- 添加字典项：通过模态窗口添加新的字典项
- 编辑字典项：通过模态窗口修改现有字典项
- 删除字典项：支持单个删除和批量删除
- 查看字典项：列表展示所有字典项

**表单字段**：
- DictType（字典类型）：必填，下拉选择或手动输入
- DictCode（字典编码）：必填，唯一性校验
- DictName（字典名称）：必填
- Description（描述）：可选
- SortOrder（排序号）：必填，默认为0
- IsActive（是否启用）：必填，默认为True

**验证规则**：
- DictCode在同一DictType下必须唯一
- 所有必填字段不能为空
- SortOrder必须为数字

#### 2.1.3 批量导入导出

**功能描述**：
- 导出：将字典数据导出为Excel文件
- 导入：从Excel文件批量导入字典数据
- 模板下载：提供标准导入模板

**Excel格式**：
| DictType | DictCode | DictName | Description | SortOrder | IsActive |
|----------|----------|----------|-------------|-----------|----------|
| merchant_type | individual | 个体工商户 | 个体经营的商户 | 1 | 1 |
| merchant_type | company | 公司 | 企业法人经营的商户 | 2 | 1 |

**导入规则**：
- 验证必填字段完整性
- 验证DictCode唯一性
- 支持更新已存在的字典项（根据DictType+DictCode判断）
- 导入失败时提供详细错误信息

#### 2.1.4 操作日志记录

**功能描述**：
- 记录所有字典操作（增、删、改）
- 记录操作人、操作时间、操作内容
- 提供日志查询功能

**日志内容**：
- 操作类型：添加/修改/删除/导入
- 操作人：当前登录用户
- 操作时间：系统时间
- 操作内容：变更前后的数据对比
- 操作IP：客户端IP地址

### 2.2 辅助功能

#### 2.2.1 搜索和筛选

**功能描述**：
- 支持按DictType筛选
- 支持按DictCode或DictName搜索
- 支持按IsActive筛选（启用/禁用）

#### 2.2.2 排序功能

**功能描述**：
- 默认按SortOrder升序排列
- 支持按创建时间、更新时间排序
- 支持拖拽调整SortOrder

#### 2.2.3 批量操作

**功能描述**：
- 批量删除
- 批量启用/禁用
- 批量修改SortOrder

---

## 3. 技术设计

### 3.1 数据库设计

#### 3.1.1 现有表结构

**Sys_Dictionary表**（已存在）：
```sql
CREATE TABLE Sys_Dictionary (
    DictID INT PRIMARY KEY IDENTITY,
    DictType NVARCHAR(50) NOT NULL,
    DictCode NVARCHAR(50) NOT NULL,
    DictName NVARCHAR(100) NOT NULL,
    Description NVARCHAR(200) NULL,
    SortOrder INT DEFAULT 0 NULL,
    IsActive BIT DEFAULT 1 NULL,
    CreateTime DATETIME DEFAULT GETDATE() NULL,
    UpdateTime DATETIME NULL
);
```

#### 3.1.2 新增表结构

**DictOperationLog表**（新增）：
```sql
CREATE TABLE DictOperationLog (
    LogID INT PRIMARY KEY IDENTITY,
    DictID INT NULL,
    DictType NVARCHAR(50) NOT NULL,
    DictCode NVARCHAR(50) NOT NULL,
    OperationType NVARCHAR(20) NOT NULL,
    OperationUser INT NOT NULL,
    OperationTime DATETIME DEFAULT GETDATE() NOT NULL,
    OperationIP NVARCHAR(50) NULL,
    OldValue NVARCHAR(MAX) NULL,
    NewValue NVARCHAR(MAX) NULL,
    Description NVARCHAR(500) NULL,
    FOREIGN KEY (OperationUser) REFERENCES [User](UserID)
);

CREATE INDEX idx_dict_log_time ON DictOperationLog(OperationTime);
CREATE INDEX idx_dict_log_type ON DictOperationLog(DictType);
CREATE INDEX idx_dict_log_user ON DictOperationLog(OperationUser);
```

### 3.2 后端架构

#### 3.2.1 文件结构

```
app/
├── services/
│   └── dictionary_service.py      # 字典服务类
├── routes/
│   └── dictionary.py              # 字典路由
├── forms/
│   └── dictionary_form.py         # 字典表单
├── models/
│   └── dictionary.py              # 字典模型
templates/
└── dictionary/
    ├── list.html                  # 字典列表页面
    └── import.html                # 导入页面（可选）
```

#### 3.2.2 服务类设计

**DictionaryService类**：

```python
class DictionaryService:
    @staticmethod
    def get_dict_types()
    # 获取所有字典类型
    
    @staticmethod
    def get_dictionaries(dict_type=None, page=1, per_page=20, search=None)
    # 获取字典列表（分页）
    
    @staticmethod
    def get_dictionary_by_id(dict_id)
    # 根据ID获取字典项
    
    @staticmethod
    def create_dictionary(dict_type, dict_code, dict_name, description, sort_order, is_active, user_id)
    # 创建字典项
    
    @staticmethod
    def update_dictionary(dict_id, dict_type, dict_code, dict_name, description, sort_order, is_active, user_id)
    # 更新字典项
    
    @staticmethod
    def delete_dictionary(dict_id, user_id)
    # 删除字典项
    
    @staticmethod
    def batch_delete(dict_ids, user_id)
    # 批量删除
    
    @staticmethod
    def export_dictionaries(dict_type=None)
    # 导出字典数据
    
    @staticmethod
    def import_dictionaries(file_path, user_id)
    # 导入字典数据
    
    @staticmethod
    def check_dict_code_exists(dict_type, dict_code, exclude_id=None)
    # 检查DictCode是否存在
    
    @staticmethod
    def log_operation(dict_id, dict_type, dict_code, operation_type, user_id, old_value=None, new_value=None, description=None)
    # 记录操作日志
```

#### 3.2.3 路由设计

**路由端点**：

| 路由 | 方法 | 功能 |
|------|------|------|
| /dictionary/list | GET | 字典列表页面 |
| /dictionary/add | POST | 添加字典项 |
| /dictionary/edit/<int:dict_id> | POST | 编辑字典项 |
| /dictionary/delete/<int:dict_id> | POST | 删除字典项 |
| /dictionary/batch_delete | POST | 批量删除 |
| /dictionary/export | GET | 导出字典数据 |
| /dictionary/import | POST | 导入字典数据 |
| /dictionary/download_template | GET | 下载导入模板 |
| /dictionary/check_code | POST | 检查DictCode是否存在 |

### 3.3 前端设计

#### 3.3.1 页面布局

**字典列表页面**：
```
+--------------------------------------------------+
| 字典管理                        [导出] [导入] [添加] |
+--------------------------------------------------+
| 字典类型: [全部 ▼]  搜索: [______] [搜索] [重置]   |
+--------------------------------------------------+
| 字典类型 | 字典编码 | 字典名称 | 描述 | 排序 | 状态 | 操作 |
|----------|----------|----------|------|------|------|------|
| merchant | individual| 个体工商户| ... | 1    | 启用 | 编辑 删除 |
| merchant | company   | 公司     | ... | 2    | 启用 | 编辑 删除 |
+--------------------------------------------------+
| 显示 1-20 条，共 50 条    [<] [1] [2] [3] [>]    |
+--------------------------------------------------+
```

#### 3.3.2 模态窗口设计

**添加/编辑字典项模态窗口**：
```
+------------------------------------------+
| 添加字典项                          [×]  |
+------------------------------------------+
| 字典类型*:   [_______________] 或 [选择▼] |
|                                          |
| 字典编码*:   [_______________]           |
|                                          |
| 字典名称*:   [_______________]           |
|                                          |
| 描述:        [_______________]           |
|              [_______________]           |
|                                          |
| 排序号*:     [_____]                     |
|                                          |
| 是否启用:    [✓]                         |
|                                          |
|              [取消]  [保存]              |
+------------------------------------------+
```

#### 3.3.3 交互设计

**添加字典项**：
1. 点击"添加"按钮，打开模态窗口
2. 填写表单，点击"保存"
3. AJAX提交表单数据
4. 成功后关闭模态窗口，刷新列表
5. 失败则显示错误信息

**编辑字典项**：
1. 点击"编辑"按钮，打开模态窗口（预填充数据）
2. 修改表单，点击"保存"
3. AJAX提交表单数据
4. 成功后关闭模态窗口，刷新列表
5. 失败则显示错误信息

**删除字典项**：
1. 点击"删除"按钮
2. 弹出确认对话框
3. 确认后AJAX提交删除请求
4. 成功后刷新列表
5. 失败则显示错误信息

**导入字典数据**：
1. 点击"导入"按钮，打开导入模态窗口
2. 下载模板（可选）
3. 选择Excel文件
4. 点击"导入"按钮
5. 显示导入结果（成功/失败条数，错误详情）

### 3.4 数据流程

#### 3.4.1 添加字典项流程

```
用户填写表单
    ↓
前端验证（必填项、格式）
    ↓
AJAX提交到 /dictionary/add
    ↓
后端验证（DictCode唯一性）
    ↓
保存到 Sys_Dictionary 表
    ↓
记录操作日志到 DictOperationLog 表
    ↓
返回成功响应
    ↓
前端刷新列表
```

#### 3.4.2 导入字典数据流程

```
用户上传Excel文件
    ↓
后端解析Excel文件
    ↓
验证数据格式和完整性
    ↓
遍历每一行数据
    ↓
检查DictCode是否存在
    ├─ 存在：更新
    └─ 不存在：插入
    ↓
记录操作日志
    ↓
返回导入结果（成功/失败条数）
```

---

## 4. 接口设计

### 4.1 获取字典类型列表

**接口**：`GET /dictionary/types`

**返回格式**：
```json
{
  "code": 0,
  "message": "success",
  "data": [
    {
      "dict_type": "merchant_type",
      "count": 4
    },
    {
      "dict_type": "business_type",
      "count": 4
    }
  ]
}
```

### 4.2 获取字典列表

**接口**：`GET /dictionary/list`

**参数**：
- dict_type: 字典类型（可选）
- page: 页码（默认1）
- per_page: 每页条数（默认20）
- search: 搜索关键词（可选）

**返回格式**：
```json
{
  "code": 0,
  "message": "success",
  "data": {
    "items": [
      {
        "dict_id": 1,
        "dict_type": "merchant_type",
        "dict_code": "individual",
        "dict_name": "个体工商户",
        "description": "个体经营的商户",
        "sort_order": 1,
        "is_active": true,
        "create_time": "2026-03-31 10:00:00",
        "update_time": null
      }
    ],
    "total": 50,
    "page": 1,
    "per_page": 20,
    "total_pages": 3
  }
}
```

### 4.3 添加字典项

**接口**：`POST /dictionary/add`

**参数**：
```json
{
  "dict_type": "merchant_type",
  "dict_code": "individual",
  "dict_name": "个体工商户",
  "description": "个体经营的商户",
  "sort_order": 1,
  "is_active": true
}
```

**返回格式**：
```json
{
  "code": 0,
  "message": "添加成功",
  "data": {
    "dict_id": 1
  }
}
```

### 4.4 编辑字典项

**接口**：`POST /dictionary/edit/<int:dict_id>`

**参数**：
```json
{
  "dict_type": "merchant_type",
  "dict_code": "individual",
  "dict_name": "个体工商户（修改）",
  "description": "个体经营的商户",
  "sort_order": 1,
  "is_active": true
}
```

**返回格式**：
```json
{
  "code": 0,
  "message": "更新成功",
  "data": null
}
```

### 4.5 删除字典项

**接口**：`POST /dictionary/delete/<int:dict_id>`

**返回格式**：
```json
{
  "code": 0,
  "message": "删除成功",
  "data": null
}
```

### 4.6 批量删除

**接口**：`POST /dictionary/batch_delete`

**参数**：
```json
{
  "dict_ids": [1, 2, 3]
}
```

**返回格式**：
```json
{
  "code": 0,
  "message": "成功删除3条记录",
  "data": null
}
```

### 4.7 导出字典数据

**接口**：`GET /dictionary/export`

**参数**：
- dict_type: 字典类型（可选，不传则导出全部）

**返回**：Excel文件下载

### 4.8 导入字典数据

**接口**：`POST /dictionary/import`

**参数**：multipart/form-data
- file: Excel文件

**返回格式**：
```json
{
  "code": 0,
  "message": "导入完成",
  "data": {
    "success_count": 10,
    "fail_count": 2,
    "errors": [
      {
        "row": 3,
        "message": "DictCode已存在"
      }
    ]
  }
}
```

### 4.9 检查DictCode是否存在

**接口**：`POST /dictionary/check_code`

**参数**：
```json
{
  "dict_type": "merchant_type",
  "dict_code": "individual",
  "exclude_id": 1
}
```

**返回格式**：
```json
{
  "code": 0,
  "message": "success",
  "data": {
    "exists": false
  }
}
```

---

## 5. 安全设计

### 5.1 权限控制

- 只有管理员角色可以管理字典
- 普通用户只能查看字典数据
- 所有操作需要登录认证

### 5.2 数据验证

- 前端验证：必填项、格式校验
- 后端验证：唯一性校验、数据类型校验、SQL注入防护
- 参数化查询：所有SQL使用参数化查询

### 5.3 操作审计

- 记录所有字典操作
- 记录操作人和操作时间
- 保留历史数据变更记录

---

## 6. 性能优化

### 6.1 数据库优化

- 为DictType和DictCode创建索引
- 分页查询避免全表扫描
- 批量操作使用事务

### 6.2 缓存策略

- 字典数据缓存（可选）
- 导入导出使用临时文件

### 6.3 前端优化

- 模态窗口延迟加载
- 列表分页加载
- 搜索防抖处理

---

## 7. 测试计划

### 7.1 单元测试

- DictionaryService各方法测试
- 数据验证逻辑测试
- 唯一性校验测试

### 7.2 集成测试

- 添加字典项完整流程
- 导入导出功能测试
- 批量操作测试

### 7.3 UI测试

- 模态窗口交互测试
- 表单验证测试
- 错误提示测试

---

## 8. 部署方案

### 8.1 数据库迁移

1. 创建DictOperationLog表
2. 添加必要的索引

### 8.2 代码部署

1. 部署后端代码
2. 部署前端模板
3. 注册蓝图路由

### 8.3 权限配置

1. 配置管理员权限
2. 配置菜单访问权限

---

## 9. 风险评估

### 9.1 技术风险

- **风险**：导入大量数据时性能问题
- **缓解**：限制单次导入数量（如1000条），使用批量插入

### 9.2 业务风险

- **风险**：误删除字典项影响系统运行
- **缓解**：删除前检查字典项是否被使用，提供软删除选项

### 9.3 安全风险

- **风险**：未授权访问字典管理功能
- **缓解**：严格的权限控制和登录验证

---

## 10. 后续扩展

### 10.1 第二阶段功能（可选）

- 字典项版本管理
- 字典项使用情况统计
- 字典项依赖关系管理
- 多语言支持

### 10.2 性能优化（可选）

- Redis缓存字典数据
- 字典数据CDN加速
- 异步导入导出

---

## 11. 验收标准

### 11.1 功能验收

- ✅ 字典列表正确显示
- ✅ 添加字典项功能正常
- ✅ 编辑字典项功能正常
- ✅ 删除字典项功能正常
- ✅ 批量删除功能正常
- ✅ 导出功能正常
- ✅ 导入功能正常
- ✅ 搜索筛选功能正常
- ✅ 操作日志记录正常

### 11.2 性能验收

- ✅ 列表加载时间<2秒
- ✅ 导入1000条数据<10秒
- ✅ 导出功能响应及时

### 11.3 安全验收

- ✅ 权限控制有效
- ✅ SQL注入测试通过
- ✅ XSS攻击测试通过

---

**文档结束**