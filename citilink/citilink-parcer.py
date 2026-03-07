from bs4 import BeautifulSoup
import json
import datetime

cards_dict = [{
    'name': '',
    'price': 0,
    'img-ref': '',
    'rating': 0.0,
    # 'process' : '',
}]

all_cards = []

def item_handler(item):
    pass
    try:
        #image
        img_element = item.find('div', class_='app-catalog-lxji0k')
        picture = img_element.findChildren('img')[0]
        img = picture.get('src')

        #name
        name = item.find('div', class_='app-catalog-1tp0ino')
        print(name.text)

        #price product-buy__price
        price = item.find('div', class_='app-catalog-1ret8x8')

        #rating
        rating_elem = item.find('div', class_='e8eovjk0')
        print(rating_elem)

        rating = 0.0
        if rating_elem == None:
            rating = 0.0
        else:
            rating = float(rating_elem.text.replace(" ", ""))

        #process
        # process_elem = item.find('div', class_='e1l56t9a0)
        # process = float(process_elem.text.replace(" ", ""))


        cards_dict.append({
            'name': name.text.strip(),
            'img': img,
            'price': int(price.text.strip().replace('₽', '').replace(" ", "").replace('\xa0106499', '')),
            'rating': rating,
            # 'process': pro
            # cess,
        })
    except Exception as e:
        print(e)


with open('./res/citilink.html') as f:
    soup = BeautifulSoup(f, 'html.parser')
    all_cards = soup.findAll('div', class_='app-catalog-1bogmvw')

print(len(all_cards))

i = 0

for item in all_cards:
    print(i)
    i += 1
    item_handler(item)

current_datetime = datetime.datetime.now()

with open('citilink_pc ' + current_datetime.strftime('%Y-%m-%d %H:%M') + '.json', 'w') as file:
    json.dump(cards_dict, file, ensure_ascii=False)
