import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

print("Запуск сбора HTML Wildberries...")

options = Options()
options.add_argument("--disable-blink-features=AutomationControlled")
options.add_argument("start-maximized")

driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

try:
    # Открываем страницу
    driver.get('https://www.wildberries.ru/catalog/elektronika/noutbuki-periferiya/kompyutery')
    print("Страница открыта, ждем загрузки...")
    time.sleep(20)

    # Прокручиваем вниз несколько раз
    for i in range(3):
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight)")
        print(f"Прокрутка {i + 1}/3")
        time.sleep(5)

    # Сохраняем HTML
    html_content = driver.page_source

    with open('wildberries-all.html', 'w', encoding='utf-8') as f:
        f.write(html_content)

    print(f"\n Файл сохранен: wildberries-all.html")
    print(f"Размер файла: {len(html_content)} символов")

except Exception as e:
    print(f"Ошибка: {e}")

finally:
    driver.quit()