# 项目长期记忆

## 项目概况
- **项目名称**：宏发金属交易市场管理系统 (HF Metal Market)
- **技术栈**：Flask 3.1.3 + pyodbc（原生SQL，非SQLAlchemy）+ Bootstrap 5.3.0 + jQuery 3.7.1 + Font Awesome 6.5.1
- **数据库**：SQL Server（连接串通过 `ODBC_CONNECTION_STRING` 配置）
- **入口**：`app.py` → `app/__init__.py` 的 `create_app()` 工厂

## 关键架构决策
- **分层架构**：Routes → Services → DBConnection（禁止在routes层直接写SQL）
- **数据库工具**：`utils/database.py` 的 `DBConnection` 上下文管理器
- **蓝图注册**：12个蓝图（auth/user/merchant/contract/plot/utility/finance/scale/admin/customer/salary/dorm）
- **后台首页**：`admin_bp` → `/admin/` → `templates/admin/index.html`（登录后默认页）
- **导航结构**：市场管理(5项+宿舍4项dropdown) + 财务管理(6项dropdown，含往来客户+工资档案+月度工资) + 用户管理(平铺)
- **客户管理**：`customer_bp` → `/customer/` → `templates/customer/list.html`（往来客户CRUD）
- **权限控制**：`@check_permission('xxx_manage')` 装饰器（定义在 `app/routes/user.py`）
- **字典管理**：所有字典从 `Sys_Dictionary` 表动态获取
- **Receivable/Payable 状态值**：`N'未付款'` / `N'部分付款'` / `N'已付款'`（统一体系，字段名 `Amount` 非 `TotalAmount`）
- **合同-商户关系**（2026-04-22 修复）：同一商户允许创建多合同。`get_available_merchants()` 从 NOT IN 改为 LEFT JOIN 标注合同数，`generate_contract_number()` 增加同日编号查重自动追加序号（-2, -3...）。前端下拉显示"已有N份合同"标注。
- **Receivable 商品字段**（2026-04-18）：ProductName/Specification/Quantity/UnitID/UnitPrice（均可空），UnitID 关联字典表 unit_type（Kg/吨/车/瓶），数量×单价=应收金额
  - 列表不显示这4列（用户要求移除），但添加弹窗和详情弹窗保留
  - 详情弹窗按费用类型显示关联数据：租金→关联合同信息（ContractID via ReferenceID），电费/水费→关联抄表明细列表（含表号/位置/月份/表底/倍率/用量/单价/小计/合计）
- **Receivable 关联数据查询**（2026-04-18 修复）：
  - 合同查询：Contract表没有PlotID/MonthlyRent/DepositAmount/SignDate字段，合同-地块关系通过ContractPlot中间表，金额字段为ContractAmount/AmountReduction/ActualAmount
  - 抄表查询：3层策略——①ReceivableDetail关联 → ②ReferenceID直接查 → ③MerchantID+BelongMonth+MeterType兜底（从Description解析月份）
  - 判断条件：租金看expense_name=='租金'或ref_type=='contract'，电费/水费看expense_name或ref_type=='utility_reading_merged'/'utility_reading'
- **Receivable 软删除**（2026-04-18）：IsActive(BIT默认1) + DeletedBy + DeletedAt + DeleteReason，所有查询必须加 `WHERE IsActive=1`，已付款/部分付款+有关联收款记录的禁止删除
- **费用类型**：已从 ExpenseType 独立表迁移到 Sys_Dictionary 字典表（2026-04-15）
  - 收入方向：`expense_item_income`（租金/水费/电费/过磅费/管理费/其他收入/物业费/宿舍租金/宿舍水费/宿舍电费）
  - 支出方向：`expense_item_expend`（采购/维修费/工资/水电费/税费/其他支出）
  - ExpenseTypeID 字段现在存储 DictID，JOIN 查询优先字典表兼容旧数据
  - 外键约束已删除（Receivable/Payable/CashFlow → ExpenseType 的 FK）
  - `DictService.get_expense_items(dict_type)` 为获取费用项的统一入口
  - ⚠️ **注意**：`_create_merged_receivables()` 已修复为优先查字典表（2026-04-18），旧代码用旧 ExpenseType 表 ID 导致电费应收的 ExpenseTypeID=3（应为1017）
- **财务管理**：统一由 `FinanceService` 管控跨表事务（收款/付款核销均4步联动）

## 模块完成度（2026-04-17）
- Auth 100% | User 95% | Merchant 100% | Plot 95%（架构违规已修复✅/Status值注意用"已出租"非"已租"）| Contract 95%（架构违规已修复✅）
- **⚠️ Contract.Status 统一值**：`N'生效'`（2026-05-03 统一，原 `N'有效'` 已全部迁移为 `N'生效'`，查生效合同用 `Status = N'生效'`，不是 `N'执行中'`）- **⚠️ 数据库枚举值以实际为准**：Merchant.MerchantType 实际为 'company'/'业务往来'/'个体工商户'/'公司'/'意向客户'；Account.AccountType 实际为 'Bank'/'WeChat'；Merchant.Status 有脏数据 '1'
- AI Agent 的 Prompt 枚举值已改为动态从数据库查询（`_refresh_enum_cache()`），缓存 1 小时自动刷新
- Utility 95%（抄表状态过滤✅）| Finance 92%（收款核销✅/应付管理✅/现金流水✅/客户类型✅/账户体系✅/直接记账✅/导出❌）| Scale 40%（数据同步✅/ScaleRecord扩展✅/Dashboard看板✅含本月/上月/去年同期趋势对比/前端展示待开发）
- Admin Dashboard 95%（统计卡✅/收支柱形图✅/最近动态✅/逾期应收✅/合同到期✅/地块数据✅/暗色模式修复✅）
- Customer 100%（CRUD✅ + 搜索API✅）
- Salary 90%（工资档案✅/月度核算✅/审核发放✅/工资条✅/联动财务✅）
- Dorm 90%（房间管理✅/入住退房✅/电表抄表✅/月度账单✅/联动财务✅）
- Portal Phase1 100%（商户门户✅：首页概览/合同查询/缴费记录/过磅记录/水电抄表/门户开通）
- Finance P1 100%（账户体系✅/直接记账✅/CashFlow扩展✅/收付款联动账户✅）
- Finance P2 100%（预收预付✅/押金管理✅/冲抵核销✅/迁移脚本已执行✅）
- Finance P3-P4 待开发（内部调拨/计次计量业务）
- ExpenseOrder（费用单）开发完成（2026-04-16）：主从结构✅/应付联动✅/列表页✅/新增页✅/详情页✅/导航✅/权限✅
- GarbageCollection（垃圾清运）开发完成（2026-04-20）：列表✅/新增✅/编辑✅/详情✅/删除✅/应付联动✅/编辑联动Payable更新✅

## AI Agent 数据查询助手（2026-05-02 集成+安全修复）
- **蓝图**：agent_bp → /agent/，路由在 app/routes/agent.py
- **核心**：AgentService（app/services/agent_service.py），DeepSeek Text-to-SQL
- **Prompt**：agent_prompt_builder.py（Schema + Few-shot + 动态枚举缓存）
- **安全**：agent_sql_validator.py（MerchantID WHERE 条件校验/危险关键字/注释移除/分号检测）
- **页面**：chat.html（管理端）+ wx_chat.html（微信端，商户权限约束）
- **数据库**：AgentConversation + AgentMessage（scripts/create_agent_tables.sql）
- **安全修复**（2026-05-02）：MerchantID 校验从字符串包含改为 WHERE 条件正则匹配/API 错误不泄露/DOMPurify 防 XSS/注释移除防绕过
- **可靠性修复**（2026-05-02）：客户端复用/历史消息去重/Schema 枚举值动态化(1h缓存)/Few-shot 示例/SQL 失败自动修复一次/简单结果跳过二次 LLM

## 商户门户（Phase 1 完成 2026-04-15）
- User表新增 UserType 字段：Admin(管理端) / Merchant(商户端)
- Merchant表新增 PortalEnabled、PortalOpenTime 字段
- 登录分流：Admin→/admin/，Merchant→/portal/
- 蓝图：portal_bp（/portal/），带 merchant_required 装饰器
- 商户数据隔离：所有查询基于 current_user.merchant_id
- 管理端"开通门户"按钮：商户列表页，自动生成账号(m_{MerchantID})，初始密码123456
- 权限：merchant角色 + 5个门户权限(portal_view/contract/finance/scale/utility)

## 已知技术债务
- ~~**架构违规**：contract.py、plot.py 在routes层直接使用DBConnection~~ → ✅ 已修复（2026-04-17，迁移到 ContractService/PlotService）
- **架构违规**：admin.py 仍直接使用 DBConnection（仪表盘统计查询，合理场景暂保留）
- **架构违规**：finance.py 的 receivable_detail 中新增了 _get_contract_summary 和 _get_utility_readings 辅助函数直接使用 DBConnection（查关联合同/抄表数据，routes层内联辅助函数，暂保留）
- **Dead code**：app/extensions.py 未被引用
- **调试代码**：utility.py 仍有部分 print() 语句
- **财务导出**：应收/应付/现金流水导出Excel功能均未实现
- **SCOPE_IDENTITY 不稳定**：add_contract 原来用 SCOPE_IDENTITY 获取新ID，可能导致 None（合同13-16无 ContractPlot 数据为证），已改为 OUTPUT INSERTED.ContractID + SCOPE_IDENTITY 回退
- **合同-应收联动**（2026-04-23 修复）：`add_contract()` 创建合同后自动创建租金应收；`update_contract()` 更新合同时同步更新/创建应收（之前缺失此逻辑）。`rent_adjust` 参数统一做 `float()` 类型保护

## 前端架构（2026-04-16 UI 全面改版后）
- **模板体系**：admin_base.html(管理端-侧边栏布局) / auth_base.html(认证页-双栏分屏) / public_base.html(公共) / merchant_base.html(商户端)
- **外部CSS/JS**：admin.css(工业金属美学主题+暗色模式) + admin.js(主题切换+侧边栏交互+微交互)
- **CDN统一**：Bootstrap 5.3.0 + Font Awesome 6.5.1 + jQuery 3.7.1 + Chart.js 4.4.1(仅首页)
- **字体**：Noto Sans SC(标题) + DM Sans(正文) + JetBrains Mono(金额数据) via Google Fonts
- **配色方案（2026-04-16 改版）**：
  - 亮色主色：深蓝 #165DFF + 铜 #C87533
  - 辅助色：深紫 #6366F1 + 青 #06B6D4
  - 暗色模式：背景 #1E1E2E、文字 #E2E8F0、强调色 #818CF8
- **暗色模式**：CSS变量 `[data-theme="dark"]` 全覆盖，localStorage持久化，topbar切换按钮
- **全局组件**：Toast通知 / GlobalLoading / emptyStateHtml / animateValue(数字跳动，支持整数/金额模式) / 金额列自动检测
- **首页仪表盘**：2 KPI卡(今日净收+在租商户) + 2环形饼图(应收账款回款率+应付账款支付率) + 地块总览(弧形仪表) + 地块明细 + 过磅统计(整数) + 磅费走势 + 月度收支(渐变柱) + 最近动态 + 逾期应收 + 合同到期
- **面包屑**：内联到topbar，旧breadcrumb block自动兼容（JS解析）
- **卡片规范**：圆角12px、阴影 0 4px 20px rgba(0,0,0,0.06)、内边距20px、1px浅色边框
- **animateValue**：第4参数 isMoney，true=¥+2位小数(默认)，false=纯整数(过磅车辆等)

## 数据库扩展
- **ReceivableDetail 表**：2026-04-15 新增，关联 Receivable 与 UtilityReading（多对多），用于合并应收回溯抄表明细
  - 字段：DetailID(PK), ReceivableID, ReadingID, CreateTime
  - 唯一约束：(ReceivableID, ReadingID)，无外键约束
- **抄表应收合并逻辑**：同一商户+同一月份+同一费用类型 → 合并为一条应收
  - 已有合并应收 → 累加金额+更新描述+补充明细
  - 无合并应收 → 新建
  - ReferenceType='utility_reading_merged' 标识合并类型

## 工资管理模块（2026-04-15 新增）
- **蓝图**：salary_bp → /salary/，路由在 app/routes/salary.py
- **服务层**：SalaryService（app/services/salary_service.py），严格遵循 Routes→Services→DBConnection 架构
- **数据库**：2张新表
  - SalaryProfile：员工工资档案（UserID/BaseSalary/PostSalary/Subsidy/Insurance/HousingFund/EffectiveDate/Status）
  - SalaryRecord：月度工资单（UserID/YearMonth/各项收入+扣款/GrossPay/NetPay/Status/PayableID）
  - 迁移脚本：scripts/add_salary_tables.sql
- **字典**：salary_status(待审核/已审核/已发放) + salary_profile_status(有效/停用) + expense_item_expend新增"工资"
- **权限**：salary_manage（管理员+工作人员角色已赋权）
- **财务联动**：发放工资 → 自动创建Payable→PaymentRecord→CashFlow，PayableID回写到SalaryRecord
- **页面**：profile(档案管理) + monthly(月度核算) + payslip(我的工资条，用户菜单入口)
- **流程**：建立档案→批量生成月度工资→编辑变动项→审核→发放（联动财务）

## 宿舍管理模块（2026-04-15 新增）
- **蓝图**：dorm_bp → /dorm/，路由在 app/routes/dorm.py
- **服务层**：DormService（app/services/dorm_service.py），严格遵循 Routes→Services→DBConnection 架构
- **数据库**：4张新表
  - DormRoom：宿舍房间（RoomNumber/RoomType/MonthlyRent/WaterQuota/ElectricityUnitPrice/MeterNumber/LastReading/Status）
  - DormOccupancy：入住记录（TenantType商户或个人/MerchantID/TenantName/IDCardNumber/IDCardFrontPhoto/IDCardBackPhoto/MoveInDate/MoveOutDate/Status）
  - DormReading：电表读数（RoomID/YearMonth/PreviousReading/CurrentReading/Consumption/Amount/ReadingDate/OccupancyID）
  - DormBill：月度账单（RoomID/OccupancyID/YearMonth/RentAmount/WaterAmount/ElectricityAmount/TotalAmount/ReadingID/ReceivableID/Status）
  - 迁移脚本：scripts/add_dorm_tables.sql
- **字典**：dorm_room_type(单间/标间/套间) + dorm_room_status(空闲/已住/维修中) + dorm_tenant_type(商户/个人) + dorm_occupancy_status(在住/已退房) + dorm_bill_status(待确认/已确认/已开账/已收清)
- **费用项**：expense_item_income新增宿舍租金/宿舍水费/宿舍电费
- **客户类型**：customer_type新增宿舍个人（个人租户自动在Customer表查找或创建）
- **权限**：dorm_manage（管理员+工作人员角色已赋权）
- **财务联动**：账单开账→创建3条Receivable（宿舍租金/宿舍水费/宿舍电费）→缴费走现有收款核销流程
- **页面**：rooms(房间管理) + occupancy(入住管理+身份证上传) + reading(电表抄表) + bill(月度账单)
- **流程**：录入房间→办理入住→每月抄电表→生成月度账单→确认→开账（联动应收）→缴费核销
- **导航**：市场管理下拉→磅秤数据下方分割线→宿舍房间/入住管理/电表抄表/宿舍账单

## 过磅数据同步模块（2026-04-16 新增）
- **程序位置**：`scale_sync/scale_sync.py` + `scale_sync/sync_config.json`
- **数据源**：Access 过磅软件数据库（Database.mdb，密码 www.fzatw.com）
- **目标**：SQL Server hf_metalmarket.ScaleRecord
- **同步方式**：增量同步，基于流水号（SourceSerialNo）对比
- **过滤条件**：只同步 RecordFinish=1（已完成）的记录
- **ScaleRecord 扩展字段**：SourceSerialNo(UNIQUE)/WeighType/SenderName/ReceiverName/DeductWeight/ActualWeight/ScaleFee/GrossTime/TareTime/GrossOperator/TareOperator/IsSynced
- **MerchantID**：允许NULL（已删外键约束），过磅数据商户信息经常为空
- **Scale 表**：默认1条记录（ScaleID=1, ScaleNumber='A', A磅秤）
- **运行模式**：前台运行 / `--once` 单次同步 / `--install` 安装为Windows服务
- **首次全量**：19414条记录同步成功（2004年至2026年）

## 权威文档
- 数据库设计：`docs/design/数据库设计.md`
- 项目结构：`docs/目录结构设计.md`
- 需求规格：`.trae/specs/generate-spec/spec.md`（V3.0，2026-04-13更新）

## 用户偏好
- 数据库字段命名使用 PascalCase（如 MerchantID、ContractNumber）
- 中文值在SQL中使用 N 前缀（如 N'正常'）
- spec以设计文档为准，发现差异需要沟通确认

## Plot表数据状态（2026-04-19 补充后）
- 总记录数：52条（补充前21条）
- 数据来源：宏发金属再生资源市场.xlsx 对比补录
- 单价规则：水泥地皮=6元/㎡/月，钢结构厂房=10元/㎡/月，砖混厂房=10元/㎡/月
- **尚未录入（面积需核实）**：B1-8-1、B1-8-2（金耀，估算各546.63㎡）、SS-01、SS-02（商铺）、ST-01（摊位）共5个
- **面积待修正**：A1-1(DB=1984.54 vs Excel=1556.87)、A1-5(DB=2064.12 vs Excel=2031.50)、C1-1(DB=798.81 vs Excel=789.81)
- **面积暂设0待核实**：A1-2、A1-3、A1-4、A1-7、B1-4、B1-5
