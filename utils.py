import datetime
from functools import lru_cache
from db import *


def date_transform(str_date):
    if not str_date:
        return None
    else:
        return datetime.datetime.strptime(str_date, '%d.%m.%Y')


@lru_cache(maxsize=None)
def create_orm_object(session, model, **kwargs):
    instance = model(**kwargs)
    session.add(instance)
    return instance


def get_or_create_extra_okved(session, data, doc):
    code = data.get('@КодОКВЭД', None)
    name = data.get('@НаимОКВЭД', None)
    ver = data.get('@ВерсОКВЭД', None)
    extra_okved = create_orm_object(session, OKVED, code=code, name=name, ver=ver)
    extra_okved.docs.append(doc)


def get_or_create_license(session, data, doc):
    series = data.get('@СерЛиценз', None)
    activity = data.get('НаимЛицВД', None)
    activity = tuple(activity) if activity else None
    address = data.get('СведАдрЛицВД', None)
    address = tuple(address) if address else None
    num = data.get('@НомЛиценз', None)
    type = data.get('@ВидЛиценз', None)
    date = date_transform(data.get('ДатаЛиценз', None))
    start_date = date_transform(data.get('ДатаНачЛиценз', None))
    end_date = date_transform(data.get('ДатаКонЛиценз', None))
    org_started = data.get('@ОргВыдЛиценз', None)
    stop_date = date_transform(data.get('ДатаОстЛиценз', None))
    org_stoped = data.get('@ОргОстЛиценз', None)
    create_orm_object(session, License, doc=doc, series=series, activity=activity, address=address, num=num, type=type,
                      date=date, start_date=start_date, end_date=end_date, org_started=org_started, stop_date=stop_date,
                      org_stoped=org_stoped)


def get_or_create_production(session, data, doc):
    code = data.get('@КодПрод', None)
    name = data.get('@НаимПрод', None)
    innov = data.get('@ПрОтнПрод', None)

    create_orm_object(session, Production, doc=doc, code=code, name=name, innov=innov)


def get_or_create_partnership(session, data, doc):
    name = data.get('@НаимЮЛ_ПП', None)
    inn = data.get('@ИННЮЛ_ПП', None)
    contract_num = data.get('@НомДог', None)
    contract_date = date_transform(data.get('@ДатаДог', None))

    create_orm_object(session, Partnership, doc=doc, name=name, inn=inn, contract_num=contract_num,
                      contract_date=contract_date)


def get_or_create_contract(session, data, doc):
    client_name = data.get('@НаимЮЛ_ЗК', None)
    client_inn = data.get('@ИННЮЛ_ЗК', None)
    subj = data.get('@ПредмКонтр', None)
    num = data.get('@НомКонтрРеестр', None)
    date = date_transform(data.get('@ДатаКонтр', None))

    create_orm_object(session, Contract, doc=doc, client_name=client_name, client_inn=client_inn, subj=subj, num=num,
                      date=date)


def get_or_create_agreement(session, data, doc):
    client_name = data.get('@НаимЮЛ_ЗД', None)
    client_inn = data.get('@ИННЮЛ_ЗД', None)
    subj = data.get('@ПредмДог', None)
    num = data.get('@НомДогРеестр', None)
    date = date_transform(data.get('@ДатаДог', None))

    create_orm_object(session, Agreement, doc=doc, client_name=client_name, client_inn=client_inn, subj=subj, num=num,
                      date=date)
