from sqlalchemy import Column, Date, ForeignKey, Integer, String, Table, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()

# association table
extra_okveds = Table('extra_okveds', Base.metadata,
                     Column('doc_id', ForeignKey('rsmp_docs.id'), primary_key=True),
                     Column('okved_id', ForeignKey('rsmp_okved.id'), primary_key=True))


class File(Base):
    """
    hfhfh
    """
    __tablename__ = 'file'
    id = Column(Integer, primary_key=True)
    url = Column(String(255))


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
    Состав и структура документа
    """
    __tablename__ = 'rsmp_docs'

    id = Column(Integer, primary_key=True)
    file_id = Column(Integer, ForeignKey('rsmp_files.id'))
    file = relationship('RSMPFile', backref="docs")
    doc_id = Column(String(36))
    create_date = Column(Date)
    input_date = Column(Date)
    subj_type = Column(String(1))
    subj_cat = Column(String(1))
    novelty = Column(String(1))
    # Сведения о месте нахождения юридического лица / месте жительства индивидуального предпринимателя
    region_id = Column(Integer, ForeignKey('rsmp_region.id'))
    region = relationship('Region', backref="docs")
    district_id = Column(Integer, ForeignKey('rsmp_district.id'))
    district = relationship('District', backref="docs")
    city_id = Column(Integer, ForeignKey('rsmp_city.id'))
    city = relationship('City', backref="docs")
    locality_id = Column(Integer, ForeignKey('rsmp_locality.id'))
    locality = relationship('Locality', backref="docs")

    main_okved_id = Column(Integer, ForeignKey('rsmp_okved.id'))
    main_okved = relationship('OKVED', foreign_keys=[main_okved_id], backref="main_okved_docs")
    # many to many RSMPDocument <-> OKVED
    extra_okveds = relationship('OKVED', secondary=extra_okveds, backref='extra_okved_docs')


class Business(Base):
    """
    Сведения о юридическом лице, включенном в реестр МСП
    """
    __tablename__ = 'rsmp_businesses'

    id = Column(Integer, primary_key=True)

    doc_id = Column(Integer, ForeignKey('rsmp_docs.id'))
    doc = relationship('RSMPDocument', backref="businesses")
    full_name = Column(String(1000))
    short_name = Column(String(500))
    inn = Column(String(10))


class IndividualEnterpeneur(Base):
    """
    Сведения об индивидуальном предпринимателе, включенном в реестр МСП
    """
    __tablename__ = 'rsmp_individual_enterpeneurs'

    id = Column(Integer, primary_key=True)

    doc_id = Column(Integer, ForeignKey('rsmp_docs.id'))
    doc = relationship('RSMPDocument', backref="ies")
    name = Column(String(60))
    surname = Column(String(60))
    middlename = Column(String(60))
    inn = Column(String(12))


class Region(Base):
    """
    Таблица регионов
    """
    __tablename__ = 'rsmp_region'

    id = Column(Integer, primary_key=True)
    region = Column(String(2))
    type = Column(String(50))
    name = Column(String(255))


class District(Base):
    """
    Таблица районов
    """
    __tablename__ = 'rsmp_district'

    id = Column(Integer, primary_key=True)
    type = Column(String(50))
    name = Column(String(255))


class City(Base):
    """
    Таблица городов
    """
    __tablename__ = 'rsmp_city'

    id = Column(Integer, primary_key=True)
    type = Column(String(50))
    name = Column(String(255))


class Locality(Base):
    """
    Таблица населенных пунктов
    """
    __tablename__ = 'rsmp_locality'

    id = Column(Integer, primary_key=True)
    type = Column(String(50))
    name = Column(String(255))


class OKVED(Base):
    """
    Сведения о видах экономической деятельности по Общероссийскому классификатору видов экономической деятельности
    """
    __tablename__ = 'rsmp_okved'

    id = Column(Integer, primary_key=True)
    doc_id = Column(Integer, ForeignKey('rsmp_docs.id'))
    code = Column(String(8))
    name = Column(String(1000))
    ver = Column(String(4))


class License(Base):
    """
    Сведения о лицензиях, выданных субъекту МСП
    """
    __tablename__ = 'rsmp_license'

    id = Column(Integer, primary_key=True)

    doc_id = Column(Integer, ForeignKey('rsmp_docs.id'))
    doc = relationship('RSMPDocument', backref='licenses')
    series = Column(String(10))
    activity = Column(JSON)
    address = Column(JSON)
    num = Column(String(100))
    type = Column(String(10))
    date = Column(Date)
    start_date = Column(Date)
    end_date = Column(Date)
    org_started = Column(String(500))
    stop_date = Column(Date)
    org_stoped = Column(String(500))


class Production(Base):
    """
    Сведения о производимой субъектом МСП продукции
    """
    __tablename__ = 'rsmp_production'

    id = Column(Integer, primary_key=True)

    doc_id = Column(Integer, ForeignKey('rsmp_docs.id'))
    doc = relationship('RSMPDocument', backref="productions")
    code = Column(String(18))
    name = Column(String(1000))
    innov = Column(String(1))


class Partnership(Base):
    """
    Сведения о включении субъекта МСП в реестры программ партнерства
    """
    __tablename__ = 'rsmp_partnerships'

    id = Column(Integer, primary_key=True)

    doc_id = Column(Integer, ForeignKey('rsmp_docs.id'))
    doc = relationship('RSMPDocument', backref="partnerships")
    name = Column(String(1000))
    inn = Column(String(10))
    contract_num = Column(String(60))
    contract_date = Column(Date)


class Contract(Base):
    """
    Сведения о наличии у субъекта МСП в предшествующем календарном году контрактов, заключенных
    в соответствии с Федеральным законом от 5 апреля 2013 года №44-ФЗ
    """
    __tablename__ = 'rsmp_contracts'

    id = Column(Integer, primary_key=True)

    doc_id = Column(Integer, ForeignKey('rsmp_docs.id'))
    doc = relationship('RSMPDocument', backref="contracts")
    client_name = Column(String(1000))
    client_inn = Column(String(10))
    subj = Column(String(1000))
    num = Column(String(60))
    date = Column(Date)


class Agreement(Base):
    """
    Сведения о наличии у субъекта МСП в предшествующем календарном году договоров, заключенных
    в соответствии с Федеральным законом от 18 июля 2011 года №223-ФЗ
    """
    __tablename__ = 'rsmp_agreements'

    id = Column(Integer, primary_key=True)

    doc_id = Column(Integer, ForeignKey('rsmp_docs.id'))
    doc = relationship('RSMPDocument', backref="agreements")
    client_name = Column(String(1000))
    client_inn = Column(String(10))
    subj = Column(String(1000))
    num = Column(String(60))
    date = Column(Date)
