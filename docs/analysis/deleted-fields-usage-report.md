# 代码中使用已删除字段的清单

**生成时间：** 2026-04-03
**已删除字段：** MeterMultiplier、UnitPrice、InstallationDate

---

## 一、使用 MeterMultiplier (倍率) 的文件

### 1. app/models/meter.py

**位置：** 第154行，第162行
**代码：**
```python
# 第154行 - WaterMeter.create() 方法
INSERT INTO WaterMeter (
    MeterNumber, MeterType, MeterMultiplier,  # ← 使用了 MeterMultiplier
    ...
)

# 第162行
data.get('meter_multiplier', 1),  # ← 使用了 meter_multiplier
```

**影响：** ❌ **WaterMeter.create() 会失败**

---

### 2. templates/utility/list.html

**位置：** 第115-123行，第393行
**代码：**
```html
<!-- 第115-123行 - 前端表单 -->
<label for="meter_multiplier" class="form-label fw-bold">倍率</label>
<input type="number"
       class="form-control"
       id="meter_multiplier"
       name="meter_multiplier"
       ...>
```

```javascript
// 第393行 - JavaScript 数据收集
meter_multiplier: parseFloat($('#meter_multiplier').val()) || 1,
```

**影响：** ⚠️ 前端会发送 meter_multiplier 数据，但后端无法保存

---

### 3. app/services/utility_service.py

**位置：** 第337行
**代码：**
```python
# 第337行
meter_multiplier = 1
usage = (current_reading - last_reading) * meter_multiplier
```

**影响：** ✅ **不影响数据库操作**（仅用于计算，硬编码为1）

---

## 二、使用 UnitPrice (单价) 的文件

### 1. app/models/meter.py

**位置：** 第155行，第164行
**代码：**
```python
# 第155行 - WaterMeter.create() 方法
INSERT INTO WaterMeter (
    ...,
    UnitPrice,  # ← 使用了 UnitPrice
    ...
)

# 第164行
data.get('unit_price', 0),  # ← 使用了 unit_price
```

**影响：** ❌ **WaterMeter.create() 会失败**

---

### 2. app/services/utility_service.py

**位置：** 第340行
**代码：**
```python
# 第340行
total_amount = 0  # 暂时设置为0，因为已删除UnitPrice字段
```

**影响：** ✅ **已注释说明**（不影响数据库操作）

---

### 3. templates/utility/water_meter.html

**位置：** 多处使用
**代码：** 在水表抄表页面中显示单价

**影响：** ⚠️ 前端显示会受影响

---

### 4. templates/utility/electricity_meter.html

**位置：** 多处使用
**代码：** 在电表抄表页面中显示单价

**影响：** ⚠️ 前端显示会受影响

---

## 三、使用 InstallationDate (安装日期) 的文件

### 1. app/models/meter.py

**位置：** 第156行，第168行
**代码：**
```python
# 第156行 - WaterMeter.create() 方法
INSERT INTO WaterMeter (
    ...,
    InstallationDate  # ← 使用了 InstallationDate
) OUTPUT INSERTED.MeterID
VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)

# 第168行
data.get('installation_date')  # ← 使用了 installation_date
```

**影响：** ❌ **WaterMeter.create() 会失败**

---

### 2. templates/utility/list.html

**位置：** 第143-150行，第395行，第417-421行，第624行
**代码：**
```html
<!-- 第143-150行 - 前端表单 -->
<label for="installation_date" class="form-label fw-bold">
    安装日期 <span class="text-danger">*</span>
</label>
<input type="date"
       class="form-control"
       id="installation_date"
       name="installation_date"
       required>
```

```javascript
// 第395行 - JavaScript 数据收集
installation_date: $('#installation_date').val()

// 第417-421行 - 表单验证
if (!formData.installation_date) {
    $('#installation_date').addClass('is-invalid');
    isValid = false;
} else {
    $('#installation_date').removeClass('is-invalid');
}

// 第624行 - 设置默认值
$('#installation_date').val(defaultDate);
```

**影响：** ⚠️ 前端会发送 installation_date 数据，但后端无法保存

---

### 3. app/routes/utility.py

**位置：** 第96行
**代码：**
```python
# 第96行
required_fields = ['meter_number', 'meter_type', 'installation_date']
```

**影响：** ❌ **后端会要求 installation_date 必填，但无法保存**

---

## 四、修复优先级

### 🔴 高优先级（必须立即修复）

1. **app/models/meter.py** - WaterMeter.create() 方法
   - 移除 `MeterMultiplier`, `UnitPrice`, `InstallationDate` 字段
   - 影响：新增水表功能完全不可用

2. **app/routes/utility.py** - 必填字段验证
   - 从 `required_fields` 中移除 `installation_date`
   - 影响：后端验证会失败

### 🟡 中优先级（建议修复）

3. **templates/utility/list.html** - 前端表单
   - 移除倍率和安装日期字段
   - 影响：用户填写了无用字段

4. **templates/utility/water_meter.html** - 抄表页面
   - 移除单价显示
   - 影响：前端显示异常

5. **templates/utility/electricity_meter.html** - 抄表页面
   - 移除单价显示
   - 影响：前端显示异常

### 🟢 低优先级（可选修复）

6. **app/services/utility_service.py** - 业务逻辑
   - 已硬编码为1，不影响功能
   - 可保留或移除

---

## 五、修复建议

### 方案A：完全移除这三个字段（推荐）

1. **修改 app/models/meter.py**
   - WaterMeter.create() 方法中移除这三个字段
   - ElectricityMeter.create() 方法已正确（不包含这三个字段）

2. **修改 app/routes/utility.py**
   - 从 required_fields 中移除 installation_date

3. **修改前端页面**
   - list.html: 移除倍率和安装日期字段
   - water_meter.html: 移除单价显示
   - electricity_meter.html: 移除单价显示

### 方案B：保留字段但修改实现

如果未来需要这些字段，可以：
1. 重新添加数据库字段
2. 保持当前代码不变

---

## 六、修复代码示例

### app/models/meter.py 修复

```python
# WaterMeter.create() 方法修改为：
cursor.execute("""
    INSERT INTO WaterMeter (
        MeterNumber, MeterType,
        InstallationLocation,
        LastReading, CurrentReading, Status
    ) OUTPUT INSERTED.MeterID
    VALUES (?, ?, ?, ?, ?, ?)
""", (
    data['meter_number'],
    data['meter_type'],
    data.get('installation_location', ''),
    data.get('last_reading', 0),
    data.get('current_reading', 0),
    data.get('status', '正常')
))
```

### app/routes/utility.py 修复

```python
# 修改为：
required_fields = ['meter_number', 'meter_type']
```

---

**报告生成人：** AI Assistant
**下一步行动：** 执行代码修复
