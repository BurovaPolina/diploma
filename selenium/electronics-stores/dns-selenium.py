#python dns-selenium.py --start 1 --end 5

import os
import time
import json
import argparse
import traceback
from urllib.parse import urljoin
from selenium import webdriver
from selenium.common.exceptions import (NoSuchElementException,
                                        TimeoutException,
                                        WebDriverException)
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# Конфигурация
PARAMS_LOG = 'last_run_params.json'
BASE_DNS_URL = "https://www.dns-shop.ru/"
params = [
    {
        'name': 'personalnye-kompyutery',
        'code': '17a8932c16404e77'
    }
]

START_PAGE = 1
END_PAGE = None
RESUME = True
OUTPUT_DIR = 'res'
PAGE_LOAD_TIMEOUT = 10
MAX_RETRIES = 3


class BrowserSession:
    def __init__(self):
        self.driver = None
        self.wait = None
        self.setup_browser()

    def setup_browser(self):
        options = Options()
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument("start-maximized")
        options.add_experimental_option("excludeSwitches", ["enable-automation", "test-type"])
        options.add_experimental_option('useAutomationExtension', False)
        options.add_argument("--incognito")

        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=options)
        self.driver.delete_all_cookies()
        self.driver.set_page_load_timeout(PAGE_LOAD_TIMEOUT)
        self.wait = WebDriverWait(self.driver, PAGE_LOAD_TIMEOUT).until(EC.presence_of_element_located((By.CSS_SELECTOR, "body")))


        self.driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
            'source': '''
                delete window.cdc_adoQpoasnfa76pfcZLmcfl_Array;
                delete window.cdc_adoQpoasnfa76pfcZLmcfl_Promise;
                delete window.cdc_adoQpoasnfa76pfcZLmcfl_Symbol;
            '''
        })

    def ensure_page_load(self, url):
        """Гарантирует загрузку страницы с проверкой URL"""
        try:
            print(f"Loading URL: {url}")
            self.driver.get(url)
            if not self.driver.current_url.startswith(('http://', 'https://')):
                raise WebDriverException(f"Invalid URL loaded: {self.driver.current_url}")

            # Явная проверка загрузки основного контента
            self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "body")))
            return True
        except Exception as e:
            print(f"Failed to load page: {str(e)}")
            return False

    def restart_if_needed(self):
        try:
            # Проверяем, что браузер отвечает
            current_url = self.driver.current_url
            if not current_url or current_url == "data:,":
                raise WebDriverException("Browser in invalid state")
            return False
        except WebDriverException:
            print("Browser session invalid, restarting...")
            self.close()
            self.setup_browser()
            return True

    def close(self):
        if self.driver:
            try:
                self.driver.quit()
            except:
                pass


def get_last_saved_page(category_name):
    """Получить номер последней сохраненной страницы для категории"""
    if not os.path.exists(OUTPUT_DIR):
        return 0

    max_page = 0
    for filename in os.listdir(OUTPUT_DIR):
        if filename.startswith(f'dns_{category_name}_page_'):
            try:
                page_num = int(filename.split('_')[-1].split('.')[0])
                max_page = max(max_page, page_num)
            except ValueError:
                continue
    return max_page


def save_page_content(category_name, page_num, content):
    """Сохранить содержимое страницы"""
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    filename = f'dns_{category_name}_page_{page_num}.html'
    filepath = os.path.join(OUTPUT_DIR, filename)

    # Проверяем, не существует ли уже файл
    if os.path.exists(filepath):
        print(f"File {filename} already exists, skipping save")
        return

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)

    metadata = {
        'last_page': page_num,
        'timestamp': time.time()
    }
    with open(os.path.join(OUTPUT_DIR, f'dns_{category_name}_metadata.json'), 'w') as f:
        json.dump(metadata, f)


def navigate_to_page(browser, base_url, target_page):
    """Перейти на указанную страницу"""
    if target_page == 1:
        if not browser.ensure_page_load(base_url):
            return False

        try:
            browser.wait.until(
                EC.presence_of_element_located((By.CLASS_NAME, 'products-page__list')))
            return True
        except TimeoutException:
            print("Failed to find products list on page 1")
            return False

    current_page = 1
    if not browser.ensure_page_load(base_url):
        return False

    time.sleep(1)

    while current_page < target_page:
        try:
            # Находим ссылку на следующую страницу
            next_page_link = browser.wait.until(
                EC.element_to_be_clickable((By.CSS_SELECTOR,
                                            f'a.pagination-widget__page-link[href*="p={current_page + 1}"]')))

            # Скроллим к ссылке и кликаем
            browser.driver.execute_script("arguments[0].scrollIntoView(true);", next_page_link)
            time.sleep(0.5)
            browser.driver.execute_script("arguments[0].click();", next_page_link)

            current_page += 1
            print(f"Navigated to page {current_page}")

            # Проверяем загрузку новой страницы
            browser.wait.until(
                EC.presence_of_element_located((By.CLASS_NAME, 'products-page__list')))
            time.sleep(2)

        except Exception as e:
            print(f"Failed to navigate to page {current_page + 1}: {str(e)}")
            return False

    return True


def scrape_category(browser, param, start_page=1, end_page=None, resume=True):
    """Основная функция сбора данных для категории"""
    category_url = urljoin(BASE_DNS_URL, f"catalog/{param['code']}/{param['name']}/")
    category_name = param["name"]

    print(f"\n{'=' * 50}")
    print(f"Processing category: {category_name}")
    print(f"Category URL: {category_url}")
    print(f"{'=' * 50}\n")

    if resume:
        last_saved_page = get_last_saved_page(category_name)
        if last_saved_page > 0:
            start_page = last_saved_page + 1
            print(f"Resuming from page {start_page}")

            if not navigate_to_page(browser, category_url, start_page):
                print("Failed to navigate to the target page")
                return

    current_page = start_page

    while True:
        if end_page and current_page > end_page:
            break

        print(f"\nProcessing page {current_page}")

        for attempt in range(MAX_RETRIES):
            try:
                if browser.restart_if_needed():
                    print("Browser was restarted, reloading page...")
                    if not navigate_to_page(browser, category_url, current_page):
                        raise Exception("Failed to navigate after restart")

                # Скролл страницы
                print("Scrolling page...")
                for i in range(1, 11):
                    browser.driver.execute_script(
                        f"window.scrollTo(0, document.body.scrollHeight * {i / 10});")
                    time.sleep(0.3)

                # Получаем содержимое страницы
                print("Extracting content...")
                content = browser.wait.until(
                    EC.presence_of_element_located((By.CLASS_NAME, 'products-page__list')))
                html_content = content.get_attribute('innerHTML')

                # Сохраняем страницу
                print("Saving content...")
                save_page_content(category_name, current_page, html_content)
                print(f"Successfully saved page {current_page}")

                # Проверяем наличие следующей страницы
                try:
                    # Ищем ссылку на следующую страницу
                    next_page_link = browser.driver.find_element(
                        By.CSS_SELECTOR, f'a.pagination-widget__page-link[href*="p={current_page + 1}"]')

                    # Скроллим и кликаем
                    browser.driver.execute_script("arguments[0].scrollIntoView(true);", next_page_link)
                    time.sleep(0.5)
                    browser.driver.execute_script("arguments[0].click();", next_page_link)

                    # Ждем загрузки новой страницы
                    browser.wait.until(EC.staleness_of(content))
                    browser.wait.until(
                        EC.presence_of_element_located((By.CLASS_NAME, 'products-page__list')))
                    time.sleep(2)

                    current_page += 1
                    break

                except NoSuchElementException:
                    print("No more pages found in pagination")
                    return

                except Exception as e:
                    print(f"Error navigating to next page: {str(e)}")
                    raise

            except Exception as e:
                print(f"Attempt {attempt + 1} failed for page {current_page}: {str(e)}")
                if attempt == MAX_RETRIES - 1:
                    print(f"Max retries reached for page {current_page}, skipping...")
                    current_page += 1
                    break

                print("Waiting before retry...")
                time.sleep(5)
                browser.restart_if_needed()

def parse_arguments():
    parser = argparse.ArgumentParser(description="DNS-shop scraper")
    parser.add_argument('--start', type=int, default=1, help='Start page number')
    parser.add_argument('--end', type=int, help='End page number')
    parser.add_argument('--no-resume', action='store_true', help='Disable resume feature')
    return parser.parse_args()

def main():
    args = parse_arguments()

    start_page = args.start
    end_page = args.end
    resume = not args.no_resume

    run_params = {
        'start_page': start_page,
        'end_page': end_page,
        'resume': resume,
        'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
    }

    # Сохраняем параметры запуска
    with open(PARAMS_LOG, 'w') as f:
        json.dump(run_params, f, indent=2)

    print("Initializing browser session...")
    browser = BrowserSession()

    try:
        for param in params:
            try:
                scrape_category(
                    browser, param,
                    start_page=start_page,
                    end_page=end_page,
                    resume=resume
                )
            except Exception as e:
                print(f"\n{'!' * 50}")
                print(f"Critical error processing category {param['name']}: {str(e)}")
                traceback.print_exc()
                print(f"{'!' * 50}\n")
                continue

    except KeyboardInterrupt:
        print("\nScript interrupted by user")
    except Exception as e:
        print(f"\n{'!' * 50}")
        print(f"Fatal error: {str(e)}")
        traceback.print_exc()
        print(f"{'!' * 50}\n")
    finally:
        print("Closing browser session...")
        browser.close()
        print("Done.")


if __name__ == "__main__":
    main()