from bs4 import BeautifulSoup
import json
import datetime
import re

cards_dict = []  # Инициализируем пустым списком, а не с пустым элементом


def item_handler(item):
    try:
        # изображение - ищем div с картинками
        img_element = item.find('div', class_='app-catalog-1dn8kmh-Wrapper--StyledImageWrapper')
        if img_element:
            picture = img_element.find('img')
            img = picture.get('src') if picture else ''
        else:
            img = ''

        # название - ищем по data-meta-name="Snippet__title"
        name_elem = item.find('a', attrs={'data-meta-name': 'Snippet__title'})
        name = name_elem.text.strip() if name_elem else ''

        # альтернативный поиск названия
        if not name:
            name_elem = item.find('div', class_='app-catalog-1p7hp34-Flex--StyledFlex-Name--StyledName')
            if name_elem:
                name_link = name_elem.find('a')
                name = name_link.text.strip() if name_link else ''

        # цена - ищем по data-meta-name="Snippet__price"
        price_elem = item.find('span', attrs={'data-meta-name': 'Snippet__price'})
        if not price_elem:
            price_elem = item.find('div', class_='app-catalog-162o4kn-MainPrice--StyledMainPrice')

        price = 0
        if price_elem:
            price_text = price_elem.text
            # очищаем от всего, кроме цифр
            price_numbers = re.findall(r'\d+', price_text)
            if price_numbers:
                price = int(''.join(price_numbers))

        # рейтинг - ищем по data-meta-name="MetaInfo_rating"
        rating_elem = item.find('div', attrs={'data-meta-name': 'MetaInfo_rating'})
        rating = 0.0
        if rating_elem:
            rating_text = rating_elem.text.strip()
            # извлекаем число с плавающей точкой
            rating_match = re.search(r'(\d+\.?\d*)', rating_text)
            if rating_match:
                rating = float(rating_match.group(1))

        # пропускаем пустые карточки
        if not name and price == 0:
            return

        cards_dict.append({
            'name': name,
            'img': img,
            'price': price,
            'rating': rating,
        })

    except Exception as e:
        print(f"Ошибка при обработке карточки: {e}")


with open('./res/citilink.html', 'r', encoding='utf-8') as f:
    soup = BeautifulSoup(f, 'html.parser')

    # пробуем разные селекторы для поиска карточек товаров
    all_cards = soup.select('div[data-meta-name="ProductVerticalSnippet"]')

    if not all_cards:
        # альтернативный селектор
        all_cards = soup.select('div[data-meta-name*="Snippet"]')

    if not all_cards:
        # поиск по классу
        all_cards = soup.find_all('div', class_=re.compile(r'VerticalSnippetGridItem'))

print(f"Найдено карточек: {len(all_cards)}")

for i, item in enumerate(all_cards):
    print(f"Обработка карточки {i + 1}")
    item_handler(item)

current_datetime = datetime.datetime.now()
filename = f'citilink_pc {current_datetime.strftime("%Y-%m-%d %H-%M")}.json'  # убрал двоеточие из имени файла
with open(filename, 'w', encoding='utf-8') as file:
    json.dump(cards_dict, file, ensure_ascii=False, indent=2)

print(f"Сохранено {len(cards_dict)} товаров в {filename}")