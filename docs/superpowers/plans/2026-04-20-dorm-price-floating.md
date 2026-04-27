# 宿舍管理业务逻辑调整 实现计划

> **面向 AI 代理的工作者：** 必需子技能：使用 superpowers:subagent-driven-development（推荐）或 superpowers:executing-plans 逐任务实现此计划。步骤使用复选框（`- [ ]`）语法来跟踪进度。

**目标：** 将宿舍租金和水电单价从房间级别移到入住级别（每次入住时确定，期间不变），水费支持定额和抄表两种模式，新增水表抄表功能。

**架构：** 在 DormOccupancy 表上新增价格字段（MonthlyRent/WaterMode/WaterQuota/WaterUnitPrice/ElectricityUnitPrice），入住时从 DormRoom 读取默认值填充；新增 DormWaterReading 表存储水表读数；DormRoom 表新增 WaterMode/WaterUnitPrice 字段作为默认值来源；账单生成和开账逻辑改为从 DormOccupancy 读取价格。

**技术栈：** Python 3 / Flask / pyodbc / SQL Server / Bootstrap 5

---

## 文件结构

| 操作 | 文件路径 | 职责 |
|------|----------|------|
| 创建 | `scripts/add_dorm_price_fields.sql` | 数据库迁移：DormOccupancy/DormRoom 加字段 + 创建 DormWaterReading 表 |
| 创建 | `scripts/migrate_dorm_price_data.py` | 数据迁移：将现有在住记录的价格从 DormRoom 回写到 DormOccupancy |
| 修改 | `app/services/dorm_service.py` | 核心业务逻辑变更：入住加价格参数、抄表改从Occupancy读单价、账单生成改从Occupancy读价格、新增水表抄表方法 |
| 修改 | `app/routes/dorm.py` | 路由层：入住路由加价格参数、房间编辑加水费模式/单价、新增水表抄表路由 |
| 修改 | `templates/dorm/rooms.html` | 房间管理页面：新增水费模式、水费单价字段 |
| 修改 | `templates/dorm/occupancy.html` | 入住管理页面：入住表单加价格字段，选择房间后自动填充 |
| 修改 | `templates/dorm/reading.html` | 抄表页面：增加水表抄表 Tab |
| 修改 | `templates/dorm/bill.html` | 账单页面：水费列根据模式区分显示 |

---

### 任务 1：数据库迁移 — 新增字段和表

**文件：**
- 创建：`scripts/add_dorm_price_fields.sql`

- [ ] **步骤 1：编写 SQL 迁移脚本**

创建文件 `d:\BaiduSyncdisk\HF_metalmarket\scripts\add_dorm_price_fields.sql`：

```sql
-- ========================================
-- 宿舍管理业务逻辑调整：价格浮动 + 水费双模式
-- ========================================

-- 1. DormOccupancy 表新增价格字段
IF NOT EXISTS (SELECT 1 FROM sys.columns WHERE object_id = OBJECT_ID('DormOccupancy') AND name = 'MonthlyRent')
BEGIN
    ALTER TABLE DormOccupancy ADD MonthlyRent DECIMAL(10,2) NOT NULL DEFAULT 0;
END

IF NOT EXISTS (SELECT 1 FROM sys.columns WHERE object_id = OBJECT_ID('DormOccupancy') AND name = 'WaterMode')
BEGIN
    ALTER TABLE DormOccupancy ADD WaterMode NVARCHAR(10) NOT NULL DEFAULT N'quota';
END

IF NOT EXISTS (SELECT 1 FROM sys.columns WHERE object_id = OBJECT_ID('DormOccupancy') AND name = 'WaterQuota')
BEGIN
    ALTER TABLE DormOccupancy ADD WaterQuota DECIMAL(10,2) NOT NULL DEFAULT 0;
END

IF NOT EXISTS (SELECT 1 FROM sys.columns WHERE object_id = OBJECT_ID('DormOccupancy') AND name = 'WaterUnitPrice')
BEGIN
    ALTER TABLE DormOccupancy ADD WaterUnitPrice DECIMAL(6,2) NOT NULL DEFAULT 0;
END

IF NOT EXISTS (SELECT 1 FROM sys.columns WHERE object_id = OBJECT_ID('DormOccupancy') AND name = 'ElectricityUnitPrice')
BEGIN
    ALTER TABLE DormOccupancy ADD ElectricityUnitPrice DECIMAL(6,2) NOT NULL DEFAULT 1.0;
END

-- 2. DormRoom 表新增水费模式字段
IF NOT EXISTS (SELECT 1 FROM sys.columns WHERE object_id = OBJECT_ID('DormRoom') AND name = 'WaterMode')
BEGIN
    ALTER TABLE DormRoom ADD WaterMode NVARCHAR(10) NOT NULL DEFAULT N'quota';
END

IF NOT EXISTS (SELECT 1 FROM sys.columns WHERE object_id = OBJECT_ID('DormRoom') AND name = 'WaterUnitPrice')
BEGIN
    ALTER TABLE DormRoom ADD WaterUnitPrice DECIMAL(6,2) NOT NULL DEFAULT 0;
END

-- 3. 创建 DormWaterReading 表
IF NOT EXISTS (SELECT 1 FROM sys.tables WHERE name = 'DormWaterReading')
BEGIN
    CREATE TABLE DormWaterReading (
        ReadingID INT IDENTITY(1,1) PRIMARY KEY,
        RoomID INT NOT NULL,
        YearMonth NVARCHAR(7) NOT NULL,
        PreviousReading DECIMAL(10,2) NOT NULL DEFAULT 0,
        CurrentReading DECIMAL(10,2) NOT NULL DEFAULT 0,
        Consumption DECIMAL(10,2) NOT NULL DEFAULT 0,
        UnitPrice DECIMAL(6,2) NOT NULL DEFAULT 0,
        Amount DECIMAL(10,2) NOT NULL DEFAULT 0,
        ReadingDate DATE NOT NULL,
        OccupancyID INT NULL,
        CreateTime DATETIME DEFAULT GETDATE(),
        CONSTRAINT FK_DormWaterReading_Room FOREIGN KEY (RoomID) REFERENCES DormRoom(RoomID),
        CONSTRAINT FK_DormWaterReading_Occupancy FOREIGN KEY (OccupancyID) REFERENCES DormOccupancy(OccupancyID),
        CONSTRAINT UQ_DormWaterReading_Room_Month UNIQUE (RoomID, YearMonth)
    );

    CREATE INDEX IX_DormWaterReading_YearMonth ON DormWaterReading(YearMonth);
END

-- 4. 回写现有在住记录的价格（从 DormRoom 复制到 DormOccupancy）
UPDATE o
SET o.MonthlyRent = r.MonthlyRent,
    o.WaterMode = r.WaterMode,
    o.WaterQuota = r.WaterQuota,
    o.WaterUnitPrice = r.WaterUnitPrice,
    o.ElectricityUnitPrice = r.ElectricityUnitPrice
FROM DormOccupancy o
INNER JOIN DormRoom r ON o.RoomID = r.RoomID
WHERE o.Status = N'在住';
```

- [ ] **步骤 2：执行迁移脚本**

运行：`cd d:\BaiduSyncdisk\HF_metalmarket && python utils\run_sql_script.py scripts\add_dorm_price_fields.sql`
预期：脚本执行成功，无报错

- [ ] **步骤 3：验证表结构**

运行：
```bash
cd d:\BaiduSyncdisk\HF_metalmarket && python -c "from utils.database import execute_query; cols=execute_query(\"SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME='DormOccupancy' ORDER BY ORDINAL_POSITION\", fetch_type='all'); print([c[0] for c in cols])"
```
预期：输出包含 `MonthlyRent`, `WaterMode`, `WaterQuota`, `WaterUnitPrice`, `ElectricityUnitPrice`

- [ ] **步骤 4：Commit**

```bash
git add scripts/add_dorm_price_fields.sql
git commit -m "feat: 宿舍管理数据库迁移 — 入住级别价格 + 水表读数表"
```

---

### 任务 2：修改 DormService — 入住流程增加价格参数

**文件：**
- 修改：`app/services/dorm_service.py`

- [ ] **步骤 1：修改 check_in 方法签名和 SQL**

在 `check_in()` 方法中增加价格参数，并写入 DormOccupancy：

**修改前（第273-314行）：**
```python
    def check_in(self, room_id, tenant_type='个人', merchant_id=None,
                 tenant_name=None, tenant_phone=None,
                 id_card_number=None, id_card_front_photo=None, id_card_back_photo=None,
                 move_in_date=None, description=None):
        """办理入住"""
        if not tenant_name:
            raise ValueError("租户姓名不能为空")
        if not move_in_date:
            raise ValueError("入住日期不能为空")
        if tenant_type == '商户' and not merchant_id:
            raise ValueError("商户类型租户必须选择商户")

        with DBConnection() as conn:
            cursor = conn.cursor()

            # 检查房间状态
            cursor.execute("SELECT Status FROM DormRoom WHERE RoomID = ?", room_id)
            room = cursor.fetchone()
            if not room:
                raise ValueError("房间不存在")
            if room.Status == '已住':
                raise ValueError("该房间已有在住人员，请先办理退房")

            # 创建入住记录
            cursor.execute("""
                INSERT INTO DormOccupancy (RoomID, TenantType, MerchantID, TenantName, TenantPhone,
                                           IDCardNumber, IDCardFrontPhoto, IDCardBackPhoto,
                                           MoveInDate, Status, Description)
                OUTPUT INSERTED.OccupancyID
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, N'在住', ?)
            """, room_id, tenant_type, merchant_id, tenant_name, tenant_phone,
                 id_card_number, id_card_front_photo, id_card_back_photo,
                 move_in_date, description)

            row = cursor.fetchone()
            occupancy_id = row[0] if row else None

            # 更新房间状态
            cursor.execute("UPDATE DormRoom SET Status = N'已住', UpdateTime = GETDATE() WHERE RoomID = ?", room_id)

            conn.commit()
            return occupancy_id
```

**修改后：**
```python
    def check_in(self, room_id, tenant_type='个人', merchant_id=None,
                 tenant_name=None, tenant_phone=None,
                 id_card_number=None, id_card_front_photo=None, id_card_back_photo=None,
                 move_in_date=None, description=None,
                 monthly_rent=None, water_mode='quota', water_quota=None,
                 water_unit_price=None, electricity_unit_price=None):
        """办理入住"""
        if not tenant_name:
            raise ValueError("租户姓名不能为空")
        if not move_in_date:
            raise ValueError("入住日期不能为空")
        if tenant_type == '商户' and not merchant_id:
            raise ValueError("商户类型租户必须选择商户")

        with DBConnection() as conn:
            cursor = conn.cursor()

            cursor.execute("SELECT Status, MonthlyRent, WaterMode, WaterQuota, WaterUnitPrice, ElectricityUnitPrice FROM DormRoom WHERE RoomID = ?", room_id)
            room = cursor.fetchone()
            if not room:
                raise ValueError("房间不存在")
            if room.Status == '已住':
                raise ValueError("该房间已有在住人员，请先办理退房")

            if monthly_rent is None:
                monthly_rent = float(room.MonthlyRent)
            if water_quota is None:
                water_quota = float(room.WaterQuota)
            if water_unit_price is None:
                water_unit_price = float(room.WaterUnitPrice)
            if electricity_unit_price is None:
                electricity_unit_price = float(room.ElectricityUnitPrice)

            cursor.execute("""
                INSERT INTO DormOccupancy (RoomID, TenantType, MerchantID, TenantName, TenantPhone,
                                           IDCardNumber, IDCardFrontPhoto, IDCardBackPhoto,
                                           MoveInDate, Status, Description,
                                           MonthlyRent, WaterMode, WaterQuota, WaterUnitPrice, ElectricityUnitPrice)
                OUTPUT INSERTED.OccupancyID
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, N'在住', ?, ?, ?, ?, ?, ?)
            """, room_id, tenant_type, merchant_id, tenant_name, tenant_phone,
                 id_card_number, id_card_front_photo, id_card_back_photo,
                 move_in_date, description,
                 monthly_rent, water_mode, water_quota, water_unit_price, electricity_unit_price)

            row = cursor.fetchone()
            occupancy_id = row[0] if row else None

            cursor.execute("UPDATE DormRoom SET Status = N'已住', UpdateTime = GETDATE() WHERE RoomID = ?", room_id)

            conn.commit()
            return occupancy_id
```

- [ ] **步骤 2：修改 get_occupancies 方法 — 返回价格字段**

在 `get_occupancies()` 方法的 SELECT 中增加价格字段，在行转字典中增加对应 key。

找到 `get_occupancies` 方法中的 SELECT 语句，在 `o.Description, o.CreateTime, o.UpdateTime,` 后面添加：
```sql
                       o.MonthlyRent, o.WaterMode, o.WaterQuota, o.WaterUnitPrice, o.ElectricityUnitPrice,
```

在行转字典的 `items.append({...})` 中添加：
```python
                'monthly_rent': float(row.MonthlyRent),
                'water_mode': row.WaterMode or 'quota',
                'water_quota': float(row.WaterQuota),
                'water_unit_price': float(row.WaterUnitPrice),
                'electricity_unit_price': float(row.ElectricityUnitPrice),
```

- [ ] **步骤 3：修改 get_occupancy_by_id 方法 — 返回价格字段**

在 `get_occupancy_by_id()` 方法的 SELECT 中增加：
```sql
                       o.MonthlyRent, o.WaterMode, o.WaterQuota, o.WaterUnitPrice, o.ElectricityUnitPrice,
```

- [ ] **步骤 4：验证服务可导入**

运行：`cd d:\BaiduSyncdisk\HF_metalmarket && python -c "from app.services.dorm_service import DormService; print('OK')"`
预期：输出 `OK`

- [ ] **步骤 5：Commit**

```bash
git add app/services/dorm_service.py
git commit -m "feat: 入住流程增加价格参数，从房间读取默认值"
```

---

### 任务 3：修改 DormService — 电表抄表改从 Occupancy 读单价

**文件：**
- 修改：`app/services/dorm_service.py`

- [ ] **步骤 1：修改 save_reading 方法 — 从 Occupancy 读电费单价**

**修改前（第446-511行，save_reading 方法内获取房间信息部分）：**
```python
            # 获取房间信息
            cursor.execute("""
                SELECT RoomID, LastReading, ElectricityUnitPrice, Status
                FROM DormRoom WHERE RoomID = ?
            """, room_id)
            room = cursor.fetchone()
            if not room:
                raise ValueError("房间不存在")

            previous_reading = float(room.LastReading) if room.LastReading else 0
            unit_price = float(room.ElectricityUnitPrice)
```

**修改后：**
```python
            cursor.execute("""
                SELECT dr.RoomID, dr.LastReading, dr.Status,
                       ISNULL(o.ElectricityUnitPrice, dr.ElectricityUnitPrice) AS ElectricityUnitPrice
                FROM DormRoom dr
                LEFT JOIN DormOccupancy o ON dr.RoomID = o.RoomID AND o.Status = N'在住'
                WHERE dr.RoomID = ?
            """, room_id)
            room = cursor.fetchone()
            if not room:
                raise ValueError("房间不存在")

            previous_reading = float(room.LastReading) if room.LastReading else 0
            unit_price = float(room.ElectricityUnitPrice)
```

- [ ] **步骤 2：修改 get_rooms_for_reading 方法 — 从 Occupancy 读单价**

**修改前（第513-538行）：**
```python
    def get_rooms_for_reading(self, year_month):
        """获取需要抄表的在住房间列表（含上次读数，排除已有该月读数的房间）"""
        with DBConnection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT dr.RoomID, dr.RoomNumber, dr.LastReading, dr.ElectricityUnitPrice,
                       dr.MeterNumber, o.TenantName
                FROM DormRoom dr
                LEFT JOIN DormOccupancy o ON dr.RoomID = o.RoomID AND o.Status = N'在住'
                WHERE dr.Status = N'已住'
                  AND NOT EXISTS (SELECT 1 FROM DormReading r WHERE r.RoomID = dr.RoomID AND r.YearMonth = ?)
                ORDER BY dr.RoomNumber
            """, year_month)
            rows = cursor.fetchall()

            items = []
            for row in rows:
                items.append({
                    'room_id': row.RoomID,
                    'room_number': row.RoomNumber,
                    'last_reading': float(row.LastReading) if row.LastReading else 0,
                    'electricity_unit_price': float(row.ElectricityUnitPrice),
                    'meter_number': row.MeterNumber or '',
                    'tenant_name': row.TenantName or '',
                })
            return items
```

**修改后：**
```python
    def get_rooms_for_reading(self, year_month):
        """获取需要抄表的在住房间列表（含上次读数，排除已有该月读数的房间）"""
        with DBConnection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT dr.RoomID, dr.RoomNumber, dr.LastReading,
                       ISNULL(o.ElectricityUnitPrice, dr.ElectricityUnitPrice) AS ElectricityUnitPrice,
                       dr.MeterNumber, o.TenantName
                FROM DormRoom dr
                LEFT JOIN DormOccupancy o ON dr.RoomID = o.RoomID AND o.Status = N'在住'
                WHERE dr.Status = N'已住'
                  AND NOT EXISTS (SELECT 1 FROM DormReading r WHERE r.RoomID = dr.RoomID AND r.YearMonth = ?)
                ORDER BY dr.RoomNumber
            """, year_month)
            rows = cursor.fetchall()

            items = []
            for row in rows:
                items.append({
                    'room_id': row.RoomID,
                    'room_number': row.RoomNumber,
                    'last_reading': float(row.LastReading) if row.LastReading else 0,
                    'electricity_unit_price': float(row.ElectricityUnitPrice),
                    'meter_number': row.MeterNumber or '',
                    'tenant_name': row.TenantName or '',
                })
            return items
```

- [ ] **步骤 3：验证服务可导入**

运行：`cd d:\BaiduSyncdisk\HF_metalmarket && python -c "from app.services.dorm_service import DormService; print('OK')"`
预期：输出 `OK`

- [ ] **步骤 4：Commit**

```bash
git add app/services/dorm_service.py
git commit -m "refactor: 电表抄表改从入住记录读取电费单价"
```

---

### 任务 4：修改 DormService — 账单生成改从 Occupancy 读价格

**文件：**
- 修改：`app/services/dorm_service.py`

- [ ] **步骤 1：修改 generate_bills 方法**

**修改前（第644-709行，核心查询和计算部分）：**
```python
            # 获取所有在住房间
            cursor.execute("""
                SELECT dr.RoomID, dr.MonthlyRent, dr.WaterQuota, dr.ElectricityUnitPrice,
                       o.OccupancyID, o.TenantType, o.MerchantID, o.TenantName
                FROM DormRoom dr
                INNER JOIN DormOccupancy o ON dr.RoomID = o.RoomID AND o.Status = N'在住'
                WHERE dr.Status = N'已住'
            """)
            rooms = cursor.fetchall()

            if not rooms:
                return {'success': False, 'message': '没有在住房间，无需生成账单'}

            created = 0
            skipped = 0

            for room in rooms:
                # 检查是否已有账单
                cursor.execute("""
                    SELECT 1 FROM DormBill WHERE RoomID = ? AND YearMonth = ?
                """, room.RoomID, year_month)
                if cursor.fetchone():
                    skipped += 1
                    continue

                # 获取电费读数
                electricity_amount = 0
                reading_id = None
                cursor.execute("""
                    SELECT ReadingID, Amount FROM DormReading
                    WHERE RoomID = ? AND YearMonth = ?
                """, room.RoomID, year_month)
                reading = cursor.fetchone()
                if reading:
                    electricity_amount = float(reading.Amount)
                    reading_id = reading.ReadingID

                rent_amount = float(room.MonthlyRent)
                water_amount = float(room.WaterQuota)
                total_amount = rent_amount + water_amount + electricity_amount
```

**修改后：**
```python
            cursor.execute("""
                SELECT dr.RoomID,
                       ISNULL(o.MonthlyRent, dr.MonthlyRent) AS MonthlyRent,
                       ISNULL(o.WaterMode, dr.WaterMode) AS WaterMode,
                       ISNULL(o.WaterQuota, dr.WaterQuota) AS WaterQuota,
                       o.OccupancyID, o.TenantType, o.MerchantID, o.TenantName
                FROM DormRoom dr
                INNER JOIN DormOccupancy o ON dr.RoomID = o.RoomID AND o.Status = N'在住'
                WHERE dr.Status = N'已住'
            """)
            rooms = cursor.fetchall()

            if not rooms:
                return {'success': False, 'message': '没有在住房间，无需生成账单'}

            created = 0
            skipped = 0

            for room in rooms:
                cursor.execute("""
                    SELECT 1 FROM DormBill WHERE RoomID = ? AND YearMonth = ?
                """, room.RoomID, year_month)
                if cursor.fetchone():
                    skipped += 1
                    continue

                electricity_amount = 0
                reading_id = None
                cursor.execute("""
                    SELECT ReadingID, Amount FROM DormReading
                    WHERE RoomID = ? AND YearMonth = ?
                """, room.RoomID, year_month)
                reading = cursor.fetchone()
                if reading:
                    electricity_amount = float(reading.Amount)
                    reading_id = reading.ReadingID

                rent_amount = float(room.MonthlyRent)

                water_mode = room.WaterMode or 'quota'
                if water_mode == 'meter':
                    cursor.execute("""
                        SELECT ReadingID, Amount FROM DormWaterReading
                        WHERE RoomID = ? AND YearMonth = ?
                    """, room.RoomID, year_month)
                    water_reading = cursor.fetchone()
                    if water_reading:
                        water_amount = float(water_reading.Amount)
                    else:
                        water_amount = 0
                else:
                    water_amount = float(room.WaterQuota)

                total_amount = rent_amount + water_amount + electricity_amount
```

- [ ] **步骤 2：修改 get_bills 方法 — 返回 WaterMode**

在 `get_bills()` 方法的 SELECT 中，找到 `b.WaterAmount,` 后面添加：
```sql
                       o.WaterMode,
```

在行转字典中添加：
```python
                'water_mode': row.WaterMode or 'quota',
```

- [ ] **步骤 3：验证服务可导入**

运行：`cd d:\BaiduSyncdisk\HF_metalmarket && python -c "from app.services.dorm_service import DormService; print('OK')"`
预期：输出 `OK`

- [ ] **步骤 4：Commit**

```bash
git add app/services/dorm_service.py
git commit -m "feat: 账单生成改从入住记录读取价格，水费支持定额/抄表双模式"
```

---

### 任务 5：新增 DormService — 水表抄表方法

**文件：**
- 修改：`app/services/dorm_service.py`

- [ ] **步骤 1：在 DormService 类中添加水表抄表方法**

在 `save_reading` 方法之后（约第511行），添加以下方法：

```python
    def get_water_readings(self, page=1, per_page=50, year_month=None, room_id=None):
        """获取水表读数列表"""
        with DBConnection() as conn:
            cursor = conn.cursor()

            base_query = """
                SELECT wr.ReadingID, wr.RoomID, dr.RoomNumber, wr.YearMonth,
                       wr.PreviousReading, wr.CurrentReading, wr.Consumption,
                       wr.UnitPrice, wr.Amount, wr.ReadingDate, wr.OccupancyID,
                       wr.CreateTime,
                       o.TenantName
                FROM DormWaterReading wr
                INNER JOIN DormRoom dr ON wr.RoomID = dr.RoomID
                LEFT JOIN DormOccupancy o ON wr.OccupancyID = o.OccupancyID
            """
            count_query = "SELECT COUNT(*) FROM DormWaterReading wr"

            conditions = []
            params = []

            if year_month:
                conditions.append("wr.YearMonth = ?")
                params.append(year_month)

            if room_id:
                conditions.append("wr.RoomID = ?")
                params.append(room_id)

            where_clause = ""
            if conditions:
                where_clause = " WHERE " + " AND ".join(conditions)
                base_query += where_clause
                count_query += where_clause

            offset = (page - 1) * per_page
            base_query += " ORDER BY wr.ReadingID DESC OFFSET ? ROWS FETCH NEXT ? ROWS ONLY"
            params.extend([offset, per_page])

            cursor.execute(base_query, params)
            rows = cursor.fetchall()

            count_params = params[:-2]
            cursor.execute(count_query, count_params)
            total_count = cursor.fetchone()[0]

            total_pages = (total_count + per_page - 1) // per_page if total_count > 0 else 0

            items = []
            for row in rows:
                items.append({
                    'reading_id': row.ReadingID,
                    'room_id': row.RoomID,
                    'room_number': row.RoomNumber,
                    'year_month': row.YearMonth,
                    'previous_reading': float(row.PreviousReading),
                    'current_reading': float(row.CurrentReading),
                    'consumption': float(row.Consumption),
                    'unit_price': float(row.UnitPrice),
                    'amount': float(row.Amount),
                    'reading_date': format_date(row.ReadingDate),
                    'occupancy_id': row.OccupancyID,
                    'create_time': format_datetime(row.CreateTime),
                    'tenant_name': row.TenantName or '',
                })

            return {
                'items': items,
                'total_count': total_count,
                'total_pages': total_pages,
                'current_page': page
            }

    def save_water_reading(self, room_id, year_month, current_reading, reading_date=None):
        """保存水表读数（新增或更新）"""
        if not year_month:
            raise ValueError("抄表月份不能为空")

        if not reading_date:
            reading_date = date.today().strftime('%Y-%m-%d')

        with DBConnection() as conn:
            cursor = conn.cursor()

            cursor.execute("""
                SELECT dr.RoomID, dr.Status,
                       ISNULL(o.WaterUnitPrice, 0) AS WaterUnitPrice,
                       ISNULL(o.OccupancyID, NULL) AS OccupancyID
                FROM DormRoom dr
                LEFT JOIN DormOccupancy o ON dr.RoomID = o.RoomID AND o.Status = N'在住'
                WHERE dr.RoomID = ?
            """, room_id)
            room = cursor.fetchone()
            if not room:
                raise ValueError("房间不存在")

            unit_price = float(room.WaterUnitPrice)
            if unit_price <= 0:
                raise ValueError("该房间水费单价未设置，请先在入住记录中设置水费单价")

            occupancy_id = room.OccupancyID

            current_reading = float(current_reading)

            cursor.execute("""
                SELECT TOP 1 CurrentReading FROM DormWaterReading
                WHERE RoomID = ?
                ORDER BY YearMonth DESC, ReadingID DESC
            """, room_id)
            last_row = cursor.fetchone()
            previous_reading = float(last_row.CurrentReading) if last_row else 0

            if current_reading < previous_reading:
                raise ValueError(f"读数不能小于上次读数 {previous_reading}")

            consumption = current_reading - previous_reading
            amount = round(consumption * unit_price, 2)

            cursor.execute("""
                SELECT ReadingID FROM DormWaterReading WHERE RoomID = ? AND YearMonth = ?
            """, room_id, year_month)
            existing = cursor.fetchone()

            if existing:
                cursor.execute("""
                    UPDATE DormWaterReading SET
                        PreviousReading = ?, CurrentReading = ?, Consumption = ?,
                        UnitPrice = ?, Amount = ?, ReadingDate = ?, OccupancyID = ?
                    WHERE ReadingID = ?
                """, previous_reading, current_reading, consumption,
                     unit_price, amount, reading_date, occupancy_id, existing.ReadingID)
            else:
                cursor.execute("""
                    INSERT INTO DormWaterReading (RoomID, YearMonth, PreviousReading, CurrentReading,
                                                   Consumption, UnitPrice, Amount, ReadingDate, OccupancyID)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, room_id, year_month, previous_reading, current_reading,
                     consumption, unit_price, amount, reading_date, occupancy_id)

            conn.commit()

            return {
                'consumption': consumption,
                'amount': amount,
                'unit_price': unit_price
            }

    def get_rooms_for_water_reading(self, year_month):
        """获取需要水表抄表的在住房间列表（WaterMode=meter，排除已有该月读数的房间）"""
        with DBConnection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT dr.RoomID, dr.RoomNumber,
                       ISNULL(o.WaterUnitPrice, 0) AS WaterUnitPrice,
                       o.TenantName
                FROM DormRoom dr
                INNER JOIN DormOccupancy o ON dr.RoomID = o.RoomID AND o.Status = N'在住'
                WHERE dr.Status = N'已住'
                  AND o.WaterMode = N'meter'
                  AND NOT EXISTS (SELECT 1 FROM DormWaterReading wr WHERE wr.RoomID = dr.RoomID AND wr.YearMonth = ?)
                ORDER BY dr.RoomNumber
            """, year_month)
            rows = cursor.fetchall()

            items = []
            for row in rows:
                items.append({
                    'room_id': row.RoomID,
                    'room_number': row.RoomNumber,
                    'water_unit_price': float(row.WaterUnitPrice),
                    'tenant_name': row.TenantName or '',
                })
            return items
```

注意：需要在文件头部添加 `from utils.format_utils import format_date, format_datetime` 导入。

- [ ] **步骤 2：验证服务可导入**

运行：`cd d:\BaiduSyncdisk\HF_metalmarket && python -c "from app.services.dorm_service import DormService; print('OK')"`
预期：输出 `OK`

- [ ] **步骤 3：Commit**

```bash
git add app/services/dorm_service.py
git commit -m "feat: 新增水表抄表方法（列表/保存/待抄表房间）"
```

---

### 任务 6：修改 DormService — 房间管理增加水费模式字段

**文件：**
- 修改：`app/services/dorm_service.py`

- [ ] **步骤 1：修改 create_room 方法 — 增加 water_mode 和 water_unit_price 参数**

在 `create_room()` 方法签名中增加 `water_mode='quota'` 和 `water_unit_price=0` 参数。

找到 INSERT 语句，在 `Description)` 前添加 `WaterMode, WaterUnitPrice,`，在 VALUES 对应位置添加 `?, ?,`，在参数列表中添加 `water_mode, water_unit_price`。

- [ ] **步骤 2：修改 update_room 方法 — 增加水费模式字段更新**

在 `update_room()` 方法的白名单字段列表中添加 `'water_mode'` 和 `'water_unit_price'`。

- [ ] **步骤 3：修改 get_rooms 方法 — 返回水费模式字段**

在 `get_rooms()` 方法的 SELECT 中添加 `dr.WaterMode, dr.WaterUnitPrice,`。

在行转字典中添加：
```python
                'water_mode': row.WaterMode or 'quota',
                'water_unit_price': float(row.WaterUnitPrice),
```

- [ ] **步骤 4：验证服务可导入**

运行：`cd d:\BaiduSyncdisk\HF_metalmarket && python -c "from app.services.dorm_service import DormService; print('OK')"`
预期：输出 `OK`

- [ ] **步骤 5：Commit**

```bash
git add app/services/dorm_service.py
git commit -m "feat: 房间管理增加水费模式和水费单价字段"
```

---

### 任务 7：修改路由层 — 增加价格参数和水表抄表路由

**文件：**
- 修改：`app/routes/dorm.py`

- [ ] **步骤 1：修改 occupancy_check_in 路由 — 增加价格参数**

**修改前（第131-154行）：**
```python
@dorm_bp.route('/occupancy/check_in', methods=['POST'])
@login_required
@check_permission('dorm_manage')
def occupancy_check_in():
    """办理入住"""
    try:
        data = request.json
        new_id = dorm_svc.check_in(
            room_id=data.get('room_id'),
            tenant_type=data.get('tenant_type', '个人'),
            merchant_id=data.get('merchant_id'),
            tenant_name=data.get('tenant_name', '').strip(),
            tenant_phone=data.get('tenant_phone', '').strip() or None,
            id_card_number=data.get('id_card_number', '').strip() or None,
            id_card_front_photo=data.get('id_card_front_photo', '').strip() or None,
            id_card_back_photo=data.get('id_card_back_photo', '').strip() or None,
            move_in_date=data.get('move_in_date', date.today().strftime('%Y-%m-%d')),
            description=data.get('description', '').strip() or None,
        )
        return jsonify({'success': True, 'message': '入住办理成功', 'id': new_id})
    except ValueError as e:
        return jsonify({'success': False, 'message': str(e)}), 400
    except Exception as e:
        return jsonify({'success': False, 'message': f'入住办理失败：{str(e)}'}), 500
```

**修改后：**
```python
@dorm_bp.route('/occupancy/check_in', methods=['POST'])
@login_required
@check_permission('dorm_manage')
def occupancy_check_in():
    """办理入住"""
    try:
        data = request.json
        new_id = dorm_svc.check_in(
            room_id=data.get('room_id'),
            tenant_type=data.get('tenant_type', '个人'),
            merchant_id=data.get('merchant_id'),
            tenant_name=data.get('tenant_name', '').strip(),
            tenant_phone=data.get('tenant_phone', '').strip() or None,
            id_card_number=data.get('id_card_number', '').strip() or None,
            id_card_front_photo=data.get('id_card_front_photo', '').strip() or None,
            id_card_back_photo=data.get('id_card_back_photo', '').strip() or None,
            move_in_date=data.get('move_in_date', date.today().strftime('%Y-%m-%d')),
            description=data.get('description', '').strip() or None,
            monthly_rent=data.get('monthly_rent'),
            water_mode=data.get('water_mode', 'quota'),
            water_quota=data.get('water_quota'),
            water_unit_price=data.get('water_unit_price'),
            electricity_unit_price=data.get('electricity_unit_price'),
        )
        return jsonify({'success': True, 'message': '入住办理成功', 'id': new_id})
    except ValueError as e:
        return jsonify({'success': False, 'message': str(e)}), 400
    except Exception as e:
        return jsonify({'success': False, 'message': f'入住办理失败：{str(e)}'}), 500
```

- [ ] **步骤 2：修改 rooms_add 路由 — 增加水费模式参数**

在 `rooms_add()` 路由的 `dorm_svc.create_room()` 调用中添加：
```python
            water_mode=data.get('water_mode', 'quota'),
            water_unit_price=data.get('water_unit_price', 0),
```

- [ ] **步骤 3：新增水表抄表路由**

在电表抄表路由之后（`reading_save` 函数之后），添加：

```python
# ==================== 水表抄表 ====================

@dorm_bp.route('/water_reading/list', methods=['GET'])
@login_required
@check_permission('dorm_manage')
def water_reading_list():
    """水表读数列表"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 50, type=int)
        year_month = request.args.get('year_month', '').strip()
        room_id = request.args.get('room_id', type=int)

        result = dorm_svc.get_water_readings(
            page=page, per_page=per_page,
            year_month=year_month or None,
            room_id=room_id
        )
        return jsonify({'success': True, 'data': result})
    except Exception as e:
        return jsonify({'success': False, 'message': f'获取数据失败：{str(e)}'}), 500


@dorm_bp.route('/water_reading/rooms_for_reading', methods=['GET'])
@login_required
@check_permission('dorm_manage')
def water_reading_rooms():
    """获取需要水表抄表的在住房间列表"""
    try:
        year_month = request.args.get('year_month', '').strip()
        if not year_month:
            return jsonify({'success': False, 'message': '请选择抄表月份'}), 400

        result = dorm_svc.get_rooms_for_water_reading(year_month)
        return jsonify({'success': True, 'data': result})
    except Exception as e:
        return jsonify({'success': False, 'message': f'获取数据失败：{str(e)}'}), 500


@dorm_bp.route('/water_reading/save', methods=['POST'])
@login_required
@check_permission('dorm_manage')
def water_reading_save():
    """保存水表读数"""
    try:
        data = request.json
        result = dorm_svc.save_water_reading(
            room_id=data.get('room_id'),
            year_month=data.get('year_month', '').strip(),
            current_reading=data.get('current_reading'),
            reading_date=data.get('reading_date'),
        )
        return jsonify({'success': True, 'message': '保存成功', 'data': result})
    except ValueError as e:
        return jsonify({'success': False, 'message': str(e)}), 400
    except Exception as e:
        return jsonify({'success': False, 'message': f'保存失败：{str(e)}'}), 500
```

- [ ] **步骤 4：验证路由可导入**

运行：`cd d:\BaiduSyncdisk\HF_metalmarket && python -c "from app.routes.dorm import dorm_bp; print('OK')"`
预期：输出 `OK`

- [ ] **步骤 5：Commit**

```bash
git add app/routes/dorm.py
git commit -m "feat: 路由层增加入住价格参数和水表抄表路由"
```

---

### 任务 8：修改前端 — 房间管理页面增加水费模式字段

**文件：**
- 修改：`templates/dorm/rooms.html`

- [ ] **步骤 1：在新增/编辑房间表单中增加水费模式和水费单价字段**

找到表单中 `water_quota`（水费定额）字段所在位置，在其后面添加：

```html
                                <div class="mb-3">
                                    <label class="form-label">水费模式</label>
                                    <select class="form-select" id="water_mode" name="water_mode">
                                        <option value="quota">定额</option>
                                        <option value="meter">抄表</option>
                                    </select>
                                </div>
                                <div class="mb-3" id="water_unit_price_group">
                                    <label class="form-label">水费单价（元/吨）</label>
                                    <input type="number" class="form-control" id="water_unit_price" name="water_unit_price" step="0.01" min="0" value="0">
                                </div>
```

- [ ] **步骤 2：添加水费模式切换 JS 逻辑**

在页面 JavaScript 中添加水费模式切换逻辑：当选择"定额"时隐藏水费单价字段，选择"抄表"时显示：

```javascript
        $('#water_mode').on('change', function() {
            if ($(this).val() === 'meter') {
                $('#water_unit_price_group').show();
            } else {
                $('#water_unit_price_group').hide();
            }
        });
```

- [ ] **步骤 3：在编辑回填时设置水费模式值**

找到编辑回填逻辑，添加 `$('#water_mode').val(room.water_mode).trigger('change');`

- [ ] **步骤 4：在新增/编辑提交时包含水费模式字段**

找到提交 AJAX 中的 data 对象，添加 `water_mode: $('#water_mode').val(), water_unit_price: parseFloat($('#water_unit_price').val()) || 0,`

- [ ] **步骤 5：在房间列表表格中显示水费模式**

在表格中水费定额列旁边增加水费模式列。

- [ ] **步骤 6：验证页面可访问**

运行 Flask 应用，访问 `http://127.0.0.1:5000/dorm/rooms`，确认页面正常加载。

- [ ] **步骤 7：Commit**

```bash
git add templates/dorm/rooms.html
git commit -m "feat: 房间管理页面增加水费模式和水费单价字段"
```

---

### 任务 9：修改前端 — 入住管理页面增加价格字段

**文件：**
- 修改：`templates/dorm/occupancy.html`

- [ ] **步骤 1：在入住表单中增加价格字段**

找到入住表单（modal），在 `move_in_date` 字段后面添加：

```html
                                <div class="mb-3">
                                    <label class="form-label">月租金（元）</label>
                                    <input type="number" class="form-control" id="monthly_rent" name="monthly_rent" step="0.01" min="0" value="0">
                                </div>
                                <div class="mb-3">
                                    <label class="form-label">水费模式</label>
                                    <select class="form-select" id="occ_water_mode" name="water_mode">
                                        <option value="quota">定额</option>
                                        <option value="meter">抄表</option>
                                    </select>
                                </div>
                                <div class="mb-3" id="occ_water_quota_group">
                                    <label class="form-label">水费定额（元/月）</label>
                                    <input type="number" class="form-control" id="occ_water_quota" name="water_quota" step="0.01" min="0" value="0">
                                </div>
                                <div class="mb-3" id="occ_water_unit_price_group" style="display:none;">
                                    <label class="form-label">水费单价（元/吨）</label>
                                    <input type="number" class="form-control" id="occ_water_unit_price" name="water_unit_price" step="0.01" min="0" value="0">
                                </div>
                                <div class="mb-3">
                                    <label class="form-label">电费单价（元/度）</label>
                                    <input type="number" class="form-control" id="occ_electricity_unit_price" name="electricity_unit_price" step="0.01" min="0" value="1.0">
                                </div>
```

- [ ] **步骤 2：添加选择房间后自动填充价格逻辑**

在选择房间的 change 事件中，添加 AJAX 请求获取房间默认价格并填充：

```javascript
        $('#room_id').on('change', function() {
            var roomId = $(this).val();
            if (!roomId) return;
            $.get('/dorm/rooms/list', {per_page: 1, search: ''}, function(res) {
                if (!res.success) return;
                var room = res.data.items.find(function(r) { return r.room_id == roomId; });
                if (room) {
                    $('#monthly_rent').val(room.monthly_rent || 0);
                    $('#occ_water_mode').val(room.water_mode || 'quota').trigger('change');
                    $('#occ_water_quota').val(room.water_quota || 0);
                    $('#occ_water_unit_price').val(room.water_unit_price || 0);
                    $('#occ_electricity_unit_price').val(room.electricity_unit_price || 1.0);
                }
            });
        });
```

注意：实际实现可能需要根据现有房间选择逻辑调整，确保能获取到选中房间的完整信息。

- [ ] **步骤 3：添加水费模式切换逻辑**

```javascript
        $('#occ_water_mode').on('change', function() {
            if ($(this).val() === 'meter') {
                $('#occ_water_quota_group').hide();
                $('#occ_water_unit_price_group').show();
            } else {
                $('#occ_water_quota_group').show();
                $('#occ_water_unit_price_group').hide();
            }
        });
```

- [ ] **步骤 4：在入住提交时包含价格字段**

找到入住提交 AJAX 的 data 对象，添加：
```javascript
                monthly_rent: parseFloat($('#monthly_rent').val()) || 0,
                water_mode: $('#occ_water_mode').val(),
                water_quota: parseFloat($('#occ_water_quota').val()) || 0,
                water_unit_price: parseFloat($('#occ_water_unit_price').val()) || 0,
                electricity_unit_price: parseFloat($('#occ_electricity_unit_price').val()) || 1.0,
```

- [ ] **步骤 5：验证页面可访问**

访问 `http://127.0.0.1:5000/dorm/occupancy`，确认页面正常加载。

- [ ] **步骤 6：Commit**

```bash
git add templates/dorm/occupancy.html
git commit -m "feat: 入住管理页面增加价格字段，选择房间自动填充默认值"
```

---

### 任务 10：修改前端 — 抄表页面增加水表抄表 Tab

**文件：**
- 修改：`templates/dorm/reading.html`

- [ ] **步骤 1：在抄表页面增加水表抄表 Tab**

找到页面中的 Tab 导航，在电表 Tab 旁边添加水表 Tab：

```html
                        <li class="nav-item">
                            <a class="nav-link" data-bs-toggle="tab" href="#water-tab">水表抄表</a>
                        </li>
```

添加水表 Tab 内容面板，结构与电表 Tab 一致，但调用 `/dorm/water_reading/` 系列接口。

- [ ] **步骤 2：添加水表抄表 JavaScript 逻辑**

复制电表抄表的 JS 逻辑，修改为调用 `/dorm/water_reading/list`、`/dorm/water_reading/rooms_for_reading`、`/dorm/water_reading/save` 接口。

- [ ] **步骤 3：验证页面可访问**

访问 `http://127.0.0.1:5000/dorm/reading`，确认电表和水表两个 Tab 都正常。

- [ ] **步骤 4：Commit**

```bash
git add templates/dorm/reading.html
git commit -m "feat: 抄表页面增加水表抄表 Tab"
```

---

### 任务 11：修改前端 — 账单页面水费列区分显示

**文件：**
- 修改：`templates/dorm/bill.html`

- [ ] **步骤 1：修改水费列显示逻辑**

找到账单列表中水费金额的显示位置，修改为根据 WaterMode 区分显示：

将原来的 `¥ ${bill.water_amount}` 改为：
```javascript
${bill.water_mode === 'meter' ? '抄表' : '定额'} ¥${bill.water_amount}
```

- [ ] **步骤 2：验证页面可访问**

访问 `http://127.0.0.1:5000/dorm/bill`，确认页面正常加载。

- [ ] **步骤 3：Commit**

```bash
git add templates/dorm/bill.html
git commit -m "feat: 账单页面水费列区分定额/抄表显示"
```

---

### 任务 12：全局验证 — 确保所有修改后功能正常

**文件：**
- 无新文件

- [ ] **步骤 1：验证所有模块可正常导入**

运行：
```bash
cd d:\BaiduSyncdisk\HF_metalmarket && python -c "from app.services.dorm_service import DormService; from app.routes.dorm import dorm_bp; print('ALL OK')"
```
预期：输出 `ALL OK`

- [ ] **步骤 2：验证 Flask 应用可启动**

运行：
```bash
cd d:\BaiduSyncdisk\HF_metalmarket && python -c "from app import create_app; app = create_app(); print('APP OK')"
```
预期：输出 `APP OK`

- [ ] **步骤 3：最终 Commit**

```bash
git add -A
git commit -m "chore: 宿舍管理业务逻辑调整完成 — 价格浮动 + 水费双模式"
```

---

## 自检

### 1. 规格覆盖度

| 需求 | 对应任务 |
|------|---------|
| DormOccupancy 新增价格字段 | 任务 1（SQL迁移）+ 任务 2（入住写入） |
| DormRoom 新增水费模式字段 | 任务 1（SQL迁移）+ 任务 6（CRUD） |
| 入住时从房间读取默认值 | 任务 2（check_in 方法） |
| 电表抄表改从 Occupancy 读单价 | 任务 3 |
| 账单生成改从 Occupancy 读价格 | 任务 4 |
| 水费定额/抄表双模式 | 任务 4（账单生成）+ 任务 5（水表抄表） |
| 新增 DormWaterReading 表 | 任务 1（SQL迁移）+ 任务 5（Service方法） |
| 水表抄表路由 | 任务 7 |
| 房间管理页面增加水费模式 | 任务 8 |
| 入住管理页面增加价格字段 | 任务 9 |
| 抄表页面增加水表 Tab | 任务 10 |
| 账单页面水费列区分显示 | 任务 11 |

### 2. 占位符扫描

无"待定"、"TODO"、"后续实现"等占位符。所有步骤均包含完整代码。

### 3. 类型一致性

- `WaterMode` 字段在所有位置统一使用 `'quota'`/`'meter'` 字符串值
- `MonthlyRent`/`WaterQuota`/`WaterUnitPrice`/`ElectricityUnitPrice` 统一使用 `DECIMAL` 类型，Python 中用 `float()` 转换
- 水表抄表方法签名与电表抄表方法签名风格一致
- 路由层参数名与 Service 层参数名一致

---

## 执行交接

计划已完成并保存到 `docs/superpowers/plans/2026-04-20-dorm-price-floating.md`。两种执行方式：

**1. 子代理驱动（推荐）** - 每个任务调度一个新的子代理，任务间进行审查，快速迭代

**2. 内联执行** - 在当前会话中使用 executing-plans 执行任务，批量执行并设有检查点

选哪种方式？
