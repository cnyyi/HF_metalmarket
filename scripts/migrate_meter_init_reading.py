import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from config import DevelopmentConfig

app = create_app(DevelopmentConfig)

with app.app_context():
    from utils.database import DBConnection

    with DBConnection() as conn:
        cursor = conn.cursor()

        for table in ['ElectricityMeter', 'WaterMeter']:
            for col in ['LastReading', 'CurrentReading']:
                cursor.execute("""
                    SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS
                    WHERE TABLE_NAME = ? AND COLUMN_NAME = ?
                """, table, col)
                if cursor.fetchone()[0] > 0:
                    print(f'Dropping {col} from {table}...')

                    # 删除该列上的 DEFAULT 约束
                    cursor.execute("""
                        SELECT dc.name
                        FROM sys.default_constraints dc
                        INNER JOIN sys.tables t ON dc.parent_object_id = t.object_id
                        INNER JOIN sys.columns c ON dc.parent_object_id = c.object_id AND dc.parent_column_id = c.column_id
                        WHERE t.name = ? AND c.name = ?
                    """, table, col)
                    constraints = cursor.fetchall()
                    for row in constraints:
                        print(f'  Dropping default constraint: {row.name}')
                        try:
                            cursor.execute(f"ALTER TABLE [{table}] DROP CONSTRAINT [{row.name}]")
                            conn.commit()
                        except Exception as e:
                            print(f'  Warning: {e}')

                    cursor.execute(f"ALTER TABLE [{table}] DROP COLUMN [{col}]")
                    conn.commit()
                    print(f'  {col} dropped from {table}.')
                else:
                    print(f'{col} already removed from {table}, skipping.')

        # 验证
        print('\n=== Verification ===')
        for table in ['ElectricityMeter', 'WaterMeter']:
            cursor.execute("""
                SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS
                WHERE TABLE_NAME = ?
                ORDER BY ORDINAL_POSITION
            """, table)
            cols = [r.COLUMN_NAME for r in cursor.fetchall()]
            print(f'{table}: {cols}')

        print('\nMigration completed successfully!')
