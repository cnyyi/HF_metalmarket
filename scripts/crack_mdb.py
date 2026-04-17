"""尝试打开带密码的 Access .mdb 文件"""
import pyodbc

mdb_path = r'D:\BaiduSyncdisk\HF_metalmarket\Database.mdb'
driver = 'Microsoft Access Driver (*.mdb, *.accdb)'

# 常见密码列表
common_passwords = [
    '',           # 空密码
    'admin',
    '123456',
    'password',
    '123',
    '1234',
    '12345',
    '123456789',
    'hf',
    'hfm',
    'hongfa',
    'hongfa123',
    'hf123',
    'hfm123',
    'hfmetal',
    'metal',
    'market',
    'db',
    'mdb',
    'access',
    '1',
    '11',
    '111',
    '000000',
    '888888',
    '666666',
    'admin123',
    'test',
    'root',
    'sa',
    'sql',
    'database',
    'metalmarket',
    'hfmetalmarket',
    'hf2018',
    'hf2019',
    'hf2020',
    'hf2021',
    'hf2022',
    'hf2023',
    'hf2024',
    'hf2025',
    'hf2026',
]

for pwd in common_passwords:
    try:
        if pwd == '':
            conn_str = f'DRIVER={{{driver}}};DBQ={mdb_path};'
        else:
            conn_str = f'DRIVER={{{driver}}};DBQ={mdb_path};PWD={pwd};'
        conn = pyodbc.connect(conn_str, timeout=3)
        print(f'SUCCESS! Password: "{pwd}"')
        # 读取表列表
        cursor = conn.cursor()
        tables = cursor.tables(tableType='TABLE')
        table_names = [t.table_name for t in tables if not t.table_name.startswith('MSys')]
        print(f'Tables ({len(table_names)}): {table_names[:20]}')
        conn.close()
        break
    except pyodbc.Error as e:
        error_msg = str(e)
        if 'password' in error_msg.lower() or 'not a valid password' in error_msg.lower() or 'invalid' in error_msg.lower():
            pass  # 密码错误，继续
        else:
            print(f'Error with pwd="{pwd}": {error_msg[:100]}')
else:
    print('Common passwords all failed.')
