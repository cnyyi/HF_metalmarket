"""从 .mdb 文件头直接提取 Access 密码"""
import struct

mdb_path = r'D:\BaiduSyncdisk\HF_metalmarket\Database.mdb'

with open(mdb_path, 'rb') as f:
    data = f.read()

# 检查 Jet 版本
# Jet 3 (Access 97): 偏移 0x00 = 0x00, 密码偏移 0x42
# Jet 4 (Access 2000-2003): 偏移 0x14-0x17 = 版本号, 密码偏移 0x42 (40字节, Unicode)

# 检查是否是 Jet 4 格式
jet4_marker = data[0x14:0x18]
print(f"Jet version bytes at 0x14: {jet4_marker.hex()}")

# Access 2000/2003 (Jet 4) 密码在偏移 0x42, 长 40 字节 (Unicode, 每字符2字节 = 最多20字符)
# XOR key 也是 40 字节

# Jet 4 XOR key (Access 2000/2003)
xor_key = bytes([
    0x86, 0xFB, 0xEC, 0x37, 0x5D, 0x44, 0x9C, 0xFA,
    0xC6, 0x5E, 0x28, 0xE6, 0x13, 0xB6, 0x8A, 0x60,
    0x54, 0x94, 0x7B, 0x37, 0x86, 0xFB, 0xEC, 0x37,
    0x5D, 0x44, 0x9C, 0xFA, 0xC6, 0x5E, 0x28, 0xE6,
    0x13, 0xB6, 0x8A, 0x60, 0x54, 0x94, 0x7B, 0x37,
])

# 读取加密密码
encrypted = data[0x42:0x42+40]
print(f"Encrypted password bytes: {encrypted.hex()}")

# 解密
decrypted = bytes([encrypted[i] ^ xor_key[i] for i in range(40)])

# 提取 Unicode 字符 (每2字节一个字符, 小端)
password_chars = []
for i in range(0, 40, 2):
    char_val = decrypted[i] | (decrypted[i+1] << 8)
    if char_val == 0:
        break
    if 0x20 <= char_val < 0x7f:
        password_chars.append(chr(char_val))
    elif 0x4e00 <= char_val <= 0x9fff:  # CJK
        password_chars.append(chr(char_val))
    else:
        password_chars.append(f'[0x{char_val:04x}]')

password = ''.join(password_chars)
print(f"Decrypted password (Jet4 XOR): '{password}'")

# 另一种方法：Access 2003 使用了不同的加密方式
# 尝试直接读取非 Unicode 模式 (Jet 3 兼容)
# 在 0x62 处有一个标志字节, 如果为 0x9D 表示使用了新加密
flag_byte = data[0x62]
print(f"Encryption flag at 0x62: 0x{flag_byte:02x}")

# 如果 flag == 0x9D, 说明密码是简单的 XOR
# 如果 flag == 0, 可能没有密码（但我们知道有密码）

# 尝试另一种解密：有些版本的 key 不同
# Access 2003 可能使用另一个 key
xor_key_2003 = bytes([
    0x13, 0xEC, 0x61, 0x37, 0x5D, 0x44, 0x9C, 0xFA,
    0xC6, 0x5E, 0x28, 0xE6, 0x13, 0xB6, 0x8A, 0x60,
    0x54, 0x94, 0x7B, 0x37, 0x13, 0xEC, 0x61, 0x37,
    0x5D, 0x44, 0x9C, 0xFA, 0xC6, 0x5E, 0x28, 0xE6,
    0x13, 0xB6, 0x8A, 0x60, 0x54, 0x94, 0x7B, 0x37,
])

decrypted_2003 = bytes([encrypted[i] ^ xor_key_2003[i] for i in range(40)])
password_chars_2003 = []
for i in range(0, 40, 2):
    char_val = decrypted_2003[i] | (decrypted_2003[i+1] << 8)
    if char_val == 0:
        break
    if 0x20 <= char_val < 0x7f:
        password_chars_2003.append(chr(char_val))
    elif 0x4e00 <= char_val <= 0x9fff:
        password_chars_2003.append(chr(char_val))
    else:
        password_chars_2003.append(f'[0x{char_val:04x}]')

password_2003 = ''.join(password_chars_2003)
print(f"Decrypted password (2003 key): '{password_2003}'")

# 再试试单字节模式（Jet 3 / Access 97）
# Jet 3 密码在 0x42, 20字节, 单字节字符
jet3_key = bytes([
    0x86, 0xFB, 0xEC, 0x37, 0x5D, 0x44, 0x9C, 0xFA,
    0xC6, 0x5E, 0x28, 0xE6, 0x13, 0xB6, 0x8A, 0x60,
    0x54, 0x94, 0x7B, 0x37,
])

encrypted_20 = data[0x42:0x42+20]
decrypted_jet3 = bytes([encrypted_20[i] ^ jet3_key[i] for i in range(20)])
pwd_jet3 = []
for c in decrypted_jet3:
    if c == 0:
        break
    if 0x20 <= c < 0x7f:
        pwd_jet3.append(chr(c))
    else:
        pwd_jet3.append(f'[0x{c:02x}]')
print(f"Decrypted password (Jet3 single-byte): '{''.join(pwd_jet3)}'")

# 打印原始数据帮助分析
print(f"\nRaw hex at 0x42 (40 bytes): {encrypted.hex()}")
print(f"Raw hex at 0x00-0x08: {data[0:8].hex()}")
print(f"File size: {len(data)} bytes")
