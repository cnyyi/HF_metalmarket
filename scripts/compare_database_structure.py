# 数据库结构对比和Spec更新脚本

import sys
import os
import re
import datetime
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app
from utils.database import execute_query
import pyodbc
from config import Config


class DatabaseStructureComparator:
    """
    数据库结构对比器
    """
    
    def __init__(self):
        self.connection_string = Config.ODBC_CONNECTION_STRING
        self.spec_file = 'd:\\BaiduSyncdisk\\HF_metalmarket\\.trae\\specs\\generate-spec\\spec.md'
        self.differences = []
        
    def get_actual_table_structure(self):
        """
        获取实际数据库表结构
        """
        print("=" * 80)
        print("获取实际数据库表结构")
        print("=" * 80)
        
        tables = {}
        
        with pyodbc.connect(self.connection_string) as conn:
            with conn.cursor() as cursor:
                # 获取所有表名
                cursor.execute("""
                    SELECT TABLE_NAME 
                    FROM INFORMATION_SCHEMA.TABLES 
                    WHERE TABLE_TYPE = 'BASE TABLE' 
                    AND TABLE_SCHEMA = 'dbo'
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
                        
                        col_info = {
                            'name': row.COLUMN_NAME,
                            'type': data_type,
                            'nullable': row.IS_NULLABLE == 'YES',
                            'default': row.COLUMN_DEFAULT,
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
    
    def parse_spec_tables(self):
        """
        解析Spec文件中的表结构定义
        """
        print("\n" + "=" * 80)
        print("解析Spec文件中的表结构定义")
        print("=" * 80)
        
        with open(self.spec_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        tables = {}
        
        # 使用正则表达式提取CREATE TABLE语句
        # 匹配模式：### 4.X 表名 (TableName) 后面跟着 ```sql ... CREATE TABLE ...
        pattern = r'### 4\.\d+\s+(.+?)\s*[\(（](.+?)[\)）]\s*\n+```sql\s+(CREATE TABLE\s+(.+?)\s*\((.+?)\);)'
        matches = re.finditer(pattern, content, re.DOTALL | re.IGNORECASE)
        
        for match in matches:
            table_desc = match.group(1).strip()
            table_name = match.group(4).strip().replace('[', '').replace(']', '')
            create_statement = match.group(3)
            columns_text = match.group(5)
            
            print(f"\n找到表定义: {table_name} ({table_desc})")
            
            # 解析字段定义
            columns = []
            lines = columns_text.split('\n')
            
            for line in lines:
                line = line.strip()
                if not line or line.startswith('FOREIGN KEY') or line.startswith('CREATE INDEX'):
                    continue
                
                # 移除末尾逗号
                line = line.rstrip(',')
                
                # 解析字段
                # 格式: FieldName DataType [CONSTRAINTS]
                parts = line.split()
                if len(parts) >= 2:
                    col_name = parts[0].replace('[', '').replace(']', '')
                    col_type = parts[1]
                    
                    # 处理带括号的类型
                    if '(' in col_type and ')' not in col_type:
                        # 类型定义跨多行，合并
                        for i in range(2, len(parts)):
                            col_type += ' ' + parts[i]
                            if ')' in parts[i]:
                                break
                    
                    col_info = {
                        'name': col_name,
                        'type': col_type.upper(),
                        'nullable': 'NOT NULL' not in line.upper(),
                        'definition': line
                    }
                    columns.append(col_info)
            
            tables[table_name] = {
                'description': table_desc,
                'columns': columns,
                'create_statement': create_statement
            }
        
        return tables
    
    def compare_structures(self, actual_tables, spec_tables):
        """
        对比实际数据库结构和Spec定义
        """
        print("\n" + "=" * 80)
        print("对比数据库结构差异")
        print("=" * 80)
        
        differences = []
        
        # 检查实际数据库中有但Spec中没有的表
        for table_name in actual_tables:
            if table_name not in spec_tables:
                diff = {
                    'type': 'missing_in_spec',
                    'table': table_name,
                    'message': f'表 {table_name} 存在于数据库中，但Spec文件中未定义'
                }
                differences.append(diff)
                print(f"\n⚠ {diff['message']}")
        
        # 检查Spec中有但实际数据库中没有的表
        for table_name in spec_tables:
            if table_name not in actual_tables:
                diff = {
                    'type': 'missing_in_database',
                    'table': table_name,
                    'message': f'表 {table_name} 在Spec文件中定义，但数据库中不存在'
                }
                differences.append(diff)
                print(f"\n⚠ {diff['message']}")
        
        # 对比共同存在的表的字段
        for table_name in actual_tables:
            if table_name in spec_tables:
                actual_table = actual_tables[table_name]
                spec_table = spec_tables[table_name]
                
                # 检查字段差异
                actual_columns = {col['name']: col for col in actual_table['columns']}
                spec_columns = {col['name']: col for col in spec_table['columns']}
                
                # 数据库中有但Spec中没有的字段
                for col_name in actual_columns:
                    if col_name not in spec_columns:
                        diff = {
                            'type': 'column_missing_in_spec',
                            'table': table_name,
                            'column': col_name,
                            'actual_type': actual_columns[col_name]['type'],
                            'message': f'表 {table_name} 的字段 {col_name} ({actual_columns[col_name]["type"]}) 存在于数据库中，但Spec文件中未定义'
                        }
                        differences.append(diff)
                        print(f"\n⚠ {diff['message']}")
                
                # Spec中有但数据库中没有的字段
                for col_name in spec_columns:
                    if col_name not in actual_columns:
                        diff = {
                            'type': 'column_missing_in_database',
                            'table': table_name,
                            'column': col_name,
                            'spec_type': spec_columns[col_name]['type'],
                            'message': f'表 {table_name} 的字段 {col_name} ({spec_columns[col_name]["type"]}) 在Spec文件中定义，但数据库中不存在'
                        }
                        differences.append(diff)
                        print(f"\n⚠ {diff['message']}")
        
        self.differences = differences
        return differences
    
    def generate_report(self, differences):
        """
        生成差异报告
        """
        print("\n" + "=" * 80)
        print("生成差异报告")
        print("=" * 80)
        
        report_file = 'd:\\BaiduSyncdisk\\HF_metalmarket\\docs\\database_structure_diff_report.md'
        
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write("# 数据库结构差异报告\n\n")
            f.write(f"生成时间: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            f.write("---\n\n")
            
            if not differences:
                f.write("✅ 数据库结构与Spec文件完全一致，没有发现差异。\n")
                print("✅ 没有发现差异")
            else:
                f.write(f"## 发现 {len(differences)} 处差异\n\n")
                
                # 按类型分组
                grouped_diffs = {}
                for diff in differences:
                    diff_type = diff['type']
                    if diff_type not in grouped_diffs:
                        grouped_diffs[diff_type] = []
                    grouped_diffs[diff_type].append(diff)
                
                for diff_type, diffs in grouped_diffs.items():
                    type_names = {
                        'missing_in_spec': 'Spec文件中缺失的表',
                        'missing_in_database': '数据库中缺失的表',
                        'column_missing_in_spec': 'Spec文件中缺失的字段',
                        'column_missing_in_database': '数据库中缺失的字段',
                        'column_type_mismatch': '字段类型不匹配'
                    }
                    
                    f.write(f"### {type_names.get(diff_type, diff_type)} ({len(diffs)} 处)\n\n")
                    
                    for diff in diffs:
                        f.write(f"- **{diff['table']}**")
                        if 'column' in diff:
                            f.write(f".{diff['column']}")
                        f.write(f": {diff['message']}\n")
                    
                    f.write("\n")
        
        print(f"\n差异报告已生成: {report_file}")
        return report_file
    
    def run(self):
        """
        执行对比流程
        """
        print("\n开始数据库结构对比...")
        
        # 获取实际数据库结构
        actual_tables = self.get_actual_table_structure()
        
        # 解析Spec文件
        spec_tables = self.parse_spec_tables()
        
        # 对比差异
        differences = self.compare_structures(actual_tables, spec_tables)
        
        # 生成报告
        report_file = self.generate_report(differences)
        
        return differences, report_file


if __name__ == "__main__":
    app = create_app()
    
    with app.app_context():
        comparator = DatabaseStructureComparator()
        differences, report_file = comparator.run()
        
        print("\n" + "=" * 80)
        print("对比完成")
        print("=" * 80)
        print(f"发现 {len(differences)} 处差异")
        print(f"报告文件: {report_file}")