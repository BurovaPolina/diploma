import os
import time
import json
import argparse
from urllib.parse import urljoin
from selenium import webdriver
from selenium.common.exceptions import TimeoutException, WebDriverException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# Конфигурация
BASE_DNS_URL = "https://www.dns-shop.ru/"
params = [
    {
        'name': 'personalnye-kompyutery',
        'code': '17a8932c16404e77'
    }
]

OUTPUT_FILE = '../../dns/src/res/dns.html'
SCROLL_PAUSE = 2
SCROLL_TIMES = 3
PAGE_LOAD_TIMEOUT = 30


class BrowserSession:
    def __init__(self):
        self.driver = None
        self.setup_browser()

    def setup_browser(self):
        options = Options()

        # Основные опции для обхода защиты
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-gpu")
        options.add_argument("--disable-web-security")
        options.add_argument("--disable-features=VizDisplayCompositor")
        options.add_argument("--disable-extensions")
        options.add_argument("--disable-default-apps")
        options.add_argument("--disable-component-extensions-with-background-pages")
        options.add_argument("--disable-client-side-phishing-detection")

        # Реалистичные параметры окна
        options.add_argument("--window-size=1920,1080")
        options.add_argument("--start-maximized")

        # User-Agent как у обычного Chrome
        options.add_argument(
            "--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/148.0.0.0 Safari/537.36")

        # Отключаем автоматизацию
        options.add_experimental_option("excludeSwitches", ["enable-automation", "enable-logging"])
        options.add_experimental_option('useAutomationExtension', False)

        # Реалистичные настройки
        prefs = {
            "profile.managed_default_content_settings.images": 1,  # Включить изображения (реалистичнее)
            "profile.default_content_setting_values.notifications": 2,
            "credentials_enable_service": False,
            "profile.password_manager_enabled": False,
            "profile.default_content_setting_values.cookies": 1
        }
        options.add_experimental_option("prefs", prefs)

        # Добавляем аргументы для стабильности
        options.add_argument("--disable-browser-side-navigation")
        options.add_argument("--disable-logging")
        options.add_argument("--log-level=3")
        options.add_argument("--silent")

        try:
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=options)

            # Модифицируем navigator после запуска
            self.driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
                'source': '''
                    // Удаляем признаки WebDriver
                    Object.defineProperty(navigator, 'webdriver', {
                        get: () => undefined
                    });

                    // Добавляем реальные свойства
                    Object.defineProperty(navigator, 'plugins', {
                        get: () => [1, 2, 3, 4, 5]
                    });

                    Object.defineProperty(navigator, 'languages', {
                        get: () => ['ru-RU', 'ru', 'en-US', 'en']
                    });

                    // Переопределяем permissions
                    const originalQuery = window.navigator.permissions.query;
                    window.navigator.permissions.query = (parameters) => (
                        parameters.name === 'notifications' ?
                            Promise.resolve({ state: Notification.permission }) :
                            originalQuery(parameters)
                    );

                    // Скрываем Chrome Automation
                    window.chrome = {
                        runtime: {}
                    };
                '''
            })

            self.driver.set_page_load_timeout(PAGE_LOAD_TIMEOUT)
            time.sleep(1)

        except Exception as e:
            print(f"Failed to setup browser: {str(e)}")
            raise

    def load_page(self, url):
        """Загружает страницу с повторными попытками"""
        max_attempts = 3

        for attempt in range(max_attempts):
            try:
                print(f"Loading attempt {attempt + 1}/{max_attempts}: {url}")
                self.driver.get(url)

                # Ждем загрузки body
                WebDriverWait(self.driver, 15).until(
                    EC.presence_of_element_located((By.TAG_NAME, "body"))
                )

                # Ждем либо каталог, либо контент
                try:
                    WebDriverWait(self.driver, 20).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR,
                                                        ".products-page, .catalog, main, .wrapper"))
                    )
                except:
                    pass

                # Проверяем, что страница не пустая
                if "catalog" in self.driver.current_url.lower():
                    print("Page loaded successfully")
                    time.sleep(5)  # Даем время для начальной загрузки JS
                    return True
                else:
                    print(f"Unexpected URL: {self.driver.current_url}")
                    continue

            except TimeoutException:
                print(f"Timeout on attempt {attempt + 1}")
                if attempt < max_attempts - 1:
                    self.restart_browser()
                continue

            except WebDriverException as e:
                print(f"WebDriver error: {str(e)}")
                if "no such window" in str(e) or "target window already closed" in str(e):
                    self.restart_browser()
                continue

            except Exception as e:
                print(f"Error: {str(e)}")
                if attempt < max_attempts - 1:
                    self.restart_browser()
                continue

        return False

    def scroll_to_load(self, times=3):
        """Прокручивает страницу для загрузки товаров"""
        print(f"Scrolling {times} times...")

        for i in range(times):
            try:
                # Разные техники скролла
                if i == 0:
                    # Первая прокрутка - до конца
                    self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                elif i == 1:
                    # Вторая - плавная
                    self.driver.execute_script("""
                        window.scrollTo({
                            top: document.body.scrollHeight,
                            behavior: 'smooth'
                        });
                    """)
                else:
                    # Третья - с задержкой
                    self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")

                print(f"  Scroll {i + 1}/{times} - waiting {SCROLL_PAUSE}s")
                time.sleep(SCROLL_PAUSE)

                # Небольшой скролл вверх для активации lazy loading
                if i < times - 1:
                    self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight * 0.7);")
                    time.sleep(1)

            except Exception as e:
                print(f"Error during scroll: {str(e)}")
                continue

        # Возвращаемся наверх
        try:
            self.driver.execute_script("window.scrollTo(0, 0);")
            time.sleep(1)
        except:
            pass

        print("Scrolling finished")

    def save_full_page(self, filepath):
        """Сохраняет полную HTML страницу"""
        try:
            # Создаем директорию
            os.makedirs(os.path.dirname(filepath), exist_ok=True)

            # Получаем HTML
            html = self.driver.page_source

            if len(html) < 10000:
                print("Warning: Page source is very small - might be incomplete")
                return False

            # Сохраняем
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(html)

            size_kb = len(html) / 1024
            print(f"Page saved! Size: {size_kb:.2f} KB")
            print(f"Path: {filepath}")

            return True

        except Exception as e:
            print(f"Error saving page: {str(e)}")
            return False

    def restart_browser(self):
        """Перезапускает браузер"""
        print("Restarting browser...")
        self.close()
        time.sleep(2)
        self.setup_browser()
        time.sleep(1)

    def close(self):
        if self.driver:
            try:
                self.driver.quit()
            except:
                pass
            time.sleep(1)


def scrape_category(browser, param, output_file):
    """Собирает данные с категории"""
    category_url = urljoin(BASE_DNS_URL, f"catalog/{param['code']}/{param['name']}/")
    category_name = param["name"]

    print(f"\n{'=' * 60}")
    print(f"Category: {category_name}")
    print(f"URL: {category_url}")
    print(f"Output: {output_file}")
    print(f"{'=' * 60}\n")

    # Загружаем страницу с повторными попытками
    if not browser.load_page(category_url):
        print("Failed to load page after all attempts")
        return False

    # Ждем дополнительно перед скроллом
    print("Waiting for page to stabilize...")
    time.sleep(5)

    # Прокручиваем
    browser.scroll_to_load(SCROLL_TIMES)

    # Еще ждем перед сохранением
    print("Waiting for all products to load...")
    time.sleep(3)

    # Сохраняем
    print("\nSaving page...")
    if browser.save_full_page(output_file):
        print("\n✓ Successfully saved!")
        return True
    else:
        print("\n✗ Failed to save")
        return False


def main():
    print("=" * 60)
    print("DNS Shop Scraper - Single File Mode")
    print(f"Scroll count: {SCROLL_TIMES}")
    print(f"Scroll pause: {SCROLL_PAUSE} sec")
    print(f"Output file: {OUTPUT_FILE}")
    print("=" * 60)

    browser = None

    try:
        browser = BrowserSession()

        for param in params:
            success = scrape_category(browser, param, OUTPUT_FILE)
            if success:
                print("\n✅ Scraping completed successfully!")
                break
            else:
                print("\n❌ Scraping failed")

    except KeyboardInterrupt:
        print("\n\n⚠️ Interrupted by user")
    except Exception as e:
        print(f"\n❌ Fatal error: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        if browser:
            print("\nClosing browser...")
            browser.close()
            print("Done.")


if __name__ == "__main__":
    main()