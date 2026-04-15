"""创建 ReceivableDetail 表的脚本"""
from utils.database import DBConnection

def create_receivable_detail():
    with DBConnection() as conn:
        cursor = conn.cursor()
        
        # 检查表是否已存在
        cursor.execute("SELECT * FROM sys.tables WHERE name = 'ReceivableDetail'")
        if cursor.fetchone():
            print("表 ReceivableDetail 已存在，跳过创建")
            return
        
        cursor.execute("""
            CREATE TABLE ReceivableDetail (
                DetailID       INT IDENTITY(1,1) PRIMARY KEY,
                ReceivableID   INT NOT NULL FOREIGN KEY REFERENCES Receivable(ReceivableID),
                ReadingID      INT NOT NULL FOREIGN KEY REFERENCES UtilityReading(ReadingID),
                CreateTime     DATETIME DEFAULT GETDATE(),
                CONSTRAINT UQ_ReceivableDetail_Unique UNIQUE (ReceivableID, ReadingID)
            )
        """)
        conn.commit()
        print("表 ReceivableDetail 创建成功")

if __name__ == '__main__':
    create_receivable_detail()
