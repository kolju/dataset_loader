###  Российский единый реестр субъектов малого и среднего предпринимательства

https://www.nalog.ru/opendata/7707329152-rsmp/

Поиск актуального набора данных по ссылке, скачивание и запись в базу данных.

Замечания:

1. В случае наличия актуальной информации в БД скачивание файла не производится.
2. В решении не используются required поля, поскольку xml файлы не соответствуют описанной по ссылке xsd структуре: required поля на самом деле могут быть не заполнены.  
По этой же причине перечислимые значения хранятся как строка.
3. Команды, которые запустят докер-контейнер, скачают файл, запишут информацию в ORM и в конце удалят скачанный файл:
```bash
docker-compose build
docker-compose up
```
Обновление БД:
```bash
docker-compose start app
```

### Russian uniform small and medium business register

https://www.nalog.ru/opendata/7707329152-rsmp/

Search and download actual register, wrighting to the database.
 
Notes:

1. The file is not downloaded in case of actual information in database.
2. There are no required fields in solution, because of xml files don't match the described xsd structure.
For the same reason enumerated values are stored as a string.
3. Commands to run docker-container, file download, write info in database and delete downloaded file in the end:
```bash
docker-compose build
docker-compose up
```
Database refreshing:
```bash
docker-compose start app
```