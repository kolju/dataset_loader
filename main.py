import urllib.request
import xmltodict
import zipfile

from bs4 import BeautifulSoup as BS
from db import (Base, File, RSMPFile, RSMPDocument, Business, IndividualEnterpeneur, Region, District, City, Locality,
                OKVED)
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy_utils import database_exists, create_database, drop_database
from tqdm import tqdm
from utils import (create_orm_object, date_transform, create_extra_okved, create_license, create_production,
                   create_partnership, create_contract, create_agreement)

MAIN_URL = 'https://www.nalog.ru/opendata/7707329152-rsmp/'
DEBUG = True


def get_actual_url_and_filename():
    """
    Поиск названия актуального файла и ссылки на его скачивание
    """
    response = urllib.request.urlopen(MAIN_URL)
    soup = BS(response, "html.parser")
    actual_url = soup.find('div', resource="#data-1").find('div', property="dc:source")['content']
    file_name = actual_url.split('/')[-1]
    return actual_url, file_name


def download_actual_file(actual_url, file_name):
    """
    Скачивание актуального файла
    """
    actual_file = urllib.request.URLopener()
    actual_file.retrieve(actual_url, file_name)


if __name__ == "__main__":
    actual_url, file_name = get_actual_url_and_filename()

    # TODO mysql instead localhost
    engine = create_engine('mysql://root:qwerty12345@localhost/rsmp?charset=utf8', echo=False)
    Session = sessionmaker(bind=engine)
    session = Session()

    if not DEBUG and (database_exists(engine.url) and actual_url == str(session.query(File).first().url)):
        print('Информация в БД актуальна')
    else:
        if DEBUG and database_exists(engine.url):
            drop_database(engine.url)
        create_database(engine.url)
        Base.metadata.create_all(engine)
        create_orm_object(session, File, url=actual_url)

        if DEBUG:
            file_name = './data/data-11062017-structure-08012016.zip'
        else:
            download_actual_file(actual_url, file_name)

        zip_file = zipfile.ZipFile(file_name)
        for name in tqdm(zip_file.namelist()):
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

                orm_doc = create_orm_object(session, RSMPDocument, file=orm_file, doc_id=doc_id,
                                            create_date=create_date, input_date=input_date, subj_type=subj_type,
                                            subj_cat=subj_cat, novelty=novelty)

                if 'ОргВклМСП' in doc and doc['ОргВклМСП']:
                    info = doc['ОргВклМСП']
                    full_name = info.get('@НаимОрг', None)
                    short_name = info.get('НаимОргСокр', None)
                    inn = info.get('@ИННЮЛ', None)

                    business = create_orm_object(session, Business, full_name=full_name, short_name=short_name, inn=inn)
                    business.doc = orm_doc

                if 'ИПВклМСП' in doc and doc['ИПВклМСП']:
                    info = doc['ИПВклМСП']
                    inn = info.get('@ИННФЛ', None)
                    name = info.get('ФИОИП', {}).get('@Имя', None)
                    surname = info.get('ФИОИП', {}).get('@Фамилия', None)
                    middlename = info.get('ФИОИП', {}).get('@Отчество', None)

                    ip = create_orm_object(session, IndividualEnterpeneur, name=name, surname=surname,
                                           middlename=middlename, inn=inn)
                    ip.doc = orm_doc

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
                            okved = create_extra_okved(session=session, data=extra_okved)
                            orm_doc.extra_okveds.append(okved)

                if 'СвЛиценз' in doc and doc['СвЛиценз']:
                    licenses = doc['СвЛиценз']
                    licenses = licenses if isinstance(licenses, list) else [licenses]
                    for license in licenses:
                        lic = create_license(session=session, data=license)
                        lic.doc = orm_doc

                if 'СвПрод' in doc and doc['СвПрод']:
                    products = doc['СвПрод']
                    items = products if isinstance(products, list) else [products]
                    for item in items:
                        prod = create_production(session=session, data=item)
                        prod.doc = orm_doc

                if 'СвПрогПарт' in doc and doc['СвПрогПарт']:
                    partnerships = doc['СвПрогПарт']
                    partnerships = partnerships if isinstance(partnerships, list) else [partnerships]
                    for partnership in partnerships:
                        pship = create_partnership(session=session, data=partnership)
                        pship.doc = orm_doc

                if 'СвКонтр' in doc and doc['СвКонтр']:
                    contracts = doc['СвКонтр']
                    contracts = contracts if isinstance(contracts, list) else [contracts]
                    for contract in contracts:
                        contr = create_contract(session=session, data=contract)
                        contr.doc = orm_doc

                if 'СвДог' in doc and doc['СвДог']:
                    agreements = doc['СвДог']
                    agreements = agreements if isinstance(agreements, list) else [agreements]
                    for agreement in agreements:
                        agr = create_agreement(session=session, data=agreement)
                        agr.doc = orm_doc

            session.commit()
            # if DEBUG:
            #     break
