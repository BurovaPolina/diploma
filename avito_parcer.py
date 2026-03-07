import zipfile
from pprint import pprint
from turtledemo.penrose import start

from bs4 import BeautifulSoup
import json
import datetime


cards_dict = []
all_cards = []
erroor = 0

flat = 0
room = 0
# function
def item_handler(item):
    pass
    try:
        global flat, room, street, metro, metro_time
        # name
        name = item.find('a', class_='styles-module-root-cfrVG')
        name = list(name)


        # room and flat
        if name[0][0].isdigit():
            room = name[0][:3]
            name = name[0][5:]
            if name[0][0] == 'а':
                flat = 'апартаменты'
            elif name[0][0] == 'к':
                flat = 'квартира'
        else:
            if name[0][0] == 'А':
                flat = 'апартаменты'
            elif name[0][0] == 'К':
                flat = 'квартира-студия'
            name = name[0]

        # print('room :', room)
        # print('flat :', flat)
        name = name[name.index(',') +2:]


        # amount
        amount = ''
        for i in name:
            if i.isdigit():
                amount += i
            else:
                break


        # print('amount : ', *amount, sep='')
        name = name[name.index(',') + 2:]
        if name.count(',') > 0:
            name = name[name.index(',') + 2:]


        # floor and floor_all
        # print(name)
        floor = name[:name.index('/')]
        floor_all = name[name.index('/') +1: -4]

        # print('floor :', floor)
        # print('floor_all :', floor_all)


        # price
        price = item.find('p', class_='styles-module-root-PY1ie').text[:-1].replace(' ', '')
        # print('price :', price)


        # price_amount
        price_amount_elem = item.find('span', class_='price-root-tm5ut')
        price_amount_elem = list(price_amount_elem.text)
        price_amount_elem = price_amount_elem[price_amount_elem.index('₽'):]
        price_amount = ''

        for i in price_amount_elem:
            if i.isdigit() and i != '²':
                price_amount += i

        # print('price_amount :', price_amount)


        # street
        geo = item.find('div', class_='geo-root-BBVai').text
        # print('geo', geo)
        if geo.count(','):
            street = geo[4:geo.index(',')]

        # print('street :', street)


        # description
        description = item.find('p', class_='styles-module-margin-bottom_4-OpB5i')
        if description:
            description = description.text
        # print('description :', description)


        # company
        company_elem = item.find('div', class_='iva-item-userInfoStep-WpSc2')
        if company_elem:
            company = ''
            for el in company_elem.text:
                if el.isdigit():
                    break
                else:
                    company += el
        else:
            company = 'None'
        # print(company)



        # bonus
        bonus_elem = item.find_all('div', class_='SnippetLayout-item-_JoCY')
        bonus = []
        if len(bonus_elem) > 0:
            for i in bonus_elem:
                bonus.append(i.text)
                # print(bonus)


        # metro and metro_time
        metro_elem = item.find('p', class_='styles-module-margin-top_0-gaF9v')
        if metro_elem:
            if metro_elem.text.count(',') > 0:
                metro_elem = metro_elem.text
                mee = str(metro_elem).index(',')
                metro_time = str(metro_elem[mee +2: -5])
                metro = str(metro_elem[:mee])

            elif metro_elem.text[:2] == 'р-н':
                metro = metro_elem.text
                metro_time = 'None'

            else:
                metro = 'None'
                metro_time = 'None'

        else:
            metro = 'None'
            metro_time = 'None'

        cards_dict.append({
            'room': room,
            'flat': flat,
            'amount': amount,
            'price_amount': price_amount,
            'price': price,
            'floor': floor,
            'floor_all': floor_all,
            'street': street,
            'metro' : metro,
            'metro_time' : metro_time,
            'company': company,
            'bonus': bonus,
            'description': description,
        })


    except Exception as e:
        print(e)
        erroor += 1


with zipfile.ZipFile('avito-html.zip', 'r') as zip_ref:
    combined_content = ""
    for file_name in zip_ref.namelist():
        with zip_ref.open(file_name) as file:
            combined_content += file.read().decode('utf-8')




soup = BeautifulSoup(combined_content, 'html.parser')

# print(soup.prettify())

all_cards = soup.find_all('div', class_ ='iva-item-content-fRmzq')
print(len(all_cards))

i = 0
for item in all_cards:
    print(i)
    i += 1
    item_handler(item)


current_datetime = datetime.datetime.now()

# print(cards_dict)
start = ''

print(cards_dict)
print('erroor', erroor)
with open('avito.json', 'w', encoding="utf-8") as file:
    json.dump(cards_dict, file, ensure_ascii=False)
