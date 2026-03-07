import requests
import time
import random
from fake_useragent import UserAgent
from bs4 import BeautifulSoup
import os
from datetime import datetime

class ZakupkiParser:
    def __init__(self):
        self.session = requests.Session()
        self.ua = UserAgent()
        self.base_url = "https://zakupki.gov.ru"
        self.search_url = f"{self.base_url}/epz/order/extendedsearch/results.html"
        self.delay_range = (2, 5)  # Случайная задержка между запросами
        self.timeout = 10
        self.setup_session()

    def setup_session(self):
        """Настройка сессии с базовыми заголовками"""
        headers = {
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
            "Accept-Language": "ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7",
            "Referer": f"{self.base_url}/epz/order/extendedsearch/search.html",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "same-origin",
            "Upgrade-Insecure-Requests": "1",
        }
        self.session.headers.update(headers)
        self.rotate_user_agent()

    def rotate_user_agent(self):
        """Смена User-Agent для имитации разных браузеров"""
        self.session.headers.update({
            "User-Agent": self.ua.random,
            "sec-ch-ua": f'"Chromium";v="{random.randint(100, 120)}", "Not A;Brand";v="{random.randint(8, 99)}"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"Windows"'
        })

    def make_request(self, params, max_retries=3):
        """Выполнение запроса с повторами"""
        for attempt in range(max_retries):
            try:
                time.sleep(random.uniform(*self.delay_range))

                response = self.session.get(
                    self.search_url,
                    params=params,
                    timeout=self.timeout
                )
                response.raise_for_status()
                self.check_for_captcha(response.text)
                return response

            except requests.exceptions.RequestException as e:
                print(f"Attempt {attempt + 1} failed: {str(e)}")
                if attempt == max_retries - 1:
                    raise
                time.sleep(5 * (attempt + 1))  # Увеличиваем задержку при повторе
                self.rotate_user_agent()
                return None
        return None

    def check_for_captcha(self, html):
        """Проверка на наличие капчи"""
        if "captcha" in html.lower():
            raise Exception("Обнаружена CAPTCHA, требуется ручное вмешательство")

    def parse_page(self, page_number=1, page_size=50):
        """Парсинг конкретной страницы"""
        params = {
            "morphology": "on",
            "search-filter": "Дате размещения",
            "pageNumber": page_number,
            "sortDirection": "false",
            "recordsPerPage": f"_{page_size}",
            "showLotsInfoHidden": "false",
            "sortBy": "UPDATE_DATE",
            "fz44": "on",
            "fz223": "on",
            "af": "on",
            "ca": "on",
            "pc": "on",
            "pa": "on",
            "currencyIdGeneral": "-1"
        }

        response = self.make_request(params)
        # return self.extract_data(response.text)
        return self.save_page(response.text, page_number)

    def save_page(selfself, html, num):
        os.makedirs("zakupki_html", exist_ok=True)

        # Генерируем имя файла с timestamp
        # timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"zakupki_html/page_{num}.html"

        # Сохраняем HTML
        with open(filename, "w", encoding="utf-8") as f:
            f.write(html)

        print(f"HTML сохранён в файл: {filename}")
        return {"status": "success", "file": filename}

    def extract_data(self, html):
        # os.makedirs("zakupki_html", exist_ok=True)
        #
        # # Генерируем имя файла с timestamp
        # timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        # filename = f"zakupki_html/page_{timestamp}.html"
        #
        # # Сохраняем HTML
        # with open(filename, "w", encoding="utf-8") as f:
        #     f.write(html)
        #
        # print(f"HTML сохранён в файл: {filename}")
        # return {"status": "success", "file": filename}

        """Извлечение данных из HTML"""
        # soup = BeautifulSoup(html, 'html.parser')
        # results = []
        # for item in soup.select('.registry-entry__header-mid'):
        #     if item:
        #         try:
        #             reg_num = item.select_one('[href*="regNumber="]')['href'].split('regNumber=')[1].split('&')[0]
        #             results.append({
        #                 'reg_number': reg_num,
        #             })
        #         except Exception as e:
        #             print(f"Ошибка парсинга элемента: {e}")
        #
        # return results

    def parse_multiple_pages(self, start_page=1, end_page=5):
        """Парсинг диапазона страниц"""
        all_results = []
        for page in range(start_page, end_page + 1):
            print(f"Парсинг страницы {page}...")
            try:
                page_results = self.parse_page(page)
                all_results.extend(page_results)
                print(f"Найдено {len(page_results)} закупок")
            except Exception as e:
                print(f"Ошибка при парсинге страницы {page}: {str(e)}")
                break
        return all_results


if __name__ == "__main__":
    parser = ZakupkiParser()

    try:
        # Парсим первые 5 страниц
        results = parser.parse_multiple_pages(1, 5)
        print(f"Всего собрано {len(results)} закупок")

        # Сохраняем результаты в файл
        import json

        with open('zakupki_results.json', 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)

    except Exception as e:
        print(f"Критическая ошибка: {str(e)}")
    finally:
        parser.session.close()