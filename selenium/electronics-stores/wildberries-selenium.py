import time
from random import randint

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
    action = webdriver.ActionChains(driver)
    iter = 0
    try:
        driver.get('https://www.wildberries.ru/catalog/elektronika/noutbuki-periferiya/kompyutery')
        scroll = True
        time.sleep(20)
        while scroll:
            time.sleep(randint(5, 12))
            try:
                try:
                    for i in range(4):
                        driver.execute_script("window.scrollTo(0, document.body.scrollHeight - 800)")
                        time.sleep(randint(1, 4))
                except Exception as e:
                    print('scroll')
                show_more = driver.find_element(By.CLASS_NAME, 'pagination-next')

                show_more.click()
                time.sleep(randint(1, 4))

                time.sleep(1)
                print('================> Click to button', iter)
                try:
                    content = driver.find_element(By.CLASS_NAME, 'main__container')
                    with open(f'res/wildberries/wildberries-{iter}.html', 'w') as file:
                        file.write(content.get_attribute('innerHTML'))
                    iter += 1
                    time.sleep(1)
                except Exception as e:
                    print('ошибка поиска элемента или файла')
                    print(e)
            except NoSuchElementException as e:
                time.sleep(1)
                scroll = False
                print('================> No such button')
    except Exception as e:
        print(e)
    finally:
        driver.quit()
        driver.close()

except Exception as e:
    print('glob', e)
    time.sleep(5)
    # driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    # driver.delete_all_cookies()
    #
    # driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
    #     'source': '''
    #             delete window.cdc_adoQpoasnfa76pfcZLmcfl_Array;
    #             delete window.cdc_adoQpoasnfa76pfcZLmcfl_Promise;
    #             delete window.cdc_adoQpoasnfa76pfcZLmcfl_Symbol;
    #       '''
    # })
    # driver.get('https://www.wildberries.ru/catalog/elektronika/noutbuki-periferiya/kompyutery')

