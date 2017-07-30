import datetime
from functools import lru_cache

from db import OKVED, License, Production, Partnership, Contract, Agreement


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


def get_or_create_extra_okved(session, data):
    code = data.get('@КодОКВЭД', None)
    name = data.get('@НаимОКВЭД', None)
    ver = data.get('@ВерсОКВЭД', None)
    extra_okved = create_orm_object(session, OKVED, code=code, name=name, ver=ver)
    return extra_okved


def get_or_create_license(session, data):
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
    lic = create_orm_object(session, License, series=series, activity=activity, address=address, num=num, type=type,
                            date=date, start_date=start_date, end_date=end_date, org_started=org_started,
                            stop_date=stop_date, org_stoped=org_stoped)
    return lic


def get_or_create_production(session, data):
    code = data.get('@КодПрод', None)
    name = data.get('@НаимПрод', None)
    innov = data.get('@ПрОтнПрод', None)
    prod = create_orm_object(session, Production, code=code, name=name, innov=innov)
    return prod


def get_or_create_partnership(session, data):
    name = data.get('@НаимЮЛ_ПП', None)
    inn = data.get('@ИННЮЛ_ПП', None)
    contract_num = data.get('@НомДог', None)
    contract_date = date_transform(data.get('@ДатаДог', None))
    pship = create_orm_object(session, Partnership, name=name, inn=inn, contract_num=contract_num,
                              contract_date=contract_date)
    return pship


def get_or_create_contract(session, data):
    client_name = data.get('@НаимЮЛ_ЗК', None)
    client_inn = data.get('@ИННЮЛ_ЗК', None)
    subj = data.get('@ПредмКонтр', None)
    num = data.get('@НомКонтрРеестр', None)
    date = date_transform(data.get('@ДатаКонтр', None))
    contr = create_orm_object(session, Contract, client_name=client_name, client_inn=client_inn, subj=subj, num=num,
                              date=date)
    return contr


def get_or_create_agreement(session, data):
    client_name = data.get('@НаимЮЛ_ЗД', None)
    client_inn = data.get('@ИННЮЛ_ЗД', None)
    subj = data.get('@ПредмДог', None)
    num = data.get('@НомДогРеестр', None)
    date = date_transform(data.get('@ДатаДог', None))
    agr = create_orm_object(session, Agreement, client_name=client_name, client_inn=client_inn, subj=subj, num=num,
                            date=date)
    return agr
