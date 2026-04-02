# 宏发金属交易市场管理系统

## 项目概述

宏发金属交易市场管理系统是一个基于Python+Flask+SQL Server+Ajax+Bootstrap 5的企业内部管理系统，用于实现金属交易市场的日常管理功能，包括用户管理、商户管理、水电计费、地块管理、合同管理和财务管理等。

## 技术栈

- **后端框架**：Flask 2.3.3
- **数据库**：SQL Server（通过pyodbc直接连接）
- **前端技术**：HTML5, CSS3, JavaScript, jQuery, Bootstrap 5
- **表单处理**：Flask-WTF, WTForms
- **认证授权**：Flask-Login, Passlib
- **文件处理**：python-docx, openpyxl
- **微信集成**：wechatpy

## 功能模块

### 1. 用户管理模块
- 用户注册和登录
- 用户角色管理（管理员、工作人员、商户）
- 权限控制（RBAC模型）
- 用户信息管理

### 2. 商户管理模块
- 商户信息的CRUD操作
- 商户列表展示（分页、排序）
- 多条件模糊查询
- 商户类型和状态管理

### 3. 地块管理模块
- 地块信息的CRUD操作
- 地块图片上传和预览
- 地块详情查看
- 地块租金自动计算

### 4. 合同管理模块
- 合同信息管理
- 合同编号自动生成
- 单个合同关联多个地块
- 租金自动计算
- 合同文档生成和下载

### 5. 水电计费模块
- 水电表管理
- 水电表与合同绑定
- 抄表功能
- 费用自动计算
- 生成应收款记录

### 6. 财务管理模块
- 应收账款管理
- 应付账款管理
- 现金流水管理
- 费用类型管理
- 付款/收款记录管理

### 7. 磅秤管理模块
- 磅秤基础信息管理
- 过磅数据采集
- 过磅记录查询
- 过磅费用管理

## 项目结构

```
hf_metalmarket/
├── app/                  # 主应用目录
│   ├── models/           # 数据模型
│   ├── routes/           # 路由定义
│   ├── services/         # 业务逻辑
│   ├── forms/            # 表单定义
│   ├── __init__.py       # 应用初始化
│   └── extensions.py     # 扩展模块
├── config/               # 配置文件
├── static/               # 静态资源
├── templates/            # 模板文件
├── utils/                # 工具函数
├── docs/                 # 项目文档
├── migrations/           # 数据库迁移
├── app.py                # 应用入口
└── requirements.txt      # 项目依赖
```

## 环境配置

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置环境变量

创建.env文件，配置以下环境变量：

```
# 数据库配置
ODBC_CONNECTION_STRING=DRIVER={ODBC Driver 17 for SQL Server};SERVER=localhost;DATABASE=hf_metalmarket;UID=sa;PWD=password;Encrypt=no;TrustServerCertificate=yes;

# Flask配置
SECRET_KEY=your-secret-key
FLASK_CONFIG=development
FLASK_HOST=0.0.0.0
FLASK_PORT=5000

# 微信配置（可选）
WECHAT_APPID=your-wechat-appid
WECHAT_SECRET=your-wechat-secret

# 磅秤配置（可选）
SCALE_DEVICE_PORT=COM3
SCALE_BAUD_RATE=9600
```

### 3. 运行应用

```bash
python app.py
```

应用将在 http://localhost:5000 上运行。

## 数据库设计

系统使用SQL Server数据库，主要表结构包括：

- 用户表（User）
- 角色表（Role）
- 权限表（Permission）
- 商户表（Merchant）
- 地块表（Plot）
- 合同表（Contract）
- 水电表表（Meter）
- 财务表（Finance）
- 磅秤表（Scale）
- 通用字典表（CommonDict）

详细的数据库设计请参考docs/design/数据库设计.md文件。

## 开发指南

### 1. 代码规范

- Python代码遵循PEP 8规范
- 变量命名使用小写字母和下划线分隔
- 函数命名使用动词+名词形式
- 类命名使用驼峰命名法
- 每个函数和类都应该有文档字符串

### 2. 模板规范

- 使用Jinja2模板引擎
- 继承base.html模板
- 使用Bootstrap 5组件
- 保持模板的简洁和可读性

### 3. 数据库操作

- 使用pyodbc直接连接SQL Server
- 避免使用SQLAlchemy，防止兼容性问题
- 所有数据库操作都应该使用参数化查询，防止SQL注入

## 部署指南

详细的部署指南请参考docs/deployment/部署指南.md文件。

## 注意事项

1. 系统为内部管理系统，请勿公开部署到互联网
2. 定期备份数据库，防止数据丢失
3. 定期更新系统依赖包，修复安全漏洞
4. 合理配置权限，确保数据安全

## 许可证

本项目仅供宏发金属交易市场内部使用，未经授权不得用于其他用途。
