from bs4 import BeautifulSoup
import json
import datetime
import os
import pandas as pd

# Инициализация пустого списка
cards_dict = []


def clean_price(price_str):
    """Очистка строки цены от лишних символов"""
    if not price_str:
        return 0
    # Удаляем все пробельные символы, символы валют, заменяем тонкие пробелы
    cleaned = price_str.replace(' ', '').replace('₽', '').replace(' ', '').replace('\u2009', '').replace(',', '')
    # Извлекаем только цифры
    import re
    numbers = re.findall(r'\d+', cleaned)
    return int(''.join(numbers)) if numbers else 0


def item_handler(item, index):
    try:
        # Пробуем разные варианты поиска изображения
        img = (item.find('img', class_='jn5_25') or
               item.find('img', class_='a9i5_25') or
               item.find('img', class_='image'))
        img_ref = img.attrs.get('src', '') if img else ''
        if img_ref and img_ref.startswith('//'):
            img_ref = 'https:' + img_ref

        # Пробуем разные варианты поиска названия
        name = (item.find('span', class_='tsBody500Medium') or
                item.find('a', class_='tile-link') or
                item.find('div', class_='title'))
        name_text = name.text.strip() if name else f'No name {index}'

        # Пробуем разные варианты поиска цены
        price = (item.find('span', class_='tsBodyControl400Small') or
                 item.find('span', class_='price') or
                 item.find('div', class_='price'))
        price_value = clean_price(price.text) if price else 0

        # Пробуем разные варианты поиска скидки
        discount = (item.find('span', class_='c3025-b4') or
                    item.find('span', class_='discount'))
        discount_text = discount.text.strip() if discount else ''

        # Пробуем разные варианты поиска цены со скидкой
        price_discount = (item.find('span', class_='c3025-a1') or
                          item.find('span', class_='price-discount'))
        price_discount_value = clean_price(price_discount.text) if price_discount else price_value

        # Пробуем разные варианты поиска наличия
        quantit = ''
        quantit_elem = (item.find('div', class_='bq017-a') or
                        item.find('div', class_='stock'))
        if quantit_elem:
            quantit_span = (quantit_elem.find('span', class_='tsBodyControl400Small') or
                            quantit_elem.find('span'))
            if quantit_span:
                quantit = quantit_span.text.strip()

        # Пробуем разные варианты поиска рейтинга
        rating = (item.find('span', class_='p6b18-a4') or
                  item.find('span', class_='rating'))
        rating_value = float(rating.text) if rating and rating.text else 0.0

        card_data = {
            'name': name_text,
            'price': price_value,
            'discount': discount_text,
            'price_discount': price_discount_value,
            'quantit': quantit,
            'img-ref': img_ref,
            'rating': rating_value,
        }

        # Добавляем только если есть название и цена
        if name_text != f'No name {index}' or price_value > 0:
            cards_dict.append(card_data)
            print(f'Added [{len(cards_dict)}]: {name_text[:50]} - {price_value}₽')
            return True
        return False

    except Exception as e:
        print(f'Error processing item {index}: {e}')
        return False


def save_to_json(data, filename):
    """Сохранение данных в JSON файл"""
    try:
        with open(filename, 'w', encoding='utf-8') as file:
            json.dump(data, file, ensure_ascii=False, indent=4)
        print(f'✓ JSON saved to: {filename}')
        return True
    except Exception as e:
        print(f'✗ Error saving JSON: {e}')
        return False


def save_to_excel(data, filename):
    """Сохранение данных в Excel файл"""
    try:
        # Создаем DataFrame из данных
        df = pd.DataFrame(data)

        # Переименовываем колонки для удобства
        df.columns = ['Название', 'Цена', 'Скидка', 'Цена со скидкой', 'Наличие', 'Ссылка на изображение', 'Рейтинг']

        # Создаем Excel файл с несколькими листами
        with pd.ExcelWriter(filename, engine='openpyxl') as writer:
            # Основной лист с данными
            df.to_excel(writer, sheet_name='Товары', index=False)

            # Лист со статистикой
            stats_data = {
                'Показатель': ['Всего товаров', 'Средняя цена', 'Мин. цена', 'Макс. цена',
                               'Средний рейтинг', 'Товаров со скидкой', 'Товаров в наличии'],
                'Значение': [
                    len(df),
                    round(df['Цена'].mean(), 2) if not df['Цена'].empty else 0,
                    df['Цена'].min() if not df['Цена'].empty else 0,
                    df['Цена'].max() if not df['Цена'].empty else 0,
                    round(df['Рейтинг'].mean(), 2) if not df['Рейтинг'].empty else 0,
                    len(df[df['Скидка'] != '']),
                    len(df[df['Наличие'] != ''])
                ]
            }
            stats_df = pd.DataFrame(stats_data)
            stats_df.to_excel(writer, sheet_name='Статистика', index=False)

            # Настраиваем ширину колонок
            worksheet = writer.sheets['Товары']
            for column in worksheet.columns:
                max_length = 0
                column_letter = column[0].column_letter
                for cell in column:
                    try:
                        if len(str(cell.value)) > max_length:
                            max_length = len(str(cell.value))
                    except:
                        pass
                adjusted_width = min(max_length + 2, 50)
                worksheet.column_dimensions[column_letter].width = adjusted_width

        print(f'✓ Excel saved to: {filename}')
        return True
    except Exception as e:
        print(f'✗ Error saving Excel: {e}')
        return False


# Определяем текущую директорию проекта
current_dir = os.path.dirname(os.path.abspath(__file__))

# Путь к HTML файлу
html_path = os.path.join(current_dir, '..', 'selenium', 'electronics-stores', 'res', 'ozon_pc.html')

# Проверка существования файла
if not os.path.exists(html_path):
    print(f'File not found: {html_path}')
    exit(1)

print(f'Found HTML file: {html_path}')

# Парсинг HTML
try:
    with open(html_path, 'r', encoding='utf-8') as f:
        content = f.read()
        soup = BeautifulSoup(content, 'html.parser')

    # Пробуем разные селекторы для поиска товаров
    possible_selectors = [
        'div.jm2_25',
        'div[class*="jm2"]',
        'div[class*="tile"]',
        'div[data-testid="tile"]',
        'div[class*="product"]',
        'div[class*="item"]',
        'div[class*="card"]',
        'a[class*="tile"]',
    ]

    all_cards = []
    for selector in possible_selectors:
        cards = soup.select(selector)
        if cards:
            print(f'Found {len(cards)} items with selector: {selector}')
            all_cards = cards
            break

    if not all_cards:
        # Если не нашли по селекторам, попробуем найти все div с потенциальными товарами
        all_divs = soup.find_all('div')
        for div in all_divs:
            if div.get('class') and any(cls in str(div.get('class')) for cls in ['tile', 'product', 'item', 'card']):
                all_cards.append(div)

        if all_cards:
            print(f'Found {len(all_cards)} potential items by heuristic search')
        else:
            # Выводим первые несколько классов из HTML для отладки
            print("\nDebug: No items found. First few div classes in HTML:")
            for i, div in enumerate(soup.find_all('div')[:20]):
                if div.get('class'):
                    print(f'  {i}: {div.get("class")}')

    print(f'Processing {len(all_cards)} items...')

    for idx, item in enumerate(all_cards[:100]):  # Ограничиваем первыми 100 для теста
        item_handler(item, idx)

    print(f'\n✓ Successfully parsed {len(cards_dict)} items')

except Exception as e:
    print(f'Error reading HTML file: {e}')
    import traceback

    traceback.print_exc()
    exit(1)

# Сохранение результата
if cards_dict:
    # Создаем директорию для результатов
    results_dir = os.path.join(current_dir, 'results')
    os.makedirs(results_dir, exist_ok=True)

    current_datetime = datetime.datetime.now()
    timestamp = current_datetime.strftime("%Y-%m-%d_%H-%M")

    json_filename = os.path.join(results_dir, f'ozon_pc_{timestamp}.json')
    excel_filename = os.path.join(results_dir, f'ozon_pc_{timestamp}.xlsx')

    print('\n' + '=' * 50)
    print('Saving results...')
    print('=' * 50)

    # Сохраняем в JSON
    save_to_json(cards_dict, json_filename)

    # Сохраняем в Excel
    save_to_excel(cards_dict, excel_filename)

    print('\n' + '=' * 50)
    print(f'✅ Total items saved: {len(cards_dict)}')
    print(f'📁 JSON file: {json_filename}')
    print(f'📊 Excel file: {excel_filename}')
    print('=' * 50)

    # Выводим небольшую статистику
    print('\n📈 Quick Statistics:')
    print(f'   • Total products: {len(cards_dict)}')
    prices = [item['price'] for item in cards_dict if item['price'] > 0]
    if prices:
        print(f'   • Average price: {sum(prices) // len(prices)}₽')
        print(f'   • Price range: {min(prices)}₽ - {max(prices)}₽')
    ratings = [item['rating'] for item in cards_dict if item['rating'] > 0]
    if ratings:
        print(f'   • Average rating: {sum(ratings) / len(ratings):.1f}/5')
    with_discount = [item for item in cards_dict if item['discount']]
    if with_discount:
        print(f'   • Products with discount: {len(with_discount)} ({len(with_discount) * 100 // len(cards_dict)}%)')

else:
    print('\n❌ No data to save')

    # Выводим пример структуры HTML для отладки
    print("\nDebug: First 2000 characters of HTML:")
    with open(html_path, 'r', encoding='utf-8') as f:
        preview = f.read()[:2000]
        print(preview)