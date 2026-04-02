# 商户模型
import datetime


class Merchant:
    """
    商户模型类，用于表示数据库中的Merchant表
    """
    def __init__(self, merchant_id=None, merchant_name=None, legal_person=None, contact_person=None,
                 phone=None, address=None, merchant_type=None, business_license=None,
                 tax_registration=None, description=None, status=None, create_time=None, update_time=None,
                 business_type=None):
        self.merchant_id = merchant_id
        self.merchant_name = merchant_name
        self.legal_person = legal_person
        self.contact_person = contact_person
        self.phone = phone
        self.address = address
        self.merchant_type = merchant_type
        self.business_license = business_license
        self.tax_registration = tax_registration
        self.description = description
        self.status = status or '正常'
        self.create_time = create_time or datetime.datetime.now()
        self.update_time = update_time
        self.business_type = business_type
    
    def __repr__(self):
        return f"<Merchant(merchant_id={self.merchant_id}, merchant_name='{self.merchant_name}', legal_person='{self.legal_person}')>"
