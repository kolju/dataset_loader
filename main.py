import re
import urllib.request
import xmltodict
import zipfile

from bs4 import BeautifulSoup as BS
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy_utils import database_exists, create_database, drop_database
from utils import *

MAIN_URL = 'https://www.nalog.ru/opendata/7707329152-rsmp/'
NEED_TO_DOWNLOAD = False
DEBUG = True


def get_actual_url_and_filename():
    """
    Поиск названия актуального файла и ссылки на его скачивание
    """
    response = urllib.request.urlopen(MAIN_URL)
    soup = BS(response, "html.parser")
    data_url = '^' + MAIN_URL + 'data'
    actual_url = soup.find_all(property="dc:source", content=re.compile(data_url))[0].get('content')
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


if __name__ == "__main__":

    # коннектимся к базе, если ее нет - создаем
    engine = create_engine('mysql://root:qwerty12345@localhost/rsmp?charset=cp1251&use_unicode=0')

    if DEBUG and database_exists(engine.url):
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
    if DEBUG:
        file_name = 'data-11062017-structure-08012016.zip'
    # идем по файлам из архива и вытаскиваем информацию
    zip_file = zipfile.ZipFile(file_name)

    for name in zip_file.namelist():
        with zip_file.open(name) as xml_file:
            dict_data = xmltodict.parse(xml_file)
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

        orm_file = create_orm_object(session, RSMPFile, file_id=file_id, file_format_ver=file_format_ver,
                                     info_type=info_type, program_ver=program_ver, docs_count=docs_count,
                                     sender_name=sender_name, sender_surname=sender_surname,
                                     sender_middlename=sender_middlename, sender_position=sender_position,
                                     sender_tel=sender_tel, sender_email=sender_email)

        for doc in file_content['Документ']:
            # Состав и структура документа
            doc_id = doc['@ИдДок']
            create_date = date_transform(doc.get('@ДатаСост', None))
            input_date = date_transform(doc.get('@ДатаВклМСП', None))
            subj_type = doc.get('@ВидСубМСП', None)
            subj_cat = doc.get('@КатСубМСП', None)
            novelty = doc.get('@ПризНовМСП', None)

            orm_doc = create_orm_object(session, RSMPDocument, file=orm_file, doc_id=doc_id, create_date=create_date,
                                        input_date=input_date, subj_type=subj_type, subj_cat=subj_cat, novelty=novelty)

            if 'ОргВклМСП' in doc and doc['ОргВклМСП']:
                info = doc['ОргВклМСП']
                full_name = info.get('@НаимОрг', None)
                short_name = info.get('НаимОргСокр', None)
                inn = info.get('@ИННЮЛ', None)

                create_orm_object(session, Business, doc=orm_doc, full_name=full_name, short_name=short_name, inn=inn)

            if 'ИПВклМСП' in doc and doc['ИПВклМСП']:
                info = doc['ИПВклМСП']
                inn = info.get('@ИННФЛ', None)
                name = info.get('ФИОИП', {}).get('@Имя', None)
                surname = info.get('ФИОИП', {}).get('@Фамилия', None)
                middlename = info.get('ФИОИП', {}).get('@Отчество', None)

                create_orm_object(session, IndividualEnterpeneur, doc=orm_doc, name=name, surname=surname,
                                  middlename=middlename, inn=inn)

            if 'СведМН' in doc and doc['СведМН']:
                location = doc['СведМН']
                region = location.get('@КодРегион', None)
                region_type = location.get('Регион', {}).get('@Тип', None)
                region_name = location.get('Регион', {}).get('@Наим', None)
                if region or region_name or region_type:
                    region = create_orm_object(session, Region, region=region, type=region_type, name=region_name)
                    orm_doc.region = region

                district_type = location.get('Район', {}).get('@Тип', None)
                district_name = location.get('Район', {}).get('@Наим', None)
                if district_type or district_name:
                    district = create_orm_object(session, District, type=district_type, name=district_name)
                    orm_doc.district = district

                city_type = location.get('Город', {}).get('@Тип', None)
                city_name = location.get('Город', {}).get('@Наим', None)
                if city_type or city_name:
                    city = create_orm_object(session, City, type=city_type, name=city_name)
                    orm_doc.city = city

                locality_type = location.get('НаселПункт', {}).get('@Тип', None)
                locality_name = location.get('НаселПункт', {}).get('@Наим', None)
                if locality_type or locality_name:
                    locality = create_orm_object(session, Locality, type=locality_type, name=locality_name)
                    orm_doc.locality = locality

            if 'СвОКВЭД' in doc and doc['СвОКВЭД']:
                okved = doc['СвОКВЭД']
                main_code = okved.get('СвОКВЭДОсн', {}).get('@КодОКВЭД', None)
                main_name = okved.get('СвОКВЭДОсн', {}).get('@НаимОКВЭД', None)
                main_ver = okved.get('СвОКВЭДОсн', {}).get('@ВерсОКВЭД', None)

                if main_code or main_name or main_ver:
                    main_okved = create_orm_object(session, OKVED, code=main_code, name=main_name, ver=main_ver)
                    orm_doc.main_okved = main_okved

                if 'СвОКВЭДДоп' in okved and okved['СвОКВЭДДоп']:
                    extra_okveds = okved['СвОКВЭДДоп']
                    extra_okveds = extra_okveds if isinstance(extra_okveds, list) else [extra_okveds]
                    for extra_okved in extra_okveds:
                        get_or_create_extra_okved(session=session, data=extra_okved, doc=orm_doc)

            if 'СвЛиценз' in doc and doc['СвЛиценз']:
                licenses = doc['СвЛиценз']
                licenses = licenses if isinstance(licenses, list) else [licenses]
                for license in licenses:
                    get_or_create_license(session=session, data=license, doc=orm_doc)

            if 'СвПрод' in doc and doc['СвПрод']:
                products = doc['СвПрод']
                items = products if isinstance(products, list) else [products]
                for item in items:
                    get_or_create_production(session=session, data=item, doc=orm_doc)

            if 'СвПрогПарт' in doc and doc['СвПрогПарт']:
                partnerships = doc['СвПрогПарт']
                partnerships = partnerships if isinstance(partnerships, list) else [partnerships]
                for partnership in partnerships:
                    get_or_create_partnership(session=session, data=partnership, doc=orm_doc)

            if 'СвКонтр' in doc and doc['СвКонтр']:
                contracts = doc['СвКонтр']
                contracts = contracts if isinstance(contracts, list) else [contracts]
                for contract in contracts:
                    get_or_create_contract(session=session, data=contract, doc=orm_doc)

            if 'СвДог' in doc and doc['СвДог']:
                agreements = doc['СвДог']
                agreements = agreements if isinstance(agreements, list) else [agreements]
                for agreement in agreements:
                    get_or_create_agreement(session=session, data=agreement, doc=orm_doc)

        session.commit()
        if DEBUG:
            break

    print(create_orm_object.cache_info())
