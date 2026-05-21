# dns_parser.py
from bs4 import BeautifulSoup
import json
import datetime
import os
import re
import pandas as pd
from typing import List, Dict, Optional

# Селекторы для DNS
SELECTOR_CARD = 'div.catalog-product'
SELECTOR_IMAGE = 'img.catalog-product__image'
SELECTOR_NAME = 'a.catalog-product__name'
SELECTOR_PRICE = 'div.product-buy__price'
SELECTOR_OLD_PRICE = 'div.product-buy__price-old'
SELECTOR_RATING = 'div.catalog-product__rating'
SELECTOR_RATING_VALUE = 'b'
SELECTOR_REVIEWS_COUNT = 'a.catalog-product__rating span'
SELECTOR_AVAILABILITY = 'div.product-buy__status'


def clean_price(price_text: str) -> int:
    """Очистка цены от символов"""
    if not price_text:
        return 0
    price_clean = re.sub(r'[^\d]', '', str(price_text))
    return int(price_clean) if price_clean else 0


def extract_image_url(item) -> Optional[str]:
    """Извлекает URL изображения из элемента карточки"""
    try:
        img = item.find('img', class_='catalog-product__image')
        if img:
            # Пробуем разные атрибуты
            for attr in ['src', 'data-src', 'srcset']:
                url = img.get(attr, '')
                if url:
                    if attr == 'srcset' and url:
                        url = url.split(',')[0].split()[0]
                    if url.startswith('//'):
                        url = 'https:' + url
                    return url
        return None
    except Exception as e:
        print(f"Error extracting image: {e}")
        return None


def extract_name(item) -> Optional[str]:
    """Извлекает название товара из элемента карточки"""
    try:
        name_element = item.find('a', class_='catalog-product__name')
        return name_element.get_text(strip=True) if name_element else None
    except Exception as e:
        print(f"Error extracting name: {e}")
        return None


def extract_price(item) -> Optional[int]:
    """Извлекает и форматирует цену товара"""
    try:
        price_element = item.find('div', class_='product-buy__price')
        if price_element:
            price_text = price_element.get_text(strip=True)
            return clean_price(price_text)
        return None
    except Exception as e:
        print(f"Error extracting price: {e}")
        return None


def extract_old_price(item) -> Optional[int]:
    """Извлекает старую цену (со скидкой)"""
    try:
        old_price_element = item.find('div', class_='product-buy__price-old')
        if old_price_element:
            price_text = old_price_element.get_text(strip=True)
            return clean_price(price_text)
        return None
    except Exception as e:
        return None


def extract_rating(item) -> Optional[float]:
    """Извлекает рейтинг товара"""
    try:
        rating_container = item.find('div', class_='catalog-product__rating')
        if rating_container:
            rating_elem = rating_container.find('b')
            if rating_elem:
                try:
                    rating_text = rating_elem.text.replace(',', '.').strip()
                    return float(rating_text)
                except ValueError:
                    return None
        return None
    except Exception as e:
        print(f"Error extracting rating: {e}")
        return None


def extract_reviews_count(item) -> Optional[int]:
    """Извлекает количество отзывов"""
    try:
        rating_container = item.find('a', class_='catalog-product__rating')
        if rating_container:
            count_span = rating_container.find('span')
            if count_span:
                count_text = count_span.get_text(strip=True)
                count_match = re.search(r'(\d+)', count_text)
                if count_match:
                    return int(count_match.group(1))
        return None
    except Exception as e:
        print(f"Error extracting reviews count: {e}")
        return None


def extract_availability(item) -> Optional[str]:
    """Извлекает статус наличия товара"""
    try:
        status_elem = item.find('div', class_='product-buy__status')
        if status_elem:
            return status_elem.get_text(strip=True)
        return None
    except Exception as e:
        return None


def process_item(item) -> Optional[Dict]:
    """Обрабатывает один элемент карточки и возвращает словарь с данными"""
    if item is None:
        return None

    try:
        name = extract_name(item)
        if not name:
            return None

        card_data = {
            'name': name,
            'img': extract_image_url(item),
            'price': extract_price(item),
            'old_price': extract_old_price(item),
            'rating': extract_rating(item),
            'reviews_count': extract_reviews_count(item),
            'availability': extract_availability(item)
        }

        return card_data
    except Exception as e:
        print(f"Error processing item: {e}")
        return None


def parse_html_file(filepath: str) -> List[Dict]:
    """Парсит HTML файл и извлекает информацию о товарах"""

    if not os.path.exists(filepath):
        print(f"Ошибка: файл {filepath} не найден!")
        return []

    print(f"Читаем файл: {filepath}")

    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        soup = BeautifulSoup(content, 'html.parser')
    except Exception as e:
        print(f"Ошибка чтения файла: {e}")
        return []

    cards_data = []

    # Поиск карточек товаров
    product_cards = []

    # Способ 1: по классу catalog-product
    product_cards = soup.find_all('div', class_='catalog-product')
    if product_cards:
        print(f"Найдено карточек по 'catalog-product': {len(product_cards)}")

    # Способ 2: по классу product-card
    if not product_cards:
        product_cards = soup.find_all('div', class_='product-card')
        if product_cards:
            print(f"Найдено карточек по 'product-card': {len(product_cards)}")

    # Способ 3: по data-атрибуту
    if not product_cards:
        product_cards = soup.find_all('div', attrs={'data-product-id': True})
        if product_cards:
            print(f"Найдено карточек по 'data-product-id': {len(product_cards)}")

    if not product_cards:
        print("Не найдено карточек товаров! Проверьте структуру HTML.")
        return []

    print(f"\nОбработка {len(product_cards)} карточек...")

    for i, card in enumerate(product_cards):
        if i % 50 == 0 and i > 0:
            print(f"  Обработано {i} из {len(product_cards)}")

        card_data = process_item(card)
        if card_data:
            cards_data.append(card_data)

    print(f"\nУспешно обработано: {len(cards_data)} товаров")
    return cards_data


def save_to_json(data: List[Dict], save_dir: str, filename_prefix: str = 'dns_pc') -> str:
    """Сохраняет данные в JSON файл с текущей датой в имени"""
    os.makedirs(save_dir, exist_ok=True)

    current_datetime = datetime.datetime.now()
    filename = f"{filename_prefix}_{current_datetime.strftime('%Y_%m_%d_%H_%M_%S')}.json"
    filepath = os.path.join(save_dir, filename)

    with open(filepath, 'w', encoding='utf-8') as file:
        json.dump(data, file, ensure_ascii=False, indent=2)

    return filepath


def save_to_excel(data: List[Dict], save_dir: str, filename_prefix: str = 'dns_pc') -> str:
    """Сохраняет данные в Excel файл"""
    os.makedirs(save_dir, exist_ok=True)

    current_datetime = datetime.datetime.now()
    filename = f"{filename_prefix}_{current_datetime.strftime('%Y_%m_%d_%H_%M_%S')}.xlsx"
    filepath = os.path.join(save_dir, filename)

    df = pd.DataFrame(data)
    df.to_excel(filepath, index=False, engine='openpyxl')

    return filepath


def print_statistics(data: List[Dict]):
    """Выводит статистику по данным"""
    if not data:
        return

    print(f"\n{'=' * 60}")
    print("📊 СТАТИСТИКА")
    print(f"{'=' * 60}")

    # Цены
    prices = [item['price'] for item in data if item['price'] and item['price'] > 0]
    if prices:
        print(f"\n💰 Цены:")
        print(f"  Средняя цена: {sum(prices) // len(prices):,} ₽")
        print(f"  Мин. цена: {min(prices):,} ₽")
        print(f"  Макс. цена: {max(prices):,} ₽")

        # Распределение по диапазонам
        ranges = {
            'до 10 000 ₽': len([p for p in prices if p < 10000]),
            '10 000 - 50 000 ₽': len([p for p in prices if 10000 <= p < 50000]),
            '50 000 - 100 000 ₽': len([p for p in prices if 50000 <= p < 100000]),
            '100 000 - 500 000 ₽': len([p for p in prices if 100000 <= p < 500000]),
            'более 500 000 ₽': len([p for p in prices if p >= 500000])
        }
        print(f"\n  Распределение по цене:")
        for range_name, count in ranges.items():
            if count > 0:
                print(f"    {range_name}: {count}")

    # Рейтинги
    ratings = [item['rating'] for item in data if item['rating']]
    if ratings:
        print(f"\n⭐ Рейтинги:")
        print(f"  Средний рейтинг: {sum(ratings) / len(ratings):.2f}")
        print(f"  Макс. рейтинг: {max(ratings):.1f}")
        print(f"  Мин. рейтинг: {min(ratings):.1f}")

    # Наличие
    availabilities = [item['availability'] for item in data if item['availability']]
    if availabilities:
        from collections import Counter
        avail_counts = Counter(availabilities)
        print(f"\n📦 Наличие:")
        for status, count in avail_counts.most_common(5):
            print(f"  {status}: {count}")

    # Скидки
    discount_count = len([item for item in data if item['old_price'] and item['old_price'] > item['price']])
    if discount_count > 0:
        print(f"\n🏷️ Скидки: {discount_count} товаров ({discount_count / len(data) * 100:.1f}%)")


def main():
    """Основная функция для выполнения скрипта"""

    # Пути к файлам
    html_dir = r'E:\diploma\selenium\electronics-stores'
    html_file = os.path.join(html_dir, 'dns.html')

    # Директория для сохранения результатов (та же, где лежит HTML)
    save_dir = r'E:\diploma\selenium\electronics-stores'

    print("=" * 60)
    print("DNS PARSER")
    print("=" * 60)
    print(f"HTML файл: {html_file}")
    print(f"Директория сохранения: {save_dir}")
    print("=" * 60)

    # Парсим HTML
    cards_data = parse_html_file(html_file)

    if not cards_data:
        print("\n❌ Не найдено данных для сохранения!")
        return

    # Сохраняем JSON
    json_file = save_to_json(cards_data, save_dir)
    print(f"\n✓ JSON сохранен: {json_file}")
    print(f"  Размер: {len(cards_data)} записей, {os.path.getsize(json_file) / 1024:.1f} KB")

    # Сохраняем Excel
    excel_file = save_to_excel(cards_data, save_dir)
    print(f"✓ Excel сохранен: {excel_file}")
    print(f"  Размер: {len(cards_data)} строк, {os.path.getsize(excel_file) / 1024:.1f} KB")

    # Выводим статистику
    print_statistics(cards_data)

    print(f"\n✅ Готово! Сохранено {len(cards_data)} товаров в {save_dir}")


if __name__ == '__main__':
    main()