from bs4 import BeautifulSoup
import json
import datetime

cards_dict = [{
    'name': '',
    'price': 0,
    'discount': 0,
    'price_discount': 0,
    'quantit': '',
    'img-ref': '',
    'rating': 0.0,
}]

all_cards = []

def item_handler(item):
    # print(item)
    try:
        #image
        img = item.find('img', class_='jn5_25')

        #name
        name = item.find('span', class_='tsBody500Medium')

        #price
        price = item.find('span', class_='tsBodyControl400Small')

        #discount
        discount = item.find('span', class_='c3025-b4')

        #price_discount
        price_discount = item.find('span', class_='c3025-a1')

        #quantit
        quantit_elem = item.find('div', class_='bq017-a')
        quantit = ''
        if quantit_elem:
            quantit = quantit_elem.find('span', class_='tsBodyControl400Small')
            if quantit:
                quantit = quantit.text




        #rating
        rating = item.find('span', class_='p6b18-a4')
        if rating:
            rating = float(rating.text)

        print('rating :', rating)


        cards_dict.append({
            'name': name.text,
            'price': int(price.text.replace(' ', '').replace('₽', '')),
            'discount': discount.text,
            'price_discount': int(price_discount.text.replace(' ', '').replace('₽', '')),
            'quantit': quantit,
            'img-ref': img.attrs['src'],
            'rating': rating,
        })

    except Exception as e:
        print(e)


with open('./ozon_pc.html') as f:
    soup = BeautifulSoup(f, 'html.parser')
    all_cards = soup.find_all('div', class_='jm2_25')

for item in all_cards:
    item_handler(item)

current_datetime = datetime.datetime.now()
with open('ozon_pc ' + current_datetime.strftime('%Y-%m-%d %H:%M') + '.json', 'w') as file:
    json.dump(cards_dict, file, ensure_ascii=False)
