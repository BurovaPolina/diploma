import asyncio
from playwright.async_api import async_playwright
import os


async def main():
    output_dir = 'res'
    os.makedirs(output_dir, exist_ok=True)

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context()
        page = await context.new_page()

        await page.goto('https://www.avito.ru/moskva/nedvizhimost')
        await page.wait_for_timeout(2000)

        show_more_element = await page.wait_for_selector('xpath=//*[starts-with(normalize-space(), "Показать больше")]',
                                                         timeout=3000)
        await show_more_element.click()
        await page.wait_for_timeout(2000)
        iter = 1
        while True:
            # Подождем немного после загрузки
            await page.wait_for_timeout(3000)

            # Прокрутим вниз для загрузки товаров
            for _ in range(5):
                await page.mouse.wheel(0, 500)
                await page.wait_for_timeout(1000)

            # Сохраним HTML контент с текущей страницы
            content_element = await page.query_selector('#bx_serp-item-list')
            if content_element:
                content_html = await content_element.inner_html()
                with open(os.path.join(output_dir, f'avito{iter}.html'), 'w', encoding='utf-8') as file:
                    file.write(content_html)
                print(f'===> Saved page {iter}')
            else:
                print(f'===> No products found on page {iter}')
                break

            try:
                # Найдём текущую активную страницу
                current_page = await page.query_selector('[aria-label="Пагинация"] [aria-current="page"]')
                current_page_number = await current_page.get_attribute('data-marker')
                if current_page_number:
                    num = int(current_page_number.split('(')[-1].rstrip(')'))
                    next_marker = f'pagination-button/page({num + 1})'

                    # Ищем ссылку на следующую страницу
                    next_page_link = await page.query_selector(f'[data-marker="{next_marker}"]')
                    if next_page_link:
                        await next_page_link.click()
                        iter += 1
                        await page.wait_for_timeout(3000)
                        continue
                    else:
                        print('===> No next page link found')
                        break
                else:
                    print('===> Could not parse current page number')
                    break
            except Exception as e:
                print('===> Pagination error:', e)
                break

        await browser.close()


asyncio.run(main())
