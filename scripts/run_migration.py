"""
执行数据库迁移：给 UtilityReading 表新增 BelongMonth 字段
"""
import sys
import os

# 将项目根目录加入 Python 路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app

app = create_app()

ADD_COLUMN_SQL = """
IF NOT EXISTS (
    SELECT 1 FROM INFORMATION_SCHEMA.COLUMNS
    WHERE TABLE_NAME = N'UtilityReading'
      AND COLUMN_NAME = N'BelongMonth'
)
BEGIN
    ALTER TABLE UtilityReading
    ADD BelongMonth NVARCHAR(20) NULL;
    PRINT N'BelongMonth 列已成功添加。';
END
ELSE
BEGIN
    PRINT N'BelongMonth 列已存在，跳过添加。';
END
"""

VERIFY_SQL = """
SELECT COLUMN_NAME, DATA_TYPE, CHARACTER_MAXIMUM_LENGTH
FROM INFORMATION_SCHEMA.COLUMNS
WHERE TABLE_NAME = N'UtilityReading'
  AND COLUMN_NAME = N'BelongMonth'
"""

with app.app_context():
    from utils.database import DBConnection
    with DBConnection() as conn:
        cursor = conn.cursor()
        cursor.execute(ADD_COLUMN_SQL)
        conn.commit()

        cursor.execute(VERIFY_SQL)
        row = cursor.fetchone()
        if row:
            print(f"[OK] BelongMonth 列存在：DATA_TYPE={row[1]}, MAX_LENGTH={row[2]}")
        else:
            print("[FAIL] BelongMonth 列未找到，请检查！")
