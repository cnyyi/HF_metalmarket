# AI Agent 改进意见报告

> 审查范围：`agent_service.py` / `agent_prompt_builder.py` / `agent_sql_validator.py` / `agent.py` / `chat.html` / `wx_chat.html`
> 审查时间：2026-05-02

---

## 🔴 P0 — 必须修复（安全/数据风险）

### 1. 商户端 MerchantID 校验形同虚设

**问题**：`validate_sql()` 只检查 SQL 字符串中是否包含 `MerchantID` 这个词，但不验证它在 WHERE 条件中。

```python
# agent_sql_validator.py 第 41-43 行
if 'MerchantID' not in upper_cleaned:
    return False, '商户端查询必须包含 MerchantID 条件'
```

以下 SQL 会通过校验，但返回所有商户数据：

```sql
SELECT TOP 500 MerchantID, MerchantName FROM Merchant
SELECT TOP 500 m.MerchantID, m.MerchantName FROM Merchant m WHERE m.Status = N'正常'
```

**修复方案**：用正则检查 `WHERE ... MerchantID\s*=\s*\d+` 出现在条件中，而不是仅检查字符串存在。

---

### 2. API Key 硬编码在 .env 并通过错误信息泄露

**问题**：
- `.env` 文件中 `DEEPSEEK_API_KEY=sk-9c5074ab6dd74dba913b5f9f83416223` 明文存储
- `_call_llm()` 异常时返回 `f'...错误：{str(e)}'`，可能暴露 API 地址、密钥片段等

```python
# agent_service.py 第 210 行
return f'AI 服务暂时不可用，请稍后重试。错误：{str(e)}'
```

**修复方案**：
- 错误信息只返回通用提示，详情只写日志
- API Key 应通过环境变量或密钥管理服务注入，不应出现在版本控制中

---

### 3. Markdown 渲染无 XSS 防护

**问题**：前端用 `marked.parse()` 直接渲染 LLM 输出，未开启 sanitize。LLM 返回含 `<script>` 或 `<img onerror=...>` 的内容会导致 XSS。

```javascript
// chat.html 第 259 行
let htmlContent = marked.parse(content || '');
bubble.innerHTML = htmlContent;  // 直接注入，无过滤
```

**修复方案**：引入 DOMPurify，渲染前做 `DOMPurify.sanitize(htmlContent)`。

---

### 4. SQL 校验的注释移除不彻底

**问题**：`_remove_comments()` 只处理 `--` 和 `/* */`，但 SQL Server 还支持 `--` 后跟换行的各种变体。更关键的是，攻击者可以通过注释隐藏关键字：

```sql
SELECT/**/TOP 1*FROM Merchant;INSERT INTO ...  -- 分号后第二条
```

当前分号检测逻辑是先清注释再检测，但注释清除的正则有边界情况。

**修复方案**：在 `_remove_comments()` 后额外检查：清注释后的 SQL 中如果仍有 `;`，直接拒绝。

---

## 🟠 P1 — 强烈建议（体验/可靠性）

### 5. OpenAI 客户端每次请求重新创建

**问题**：`_call_llm()` 每次调用都 `client = OpenAI(...)`，建立新 HTTP 连接，无连接复用。

```python
# agent_service.py 第 200 行
client = OpenAI(api_key=api_key, base_url=base_url)
```

**修复方案**：在 `AgentService.__init__` 中初始化客户端并缓存，或用懒加载模式。

---

### 6. 没有流式输出（Streaming）

**问题**：LLM 响应要等完整生成才返回，复杂查询可能等 5-10 秒，用户只看到 loading 动画，体验差。

**修复方案**：使用 OpenAI SDK 的 `stream=True`，配合 SSE（Server-Sent Events）逐步推送到前端，让用户看到逐字输出。

---

### 7. Prompt 中 Schema 与实际数据库不同步

**问题**：`DATABASE_SCHEMA` 是手写硬编码的，多处与 MEMORY.md 记录的实际结构不一致：

| 表 | Prompt 中 | 实际 |
|---|---|---|
| Plot.Status | `N'已租'` | 应为 `N'已出租'` |
| Receivable | 缺少 IsActive/DeletedBy/DeletedAt/DeleteReason | 有软删除字段 |
| Receivable.Status | `N'待付款'` | 实际为 `N'未付款'`（见 MEMORY.md） |
| Contract | 缺少 ContractAmount/AmountReduction/ActualAmount | 实际有这些字段 |
| SalaryProfile | 字段简写，缺少 UserID/EffectiveDate/Status | 与实际不符 |

这些不一致会导致 LLM 生成错误 SQL。

**修复方案**：
- 方案 A：启动时从数据库 `INFORMATION_SCHEMA.COLUMNS` 动态生成 Schema
- 方案 B（更实用）：手动维护但加版本号，Schema 变更时同步更新并标注日期

---

### 8. 没有 Few-shot 示例

**问题**：System Prompt 只告诉 LLM 规则和 Schema，没有任何示例查询。LLM 对中文场景的 Text-to-SQL 经常犯低级错误（如忘记 N 前缀、表名方括号等）。

**修复方案**：在 Prompt 中加入 5-8 个典型 Q&A 示例：

```
用户：本月应收账款有多少？
助手：```sql
SELECT SUM(Amount) AS 总应收, SUM(PaidAmount) AS 已收, SUM(RemainingAmount) AS 未收
FROM Receivable WHERE IsActive = 1
AND CreateTime >= DATEADD(MONTH, DATEDIFF(MONTH, 0, GETDATE()), 0)
```

用户：当前空闲地块有哪些？
助手：```sql
SELECT TOP 500 PlotNumber AS 地块编号, Area AS 面积, PlotType AS 类型
FROM Plot WHERE Status = N'空闲'
```
```

---

### 9. SQL 执行失败无自动修复

**问题**：SQL 执行失败后直接返回"查询执行失败"，没有利用错误信息让 LLM 修复。

**修复方案**：增加一次重试机会——把 SQL 错误信息反馈给 LLM，让它修正 SQL 再执行：

```python
if query_result is None:
    # 把错误信息给 LLM，让它修正
    retry_messages = messages + [
        {'role': 'assistant', 'content': first_reply},
        {'role': 'user', 'content': f'刚才的 SQL 执行报错：{error_msg}，请修正后重新生成 SQL。'}
    ]
    retry_reply = self._call_llm(retry_messages)
    # 再提取、校验、执行...
```

---

### 10. 历史对话加载重复消息

**问题**：`chat()` 方法先 `_save_message()` 保存用户消息，再 `_load_history()` 加载历史，然后又手动 `append` 同一条消息：

```python
# agent_service.py 第 19-27 行
self._save_message(conversation_id, 'user', message)  # 保存
history = self._load_history(conversation_id)           # 加载（包含刚保存的）
messages = [{'role': 'system', 'content': system_prompt}]
for msg in history:
    messages.append({'role': msg['role'], 'content': msg['content']})  # 已含当前消息
messages.append({'role': 'user', 'content': message})  # 又手动追加 → 重复！
```

**修复方案**：去掉第 27 行的手动 append，或在 `_load_history` 排除刚保存的消息。

---

## 🟡 P2 — 建议改进（效率/可维护性）

### 11. 双倍 LLM 调用可优化

**问题**：每次有 SQL 的查询都调两次 LLM（生成 SQL + 总结结果）。对于简单查询（如"查商户数量"），结果本身就够清晰了。

**修复方案**：判断结果行数，≤3 行直接格式化展示，省掉第二次 LLM 调用。

---

### 12. 无查询结果缓存

**问题**：同一问题问两次，完整走两遍 LLM+SQL 流程。

**修复方案**：对 `(user_id, message_hash)` 做短期缓存（5 分钟），相同问题直接返回上次结果。

---

### 13. 同步阻塞，无异步处理

**问题**：整个 chat 流程是同步的，LLM 调用 + SQL 执行阻塞 Flask worker。高并发时会导致所有 worker 卡住。

**修复方案**：短期可增加 worker 数量 + 超时保护；长期考虑 Celery 异步任务。

---

### 14. 无使用审计

**问题**：没有记录谁查了什么数据、执行了什么 SQL。对于财务系统这是合规风险。

**修复方案**：增加 `AgentQueryLog` 表，记录每次查询的 UserID、SQL、执行时间、返回行数。

---

### 15. Schema Token 浪费

**问题**：每次对话都发送完整 Schema（~3000 token），即使问题只涉及 1-2 张表。

**修复方案**：两阶段策略——先让 LLM 判断涉及哪些表，再只发送相关表的 Schema。

---

### 16. 前端体验细节

| 问题 | 改进 |
|---|---|
| SQL 代码块无复制按钮 | 添加一键复制 |
| 无对话搜索功能 | 支持搜索历史对话 |
| 无回答反馈（👍👎） | 加反馈按钮，收集 bad case 优化 Prompt |
| 无后续建议问题 | LLM 回答后推荐 2-3 个相关追问 |
| 微信端无会话管理 | 至少支持查看/切换最近 3 个会话 |
| 暗色模式下代码块配色硬编码 | `#1e1e2e` 改用 CSS 变量 |

---

### 17. 对话数据无清理策略

**问题**：`AgentMessage` 无限增长，敏感数据（金额、手机号）明文存储且永不清理。

**修复方案**：
- 定期归档 90 天前的对话
- 敏感字段查询结果脱敏（手机号中间 4 位用 * 替代）
- 添加数据保留策略配置

---

## 📊 改进优先级总览

| 优先级 | 编号 | 问题 | 工作量 |
|---|---|---|---|
| 🔴 P0 | #1 | MerchantID 校验漏洞 | 0.5天 |
| 🔴 P0 | #2 | API Key 泄露风险 | 0.5天 |
| 🔴 P0 | #3 | XSS 防护缺失 | 0.5天 |
| 🔴 P0 | #4 | 注释绕过风险 | 0.5天 |
| 🟠 P1 | #5 | 客户端重复创建 | 0.5天 |
| 🟠 P1 | #6 | 无流式输出 | 2天 |
| 🟠 P1 | #7 | Schema 不同步 | 1天 |
| 🟠 P1 | #8 | 缺少 Few-shot | 0.5天 |
| 🟠 P1 | #9 | SQL 失败无自动修复 | 1天 |
| 🟠 P1 | #10 | 历史消息重复 | 0.5天 |
| 🟡 P2 | #11 | 双倍 LLM 调用 | 0.5天 |
| 🟡 P2 | #12 | 查询缓存 | 1天 |
| 🟡 P2 | #13 | 异步处理 | 3天 |
| 🟡 P2 | #14 | 使用审计 | 1天 |
| 🟡 P2 | #15 | Schema Token 优化 | 2天 |
| 🟡 P2 | #16 | 前端体验 | 2天 |
| 🟡 P2 | #17 | 数据清理 | 1天 |

**P0 合计约 2 天，P0+P1 合计约 7.5 天，全部约 17 天。**

建议先集中修 P0（安全无小事），再逐步推进 P1。
