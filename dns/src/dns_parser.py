from bs4 import BeautifulSoup
import json
import datetime
from typing import List, Dict, Optional


# Селекторы вынесены в константы
SELECTOR_CARD = 'div.catalog-product'
SELECTOR_IMAGE_CONTAINER = 'div.catalog-product__image'
SELECTOR_NAME = 'a.catalog-product__name'
SELECTOR_PRICE = 'div.product-buy__price'
SELECTOR_RATING_CONTAINER = 'a.catalog-product__rating'
SELECTOR_RATING_VALUE = 'b'


def create_card_template() -> List[Dict]:
    return [{'name': '', 'price': 0, 'img': '', 'rating': 0.0}]

def extract_image_url(item) -> Optional[str]:
    """Извлекает URL изображения из элемента карточки"""
    try:
        img_container = item.select_one(SELECTOR_IMAGE_CONTAINER)
        if img_container:
            source = img_container.select('picture source[srcset]')
            if source:
                return source[0]['srcset']
        return None
    except Exception as e:
        print(f"Error extracting image: {e}")
        return None


def extract_name(item) -> Optional[str]:
    """Извлекает название товара из элемента карточки"""
    try:
        name_element = item.select_one(SELECTOR_NAME)
        return name_element.get_text(strip=True) if name_element else None
    except Exception as e:
        print(f"Error extracting name: {e}")
        return None


def extract_price(item) -> Optional[int]:
    """Извлекает и форматирует цену товара из элемента карточки"""
    try:
        price_element = item.select_one(SELECTOR_PRICE)
        if price_element:
            price_text = price_element.get_text(strip=True)
            # Удаляем всё, кроме цифр
            price_clean = ''.join(c for c in price_text if c.isdigit())
            return int(price_clean) if price_clean else None
        return None
    except Exception as e:
        print(f"Error extracting price: {e}")
        return None


def extract_rating(item) -> Optional[float]:
    rating_elem = item.select_one(f"{SELECTOR_RATING_CONTAINER} {SELECTOR_RATING_VALUE}")
    if rating_elem:
        try:
            return float(rating_elem.text.replace(" ", ""))
        except ValueError:
            return None
    return None


def process_item(item) -> Dict:
    """"Обрабатывает один элемент карточки и возвращает словарь с данными"""
    if item is None:
        return None

    try:
        card_data = {
            'name': extract_name(item),
            'img': extract_image_url(item),
            'price': extract_price(item),
            'rating': extract_rating(item)
        }

        # Проверяем, что хотя бы одно поле заполнено
        if any(card_data.values()):
            return card_data
        return None
    except Exception as e:
        print(f"Error processing item: {e}")
        return None



def parse_html_file(file_path: str) -> List[Dict]:
    """Парсит HTML файл и возвращает список карточек"""
    with open(file_path) as f:
        soup = BeautifulSoup(f, 'html.parser')
        all_cards = soup.select(SELECTOR_CARD)

    cards = create_card_template()
    for item in all_cards:
        card_data = process_item(item)
        if card_data:
            cards.append(card_data)

    return cards


def save_to_json(data: List[Dict], filename_prefix: str = 'dns_pc') -> str:
    """Сохраняет данные в JSON файл с текущей датой в имени"""
    current_datetime = datetime.datetime.now()
    filename = f"{filename_prefix} {current_datetime.strftime('%Y-%m-%d %H:%M')}.json"

    with open(filename, 'w') as file:
        json.dump(data, file, ensure_ascii=False)

    return filename


def main():
    """Основная функция для выполнения скрипта"""
    cards_data = parse_html_file('res/dns.html')
    saved_file = save_to_json(cards_data)
    print(f"Data saved to {saved_file}")


if __name__ == '__main__':
    main()