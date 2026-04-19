1. 严格按顺序执行：
   PM → Architect → Backend → QA → DevOps

2. 不允许跳过步骤：
   - 若缺少上一步输出，必须返回重新生成

3. 出现问题时回退：
   - 代码问题 → Backend
   - 设计问题 → Architect
   - 需求问题 → PM

4. 每个Agent只处理自己的职责，不允许越权