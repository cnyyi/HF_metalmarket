# AI 数据查询助手设计

## 目标

在宏发金属交易市场管理系统中接入 DeepSeek 大模型，创建 AI Agent，基于系统数据库解答用户的业务数据问题。

示例问题：
- "本月应付账款有多少？"
- "本月合同到期的有哪些？"
- "商户XX的应收账款还有多少未收？"
- "今年水电费收入总计多少？"

## 决策记录

| 项目 | 决策 |
|------|------|
| LLM | DeepSeek (OpenAI 兼容 API) |
| 架构 | 轻量自定义 Agent（无重型框架） |
| 数据访问 | Text-to-SQL（只读） |
| 交互方式 | 多轮对话 |
| 使用场景 | 后台管理端 + 微信商户端 |
| 安全策略 | SQL 校验 + 只读连接 + 权限约束 |
| 新增依赖 | 仅 `openai` 包 |
| 新增表 | AgentConversation + AgentMessage |

## 整体架构

```
用户提问 → Flask API → Agent Service → DeepSeek API（带 schema 提示词）
                                        ↓ 生成 SQL
                                    SQL 安全校验层（只允许 SELECT）
                                        ↓
                                    执行 SQL → 返回结果
                                        ↓
                                    DeepSeek API（结果 → 自然语言回答）
                                        ↓
                                    返回给用户
```

核心流程：用户提问 → 构建 Prompt（含 schema + 权限）→ DeepSeek 生成 SQL → 安全校验 → 执行 → 结果喂回 DeepSeek → 自然语言回答

## 数据库表设计

### AgentConversation（对话会话表）

| 字段 | 类型 | 说明 |
|------|------|------|
| ConversationID | INT IDENTITY PK | 会话ID |
| UserID | INT FK → [User] | 所属用户 |
| Title | NVARCHAR(200) | 会话标题（自动取首条消息摘要） |
| Source | NVARCHAR(20) | 来源：admin / wx |
| CreateTime | DATETIME | 创建时间 |
| UpdateTime | DATETIME | 最后活跃时间 |

### AgentMessage（对话消息表）

| 字段 | 类型 | 说明 |
|------|------|------|
| MessageID | INT IDENTITY PK | 消息ID |
| ConversationID | INT FK | 所属会话 |
| Role | NVARCHAR(20) | user / assistant / system |
| Content | NVARCHAR(MAX) | 消息内容 |
| GeneratedSQL | NVARCHAR(MAX) | AI生成的SQL（仅assistant消息） |
| QueryResult | NVARCHAR(MAX) | SQL执行结果摘要（仅assistant消息） |
| CreateTime | DATETIME | 创建时间 |

设计要点：
- 保存 GeneratedSQL 和 QueryResult 便于审计和调试
- Source 字段区分来源，用于权限控制
- 多轮对话通过 ConversationID 关联消息

## Agent Service 核心设计

### System Prompt 策略

System Prompt 包含以下部分：

1. **角色定义**：你是宏发金属交易市场的数据助手，帮助用户查询业务数据
2. **数据库 Schema**：所有表的 CREATE TABLE 语句（含中文注释），包括字段说明和表关系
3. **权限约束**：
   - 管理员：可查询所有数据
   - 商户：只能查询自己商户相关的数据（WHERE MerchantID = ?）
4. **SQL 规则**：
   - 只允许 SELECT 语句
   - 禁止 INSERT/UPDATE/DELETE/DROP/ALTER
   - 中文值必须加 N 前缀（如 N'已签约'）
   - 日期范围查询使用标准格式
   - 必须使用 TOP 限制结果数量
5. **回答格式**：
   - 先给出自然语言回答
   - SQL 语句用 markdown code block 包裹

### SQL 安全校验层

```python
def validate_sql(sql: str) -> tuple[bool, str]:
    # 1. 去除注释
    # 2. 检查是否只包含 SELECT（禁止 INSERT/UPDATE/DELETE/DROP/ALTER/TRUNCATE/EXEC）
    # 3. 检查是否包含危险操作（INTO, BULK, OPENROWSET 等）
    # 4. 如果没有 TOP，强制添加 TOP 500
    # 5. 返回 (是否合法, 错误信息/清理后的SQL)
```

### Agent 工作流程

```python
def chat(user_id, conversation_id, message, source):
    # 1. 加载对话历史（最近 10 轮，控制 token）
    # 2. 构建 messages = [system_prompt] + history + [user_message]
    # 3. 第一次调用 DeepSeek → 获取回复（可能包含 SQL）
    # 4. 解析 SQL（从 markdown code block 中提取）
    # 5. 如果包含 SQL：
    #    a. validate_sql(sql)
    #    b. 如果是商户端，校验 SQL 包含商户过滤条件
    #    c. 执行 SQL（只读连接，超时 30s）
    #    d. 将结果格式化为表格文本
    #    e. 第二次调用 DeepSeek → 生成自然语言回答
    # 6. 如果不包含 SQL（闲聊/澄清）：
    #    a. 直接返回第一次调用的回答
    # 7. 保存消息到数据库
    # 8. 返回回答
```

### 权限控制

- **管理员端**：System Prompt 中不加商户过滤约束，可查询所有数据
- **商户端**：System Prompt 中注入商户 ID，要求所有 SQL 必须包含 `WHERE MerchantID = {merchant_id}`，且执行前二次校验 SQL 文本中是否包含该商户 ID

### Token 管理

- 对话历史保留最近 10 轮（20 条消息）
- System Prompt（含 schema）约 3000-4000 tokens
- 每轮对话约 500-1000 tokens
- 总计约 10000-15000 tokens，在 DeepSeek 上下文窗口内

## API 路由设计

Blueprint：`agent_bp`，URL 前缀 `/agent`

| 路由 | 方法 | 说明 |
|------|------|------|
| `/agent/chat` | POST | 发送消息，返回 AI 回答 |
| `/agent/history` | GET | 获取对话历史 |
| `/agent/conversations` | GET | 获取会话列表 |
| `/agent/conversation/create` | POST | 创建新会话 |
| `/agent/conversation/delete/<id>` | POST | 删除会话 |

### `/agent/chat` 请求体

```json
{
  "conversation_id": 1,
  "message": "本月应付账款有多少？"
}
```

### `/agent/chat` 响应体

```json
{
  "success": true,
  "data": {
    "message_id": 123,
    "content": "本月应付账款总计为 ¥125,000.00，涉及 8 笔...",
    "generated_sql": "SELECT SUM(Amount) FROM Payable WHERE ...",
    "conversation_id": 1
  }
}
```

## 前端设计

### 后台管理端

- 侧边栏添加"AI 助手"菜单项
- 全页面对话界面，类似 ChatGPT 布局
- 左侧：会话列表
- 右侧：对话区域，支持 Markdown 渲染，SQL 可折叠展示

### 微信商户端

- 微信门户添加"智能客服"入口
- 简洁对话界面
- 单会话模式（不需要会话列表）
- 底部输入框 + 发送按钮
- 消息气泡展示

## 文件结构

```
app/
  routes/agent.py                  # Agent 路由
  services/agent_service.py        # Agent 核心服务
  services/agent_sql_validator.py  # SQL 安全校验
  services/agent_prompt_builder.py # Prompt 构建（含 schema）
templates/
  agent/
    chat.html                      # 后台 AI 助手页面
    wx_chat.html                   # 微信端对话页面
```

## 配置

### 环境变量（.env）

```
DEEPSEEK_API_KEY=sk-xxx
DEEPSEEK_BASE_URL=https://api.deepseek.com
DEEPSEEK_MODEL=deepseek-chat
AGENT_MAX_HISTORY_ROUNDS=10
AGENT_SQL_TIMEOUT=30
AGENT_MAX_RESULT_ROWS=500
```

### 依赖新增

```
openai>=1.0.0    # DeepSeek 兼容 OpenAI API
```

### 数据库连接

- Agent 执行 SQL 使用独立的只读连接，与业务写操作连接分离
- 只读连接的数据库用户只有 SELECT 权限，从数据库层面保证安全

## 成本估算

- DeepSeek-Chat 定价：输入 ¥1/百万 tokens，输出 ¥2/百万 tokens
- 每次查询约消耗 5000-8000 tokens（含 schema prompt）
- 预估每次查询成本约 ¥0.01-0.02

## 安全措施

1. **SQL 校验**：只允许 SELECT，禁止所有写操作
2. **只读连接**：数据库层面使用只有 SELECT 权限的用户
3. **权限约束**：商户端 SQL 必须包含商户 ID 过滤
4. **结果限制**：强制 TOP 500，防止大量数据泄露
5. **超时控制**：SQL 执行超时 30s
6. **审计日志**：保存所有生成的 SQL 和查询结果
