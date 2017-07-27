from sqlalchemy import Column, Date, ForeignKey, Integer, String, Table, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()

# association table
extra_okveds = Table('extra_okveds', Base.metadata,
                     Column('doc_id', ForeignKey('rsmp_docs.id'), primary_key=True),
                     Column('okved_id', ForeignKey('rsmp_okved.id'), primary_key=True))


class RSMPFile(Base):
    """
    Сведения о файле и отправителе
    """

    __tablename__ = 'rsmp_files'
    id = Column(Integer, primary_key=True)

    file_id = Column(String(255))
    file_format_ver = Column(String(5))
    info_type = Column(String(50))
    program_ver = Column(String(40))
    docs_count = Column(Integer)

    sender_name = Column(String(60))
    sender_surname = Column(String(60))
    sender_middlename = Column(String(60))
    sender_position = Column(String(100))
    sender_tel = Column(String(20))
    sender_email = Column(String(45))


class RSMPDocument(Base):
    """
    Состав и структура документ
    """

    __tablename__ = 'rsmp_docs'

    id = Column(Integer, primary_key=True)
    file_id = Column(Integer, ForeignKey('rsmp_files.id'))
    doc_id = Column(String(36))
    doc_create_date = Column(Date)
    msp_input_date = Column(Date)
    subj_type = Column(String(1))
    subj_cat = Column(String(1))
    novelity = Column(String(1))

    # many to many RSMPDocument <-> OKVED
    extra_okved = relationship('OKVED', secondary=extra_okveds, back_populates='docs')


class LegalEntity(Base):
    """
    Сведения о юридическом лице, включенном в реестр МСП
    """
    __tablename__ = 'rsmp_legal_entities'

    id = Column(Integer, primary_key=True)

    doc_id = Column(Integer, ForeignKey('rsmp_docs.id'))
    org_full_name = Column(String(1000))
    org_short_name = Column(String(500))
    org_inn = Column(String(10))


class IndividualEnterpeneur(Base):
    """
    Сведения об индивидуальном предпринимателе, включенном в реестр МСП
    """
    __tablename__ = 'rsmp_individual_enterpeneurs'

    id = Column(Integer, primary_key=True)

    doc_id = Column(Integer, ForeignKey('rsmp_docs.id'))
    ip_name = Column(String(60))
    ip_surname = Column(String(60))
    ip_middlename = Column(String(60))
    ip_inn = Column(String(12))


class Region(Base):
    """
    Таблица регионов
    """
    __tablename__ = 'rsmp_region'

    id = Column(Integer, primary_key=True)
    region = Column(String(2))
    type = Column(String(50))
    name = Column(String(255))


class Address(Base):
    """
    Таблица адресов (районов, городов и населенных пунктов)
    """
    __tablename__ = 'rsmp_address'

    id = Column(Integer, primary_key=True)
    type = Column(String(50))
    name = Column(String(255))


class Location(Base):
    """
    Сведения о месте нахождения юридического лица / месте жительства индивидуального предпринимателя
    """
    __tablename__ = 'rsmp_location'
    id = Column(Integer, primary_key=True)

    doc_id = Column(Integer, ForeignKey('rsmp_docs.id'))

    region_id = Column(Integer, ForeignKey('rsmp_region.id'))
    district_id = Column(Integer, ForeignKey('rsmp_address.id'))
    city_id = Column(Integer, ForeignKey('rsmp_address.id'))
    locality_id = Column(Integer, ForeignKey('rsmp_address.id'))


class OKVED(Base):
    """
    Сведения о видах экономической деятельности по Общероссийскому классификатору видов экономической деятельности
    """

    __tablename__ = 'rsmp_okved'

    id = Column(Integer, primary_key=True)

    doc_id = Column(Integer, ForeignKey('rsmp_docs.id'))

    okved_code = Column(String(8))
    okved_name = Column(String(1000))
    okved_ver = Column(String(4))

    # many to many OKVED <-> RSMPDocument
    docs = relationship('RSMPDocument', secondary=extra_okveds, back_populates='extra_okved')


class License(Base):
    """
    Сведения о лицензиях, выданных субъекту МСП
    """

    __tablename__ = 'rsmp_license'

    id = Column(Integer, primary_key=True)

    doc_id = Column(Integer, ForeignKey('rsmp_docs.id'))

    lic_series = Column(String(10))
    lic_activity = Column(JSON)
    # lic_activity = Column(String(1000))
    lic_address = Column(JSON)
    # lic_address = Column(String(500))
    lic_num = Column(String(100))
    lic_type = Column(String(10))
    lic_date = Column(Date)
    lic_start_date = Column(Date)
    lic_end_date = Column(Date)
    licensor = Column(String(500))
    lic_stop_date = Column(Date)
    org_stoped_lic = Column(String(500))


class Production(Base):
    """
    Сведения о производимой субъектом МСП продукции
    """

    __tablename__ = 'rsmp_production'

    id = Column(Integer, primary_key=True)

    doc_id = Column(Integer, ForeignKey('rsmp_docs.id'))

    prod_code = Column(String(18))
    prod_name = Column(String(1000))
    prod_innov = Column(String(1))


class Partnership(Base):
    """
    Сведения о включении субъекта МСП в реестры программ партнерства
    """

    __tablename__ = 'rsmp_partnerships'

    id = Column(Integer, primary_key=True)

    doc_id = Column(Integer, ForeignKey('rsmp_docs.id'))

    partner_name = Column(String(1000))
    partner_inn = Column(String(10))
    partner_contract_num = Column(String(60))
    partner_contract_date = Column(Date)


class Contract(Base):
    """
    Сведения о наличии у субъекта МСП в предшествующем календарном году контрактов, заключенных
    в соответствии с Федеральным законом от 5 апреля 2013 года №44-ФЗ
    """

    __tablename__ = 'rsmp_contracts'

    id = Column(Integer, primary_key=True)

    doc_id = Column(Integer, ForeignKey('rsmp_docs.id'))

    contract_client_name = Column(String(1000))
    contract_client_inn = Column(String(10))
    contract_subj = Column(String(1000))
    contract_num = Column(String(60))
    contract_date = Column(Date)


class Agreement(Base):
    """
    Сведения о наличии у субъекта МСП в предшествующем календарном году договоров, заключенных
    в соответствии с Федеральным законом от 18 июля 2011 года №223-ФЗ
    """

    __tablename__ = 'rsmp_agreements'

    id = Column(Integer, primary_key=True)

    doc_id = Column(Integer, ForeignKey('rsmp_docs.id'))

    dog_client_name = Column(String(1000))
    dog_client_inn = Column(String(10))
    dog_subj = Column(String(1000))
    dog_num = Column(String(60))
    dog_date = Column(Date)
