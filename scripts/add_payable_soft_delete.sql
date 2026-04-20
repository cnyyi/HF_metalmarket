-- Payable 表新增软删除字段
-- 2026-04-20

-- IsActive: 1=有效, 0=已删除 (BIT NOT NULL DEFAULT 1)
ALTER TABLE Payable ADD IsActive BIT NOT NULL DEFAULT 1;

-- DeletedBy: 删除操作人UserID
ALTER TABLE Payable ADD DeletedBy INT NULL;

-- DeletedAt: 删除时间
ALTER TABLE Payable ADD DeletedAt DATETIME NULL;

-- DeleteReason: 删除原因
ALTER TABLE Payable ADD DeleteReason NVARCHAR(500) NULL;
