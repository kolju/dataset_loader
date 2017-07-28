import datetime
import re
import urllib.request
import xmltodict
import zipfile

from bs4 import BeautifulSoup as BS
from db import *
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy_utils import database_exists, create_database, drop_database

MAIN_URL = 'https://www.nalog.ru/opendata/7707329152-rsmp/'
NEED_TO_DOWNLOAD = False


def get_actual_url_and_filename():
    """
    Поиск названия актуального файла и ссылки на его скачивание
    """
    response = urllib.request.urlopen(MAIN_URL)
    soup = BS(response, "html.parser")
    data_url = '^' + MAIN_URL + 'data'
    urls = soup.findAll('a', attrs={'href': re.compile(data_url)})
    actual_url = list(map(lambda x: x.get('href'), urls))[0]
    file_name = actual_url.split('/')[-1]
    return actual_url, file_name


def download_actual_file():
    """
    Скачивание актуального файла
    """
    actual_url, file_name = get_actual_url_and_filename()
    if NEED_TO_DOWNLOAD:
        actual_file = urllib.request.URLopener()
        actual_file.retrieve(actual_url, file_name)


def get_or_create(session, model, **kwargs):
    instance = session.query(model).filter_by(**kwargs).first()
    if not instance:
        instance = model(**kwargs)
        session.add(instance)
    return instance


def date_transform(str_date):
    if not str_date:
        return None
    else:
        return datetime.datetime.strptime(str_date, '%d.%m.%Y')


def get_or_create_extra_okved(session, data, doc):
    okved_code = data.get('@КодОКВЭД', None)
    okved_name = data.get('@НаимОКВЭД', None)
    okved_ver = data.get('@ВерсОКВЭД', None)
    extra_okved = get_or_create(session, OKVED, okved_code=okved_code, okved_name=okved_name, okved_ver=okved_ver)
    extra_okved.docs.append(doc)


def get_or_create_license(session, data, doc):
    lic_series = data.get('@СерЛиценз', None)
    lic_activity = data.get('НаимЛицВД', None)
    lic_address = data.get('СведАдрЛицВД', None)
    lic_num = data.get('@НомЛиценз', None)
    lic_type = data.get('@ВидЛиценз', None)
    lic_date = date_transform(data.get('ДатаЛиценз', None))
    lic_start_date = date_transform(data.get('ДатаНачЛиценз', None))
    lic_end_date = date_transform(data.get('ДатаКонЛиценз', None))
    licensor = data.get('@ОргВыдЛиценз', None)
    lic_stop_date = date_transform(data.get('ДатаОстЛиценз', None))
    org_stoped_lic = data.get('@ОргОстЛиценз', None)

    get_or_create(session, License, doc=doc, lic_series=lic_series, lic_activity=lic_activity, lic_address=lic_address,
                  lic_num=lic_num, lic_type=lic_type, lic_date=lic_date, lic_start_date=lic_start_date,
                  lic_end_date=lic_end_date, licensor=licensor, lic_stop_date=lic_stop_date,
                  org_stoped_lic=org_stoped_lic)


def get_or_create_production(session, data, doc):
    prod_code = data.get('@КодПрод', None)
    prod_name = data.get('@НаимПрод', None)
    prod_innov = data.get('@ПрОтнПрод', None)

    get_or_create(session, Production, doc=doc, prod_code=prod_code, prod_name=prod_name, prod_innov=prod_innov)


def get_or_create_partnership(session, data, doc):
    partner_name = data.get('@НаимЮЛ_ПП', None)
    partner_inn = data.get('@ИННЮЛ_ПП', None)
    partner_contract_num = data.get('@НомДог', None)
    partner_contract_date = date_transform(data.get('@ДатаДог', None))

    get_or_create(session, Partnership, doc=doc, partner_name=partner_name, partner_inn=partner_inn,
                  partner_contract_num=partner_contract_num, partner_contract_date=partner_contract_date)


def get_or_create_contract(session, data, doc):
    contract_client_name = data.get('@НаимЮЛ_ЗК', None)
    contract_client_inn = data.get('@ИННЮЛ_ЗК', None)
    contract_subj = data.get('@ПредмКонтр', None)
    contract_num = data.get('@НомКонтрРеестр', None)
    contract_date = date_transform(data.get('@ДатаКонтр', None))

    get_or_create(session, Contract, doc=doc, contract_client_name=contract_client_name,
                  contract_client_inn=contract_client_inn, contract_subj=contract_subj,
                  contract_num=contract_num, contract_date=contract_date)


def get_or_create_agreement(session, data, doc):
    dog_client_name = data.get('@НаимЮЛ_ЗД', None)
    dog_client_inn = data.get('@ИННЮЛ_ЗД', None)
    dog_subj = data.get('@ПредмДог', None)
    dog_num = data.get('@НомДогРеестр', None)
    dog_date = date_transform(data.get('@ДатаДог', None))

    get_or_create(session, Agreement, doc=doc, dog_client_name=dog_client_name, dog_client_inn=dog_client_inn,
                  dog_subj=dog_subj, dog_num=dog_num, dog_date=dog_date)


if __name__ == "__main__":
    # коннектимся к базе, если ее нет - создаем
    engine = create_engine('mysql://root:qwerty12345@localhost/rsmp?charset=cp1251&use_unicode=0')
    if database_exists(engine.url):
        drop_database(engine.url)
    if not database_exists(engine.url):
        create_database(engine.url)
        # создаем таблицы
        Base.metadata.create_all(engine)
    # создаем сессию
    Session = sessionmaker(bind=engine)
    session = Session()
    actual_url, file_name = get_actual_url_and_filename()
    # TODO убрать хардкод
    file_name = 'data-11062017-structure-08012016.zip'
    # идем по файлам из архива и вытаскиваем информацию
    zip_file = zipfile.ZipFile(file_name)

    i = 0
    for name in zip_file.namelist():
        xml_file = zip_file.open(name)
        data = xml_file.read().decode('utf-8')
        dict_data = xmltodict.parse(data)
        file_content = dict_data['Файл']

        # Сведения о файле и отправителе
        file_id = file_content['@ИдФайл']
        file_format_ver = file_content.get('@ВерсФорм', None)
        info_type = file_content.get('@ТипИнф', None)
        program_ver = file_content.get('@ВерсПрог', None)
        docs_count = file_content.get('@КолДок', None)

        sender_position = file_content.get('ИдОтпр', {}).get('@ДолжОтв', None)
        sender_tel = file_content.get('ИдОтпр', {}).get('@Тлф', None)
        sender_email = file_content.get('ИдОтпр', {}).get('@E-mail', None)

        sender_name = file_content.get('ИдОтпр', {}).get('ФИООтв', {}).get('@Имя', None)
        sender_surname = file_content.get('ИдОтпр', {}).get('ФИООтв', {}).get('@Фамилия', None)
        sender_middlename = file_content.get('ИдОтпр', {}).get('ФИООтв', {}).get('@Отчество', None)

        orm_file = get_or_create(session, RSMPFile, file_id=file_id, file_format_ver=file_format_ver,
                                 info_type=info_type, program_ver=program_ver, docs_count=docs_count,
                                 sender_name=sender_name, sender_surname=sender_surname,
                                 sender_middlename=sender_middlename, sender_position=sender_position,
                                 sender_tel=sender_tel, sender_email=sender_email)

        for doc in file_content['Документ']:
            # Состав и структура документ
            doc_id = doc['@ИдДок']
            doc_create_date = date_transform(doc.get('@ДатаСост', None))
            msp_input_date = date_transform(doc.get('@ДатаВклМСП', None))
            subj_type = doc.get('@ВидСубМСП', None)
            subj_cat = doc.get('@КатСубМСП', None)
            novelity = doc.get('@ПризНовМСП', None)

            orm_doc = get_or_create(session, RSMPDocument, file=orm_file, doc_id=doc_id,
                                    doc_create_date=doc_create_date, msp_input_date=msp_input_date, subj_type=subj_type,
                                    subj_cat=subj_cat, novelity=novelity)
            # Сведения о юридическом/индивидуальном предпринимателе лице, включенном в реестр МСП
            if 'ОргВклМСП' in doc and doc['ОргВклМСП']:
                org_full_name = doc['ОргВклМСП'].get('@НаимОрг', None)
                org_short_name = doc['ОргВклМСП'].get('НаимОргСокр', None)
                org_inn = doc['ОргВклМСП'].get('@ИННЮЛ', None)

                le = get_or_create(session, LegalEntity, doc=orm_doc, org_full_name=org_full_name,
                                   org_short_name=org_short_name, org_inn=org_inn)

            if 'ИПВклМСП' in doc and doc['ИПВклМСП']:
                ip_inn = doc['ИПВклМСП'].get('@ИННФЛ', None)
                ip_name = doc['ИПВклМСП'].get('ФИОИП', {}).get('@Имя', None)
                ip_surname = doc['ИПВклМСП'].get('ФИОИП', {}).get('@Фамилия', None)
                ip_middlename = doc['ИПВклМСП'].get('ФИОИП', {}).get('@Отчество', None)

                ie = get_or_create(session, IndividualEnterpeneur, doc=orm_doc, ip_name=ip_name, ip_surname=ip_surname,
                                   ip_middlename=ip_middlename, ip_inn=ip_inn)

            # Сведения о месте нахождения юридического лица / месте жительства индивидуального предпринимателя
            if 'СведМН' in doc and doc['СведМН']:

                region = doc['СведМН'].get('@КодРегион', None)
                region_type = doc['СведМН'].get('Регион', {}).get('@Тип', None)
                region_name = doc['СведМН'].get('Регион', {}).get('@Наим', None)
                if region or region_name or region_type:
                    region = get_or_create(session, Region, region=region, type=region_type, name=region_name)
                    orm_doc.region = region

                district_type = doc['СведМН'].get('Район', {}).get('@Тип', None)
                district_name = doc['СведМН'].get('Район', {}).get('@Наим', None)
                if district_type or district_name:
                    district = get_or_create(session, District, type=district_type, name=district_name)
                    orm_doc.district = district

                city_type = doc['СведМН'].get('Город', {}).get('@Тип', None)
                city_name = doc['СведМН'].get('Город', {}).get('@Наим', None)
                if city_type or city_name:
                    city = get_or_create(session, City, type=city_type, name=city_name)
                    orm_doc.city = city

                locality_type = doc['СведМН'].get('НаселПункт', {}).get('@Тип', None)
                locality_name = doc['СведМН'].get('НаселПункт', {}).get('@Наим', None)
                if locality_type or locality_name:
                    locality = get_or_create(session, Locality, type=locality_type, name=locality_name)
                    orm_doc.locality = locality

            # Сведения о видах экономической деятельности
            # по Общероссийскому классификатору видов экономической деятельности
            if 'СвОКВЭД' in doc and doc['СвОКВЭД']:
                okved_main_code = doc['СвОКВЭД'].get('СвОКВЭДОсн', {}).get('@КодОКВЭД', None)
                okved_main_name = doc['СвОКВЭД'].get('СвОКВЭДОсн', {}).get('@НаимОКВЭД', None)
                okved_main_ver = doc['СвОКВЭД'].get('СвОКВЭДОсн', {}).get('@ВерсОКВЭД', None)

                main_okved = get_or_create(session, OKVED, okved_code=okved_main_code, okved_name=okved_main_name,
                                           okved_ver=okved_main_ver)
                orm_doc.main_okved = main_okved

                dop_okved = doc['СвОКВЭД'].get('СвОКВЭДДоп', [])
                if isinstance(dop_okved, list):
                    for item in dop_okved:
                        get_or_create_extra_okved(session=session, data=item, doc=orm_doc)
                else:
                    get_or_create_extra_okved(session=session, data=dop_okved, doc=orm_doc)

            # Сведения о лицензиях, выданных субъекту МСП
            if 'СвЛиценз' in doc and doc['СвЛиценз']:
                items = doc['СвЛиценз'] if isinstance(doc['СвЛиценз'], list) else [doc['СвЛиценз']]
                for item in items:
                    get_or_create_license(session=session, data=item, doc=orm_doc)

            # Сведения о производимой субъектом МСП продукции
            if 'СвПрод' in doc and doc['СвПрод']:
                items = doc['СвПрод'] if isinstance(doc['СвПрод'], list) else [doc['СвПрод']]
                for item in items:
                    get_or_create_production(session=session, data=item, doc=orm_doc)

            # Сведения о включении субъекта МСП в реестры программ партнерства
            if 'СвПрогПарт' in doc and doc['СвПрогПарт']:
                items = doc['СвПрогПарт'] if isinstance(doc['СвПрогПарт'], list) else [doc['СвПрогПарт']]
                for item in items:
                    get_or_create_partnership(session=session, data=item, doc=orm_doc)

            # Сведения о наличии у субъекта МСП в предшествующем календарном году контрактов, заключенных
            # в соответствии с Федеральным законом от 5 апреля 2013 года №44-ФЗ
            if 'СвКонтр' in doc and doc['СвКонтр']:
                items = doc['СвКонтр'] if isinstance(doc['СвКонтр'], list) else [doc['СвКонтр']]
                for item in items:
                    get_or_create_contract(session=session, data=item, doc=orm_doc)

            # Сведения о наличии у субъекта МСП в предшествующем календарном году договоров, заключенных
            # в соответствии с Федеральным законом от 18 июля 2011 года №223-ФЗ
            # TODO убрать костыль
            if 'СвДог' in doc and doc['СвДог']:
                items = doc['СвДог'] if isinstance(doc['СвДог'], list) else [doc['СвДог']]
                for item in items:
                    get_or_create_agreement(session=session, data=item, doc=orm_doc)

            session.commit()

        xml_file.close()
        break

    # session.commit()
