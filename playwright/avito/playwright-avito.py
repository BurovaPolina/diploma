import asyncio
from playwright.async_api import async_playwright
import os

async def main():
    # Директория для сохранения HTML
    output_dir = 'res'
    os.makedirs(output_dir, exist_ok=True)

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        )
        page = await context.new_page()

        # Открываем страницу с недвижимостью
        await page.goto('https://www.avito.ru/moskva/nedvizhimost', timeout=60000, wait_until='domcontentloaded')
        await page.wait_for_timeout(5000)

        iter_num = 1
        while True:
            await page.wait_for_timeout(3000)

            # Прокрутка страницы для загрузки объявлений
            for _ in range(5):
                await page.mouse.wheel(0, 800)
                await page.wait_for_timeout(1500)

            # Сохраняем HTML
            page_html = await page.content()
            file_path = os.path.join(output_dir, f'avito{iter_num}.html')
            with open(file_path, 'w', encoding='utf-8') as file:
                file.write(page_html)
            print(f'Сохранен файл {iter_num}: {file_path}')

            # Пагинация
            try:
                next_button = await page.query_selector('[data-marker="pagination-button/next"]')
                if next_button:
                    await next_button.click()
                    iter_num += 1
                    await page.wait_for_timeout(3000)
                else:
                    print('Кнопка "Далее" не найдена, завершаем сбор')
                    break
            except Exception as e:
                print(f'Ошибка пагинации: {e}')
                break

        print(f'\n Сбор HTML завершен! Сохранено {iter_num} файлов в {output_dir}')
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())