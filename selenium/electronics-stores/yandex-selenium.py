import time
from selenium import webdriver
from selenium.common import NoSuchElementException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By

try:
    options = Options()
    # options.add_argument('--headless')
    # options.add_argument('--no-sandbox')
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument("start-maximized")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    options.add_argument('--disable-dev-shm-usage')
    options.add_experimental_option("excludeSwitches", ["test-type"])
    options.add_argument("--incognito")

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    driver.delete_all_cookies()

    driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
        'source': '''
            delete window.cdc_adoQpoasnfa76pfcZLmcfl_Array;
            delete window.cdc_adoQpoasnfa76pfcZLmcfl_Promise;
            delete window.cdc_adoQpoasnfa76pfcZLmcfl_Symbol;
      '''
    })

    iter = 0
    try:
        driver.get('https://yandex.ru/products/search?text=компьютеры')
        time.sleep(5)
        scroll = True
        while scroll:
            try:
                for i in range(12):
                    driver.execute_script("window.scrollTo(0, document.body.scrollHeight)")
                    time.sleep(2)
                show_more = driver.find_element(By.CLASS_NAME, 'SearchPage-MoreButton')
                show_more.click()
                time.sleep(2)
                print('================> Click to button')
                iter += 1
            except NoSuchElementException as e:
                time.sleep(1)
                scroll = False
                print('================> No such button')


        content = driver.find_element(By.CLASS_NAME, 'SearchPage-Products')
        print('all iteration: ' , iter)
        with open('res/yandex_pc.html', 'w') as file:
            file.write(content.get_attribute('innerHTML'))

    except Exception as e:
        print(e)
    finally:
        driver.quit()
        driver.close()

except Exception as e:
    print('glob', e)
