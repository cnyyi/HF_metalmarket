-- 补充缺失地块数据
-- 生成时间: 2026-04-19
-- 来源: 宏发金属再生资源市场.xlsx 对比分析
-- 说明:
--   1. B1-8-1/B1-8-2 (金耀承租) 面积待核实，暂不录入
--   2. SS-01/SS-02/ST-01 (商铺/摊位) 面积待核实，暂不录入
--   3. A1-2/A1-3/A1-4/A1-7/B1-4/B1-5 面积暂设0，录入后需补充实际面积
--   4. 现有地块面积差异 (A1-1/A1-5/C1-1) 留后续处理

-- ========== A区 ==========

-- A1-2: 闲置（面积待核实，暂设0）
INSERT INTO Plot (PlotNumber, PlotName, Area, UnitPrice, TotalPrice, Status, PlotType, MonthlyRent, YearlyRent, CreateTime)
VALUES (N'A1-2', N'A1-2', 0, 6.0, 0, N'空闲', N'水泥地皮', 0, 0, GETDATE());

-- A1-3: 闲置（面积待核实，暂设0）
INSERT INTO Plot (PlotNumber, PlotName, Area, UnitPrice, TotalPrice, Status, PlotType, MonthlyRent, YearlyRent, CreateTime)
VALUES (N'A1-3', N'A1-3', 0, 6.0, 0, N'空闲', N'水泥地皮', 0, 0, GETDATE());

-- A1-4: 曹锦富租户（面积待核实，暂设0）
INSERT INTO Plot (PlotNumber, PlotName, Area, UnitPrice, TotalPrice, Status, PlotType, MonthlyRent, YearlyRent, CreateTime)
VALUES (N'A1-4', N'A1-4', 0, 6.0, 0, N'空闲', N'水泥地皮', 0, 0, GETDATE());

-- A1-6: 苏清友，空地1260㎡
INSERT INTO Plot (PlotNumber, PlotName, Area, UnitPrice, TotalPrice, Status, PlotType, MonthlyRent, YearlyRent, CreateTime)
VALUES (N'A1-6', N'A1-6', 1260.00, 6.0, 7560.00, N'已出租', N'水泥地皮', 7560.00, 90720.00, GETDATE());

-- A1-7: 闲置（面积待核实，暂设0）
INSERT INTO Plot (PlotNumber, PlotName, Area, UnitPrice, TotalPrice, Status, PlotType, MonthlyRent, YearlyRent, CreateTime)
VALUES (N'A1-7', N'A1-7', 0, 6.0, 0, N'空闲', N'水泥地皮', 0, 0, GETDATE());

-- ========== B1区 ==========

-- B1-4: 来源租户信息表（面积待核实，暂设0）
INSERT INTO Plot (PlotNumber, PlotName, Area, UnitPrice, TotalPrice, Status, PlotType, MonthlyRent, YearlyRent, CreateTime)
VALUES (N'B1-4', N'B1-4', 0, 6.0, 0, N'空闲', N'水泥地皮', 0, 0, GETDATE());

-- B1-5: 来源租户信息表（面积待核实，暂设0）
INSERT INTO Plot (PlotNumber, PlotName, Area, UnitPrice, TotalPrice, Status, PlotType, MonthlyRent, YearlyRent, CreateTime)
VALUES (N'B1-5', N'B1-5', 0, 6.0, 0, N'空闲', N'水泥地皮', 0, 0, GETDATE());

-- B1-7: 王银福，钢结构厂房1427.75㎡
INSERT INTO Plot (PlotNumber, PlotName, Area, UnitPrice, TotalPrice, Status, PlotType, MonthlyRent, YearlyRent, CreateTime)
VALUES (N'B1-7', N'B1-7', 1427.75, 10.0, 14277.50, N'已出租', N'钢结构厂房', 14277.50, 171330.00, GETDATE());

-- B1-7-1: 王银福，附属空地111㎡
INSERT INTO Plot (PlotNumber, PlotName, Area, UnitPrice, TotalPrice, Status, PlotType, MonthlyRent, YearlyRent, CreateTime)
VALUES (N'B1-7-1', N'B1-7-1', 111.00, 6.0, 666.00, N'已出租', N'水泥地皮', 666.00, 7992.00, GETDATE());

-- B1-8-3: 金耀，混凝土建筑137㎡（B1-8-1/B1-8-2面积待核实，暂不录入）
INSERT INTO Plot (PlotNumber, PlotName, Area, UnitPrice, TotalPrice, Status, PlotType, MonthlyRent, YearlyRent, CreateTime)
VALUES (N'B1-8-3', N'B1-8-3', 137.00, 10.0, 1370.00, N'已出租', N'砖混厂房', 1370.00, 16440.00, GETDATE());

-- ========== B3区 ==========

-- B3-1: 祖维成，钢结构厂房1602.19㎡
INSERT INTO Plot (PlotNumber, PlotName, Area, UnitPrice, TotalPrice, Status, PlotType, MonthlyRent, YearlyRent, CreateTime)
VALUES (N'B3-1', N'B3-1', 1602.19, 10.0, 16021.90, N'已出租', N'钢结构厂房', 16021.90, 192262.80, GETDATE());

-- B3-1-1: 祖维成，附属空地251.81㎡
INSERT INTO Plot (PlotNumber, PlotName, Area, UnitPrice, TotalPrice, Status, PlotType, MonthlyRent, YearlyRent, CreateTime)
VALUES (N'B3-1-1', N'B3-1-1', 251.81, 6.0, 1510.86, N'已出租', N'水泥地皮', 1510.86, 18130.32, GETDATE());

-- B3-3: 崔宇文，空地930.38㎡
INSERT INTO Plot (PlotNumber, PlotName, Area, UnitPrice, TotalPrice, Status, PlotType, MonthlyRent, YearlyRent, CreateTime)
VALUES (N'B3-3', N'B3-3', 930.38, 6.0, 5582.28, N'已出租', N'水泥地皮', 5582.28, 66987.36, GETDATE());

-- B3-4: 冯成，钢结构厂房599.67㎡
INSERT INTO Plot (PlotNumber, PlotName, Area, UnitPrice, TotalPrice, Status, PlotType, MonthlyRent, YearlyRent, CreateTime)
VALUES (N'B3-4', N'B3-4', 599.67, 10.0, 5996.70, N'已出租', N'钢结构厂房', 5996.70, 71960.40, GETDATE());

-- B3-4-1: 冯成，附属空地331.52㎡
INSERT INTO Plot (PlotNumber, PlotName, Area, UnitPrice, TotalPrice, Status, PlotType, MonthlyRent, YearlyRent, CreateTime)
VALUES (N'B3-4-1', N'B3-4-1', 331.52, 6.0, 1989.12, N'已出租', N'水泥地皮', 1989.12, 23869.44, GETDATE());

-- B3-5: 马世平，空地571.88㎡
INSERT INTO Plot (PlotNumber, PlotName, Area, UnitPrice, TotalPrice, Status, PlotType, MonthlyRent, YearlyRent, CreateTime)
VALUES (N'B3-5', N'B3-5', 571.88, 6.0, 3431.28, N'已出租', N'水泥地皮', 3431.28, 41175.36, GETDATE());

-- B3-6: 马世平，混凝土建筑223.78㎡
INSERT INTO Plot (PlotNumber, PlotName, Area, UnitPrice, TotalPrice, Status, PlotType, MonthlyRent, YearlyRent, CreateTime)
VALUES (N'B3-6', N'B3-6', 223.78, 10.0, 2237.80, N'已出租', N'砖混厂房', 2237.80, 26853.60, GETDATE());

-- B3-7: 崔汝义，空地774.07㎡
INSERT INTO Plot (PlotNumber, PlotName, Area, UnitPrice, TotalPrice, Status, PlotType, MonthlyRent, YearlyRent, CreateTime)
VALUES (N'B3-7', N'B3-7', 774.07, 6.0, 4644.42, N'已出租', N'水泥地皮', 4644.42, 55733.04, GETDATE());

-- B3-8: 崔文交，空地1108㎡
INSERT INTO Plot (PlotNumber, PlotName, Area, UnitPrice, TotalPrice, Status, PlotType, MonthlyRent, YearlyRent, CreateTime)
VALUES (N'B3-8', N'B3-8', 1108.00, 6.0, 6648.00, N'已出租', N'水泥地皮', 6648.00, 79776.00, GETDATE());

-- B3-9: 杨文仁，空地91.24㎡
INSERT INTO Plot (PlotNumber, PlotName, Area, UnitPrice, TotalPrice, Status, PlotType, MonthlyRent, YearlyRent, CreateTime)
VALUES (N'B3-9', N'B3-9', 91.24, 6.0, 547.44, N'已出租', N'水泥地皮', 547.44, 6569.28, GETDATE());

-- ========== C1区 ==========

-- C1-2: 李世坤，空地949.72㎡
INSERT INTO Plot (PlotNumber, PlotName, Area, UnitPrice, TotalPrice, Status, PlotType, MonthlyRent, YearlyRent, CreateTime)
VALUES (N'C1-2', N'C1-2', 949.72, 6.0, 5698.32, N'已出租', N'水泥地皮', 5698.32, 68379.84, GETDATE());

-- C1-3: 崔占维，空地822.83㎡
INSERT INTO Plot (PlotNumber, PlotName, Area, UnitPrice, TotalPrice, Status, PlotType, MonthlyRent, YearlyRent, CreateTime)
VALUES (N'C1-3', N'C1-3', 822.83, 6.0, 4936.98, N'已出租', N'水泥地皮', 4936.98, 59243.76, GETDATE());

-- C1-4: 代家虎，空地809.38㎡
INSERT INTO Plot (PlotNumber, PlotName, Area, UnitPrice, TotalPrice, Status, PlotType, MonthlyRent, YearlyRent, CreateTime)
VALUES (N'C1-4', N'C1-4', 809.38, 6.0, 4856.28, N'已出租', N'水泥地皮', 4856.28, 58275.36, GETDATE());

-- C1-5: 代家超，空地1060.43㎡
INSERT INTO Plot (PlotNumber, PlotName, Area, UnitPrice, TotalPrice, Status, PlotType, MonthlyRent, YearlyRent, CreateTime)
VALUES (N'C1-5', N'C1-5', 1060.43, 6.0, 6362.58, N'已出租', N'水泥地皮', 6362.58, 76350.96, GETDATE());

-- C1-6: 代永德，空地1052.46㎡
INSERT INTO Plot (PlotNumber, PlotName, Area, UnitPrice, TotalPrice, Status, PlotType, MonthlyRent, YearlyRent, CreateTime)
VALUES (N'C1-6', N'C1-6', 1052.46, 6.0, 6314.76, N'已出租', N'水泥地皮', 6314.76, 75777.12, GETDATE());

-- C1-7: 代家鹏，空地1111.10㎡
INSERT INTO Plot (PlotNumber, PlotName, Area, UnitPrice, TotalPrice, Status, PlotType, MonthlyRent, YearlyRent, CreateTime)
VALUES (N'C1-7', N'C1-7', 1111.10, 6.0, 6666.60, N'已出租', N'水泥地皮', 6666.60, 79999.20, GETDATE());

-- C1-8-1: 崔大云，空地190㎡
INSERT INTO Plot (PlotNumber, PlotName, Area, UnitPrice, TotalPrice, Status, PlotType, MonthlyRent, YearlyRent, CreateTime)
VALUES (N'C1-8-1', N'C1-8-1', 190.00, 6.0, 1140.00, N'已出租', N'水泥地皮', 1140.00, 13680.00, GETDATE());

-- C1-8-2: 崔大云，钢结构466.56㎡
INSERT INTO Plot (PlotNumber, PlotName, Area, UnitPrice, TotalPrice, Status, PlotType, MonthlyRent, YearlyRent, CreateTime)
VALUES (N'C1-8-2', N'C1-8-2', 466.56, 10.0, 4665.60, N'已出租', N'钢结构厂房', 4665.60, 55987.20, GETDATE());

-- C1-9-1: 崔大洪，空地117.56㎡
INSERT INTO Plot (PlotNumber, PlotName, Area, UnitPrice, TotalPrice, Status, PlotType, MonthlyRent, YearlyRent, CreateTime)
VALUES (N'C1-9-1', N'C1-9-1', 117.56, 6.0, 705.36, N'已出租', N'水泥地皮', 705.36, 8464.32, GETDATE());

-- C1-9-2: 崔大洪，钢结构465.06㎡
INSERT INTO Plot (PlotNumber, PlotName, Area, UnitPrice, TotalPrice, Status, PlotType, MonthlyRent, YearlyRent, CreateTime)
VALUES (N'C1-9-2', N'C1-9-2', 465.06, 10.0, 4650.60, N'已出租', N'钢结构厂房', 4650.60, 55807.20, GETDATE());

-- ========== D区 ==========

-- D1: 杨文仁，砖混建筑227.03㎡
INSERT INTO Plot (PlotNumber, PlotName, Area, UnitPrice, TotalPrice, Status, PlotType, MonthlyRent, YearlyRent, CreateTime)
VALUES (N'D1', N'D1', 227.03, 10.0, 2270.30, N'已出租', N'砖混厂房', 2270.30, 27243.60, GETDATE());

-- ========== 待录入（面积需核实后补充）==========
-- B1-8-1: 金耀承租，面积待核实
-- B1-8-2: 金耀承租，面积待核实
-- SS-01: 王文奇商铺，面积待核实
-- SS-02: 谢贤祥商铺，面积待核实
-- ST-01: 卯声平摊位，面积待核实
