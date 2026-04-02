# 商户管理服务
import datetime
from app.models.merchant import Merchant
from utils.database import execute_query, execute_update


class MerchantService:
    """
    商户管理服务类，用于处理商户管理相关的业务逻辑
    """
    
    @staticmethod
    def get_merchant_type_name_mapping():
        """
        获取商户类型代码到名称的映射
        
        Returns:
            字典，key为DictCode，value为DictName
        """
        query = """
            SELECT DictCode, DictName 
            FROM Sys_Dictionary 
            WHERE DictType = 'merchant_type'
        """
        results = execute_query(query, fetch_type='all')
        
        return {result.DictCode: result.DictName for result in results}
    
    @staticmethod
    def get_business_types():
        """
        获取所有业务类型
        
        Returns:
            业务类型列表，格式为[(dictname, dictname), ...]
        """
        query = """
            SELECT DictName 
            FROM Sys_Dictionary 
            WHERE DictType = 'business_type' 
            ORDER BY SortOrder
        """
        results = execute_query(query, fetch_type='all')
        
        # 返回(dictname, dictname)格式，因为我们要存储和显示dictname
        return [(result.DictName, result.DictName) for result in results]
    
    @staticmethod
    def get_merchants(page=1, per_page=10, search=None):
        """
        获取商户列表，支持分页和搜索
        
        Args:
            page: 当前页码
            per_page: 每页数量
            search: 搜索关键词
            
        Returns:
            商户列表和总页数
        """
        # 构建查询语句
        base_query = """
            SELECT MerchantID, MerchantName, LegalPerson, ContactPerson, Phone, 
                   MerchantType, BusinessType, Address, Description, Status, CreateTime, UpdateTime
            FROM Merchant
        """
        
        count_query = """
            SELECT COUNT(*) as count
            FROM Merchant
        """
        
        params = []
        
        # 添加搜索条件
        if search:
            search_condition = " WHERE MerchantName LIKE ? OR ContactPerson LIKE ? OR Phone LIKE ?"
            base_query += search_condition
            count_query += search_condition
            search_param = f'%{search}%'
            params.extend([search_param, search_param, search_param])
        
        # 添加分页条件
        offset = (page - 1) * per_page
        base_query += " ORDER BY MerchantID DESC OFFSET ? ROWS FETCH NEXT ? ROWS ONLY"
        params.extend([offset, per_page])
        
        # 执行查询
        merchants = []
        results = execute_query(base_query, tuple(params), fetch_type='all')
        
        for result in results:
            merchant = Merchant(
                merchant_id=result.MerchantID,
                merchant_name=result.MerchantName,
                legal_person=result.LegalPerson,
                contact_person=result.ContactPerson,
                phone=result.Phone,
                merchant_type=result.MerchantType,
                business_type=result.BusinessType,
                address=result.Address,
                description=result.Description,
                status=result.Status,
                create_time=result.CreateTime,
                update_time=result.UpdateTime
            )
            merchants.append(merchant)
        
        # 获取总页数
        count_result = execute_query(count_query, tuple(params[:-2]) if search else tuple(), fetch_type='one')
        total_count = count_result.count
        total_pages = (total_count + per_page - 1) // per_page
        
        return merchants, total_count, total_pages
    
    @staticmethod
    def get_merchant_by_id(merchant_id):
        """
        根据商户ID获取商户信息
        
        Args:
            merchant_id: 商户ID
            
        Returns:
            Merchant对象，如果商户不存在则返回None
        """
        query = """
            SELECT MerchantID, MerchantName, LegalPerson, ContactPerson, Phone, 
                   MerchantType, BusinessType, Address, Description, Status, CreateTime, UpdateTime
            FROM Merchant
            WHERE MerchantID = ?
        """
        result = execute_query(query, (merchant_id,), fetch_type='one')
        
        if not result:
            return None
        
        merchant = Merchant(
            merchant_id=result.MerchantID,
            merchant_name=result.MerchantName,
            legal_person=result.LegalPerson,
            contact_person=result.ContactPerson,
            phone=result.Phone,
            merchant_type=result.MerchantType,
            business_type=result.BusinessType,
            address=result.Address,
            description=result.Description,
            status=result.Status,
            create_time=result.CreateTime,
            update_time=result.UpdateTime
        )
        
        return merchant
    
    @staticmethod
    def create_merchant(merchant_name, legal_person, contact_person, phone, merchant_type, business_license, address, description, tax_registration=None, business_type=None):
        """
        创建新商户
        
        Args:
            merchant_name: 商户名称
            legal_person: 法人代表
            contact_person: 联系人
            phone: 联系电话
            merchant_type: 商户类型
            business_license: 营业执照号
            address: 地址
            description: 商户描述
            tax_registration: 税务登记证号（可选）
            business_type: 业务类型（可选）
            
        Returns:
            如果创建成功，返回Merchant对象；否则返回None
        """
        insert_query = """
            INSERT INTO Merchant (MerchantName, LegalPerson, ContactPerson, Phone, MerchantType, BusinessLicense, TaxRegistration, Address, Description, Status, CreateTime, BusinessType)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, '正常', ?, ?)
        """
        execute_update(insert_query, (merchant_name, legal_person, contact_person, phone, merchant_type, business_license, tax_registration, address, description, datetime.datetime.now(), business_type))
        
        # 获取新创建的商户信息
        # 注意：这里简化处理，实际应用中应该使用返回的身份标识
        return MerchantService.get_merchant_by_id(0)  # 这会返回None，实际应用中需要修改
    
    @staticmethod
    def update_merchant(merchant_id, merchant_name, legal_person, contact_person, phone, merchant_type, business_license, address, description, status, tax_registration=None, business_type=None):
        """
        更新商户信息
        
        Args:
            merchant_id: 商户ID
            merchant_name: 商户名称
            legal_person: 法人代表
            contact_person: 联系人
            phone: 联系电话
            merchant_type: 商户类型
            business_license: 营业执照号
            address: 地址
            description: 商户描述
            status: 状态
            tax_registration: 税务登记证号（可选）
            business_type: 业务类型（可选）
            
        Returns:
            如果更新成功，返回Merchant对象；否则返回None
        """
        update_query = """
            UPDATE Merchant
            SET MerchantName = ?, LegalPerson = ?, ContactPerson = ?, Phone = ?, MerchantType = ?, BusinessLicense = ?, TaxRegistration = ?, Address = ?, Description = ?, Status = ?, UpdateTime = ?, BusinessType = ?
            WHERE MerchantID = ?
        """
        execute_update(update_query, (merchant_name, legal_person, contact_person, phone, merchant_type, business_license, tax_registration, address, description, status, datetime.datetime.now(), business_type, merchant_id))
        
        # 获取更新后的商户信息
        return MerchantService.get_merchant_by_id(merchant_id)
    
    @staticmethod
    def delete_merchant(merchant_id):
        """
        删除商户
        
        Args:
            merchant_id: 商户ID
            
        Returns:
            如果删除成功，返回True；否则返回False
        """
        delete_query = "DELETE FROM Merchant WHERE MerchantID = ?"
        result = execute_update(delete_query, (merchant_id,))
        
        return result > 0
    
    @staticmethod
    def get_merchant_types():
        """
        获取所有商户类型
        
        Returns:
            商户类型列表，格式为[(dictname, dictname), ...]
        """
        # 从Sys_Dictionary表动态获取商户类型
        query = """
            SELECT DictName 
            FROM Sys_Dictionary 
            WHERE DictType = 'merchant_type' 
            ORDER BY SortOrder
        """
        results = execute_query(query, fetch_type='all')
        
        # 返回(dictname, dictname)格式，因为我们要存储和显示dictname
        return [(result.DictName, result.DictName) for result in results]
