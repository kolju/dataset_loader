import re
import urllib.request
import xmltodict
import zipfile

from bs4 import BeautifulSoup as BS

url = 'https://www.nalog.ru/opendata/7707329152-rsmp/'
response = urllib.request.urlopen(url)
soup = BS(response, "html.parser")
urls = soup.findAll('a', attrs={'href': re.compile("^https://www.nalog.ru/opendata/7707329152-rsmp/data")})
# TODO get actual url by date, not just first url
actual_url = list(map(lambda x: x.get('href'), urls))[0]
file_name = actual_url.split('/')[-1]
actual_file = urllib.request.URLopener()
actual_file.retrieve(actual_url, file_name)

zip_file = zipfile.ZipFile(file_name)
for name in zip_file.namelist():
    xml_file = zip_file.open(name)
    data = xml_file.read().decode('utf-8')
    dict_data = dict(xmltodict.parse(data))
    [(doc_type, doc_content)] = dict_data.items()
    for key, value in dict(doc_content).items():
        print(key, value)
    xml_file.close()
