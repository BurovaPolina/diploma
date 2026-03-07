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
        driver.get('https://www.citilink.ru/catalog/kompyutery/')
        time.sleep(5)

        scroll = True
        content = ''
        while scroll:
            try:
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight - 2800)")
                time.sleep(1)
                show_more = None
                buttons_container = driver.find_elements(By.CLASS_NAME, 'fresnel-container')

                print(driver.find_element(By.CLASS_NAME, 'e59n8xw0').get_attribute('innerHTML'))

                scroll = False

                for item in buttons_container:
                    try:
                        if item.text == 'Показать ещё':

                            item.click()
                            break
                    except Exception as e:
                       print('-', e)

                iter += 1
                print('iteration:', iter)
                if iter > 9:
                    time.sleep(1)
                    scroll = False
                time.sleep(5)
            except Exception as e:
                print(e)

            except NoSuchElementException as e:
                time.sleep(1)
                scroll = False
                print('================> No such button')

        # content = driver.find_element(By.CLASS_NAME, 'app-catalog-1r4e8wl').get_attribute('innerHTML')
        # print(len(content))
        # print('all iteration: ', iter)
        # with open('res/citilink_pc.html', 'w') as file:
        #     file.write(content)

    except Exception as e:
        print('>',e)
    finally:
        driver.quit()
        driver.close()

except Exception as e:
    print('glob', e)

