"""
使用更全面的方法尝试恢复 Access .mdb 密码
方法：尝试所有可能的单字节 XOR key 组合
"""
import struct

mdb_path = r'D:\BaiduSyncdisk\HF_metalmarket\Database.mdb'

with open(mdb_path, 'rb') as f:
    data = f.read()

# 读取密码区域
encrypted = data[0x42:0x42+40]

# Jet 4 格式的 XOR key（最常用的几个版本）
keys = {
    'Access 2000': [
        0x86, 0xFB, 0xEC, 0x37, 0x5D, 0x44, 0x9C, 0xFA,
        0xC6, 0x5E, 0x28, 0xE6, 0x13, 0xB6, 0x8A, 0x60,
        0x54, 0x94, 0x7B, 0x37, 0x86, 0xFB, 0xEC, 0x37,
        0x5D, 0x44, 0x9C, 0xFA, 0xC6, 0x5E, 0x28, 0xE6,
        0x13, 0xB6, 0x8A, 0x60, 0x54, 0x94, 0x7B, 0x37,
    ],
    'Access 2003': [
        0x13, 0xEC, 0x61, 0x37, 0x5D, 0x44, 0x9C, 0xFA,
        0xC6, 0x5E, 0x28, 0xE6, 0x13, 0xB6, 0x8A, 0x60,
        0x54, 0x94, 0x7B, 0x37, 0x13, 0xEC, 0x61, 0x37,
        0x5D, 0x44, 0x9C, 0xFA, 0xC6, 0x5E, 0x28, 0xE6,
        0x13, 0xB6, 0x8A, 0x60, 0x54, 0x94, 0x7B, 0x37,
    ],
    'Access 2003 alt': [
        0xA7, 0xD1, 0x1E, 0x57, 0x5D, 0x44, 0x9C, 0xFA,
        0xC6, 0x5E, 0x28, 0xE6, 0x13, 0xB6, 0x8A, 0x60,
        0x54, 0x94, 0x7B, 0x37, 0xA7, 0xD1, 0x1E, 0x57,
        0x5D, 0x44, 0x9C, 0xFA, 0xC6, 0x5E, 0x28, 0xE6,
        0x13, 0xB6, 0x8A, 0x60, 0x54, 0x94, 0x7B, 0x37,
    ],
}

for name, key in keys.items():
    decrypted = bytes([encrypted[i] ^ key[i] for i in range(40)])
    
    # 提取 Unicode 字符
    chars = []
    for i in range(0, 40, 2):
        char_val = decrypted[i] | (decrypted[i+1] << 8)
        if char_val == 0:
            break
        chars.append(char_val)
    
    # 检查是否全是可打印字符
    all_printable = all((0x20 <= c < 0x7f) or (0x4e00 <= c <= 0x9fff) for c in chars)
    
    password = ''.join(chr(c) if (0x20 <= c < 0x7f) or (0x4e00 <= c <= 0x9fff) else f'[{c:04x}]' for c in chars)
    print(f"{name}: '{password}' (printable: {all_printable})")

# 也许密码只有几位，看看有没有规律
print(f"\nEncrypted hex: {encrypted.hex()}")

# 另一个思路：如果密码很短（1-4位），我们可以暴力尝试
# Access 的密码验证是通过 ODBC，直接暴力太慢
# 但我们可以尝试用 DAO 或 ADOX 来操作

# 试试用 comtypes 或 win32com
try:
    import win32com.client
    print("\nwin32com available, trying ADOX...")
    
    # 用 ADOX 打开（不需要密码也能读取结构）
    cat = win32com.client.Dispatch("ADOX.Catalog")
    
    # 尝试无密码打开
    try:
        conn_str = f"Provider=Microsoft.Jet.OLEDB.4.0;Data Source={mdb_path};"
        cat.ActiveConnection = conn_str
        print("Opened WITHOUT password!")
        for table in cat.Tables:
            if table.Type == 'TABLE':
                print(f"  Table: {table.Name}")
    except Exception as e:
        print(f"No password failed: {e}")
    
    # 尝试用密码
    try:
        conn_str = f"Provider=Microsoft.Jet.OLEDB.4.0;Data Source={mdb_path};Jet OLEDB:Database Password=123456;"
        cat.ActiveConnection = conn_str
        print("Opened with password '123456'!")
    except Exception as e:
        print(f"Password '123456' failed: {str(e)[:80]}")
        
except ImportError:
    print("\nwin32com not available")

# 也试试 ACE.OLEDB
try:
    import win32com.client
    print("\nTrying ACE.OLEDB.12.0...")
    
    # 先尝试无密码
    try:
        conn_str = f"Provider=Microsoft.ACE.OLEDB.12.0;Data Source={mdb_path};"
        cat = win32com.client.Dispatch("ADOX.Catalog")
        cat.ActiveConnection = conn_str
        print("Opened WITHOUT password via ACE!")
        for table in cat.Tables:
            if table.Type == 'TABLE':
                print(f"  Table: {table.Name}")
    except Exception as e:
        err_msg = str(e)
        print(f"ACE no password: {err_msg[:100]}")
        if 'password' in err_msg.lower() or 'invalid' in err_msg.lower():
            print("-> Database has password, confirmed")
except ImportError:
    pass
