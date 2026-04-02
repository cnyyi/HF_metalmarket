# 执行SQL脚本的工具脚本
import os
import sys
import pyodbc

# 将项目根目录添加到Python路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)

# 现在可以导入Config类了
from config import Config


def run_sql_script(script_path):
    """
    执行SQL脚本文件
    
    Args:
        script_path: SQL脚本文件路径
    """
    try:
        # 获取数据库连接字符串
        connection_string = Config.ODBC_CONNECTION_STRING
        
        # 读取SQL脚本
        with open(script_path, 'r', encoding='utf-8') as f:
            sql_script = f.read()
        
        # 连接数据库
        with pyodbc.connect(connection_string) as conn:
            conn.autocommit = True
            with conn.cursor() as cursor:
                print(f"正在执行SQL脚本: {script_path}")
                
                # 分割脚本为多个批处理（按GO命令）
                batches = sql_script.split('GO')
                
                # 执行每个批处理
                for i, batch in enumerate(batches):
                    batch = batch.strip()
                    if not batch:
                        continue
                    
                    print(f"执行批处理 {i+1}/{len(batches)}")
                    cursor.execute(batch)
                
                print("SQL脚本执行完成")
    except Exception as e:
        print(f"执行SQL脚本失败: {e}")
        raise


if __name__ == "__main__":
    # 执行SQL脚本
    script_path = os.path.join(project_root, "utils/update_database_to_nvarchar.sql")
    run_sql_script(script_path)
