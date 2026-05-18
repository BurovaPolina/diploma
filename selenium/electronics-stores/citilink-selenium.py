import time
import json
import datetime
import os
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
import pandas as pd


def setup_driver():
    """Настройка и запуск браузера"""
    options = Options()
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument("start-maximized")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    options.add_experimental_option("excludeSwitches", ["test-type"])
    options.add_argument("--incognito")

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    driver.delete_all_cookies()

    # Маскировка под реального пользователя
    driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
        'source': '''
            delete window.cdc_adoQpoasnfa76pfcZLmcfl_Array;
            delete window.cdc_adoQpoasnfa76pfcZLmcfl_Promise;
            delete window.cdc_adoQpoasnfa76pfcZLmcfl_Symbol;
        '''
    })
    return driver


def save_html(driver, filename):
    """Сохраняет HTML страницы в файл"""
    os.makedirs('res', exist_ok=True)
    filepath = os.path.join('res', filename)
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(driver.page_source)
    print(f"HTML saved to {filepath}")
    return filepath


def save_to_json(data, filename_prefix='citilink_pc'):
    """Сохраняет данные в JSON файл"""
    current_datetime = datetime.datetime.now()
    filename = f"{filename_prefix} {current_datetime.strftime('%Y_%m_%d_%H_%M')}.json"
    with open(filename, 'w', encoding='utf-8') as file:
        json.dump(data, file, ensure_ascii=False, indent=2)
    print(f"Data saved to {filename}")
    return filename


def save_to_excel(data, json_filename):
    """Сохраняет данные в Excel файл"""
    excel_filename = json_filename.replace('.json', '.xlsx')
    df = pd.DataFrame(data)
    df = df.rename(columns={
        'name': 'Название',
        'price': 'Цена',
        'img': 'Изображение',
        'rating': 'Рейтинг'
    })
    df.to_excel(excel_filename, index=False, engine='openpyxl')
    print(f"Data saved to {excel_filename}")


def parse_page(driver):
    """Парсит текущую страницу и извлекает данные о товарах"""
    time.sleep(3)
    page_html = driver.page_source
    soup = BeautifulSoup(page_html, 'html.parser')

    # ОБНОВЛЁННЫЕ СЕЛЕКТОРЫ (на основе актуального HTML)
    # Карточки товаров теперь находятся по другому классу
    all_cards = soup.find_all('div', class_='e1k9rx9o0')

    # Если не нашли, пробуем альтернативный селектор
    if len(all_cards) == 0:
        all_cards = soup.find_all('div', attrs={'data-meta-name': 'ProductVerticalSnippet'})

    print(f"Found {len(all_cards)} products on page")

    products = []

    for item in all_cards:
        try:
            # Извлечение названия
            name_elem = item.find('a', class_='app-catalog-n3i2jz-Anchor--Anchor-Anchor--StyledAnchor')
            if not name_elem:
                name_elem = item.find('a', attrs={'data-meta-name': 'Snippet__title'})
            name = name_elem.text.strip() if name_elem else ''

            # Извлечение цены
            price_elem = item.find('span', class_='e4ahr150')
            if not price_elem:
                price_elem = item.find('span', attrs={'data-meta-price': True})
            price = 0
            if price_elem:
                price_text = price_elem.text.strip()
                price_clean = ''.join(c for c in price_text if c.isdigit())
                price = int(price_clean) if price_clean else 0

            # Извлечение рейтинга
            rating_elem = item.find('div', class_='e14046d20')
            rating = 0.0
            if rating_elem:
                rating_text = rating_elem.text.strip().replace(',', '.').replace(' ', '')
                try:
                    rating = float(rating_text)
                except ValueError:
                    rating = 0.0

            # Извлечение изображения
            img_elem = item.find('img', class_='eikooao0')
            img = ''
            if img_elem:
                img = img_elem.get('src', '')

            if name:
                products.append({
                    'name': name,
                    'price': price,
                    'img': img,
                    'rating': rating
                })
                print(f"  Parsed: {name[:50]}... - {price} руб.")

        except Exception as e:
            print(f"Error parsing item: {e}")
            continue

    return products


def main():
    """Основная функция"""
    driver = None
    try:
        print("Starting Citilink parser...")
        driver = setup_driver()

        print("Opening page...")
        driver.get('https://www.citilink.ru/catalog/kompyutery/')
        time.sleep(5)

        # Прокрутка для загрузки контента
        for i in range(3):
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight)")
            time.sleep(2)

        # СОХРАНЯЕМ HTML СТРАНИЦЫ (ЭТО ГЛАВНОЕ ДЛЯ ДИПЛОМА)
        html_file = save_html(driver, 'citilink_page.html')
        print(f"HTML страницы сохранён: {html_file}")

        # Парсим страницу
        products = parse_page(driver)

        print(f"\nTotal products parsed: {len(products)}")

        if products:
            json_file = save_to_json(products)
            save_to_excel(products, json_file)
            print("\n=== Parsing completed successfully ===")
        else:
            print("\n=== No products found, but HTML was saved ===")

    except Exception as e:
        print(f"Error: {e}")
    finally:
        if driver:
            driver.quit()
            print("Browser closed")


if __name__ == '__main__':
    main()