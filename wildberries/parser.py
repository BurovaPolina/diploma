from bs4 import BeautifulSoup
import json
import datetime
import re
import os
import pandas as pd


def parse_wildberries():
    """Парсинг HTML файла Wildberries и сохранение в Excel"""

    cards_dict = []

    def clean_price(price_text):
        if not price_text:
            return 0
        price_clean = re.sub(r'[^\d]', '', str(price_text))
        return int(price_clean) if price_clean else 0

    def clean_percentage(percent_text):
        if not percent_text:
            return ''
        percent_clean = re.sub(r'[^\d\-]', '', str(percent_text))
        return percent_clean if percent_clean else ''

    def extract_text(element, selector, attribute=None):
        """Безопасное извлечение текста из элемента"""
        try:
            if attribute:
                elem = element.find(selector) if isinstance(selector, str) else selector
                if elem:
                    return elem.get(attribute, '')
            else:
                elem = element.find(selector) if isinstance(selector, str) else selector
                if elem:
                    return elem.text.strip()
        except:
            pass
        return ''

    html_path = r'E:\diploma\selenium\electronics-stores\wildberries-all.html'

    if not os.path.exists(html_path):
        print(f"Ошибка: файл {html_path} не найден!")
        return

    print(f"Читаем файл: {html_path}")

    with open(html_path, 'r', encoding='utf-8') as f:
        content = f.read()

    soup = BeautifulSoup(content, 'html.parser')

    # Пробуем разные варианты поиска карточек
    all_cards = []

    # Вариант 1: article с классом product-card
    cards1 = soup.find_all('article', class_='product-card')
    if cards1:
        all_cards = cards1
        print(f"Найдено карточек по 'article.product-card': {len(cards1)}")

    # Вариант 2: div с классом product-card
    if not all_cards:
        cards2 = soup.find_all('div', class_='product-card')
        if cards2:
            all_cards = cards2
            print(f"Найдено карточек по 'div.product-card': {len(cards2)}")

    # Вариант 3: по data-атрибуту
    if not all_cards:
        cards3 = soup.find_all('div', attrs={'data-name': 'product'})
        if cards3:
            all_cards = cards3
            print(f"Найдено карточек по 'data-name=product': {len(cards3)}")

    # Вариант 4: по классу, содержащему card
    if not all_cards:
        cards4 = soup.find_all(class_=re.compile(r'card'))
        if cards4:
            all_cards = cards4
            print(f"Найдено карточек по классу с 'card': {len(cards4)}")

    if not all_cards:
        print("Не найдено карточек товаров! Проверьте структуру HTML.")
        return

    print(f"\nОбработка {len(all_cards)} карточек...")

    for i, item in enumerate(all_cards):
        if i % 100 == 0:
            print(f"Обработано {i} из {len(all_cards)}")

        try:
            # Варианты названия
            name = ''
            name_selectors = [
                ('span', 'product-card__name'),
                ('a', 'product-card__name'),
                ('span', 'goods-name'),
                ('div', 'product-name'),
                ('a', {'class': re.compile(r'name')})
            ]

            for tag, class_name in name_selectors:
                if isinstance(class_name, dict):
                    elem = item.find(tag, class_name)
                else:
                    elem = item.find(tag, class_=class_name)
                if elem:
                    name = elem.text.strip()
                    break

            # Варианты цены
            price_sell = 0
            price_selectors = [
                ('ins', 'price__lower-price'),
                ('span', 'price__lower-price'),
                ('span', 'price'),
                ('span', {'class': re.compile(r'price')})
            ]

            for tag, class_name in price_selectors:
                if isinstance(class_name, dict):
                    elem = item.find(tag, class_name)
                else:
                    elem = item.find(tag, class_=class_name)
                if elem:
                    price_sell = clean_price(elem.text)
                    if price_sell > 0:
                        break

            # Варианты скидки
            sell = ''
            sell_selectors = [
                ('span', 'percentage-sale'),
                ('span', 'sale'),
                ('div', {'class': re.compile(r'sale|discount')})
            ]

            for tag, class_name in sell_selectors:
                if isinstance(class_name, dict):
                    elem = item.find(tag, class_name)
                else:
                    elem = item.find(tag, class_=class_name)
                if elem:
                    sell = clean_percentage(elem.text)
                    if sell:
                        break

            # Варианты рейтинга
            rating = 0.0
            rating_selectors = [
                ('span', 'address-rate-mini'),
                ('span', 'rating'),
                ('div', {'class': re.compile(r'rating')})
            ]

            for tag, class_name in rating_selectors:
                if isinstance(class_name, dict):
                    elem = item.find(tag, class_name)
                else:
                    elem = item.find(tag, class_=class_name)
                if elem and elem.text:
                    try:
                        rating = float(re.search(r'(\d+\.?\d*)', elem.text).group(1))
                        break
                    except:
                        pass

            # Количество оценок
            rating_count = ''
            count_selectors = [
                ('span', 'product-card__count'),
                ('span', 'count'),
                ('span', {'class': re.compile(r'count|reviews')})
            ]

            for tag, class_name in count_selectors:
                if isinstance(class_name, dict):
                    elem = item.find(tag, class_name)
                else:
                    elem = item.find(tag, class_=class_name)
                if elem:
                    rating_count = elem.text.strip()
                    if rating_count:
                        break

            # Изображение
            img = ''
            img_elem = item.find('img')
            if img_elem:
                img = img_elem.get('src') or img_elem.get('data-src', '')

            if not name and price_sell == 0:
                continue

            cards_dict.append({
                'name': name,
                'price_sell': price_sell,
                'sell': sell,
                'img': img,
                'rating': rating,
                'rating_count': rating_count,
            })

        except Exception as e:
            print(f"Ошибка при обработке карточки {i}: {e}")

    print(f"\nВсего обработано товаров: {len(cards_dict)}")

    if len(cards_dict) == 0:
        print("\nВНИМАНИЕ: Не найдено ни одного товара!")
        print("Возможные причины:")
        print("1. Изменилась структура страницы Wildberries")
        print("2. Не загрузились товары при сборе HTML")
        print("3. Нужно обновить селекторы в парсере")
        return

    # Сохраняем результаты
    timestamp = datetime.datetime.now().strftime("%Y_%m_%d_%H_%M")

    json_path = f'wildberries_pc_{timestamp}.json'
    with open(json_path, 'w', encoding='utf-8') as file:
        json.dump(cards_dict, file, ensure_ascii=False, indent=2)

    excel_path = f'wildberries_pc_{timestamp}.xlsx'
    df = pd.DataFrame(cards_dict)
    df.to_excel(excel_path, index=False, engine='openpyxl')

    print(f"\n JSON сохранен: {json_path}")
    print(f"Excel сохранен: {excel_path}")
    print(f"Сохранено {len(cards_dict)} товаров")


if __name__ == "__main__":
    parse_wildberries()