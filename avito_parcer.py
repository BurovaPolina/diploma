from bs4 import BeautifulSoup
import json
import datetime
import os
import re
import pandas as pd


def parse_avito():
    """Парсинг HTML файлов Avito и сохранение в Excel и JSON"""

    cards_dict = []
    errors = 0
    skipped_no_name = 0

    def clean_price(price_text):
        """Очистка цены от символов"""
        if not price_text:
            return 0
        price_clean = re.sub(r'[^\d]', '', str(price_text))
        return int(price_clean) if price_clean else 0

    def extract_price(item):
        """Извлечение цены из карточки"""
        # Пробуем найти цену по основному селектору
        price_elem = item.find('span', class_=re.compile(r'price-'))
        if price_elem:
            price_text = price_elem.get_text(strip=True)
            return clean_price(price_text)

        # Альтернативный поиск: мета-тег Offer
        meta_price = item.find('meta', {'itemprop': 'price'})
        if meta_price and meta_price.get('content'):
            return clean_price(meta_price.get('content'))

        # Поиск по data-marker
        price_elem = item.find('[data-marker="item-price"]')
        if price_elem:
            price_span = price_elem.find('span', class_=re.compile(r'price-'))
            if price_span:
                return clean_price(price_span.get_text(strip=True))

        # Поиск любого элемента с ценой (содержит ₽ и цифры)
        for elem in item.find_all(['span', 'p', 'strong']):
            text = elem.get_text(strip=True)
            if '₽' in text and re.search(r'\d', text):
                return clean_price(text)

        return 0

    def extract_name(item):
        """Извлечение названия"""
        # По ссылке с заголовком
        title_link = item.find('a', class_=re.compile(r'title|styles-module-root-cfrVG'))
        if title_link:
            return title_link.get_text(strip=True)

        # По h2 с itemprop="name"
        name_elem = item.find('h2', {'itemprop': 'name'})
        if name_elem:
            return name_elem.get_text(strip=True)

        # По data-marker
        title_elem = item.find('[data-marker="title"]')
        if title_elem:
            return title_elem.get_text(strip=True)

        return ''

    def extract_location(item):
        """Извлечение локации"""
        # Основной селектор для гео
        geo_elem = item.find('div', class_=re.compile(r'geo-root'))
        if geo_elem:
            return geo_elem.get_text(strip=True)

        # По data-marker
        geo_elem = item.find('[data-marker="item-location"]')
        if geo_elem:
            return geo_elem.get_text(strip=True)

        # Поиск по классу с geo
        geo_elem = item.find('p', class_=re.compile(r'geo'))
        if geo_elem:
            return geo_elem.get_text(strip=True)

        return ''

    def extract_metro(location_text):
        """Извлечение метро из текста локации"""
        if not location_text:
            return ''
        # Ищем станцию метро в скобках или после запятой
        metro_match = re.search(r'[мМ]\.?\s*([^,]+)', location_text)
        if metro_match:
            return metro_match.group(1).strip()

        # Ищем слово "метро" или "м."
        parts = re.split(r'[,.]', location_text)
        for part in parts:
            part = part.strip()
            if 'метро' in part.lower() or part.startswith('м '):
                return part.replace('метро', '').replace('м', '').strip()

        return ''

    def extract_image_url(item):
        """Извлечение URL изображения"""
        img = item.find('img')
        if img:
            # Пробуем разные атрибуты
            for attr in ['src', 'data-src', 'data-url', 'srcset']:
                url = img.get(attr, '')
                if url:
                    # Берем первый URL из srcset если есть
                    if attr == 'srcset' and url:
                        url = url.split(',')[0].split()[0]
                    if url.startswith('//'):
                        url = 'https:' + url
                    return url
        return ''

    def find_card_containers(soup):
        """Поиск контейнеров карточек"""
        containers = []

        # Способ 1: по основному классу карточки (из вашего HTML)
        containers = soup.find_all('div', class_='styles-root-Wm6wB')
        if containers:
            print(f"  Найдено по 'styles-root-Wm6wB': {len(containers)}")
            return containers

        # Способ 2: по data-marker="bx-recommendations-block-item"
        containers = soup.find_all('div', {'data-marker': 'bx-recommendations-block-item'})
        if containers:
            print(f"  Найдено по 'data-marker': {len(containers)}")
            return containers

        # Способ 3: по классу item
        containers = soup.find_all('div', class_=re.compile(r'styles-item-'))
        if containers:
            print(f"  Найдено по 'styles-item-': {len(containers)}")
            return containers

        # Способ 4: поиск parent для цены
        price_spans = soup.find_all('span', string=re.compile(r'\d+\s*[₽P]'))
        seen = set()
        for span in price_spans:
            parent = span.find_parent('div', class_=re.compile(r'styles-root|item'))
            if parent and parent not in seen:
                seen.add(parent)
                containers.append(parent)
        if containers:
            print(f"  Найдено через цены: {len(containers)}")

        return containers

    # Директория с HTML файлами
    html_dir = r'E:\diploma\playwright\avito\res'

    # Директория для сохранения результатов
    save_dir = r'E:\diploma\playwright\avito\res'

    if not os.path.exists(html_dir):
        print(f"Ошибка: директория {html_dir} не найдена!")
        return

    # Создаем директорию для сохранения
    os.makedirs(save_dir, exist_ok=True)

    html_files = [f for f in os.listdir(html_dir) if f.endswith('.html')]

    if not html_files:
        print(f"Ошибка: в {html_dir} нет HTML файлов!")
        return

    print(f"Найдено HTML файлов: {len(html_files)}")
    print(f"HTML файлы: {html_files}")
    print(f"Результаты будут сохранены в: {save_dir}")

    # Обрабатываем каждый HTML файл
    for html_file in html_files:
        html_path = os.path.join(html_dir, html_file)
        print(f"\nОбработка: {html_file}")

        try:
            with open(html_path, 'r', encoding='utf-8') as f:
                content = f.read()
                soup = BeautifulSoup(content, 'html.parser')
        except Exception as e:
            print(f"  Ошибка чтения файла: {e}")
            continue

        # Поиск карточек
        containers = find_card_containers(soup)
        print(f"  Найдено карточек: {len(containers)}")

        file_cards_count = 0
        for i, container in enumerate(containers):
            try:
                # Извлечение данные
                name = extract_name(container)
                if not name:
                    skipped_no_name += 1
                    continue

                price = extract_price(container)
                location = extract_location(container)
                metro = extract_metro(location)
                img_url = extract_image_url(container)

                cards_dict.append({
                    'name': name,
                    'price': price,
                    'location': location,
                    'metro': metro,
                    'img_url': img_url,
                })
                file_cards_count += 1

                if file_cards_count % 50 == 0:
                    print(f"    Обработано {file_cards_count} карточек в файле")

            except Exception as e:
                errors += 1
                if errors <= 10:
                    print(f"    Ошибка обработки карточки {i}: {e}")

        print(f"  Извлечено из файла: {file_cards_count}")

    print(f"\n{'=' * 60}")
    print(f"ВСЕГО ОБРАБОТАНО: {len(cards_dict)} товаров")
    print(f"Пропущено (без названия): {skipped_no_name}")
    print(f"Ошибок: {errors}")
    print(f"{'=' * 60}")

    if len(cards_dict) == 0:
        print("\nВНИМАНИЕ: Не найдено ни одного товара!")
        print("Проверьте структуру HTML файлов.")
        print("Пример названия файла с объявлениями должен содержать карточки товаров.")
        return

    # Сохранение результатов
    timestamp = datetime.datetime.now().strftime("%Y_%m_%d_%H_%M_%S")

    # Сохранение JSON
    json_path = os.path.join(save_dir, f'avito_parsed_{timestamp}.json')
    with open(json_path, 'w', encoding='utf-8') as file:
        json.dump(cards_dict, file, ensure_ascii=False, indent=2)
    print(f"\n✓ JSON сохранен: {json_path}")
    print(f"  Размер: {len(cards_dict)} записей, {os.path.getsize(json_path) / 1024:.1f} KB")

    # Сохранение Excel
    excel_path = os.path.join(save_dir, f'avito_parsed_{timestamp}.xlsx')
    df = pd.DataFrame(cards_dict)

    # Добавление столбец с датой парсинга
    df['parse_date'] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Переупорядочивание колонки
    df = df[['name', 'price', 'location', 'metro', 'img_url', 'parse_date']]

    df.to_excel(excel_path, index=False, engine='openpyxl')
    print(f"✓ Excel сохранен: {excel_path}")
    print(f"  Размер: {len(df)} строк, {os.path.getsize(excel_path) / 1024:.1f} KB")

    # Статистика по ценам
    if len(cards_dict) > 0:
        prices = [c['price'] for c in cards_dict if c['price'] > 0]
        if prices:
            print(f"\n📊 Статистика:")
            print(f"  Средняя цена: {sum(prices) // len(prices):,} ₽")
            print(f"  Мин. цена: {min(prices):,} ₽")
            print(f"  Макс. цена: {max(prices):,} ₽")

            # Распределение по диапазонам цен
            price_ranges = {
                'до 1 млн': len([p for p in prices if p < 1_000_000]),
                '1-5 млн': len([p for p in prices if 1_000_000 <= p < 5_000_000]),
                '5-10 млн': len([p for p in prices if 5_000_000 <= p < 10_000_000]),
                '10-20 млн': len([p for p in prices if 10_000_000 <= p < 20_000_000]),
                '20-50 млн': len([p for p in prices if 20_000_000 <= p < 50_000_000]),
                'более 50 млн': len([p for p in prices if p >= 50_000_000])
            }
            print(f"\n  Распределение по цене:")
            for range_name, count in price_ranges.items():
                if count > 0:
                    print(f"    {range_name}: {count}")

    print(f"\n Готово! Сохранено {len(cards_dict)} товаров в {save_dir}")


if __name__ == "__main__":
    parse_avito()