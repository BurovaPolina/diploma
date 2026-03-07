import zipfile
from bs4 import BeautifulSoup
import json
import datetime

cards_dict = [{
    'name': '',
    'price_sell': 0,
    'sell': 0,
    'img': '',
    'rating': 0.0,
    'rating_count' : '',
}]

all_cards = []

# function
def item_handler(item):
    pass
    try:

        #name
        name = item.find('span', class_='product-card__name')
        print('name', name.text)

        #price_sell
        price_sell = item.find('ins', class_='price__lower-price')
        price_sell_text = price_sell.text.strip('₽').replace(' ', '')
        print('price', price_sell_text)

        #price


        # sell
        sell = item.find('span', class_ = 'percentage-sale')
        print('sell', sell.text)

        #rating
        rating = item.find('span', class_='address-rate-mini address-rate-mini--sm')
        if rating == None :
            rating = 0.0
        else:
            rating = rating.text
        print('rating', rating)

        # rating_count
        rating_count = item.find('span', class_ = 'product-card__count')
        rating_count = rating_count.text
        print('rating_count', rating_count)

        #image
        img_elem = item.find('img', class_='j-thumbnail')
        # picture = img.findChildren('img')[0]
        img = img_elem.get('src')
        print('image', img)

        cards_dict.append({
            'name': name.text.strip(),
            'sell': sell.text,
            'img': img,
            'price_sell': price_sell_text,
            'rating': rating,
            'rating_count' : rating_count,
        })
    except Exception as e:
        print(e)


with zipfile.ZipFile('wildberries-.zip', 'r') as zip_ref:
    combined_content = ""
    for file_name in zip_ref.namelist():
        with zip_ref.open(file_name) as file:
            combined_content += file.read().decode('utf-8')


soup = BeautifulSoup(combined_content, 'html.parser')

print(soup.prettify())

all_cards = soup.find_all('article', class_ ='product-card')
print(len(all_cards))

i = 0
for item in all_cards:
    print(i)
    i += 1
    item_handler(item)

current_datetime = datetime.datetime.now()

with open('wildberries_pc ' + current_datetime.strftime('%Y-%m-%d %H:%M') + '.json', 'w') as file:
    json.dump(cards_dict, file, ensure_ascii=False)
