import re
import urllib.request
import xmltodict
import zipfile

from bs4 import BeautifulSoup as BS
from sqlalchemy import Column, Date, Integer, String, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy_utils import database_exists, create_database

MAIN_URL = 'https://www.nalog.ru/opendata/7707329152-rsmp/'
NEED_TO_DOWNLOAD = False

Base = declarative_base()


class RSMP(Base):

    __tablename__ = 'rsmp'

    id = Column(Integer, primary_key=True)

    file_id = Column(String(255))
    file_form_ver = Column(String(5))
    info_type = Column(String(50))
    docs_count = Column(Integer)

    sender_name = Column(String(60))
    sender_surname = Column(String(60))

    doc_id = Column(String(36))
    doc_create_date = Column(Date)
    msp_input_date = Column(Date)
    subj_type = Column(String(1))
    subj_cat = Column(String(1))
    novelity = Column(String(1))

    full_name = Column(String(1000))
    short_name = Column(String(500))
    inn = Column(String(500))

    region = Column(String(2))
    region_type = Column(String(50))
    region_name = Column(String(255))
    locality_type = Column(String(50))
    locality_name = Column(String(255))

    okved_ver = Column(String(4))
    okved_name = Column(String(1000))
    okved_main_code = Column(String(8))
    okved_add_code = Column(String(8))


def get_actual_url_and_filename():
    """
    Поиск названия актуального файла и ссылки на его скачивание
    """
    # TODO get actual url by date, not just first url
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


def download_xds():
    """
    Скачивание файла со структурой
    """
    # TODO убрать хардкод
    xsd_url = 'https://www.nalog.ru/opendata/7707329152-rsmp/structure-08012016.xsd'
    xsd_file_name = 'structure-08012016.xsd'
    xsd_actual_file = urllib.request.URLopener()
    xsd_actual_file.retrieve(xsd_url, xsd_file_name)

if __name__ == "__main__":
    # коннектимся к базе, если ее нет - создаем
    mysql_engine = create_engine('mysql+pymysql://root:****@localhost/rsmp')
    if not database_exists(mysql_engine.url):
        create_database(mysql_engine.url)

    # создаем таблицу
    Base.metadata.create_all(mysql_engine)
    actual_url, file_name = get_actual_url_and_filename()

    # идем по файлам из архива и вытаскиваем информацию
    zip_file = zipfile.ZipFile(file_name)
    for name in zip_file.namelist():
        xml_file = zip_file.open(name)
        data = xml_file.read().decode('utf-8')
        dict_data = dict(xmltodict.parse(data))
        [(doc_type, doc_content)] = dict_data.items()
        for key, value in dict(doc_content).items():
            print(key, value)
        xml_file.close()

