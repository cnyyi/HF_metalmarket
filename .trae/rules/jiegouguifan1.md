1. 所有 HTML 必须放在 templates/ 目录
2. render\_template 必须使用相对 templates 的路径，例如：
   render\_template('merchant/list.html')
3. 不允许把 templates 放在 app/ 目录下
4. 不允许自定义 template\_folder（除非我明确要求）
5. 所有路径必须可直接运行，不允许省略
6. SQL：必须 N'中文'
7. Python：参数化 + NVARCHAR字段
9. URL 要“像目录结构一样清晰，例如：，/merchant/list、/merchant/create、/merchant/edit/1，一看就知道干嘛的
10. 一个模块，一组路由
    商户 /merchant
    合同 /contract
    财务 /finance
13. 表单提交方式：
    必须使用 Ajax，禁止传统 form submit（页面刷新）
14. 文件统一管理
    所有文件必须走 /uploads/，数据库存路径，不存文件
15. SQL规范：必须使用参数化查询，禁止拼接SQL
    正确示例：
    cursor.execute("SELECT \* FROM merchant WHERE id = ?", (merchant\_id,))
16. 所有功能的实现（含页面+后端）均按照Spec进行，有模糊的地方，需要与我沟通确认
17. 当我让你实现功能时，必须按照spec全局约束（强制执行）进行，先查看spec中是否有相关描述，并分析相关描述，没有则与我沟通确认
