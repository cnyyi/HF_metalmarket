# add_permission.py
import pyodbc

# 数据库连接信息
server = 'yyi.myds.me'
database = 'hf_metalmarket'
username = 'sa'
password = 'yyI.123456'

# 连接数据库
conn = pyodbc.connect('DRIVER={SQL Server};SERVER=' + server + ';DATABASE=' + database + ';UID=' + username + ';PWD=' + password)
cursor = conn.cursor()

# 添加垃圾清运管理权限
cursor.execute("""
    IF NOT EXISTS (SELECT * FROM Permission WHERE PermissionCode = N'garbage_manage')
    BEGIN
        INSERT INTO Permission (PermissionName, PermissionCode, Description, ModuleName, IsActive, CreateTime)
        VALUES (N'垃圾清运管理', N'garbage_manage', N'管理垃圾清运记录', N'运营管理', 1, GETDATE());
    END
""")

# 获取权限ID
cursor.execute("SELECT PermissionID FROM Permission WHERE PermissionCode = N'garbage_manage'")
permission_id = cursor.fetchone()[0]

# 为admin角色添加权限
cursor.execute("""
    IF NOT EXISTS (SELECT * FROM RolePermission WHERE RoleID = (SELECT RoleID FROM Role WHERE RoleCode = N'admin') AND PermissionID = ?)
    BEGIN
        INSERT INTO RolePermission (RoleID, PermissionID, CreateTime)
        VALUES ((SELECT RoleID FROM Role WHERE RoleCode = N'admin'), ?, GETDATE());
    END
""", (permission_id,))

# 为staff角色添加权限
cursor.execute("""
    IF NOT EXISTS (SELECT * FROM RolePermission WHERE RoleID = (SELECT RoleID FROM Role WHERE RoleCode = N'staff') AND PermissionID = ?)
    BEGIN
        INSERT INTO RolePermission (RoleID, PermissionID, CreateTime)
        VALUES ((SELECT RoleID FROM Role WHERE RoleCode = N'staff'), ?, GETDATE());
    END
""", (permission_id,))

# 提交并关闭连接
conn.commit()
cursor.close()
conn.close()

print("权限添加成功！")