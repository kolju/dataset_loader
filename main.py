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
    if instance:
        return instance
    else:
        instance = model(**kwargs)
        session.add(instance)
        session.commit()
        return instance


def date_transform(str):
    if not str:
        return None
    else:
        return datetime.datetime.strptime(str, '%d.%m.%Y')


def get_or_create_extra_okved(session, data, doc_id, orm_doc):
    okved_code = data.get('@КодОКВЭД', None)
    okved_name = data.get('@НаимОКВЭД', None)
    okved_ver = data.get('@ВерсОКВЭД', None)
    okved = get_or_create(session, OKVED, doc_id=doc_id, okved_code=okved_code, okved_name=okved_name,
                          okved_ver=okved_ver)
    okved.docs.append(orm_doc)


def get_or_create_license(session, data, doc_id):
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

    get_or_create(session, License, doc_id=doc_id, lic_series=lic_series, lic_activity=lic_activity,
                  lic_address=lic_address, lic_num=lic_num, lic_type=lic_type, lic_date=lic_date,
                  lic_start_date=lic_start_date, lic_end_date=lic_end_date, licensor=licensor,
                  lic_stop_date=lic_stop_date, org_stoped_lic=org_stoped_lic)


def get_or_create_production(session, data, doc_id):
    prod_code = data.get('@КодПрод', None)
    prod_name = data.get('@НаимПрод', None)
    prod_innov = data.get('@ПрОтнПрод', None)

    get_or_create(session, Production, doc_id=doc_id, prod_code=prod_code, prod_name=prod_name, prod_innov=prod_innov)


def get_or_create_partnership(session, data, doc_id):
    partner_name = data.get('@НаимЮЛ_ПП', None)
    partner_inn = data.get('@ИННЮЛ_ПП', None)
    partner_contract_num = data.get('@НомДог', None)
    partner_contract_date = date_transform(data.get('@ДатаДог', None))

    get_or_create(session, Partnership, doc_id=doc_id, partner_name=partner_name, partner_inn=partner_inn,
                  partner_contract_num=partner_contract_num, partner_contract_date=partner_contract_date)


def get_or_create_contract(session, data, doc_id):
    contract_client_name = data.get('@НаимЮЛ_ЗК', None)
    contract_client_inn = data.get('@ИННЮЛ_ЗК', None)
    contract_subj = data.get('@ПредмКонтр', None)
    contract_num = data.get('@НомКонтрРеестр', None)
    contract_date = date_transform(data.get('@ДатаКонтр', None))

    get_or_create(session, Contract, doc_id=doc_id, contract_client_name=contract_client_name,
                  contract_client_inn=contract_client_inn, contract_subj=contract_subj,
                  contract_num=contract_num, contract_date=contract_date)


def get_or_create_agreement(session, data, doc_id):
    dog_client_name = data.get('@НаимЮЛ_ЗД', None)
    dog_client_inn = data.get('@ИННЮЛ_ЗД', None)
    dog_subj = data.get('@ПредмДог', None)
    dog_num = data.get('@НомДогРеестр', None)
    dog_date = date_transform(data.get('@ДатаДог', None))

    get_or_create(session, Agreement, doc_id=doc_id, dog_client_name=dog_client_name, dog_client_inn=dog_client_inn,
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

        """
        Сведения о файле и отправителе
        """
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
            """
            Состав и структура документ
            """
            doc_id = doc['@ИдДок']
            doc_create_date = date_transform(doc.get('@ДатаСост', None))
            msp_input_date = date_transform(doc.get('@ДатаВклМСП', None))
            subj_type = doc.get('@ВидСубМСП', None)
            subj_cat = doc.get('@КатСубМСП', None)
            novelity = doc.get('@ПризНовМСП', None)

            orm_doc = get_or_create(session, RSMPDocument, file_id=orm_file.id, doc_id=doc_id,
                                    doc_create_date=doc_create_date, msp_input_date=msp_input_date, subj_type=subj_type,
                                    subj_cat=subj_cat, novelity=novelity)
            doc_id = orm_doc.id
            """
            Сведения о юридическом/индивидуальном предпринимателе лице, включенном в реестр МСП
            """
            if 'ОргВклМСП' in doc and doc['ОргВклМСП']:
                org_full_name = doc['ОргВклМСП'].get('@НаимОрг', None)
                org_short_name = doc['ОргВклМСП'].get('НаимОргСокр', None)
                org_inn = doc['ОргВклМСП'].get('@ИННЮЛ', None)

                le = get_or_create(session, LegalEntity, doc_id=orm_doc.id, org_full_name=org_full_name,
                                   org_short_name=org_short_name, org_inn=org_inn)
                le_id = le.id

            if 'ИПВклМСП' in doc and doc['ИПВклМСП']:
                ip_inn = doc['ИПВклМСП'].get('@ИННФЛ', None)
                ip_name = doc['ИПВклМСП'].get('ФИОИП', {}).get('@Имя', None)
                ip_surname = doc['ИПВклМСП'].get('ФИОИП', {}).get('@Фамилия', None)
                ip_middlename = doc['ИПВклМСП'].get('ФИОИП', {}).get('@Отчество', None)

                ie = get_or_create(session, IndividualEnterpeneur, doc_id=orm_doc.id, ip_name=ip_name,
                                   ip_surname=ip_surname, ip_middlename=ip_middlename, ip_inn=ip_inn)

            """
            Сведения о месте нахождения юридического лица / месте жительства индивидуального предпринимателя
            """
            if 'СведМН' in doc and doc['СведМН']:

                region = doc['СведМН'].get('@КодРегион', None)
                region_type = doc['СведМН'].get('Регион', {}).get('@Тип', None)
                region_name = doc['СведМН'].get('Регион', {}).get('@Наим', None)
                region = get_or_create(session, Region, region=region, type=region_type, name=region_name)

                district_type = doc['СведМН'].get('Район', {}).get('@Тип', None)
                district_name = doc['СведМН'].get('Район', {}).get('@Наим', None)
                district = get_or_create(session, Address, type=district_type, name=district_name)

                city_type = doc['СведМН'].get('Город', {}).get('@Тип', None)
                city_name = doc['СведМН'].get('Город', {}).get('@Наим', None)
                city = get_or_create(session, Address, type=city_type, name=city_name)

                locality_type = doc['СведМН'].get('НаселПункт', {}).get('@Тип', None)
                locality_name = doc['СведМН'].get('НаселПункт', {}).get('@Наим', None)
                locality = get_or_create(session, Address, type=locality_type, name=locality_name)

                get_or_create(session, Location, doc_id=doc_id, region_id=region.id,
                              district_id=district.id, city_id=city.id, locality_id=locality.id)

            """
            Сведения о видах экономической деятельности
            по Общероссийскому классификатору видов экономической деятельности
            """
            if 'СвОКВЭД' in doc and doc['СвОКВЭД']:
                okved_main_code = doc['СвОКВЭД'].get('СвОКВЭДОсн', {}).get('@КодОКВЭД', None)
                okved_main_name = doc['СвОКВЭД'].get('СвОКВЭДОсн', {}).get('@НаимОКВЭД', None)
                okved_main_ver = doc['СвОКВЭД'].get('СвОКВЭДОсн', {}).get('@ВерсОКВЭД', None)

                get_or_create(session, OKVED, okved_code=okved_main_code, okved_name=okved_main_name,
                              okved_ver=okved_main_ver)

                dop_okved = doc['СвОКВЭД'].get('СвОКВЭДДоп', [])
                if isinstance(dop_okved, list):
                    for item in dop_okved:
                        get_or_create_extra_okved(session=session, data=item, doc_id=doc_id, orm_doc=orm_doc)
                else:
                    get_or_create_extra_okved(session=session, data=dop_okved, doc_id=doc_id, orm_doc=orm_doc)

            """
            Сведения о лицензиях, выданных субъекту МСП
            """
            # TODO убрать костыль
            if 'СвЛиценз' in doc and doc['СвЛиценз']:
                if isinstance(doc['СвЛиценз'], list):
                    for item in doc['СвЛиценз']:
                        get_or_create_license(session=session, data=item, doc_id=doc_id)
                else:
                    get_or_create_license(session=session, data=doc['СвЛиценз'], doc_id=doc_id)

            """
            Сведения о производимой субъектом МСП продукции
            """
            # TODO убрать костыль
            if 'СвПрод' in doc and doc['СвПрод']:
                if isinstance(doc['СвПрод'], list):
                    for item in doc['СвПрод']:
                        get_or_create_production(session=session, data=item, doc_id=doc_id)
                else:
                    get_or_create_production(session, data=doc['СвПрод'], doc_id=doc_id)

            """
            Сведения о включении субъекта МСП в реестры программ партнерства
            """
            # TODO убрать костыль
            if 'СвПрогПарт' in doc and doc['СвПрогПарт']:
                if isinstance(doc['СвПрогПарт'], list):
                    for item in doc['СвПрогПарт']:
                        get_or_create_partnership(session=session, data=item, doc_id=doc_id)
                else:
                    get_or_create_partnership(session=session, data=doc['СвПрогПарт'], doc_id=doc_id)

            """
            Сведения о наличии у субъекта МСП в предшествующем календарном году контрактов, заключенных
            в соответствии с Федеральным законом от 5 апреля 2013 года №44-ФЗ
            """
            # TODO убрать костыль
            if 'СвКонтр' in doc and doc['СвКонтр']:
                if isinstance(doc['СвКонтр'], list):
                    for item in doc['СвКонтр']:
                        get_or_create_contract(session=session, data=item, doc_id=doc_id)
                else:
                    get_or_create_contract(session=session, data=doc['СвКонтр'], doc_id=doc_id)

            """
            Сведения о наличии у субъекта МСП в предшествующем календарном году договоров, заключенных
            в соответствии с Федеральным законом от 18 июля 2011 года №223-ФЗ
            """
            # TODO убрать костыль
            if 'СвДог' in doc and doc['СвДог']:
                if isinstance(doc['СвДог'], list):
                    for item in doc['СвДог']:
                        get_or_create_agreement(session=session, data=item, doc_id=doc_id)
                else:
                    get_or_create_agreement(session=session, data=doc['СвДог'], doc_id=doc_id)

        xml_file.close()
        print('end')
        break

    session.commit()
