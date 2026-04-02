# 自动更新Spec文件中的数据库定义

import sys
import os
import re
import datetime
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app
from utils.database import execute_query
import pyodbc
from config import Config


class SpecUpdater:
    """
    Spec文件更新器
    """
    
    def __init__(self):
        self.connection_string = Config.ODBC_CONNECTION_STRING
        self.spec_file = 'd:\\BaiduSyncdisk\\HF_metalmarket\\.trae\\specs\\generate-spec\\spec.md'
        self.backup_file = f'd:\\BaiduSyncdisk\\HF_metalmarket\\.trae\\specs\\generate-spec\\spec_backup_{datetime.datetime.now().strftime("%Y%m%d_%H%M%S")}.md'
        
    def backup_spec(self):
        """
        备份Spec文件
        """
        print("=" * 80)
        print("备份Spec文件")
        print("=" * 80)
        
        with open(self.spec_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        with open(self.backup_file, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"✓ Spec文件已备份到: {self.backup_file}")
        
    def get_actual_table_structure(self):
        """
        获取实际数据库表结构
        """
        print("\n" + "=" * 80)
        print("获取实际数据库表结构")
        print("=" * 80)
        
        tables = {}
        
        with pyodbc.connect(self.connection_string) as conn:
            with conn.cursor() as cursor:
                # 获取所有表名（排除备份表）
                cursor.execute("""
                    SELECT TABLE_NAME 
                    FROM INFORMATION_SCHEMA.TABLES 
                    WHERE TABLE_TYPE = 'BASE TABLE' 
                    AND TABLE_SCHEMA = 'dbo'
                    AND TABLE_NAME NOT LIKE '%Backup%'
                    ORDER BY TABLE_NAME
                """)
                
                table_names = [row.TABLE_NAME for row in cursor.fetchall()]
                
                # 获取每个表的结构
                for table_name in table_names:
                    print(f"\n获取表 {table_name} 的结构...")
                    
                    # 获取列信息
                    cursor.execute("""
                        SELECT 
                            COLUMN_NAME,
                            DATA_TYPE,
                            CHARACTER_MAXIMUM_LENGTH,
                            NUMERIC_PRECISION,
                            NUMERIC_SCALE,
                            IS_NULLABLE,
                            COLUMN_DEFAULT,
                            ORDINAL_POSITION
                        FROM INFORMATION_SCHEMA.COLUMNS
                        WHERE TABLE_NAME = ?
                        ORDER BY ORDINAL_POSITION
                    """, (table_name,))
                    
                    columns = []
                    for row in cursor.fetchall():
                        # 构建数据类型字符串
                        data_type = row.DATA_TYPE.upper()
                        if row.CHARACTER_MAXIMUM_LENGTH:
                            data_type = f"{data_type}({row.CHARACTER_MAXIMUM_LENGTH})"
                        elif row.NUMERIC_PRECISION and row.DATA_TYPE in ('decimal', 'numeric'):
                            if row.NUMERIC_SCALE:
                                data_type = f"{data_type}({row.NUMERIC_PRECISION},{row.NUMERIC_SCALE})"
                            else:
                                data_type = f"{data_type}({row.NUMERIC_PRECISION})"
                        
                        # 构建约束字符串
                        constraints = []
                        if row.COLUMN_DEFAULT:
                            default_value = row.COLUMN_DEFAULT.strip()
                            if 'GETDATE' in default_value.upper():
                                constraints.append(f"DEFAULT {default_value}")
                            elif 'IDENTITY' not in default_value.upper():
                                constraints.append(f"DEFAULT {default_value}")
                        
                        if row.IS_NULLABLE == 'NO':
                            constraints.append('NOT NULL')
                        else:
                            constraints.append('NULL')
                        
                        col_info = {
                            'name': row.COLUMN_NAME,
                            'type': data_type,
                            'constraints': ' '.join(constraints),
                            'position': row.ORDINAL_POSITION
                        }
                        columns.append(col_info)
                    
                    # 获取主键信息
                    cursor.execute("""
                        SELECT kcu.COLUMN_NAME
                        FROM INFORMATION_SCHEMA.TABLE_CONSTRAINTS tc
                        INNER JOIN INFORMATION_SCHEMA.KEY_COLUMN_USAGE kcu 
                            ON tc.CONSTRAINT_NAME = kcu.CONSTRAINT_NAME
                        WHERE tc.TABLE_NAME = ? AND tc.CONSTRAINT_TYPE = 'PRIMARY KEY'
                        ORDER BY kcu.ORDINAL_POSITION
                    """, (table_name,))
                    
                    primary_keys = [row.COLUMN_NAME for row in cursor.fetchall()]
                    
                    # 获取外键信息
                    cursor.execute("""
                        SELECT 
                            kcu.COLUMN_NAME,
                            ccu.TABLE_NAME AS FOREIGN_TABLE_NAME,
                            ccu.COLUMN_NAME AS FOREIGN_COLUMN_NAME
                        FROM INFORMATION_SCHEMA.TABLE_CONSTRAINTS tc
                        INNER JOIN INFORMATION_SCHEMA.KEY_COLUMN_USAGE kcu 
                            ON tc.CONSTRAINT_NAME = kcu.CONSTRAINT_NAME
                        INNER JOIN INFORMATION_SCHEMA.CONSTRAINT_COLUMN_USAGE ccu 
                            ON tc.CONSTRAINT_NAME = ccu.CONSTRAINT_NAME
                        WHERE tc.TABLE_NAME = ? AND tc.CONSTRAINT_TYPE = 'FOREIGN KEY'
                    """, (table_name,))
                    
                    foreign_keys = []
                    for row in cursor.fetchall():
                        fk_info = {
                            'column': row.COLUMN_NAME,
                            'ref_table': row.FOREIGN_TABLE_NAME,
                            'ref_column': row.FOREIGN_COLUMN_NAME
                        }
                        foreign_keys.append(fk_info)
                    
                    tables[table_name] = {
                        'columns': columns,
                        'primary_keys': primary_keys,
                        'foreign_keys': foreign_keys
                    }
        
        return tables
    
    def generate_create_table_sql(self, table_name, table_info):
        """
        生成CREATE TABLE SQL语句
        """
        lines = [f"CREATE TABLE {table_name} ("]
        
        # 添加字段定义
        for i, col in enumerate(table_info['columns']):
            # 检查是否是主键
            is_primary = col['name'] in table_info['primary_keys']
            
            # 构建字段定义
            field_def = f"    {col['name']} {col['type']}"
            
            # 添加IDENTITY标记（如果是主键且是int类型）
            if is_primary and col['type'] == 'INT':
                field_def += " PRIMARY KEY IDENTITY"
            else:
                # 添加约束
                if col['constraints']:
                    field_def += f" {col['constraints']}"
            
            # 添加逗号（除了最后一行）
            if i < len(table_info['columns']) - 1 or table_info['foreign_keys']:
                field_def += ","
            
            lines.append(field_def)
        
        # 添加外键约束
        for i, fk in enumerate(table_info['foreign_keys']):
            fk_def = f"    FOREIGN KEY ({fk['column']}) REFERENCES {fk['ref_table']}({fk['ref_column']})"
            if i < len(table_info['foreign_keys']) - 1:
                fk_def += ","
            lines.append(fk_def)
        
        lines.append(");")
        
        return '\n'.join(lines)
    
    def update_spec_file(self, actual_tables):
        """
        更新Spec文件
        """
        print("\n" + "=" * 80)
        print("更新Spec文件")
        print("=" * 80)
        
        with open(self.spec_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 找到数据库结构部分
        # 匹配 ## 4. 数据库结构 到下一个 ## 之间的内容
        pattern = r'(## 4\. 数据库结构.*?)(\n## 5\.|$)'
        match = re.search(pattern, content, re.DOTALL)
        
        if not match:
            print("✗ 未找到数据库结构部分")
            return False
        
        # 生成新的数据库结构内容
        new_db_structure = "\n## 4. 数据库结构（基于现有项目）\n\n"
        
        # 表名到中文描述的映射
        table_descriptions = {
            'User': '用户表',
            'Role': '角色表',
            'Permission': '权限表',
            'UserRole': '用户角色关联表',
            'RolePermission': '角色权限关联表',
            'Merchant': '商户表',
            'Plot': '地块表',
            'Contract': '合同表',
            'ContractPlot': '合同地块关联表',
            'ElectricityMeter': '电表信息表',
            'WaterMeter': '水表信息表',
            'ContractElectricityMeter': '合同电表关联表',
            'ContractWaterMeter': '合同水表关联表',
            'MeterChangeRecord': '换表记录表',
            'UtilityReading': '水电费抄表记录表',
            'Receivable': '应收账款表',
            'Payable': '应付账款表',
            'CashFlow': '现金流水表',
            'CollectionRecord': '收款记录表',
            'PaymentRecord': '付款记录表',
            'Scale': '磅秤信息表',
            'ScaleRecord': '过磅记录表',
            'Sys_Dictionary': '系统字典表',
            'FileAttachment': '文件管理表',
            'ExpenseType': '费用类型表'
        }
        
        # 按顺序生成表定义
        table_order = [
            'User', 'Role', 'Permission', 'UserRole', 'RolePermission',
            'Merchant', 'Plot', 'Contract', 'ContractPlot',
            'ElectricityMeter', 'WaterMeter', 'ContractElectricityMeter', 'ContractWaterMeter',
            'MeterChangeRecord', 'UtilityReading',
            'Receivable', 'Payable', 'CashFlow', 'CollectionRecord', 'PaymentRecord',
            'Scale', 'ScaleRecord',
            'Sys_Dictionary', 'FileAttachment', 'ExpenseType'
        ]
        
        index = 1
        for table_name in table_order:
            if table_name in actual_tables:
                table_info = actual_tables[table_name]
                description = table_descriptions.get(table_name, table_name)
                
                new_db_structure += f"### 4.{index} {description} ({table_name})\n\n"
                new_db_structure += "```sql\n"
                new_db_structure += self.generate_create_table_sql(table_name, table_info)
                new_db_structure += "\n```\n\n"
                
                index += 1
        
        # 替换原内容
        new_content = content[:match.start()] + new_db_structure + content[match.end():]
        
        # 写入文件
        with open(self.spec_file, 'w', encoding='utf-8') as f:
            f.write(new_content)
        
        print(f"✓ Spec文件已更新")
        return True
    
    def run(self):
        """
        执行更新流程
        """
        print("\n开始更新Spec文件...")
        
        # 备份Spec文件
        self.backup_spec()
        
        # 获取实际数据库结构
        actual_tables = self.get_actual_table_structure()
        
        # 更新Spec文件
        success = self.update_spec_file(actual_tables)
        
        if success:
            print("\n" + "=" * 80)
            print("✓ Spec文件更新完成")
            print("=" * 80)
            print(f"备份文件: {self.backup_file}")
        else:
            print("\n" + "=" * 80)
            print("✗ Spec文件更新失败")
            print("=" * 80)
        
        return success


if __name__ == "__main__":
    app = create_app()
    
    with app.app_context():
        updater = SpecUpdater()
        success = updater.run()