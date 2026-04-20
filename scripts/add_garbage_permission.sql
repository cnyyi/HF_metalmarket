-- 垃圾清运管理权限补充
-- 执行时间：2026-04-19

-- 1. 插入 garbage_manage 权限
INSERT INTO Permission (PermissionName, PermissionCode, Description, ModuleName, IsActive, CreateTime)
VALUES (N'垃圾清运管理', 'garbage_manage', N'管理垃圾清运记录的查看、新增、编辑、删除', N'市场管理', 1, GETDATE());

-- 2. 获取刚插入的 PermissionID，赋给管理员角色（RoleID=1020）
INSERT INTO RolePermission (RoleID, PermissionID)
SELECT 1020, PermissionID FROM Permission WHERE PermissionCode = 'garbage_manage';

-- 3. 赋给工作人员角色（RoleID=1021）
INSERT INTO RolePermission (RoleID, PermissionID)
SELECT 1021, PermissionID FROM Permission WHERE PermissionCode = 'garbage_manage';

-- 验证
SELECT r.RoleName, p.PermissionName, p.PermissionCode
FROM Permission p
JOIN RolePermission rp ON p.PermissionID = rp.PermissionID
JOIN Role r ON rp.RoleID = r.RoleID
WHERE p.PermissionCode = 'garbage_manage';
