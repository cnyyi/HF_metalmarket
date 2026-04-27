# MEMORY.md - 长期记忆

## 项目技术栈
- Python 后端 + SQL Server，前端 jQuery + Bootstrap 5
- 过磅同步：pyodbc 连 Access + SQL Server，60秒轮询
- 分页方式：OFFSET/FETCH NEXT

## SQL Server 字段类型陷阱
- `DueDate`、`CreateTime`、`InstallationDate` 等列在 SQL Server 中是 VARCHAR，pyodbc 返回 str
- **不能用 `.strftime()`**，必须用 `_format_date()` / `_format_datetime()` 安全函数
- 此问题在 meter.py、receivable_service.py 中均已修复，新增代码务必注意

## openpyxl 合并单元格陷阱
- `ws.merge_cells()` 后，非左上角单元格为 MergedCell，value 只读
- 合并区域只能写左上角的值，其余列只设样式不赋值

## 过磅同步三阶段机制
1. **阶段1 - 增量上传**：`流水号 > last_serial AND RecordFinish=1`
2. **阶段2 - 变更检测**：对比 Access 最近3天更新记录与 SQL Server 已同步记录的6个字段（毛重/皮重/净重/毛重时间/皮重时间/过磅费），以 Access 为准更新
3. **阶段3 - 补漏**：对比 Access 最近7天 RecordFinish=1 的记录与 SQL Server 已同步记录，差集补录。解决跨天过磅记录遗漏问题

## 配置项
- `only_finished: true` — 阶段1/2 只处理已完成记录
- `change_detection_days: 3` — 变更检测回查天数
- `missing_detection_days: 7` — 补漏检测回查天数
- `sync_interval: 60` — 同步间隔秒数
