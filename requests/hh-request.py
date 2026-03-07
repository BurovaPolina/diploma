import requests      # Для запросов по API
import json          # Для обработки полученных результатов
import time          # Для задержки между запросами
import os            # Для работы с файлами
import pandas as pd  # Для формирования датафрейма с результатами
import datetime


def getAreas():
    req = requests.get('https://api.hh.ru/areas')
    data = req.content.decode()
    req.close()
    jsObj = json.loads(data)
    areas = []
    for k in jsObj:
        for i in range(len(k['areas'])):
            if len(k['areas'][i]['areas']) != 0:                      # Если у зоны есть внутренние зоны
                for j in range(len(k['areas'][i]['areas'])):
                    areas.append([k['id'],
                                  k['name'],
                                  k['areas'][i]['areas'][j]['id'],
                                  k['areas'][i]['areas'][j]['name']])
            else:                                                                # Если у зоны нет внутренних зон
                areas.append([k['id'],
                              k['name'],
                              k['areas'][i]['id'],
                              k['areas'][i]['name']])
    return areas

# areas = getAreas()


def get_vacancies(city, vacancy, page):
    url = 'https://api.hh.ru/vacancies'
    params = {
        # 'text': f"{vacancy} {city}",
        'area': city,
        #'specialization': 1,
        'per_page': 20,
        'page': page
    }
    headers = {
        # 'Authorization': f'Bearer {hh_api_token}'
    }

    response = requests.get(url, params=params, headers=headers)
    response.raise_for_status()
    return response.json()

general_json = []

for i in range(100):
    general_json.append(get_vacancies(98, '', i))
    time.sleep(1)
    print('page:', i)

j = []
for i in general_json:
    print('items', len(i['items']))
    j += i['items']

print(len(j))

current_datetime = datetime.datetime.now()
with open('hh_1 ' + current_datetime.strftime('%Y-%m-%d %H:%M') + '.json', 'w') as file:
    json.dump(j, file, ensure_ascii=False)