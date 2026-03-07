import unittest
from unittest.mock import mock_open, patch

from bs4 import BeautifulSoup
from dns.src.dns_parser import (
    create_card_template,
    extract_price,
    extract_rating,
    process_item,
    parse_html_file,
    save_to_json,
    SELECTOR_CARD,
    SELECTOR_IMAGE_CONTAINER,
    SELECTOR_NAME,
    SELECTOR_PRICE,
    SELECTOR_RATING_CONTAINER,
    SELECTOR_RATING_VALUE, extract_name, extract_image_url
)

class TestDNSParser(unittest.TestCase):
    def setUp(self):
        self.test_html = """
        <div class="catalog-product">
            <div class="catalog-product__image">
                <picture><source srcset="test.jpg"></picture>
            </div>
            <a class="catalog-product__name">Test Product</a>
            <div class="product-buy__price">10 999 ₽</div>
            <a class="catalog-product__rating"><b>4.5</b></a>
        </div>
        """
        print("\nTest HTML:", self.test_html)  # Отладочная печать
        self.soup = BeautifulSoup(self.test_html, 'html.parser')
        self.item = self.soup.select_one(SELECTOR_CARD)
        print("Parsed item:", self.item)  # Отладочная печать

    def test_create_card_template(self):
        template = create_card_template()
        self.assertEqual(len(template), 1)
        self.assertEqual(template[0]['name'], '')
        self.assertEqual(template[0]['price'], 0)
        self.assertEqual(template[0]['img'], '')
        self.assertEqual(template[0]['rating'], 0.0)

    def test_extract_price(self):
        html = """
        <div class="catalog-product"><div class="product-buy__price">10 999 ₽</div></div>
        <div class="catalog-product"><div class="product-buy__price">20 000 руб.</div></div>
        <div class="catalog-product"><div class="product-buy__price">15,000</div></div>
        """
        soup = BeautifulSoup(html, 'html.parser')
        items = soup.select(SELECTOR_CARD)

        self.assertEqual(extract_price(items[0]), 10999)
        self.assertEqual(extract_price(items[1]), 20000)
        self.assertEqual(extract_price(items[2]), 15000)

    def test_extract_rating(self):
        html = """
        <a class="catalog-product__rating"><b>4.5</b></a>
        <a class="catalog-product__rating"><b>5</b></a>
        <a class="catalog-product__rating"></a>
        """
        soup = BeautifulSoup(html, 'html.parser')
        items = soup.select(SELECTOR_RATING_CONTAINER)
        self.assertEqual(extract_rating(items[0]), 4.5)
        self.assertEqual(extract_rating(items[1]), 5.0)
        self.assertEqual(extract_rating(items[2]), None)


    def test_process_item(self):
        print("\nTesting with item:", self.item)  # Отладочная печать

        # Проверяем извлечение каждого поля отдельно
        name = extract_name(self.item)
        print("Extracted name:", name)
        self.assertEqual(name, 'Test Product')

        img = extract_image_url(self.item)
        print("Extracted image:", img)
        self.assertEqual(img, 'test.jpg')

        price = extract_price(self.item)
        print("Extracted price:", price)
        self.assertEqual(price, 10999)  # Ожидаем 10999, а не None

        rating = extract_rating(self.item)
        print("Extracted rating:", rating)
        self.assertEqual(rating, 4.5)

        # Теперь проверяем process_item
        result = process_item(self.item)
        print("Process item result:", result)
        self.assertIsNotNone(result, "Функция process_item вернула None")

        self.assertEqual(result['name'], 'Test Product')
        self.assertEqual(result['img'], 'test.jpg')
        self.assertEqual(result['price'], 10999)  # Здесь тоже должно быть 10999
        self.assertEqual(result['rating'], 4.5)

    @patch('builtins.open', new_callable=mock_open, read_data='<html></html>')
    @patch('json.dump')
    def test_save_to_json(self, mock_json_dump, mock_file):
        test_data = [{'test': 'data'}]
        filename = save_to_json(test_data)
        self.assertIn('dns_pc', filename)
        mock_json_dump.assert_called_once_with(test_data, mock_file(), ensure_ascii=False)

    @patch('builtins.open', new_callable=mock_open, read_data='<html><div class="catalog-product"></div></html>')
    def test_parse_html_file(self, mock_file):
        result = parse_html_file('dummy_path.html')
        self.assertEqual(len(result), 1)

    def test_selectors_usage_in_code(self):
        """Проверяем, что селекторы используются в функциях"""
        self.assertEqual(SELECTOR_CARD, 'div.catalog-product')
        self.assertEqual(SELECTOR_IMAGE_CONTAINER, 'div.catalog-product__image')
        self.assertEqual(SELECTOR_NAME, 'a.catalog-product__name')
        self.assertEqual(SELECTOR_PRICE, 'div.product-buy__price')
        self.assertEqual(SELECTOR_RATING_CONTAINER, 'a.catalog-product__rating')
        self.assertEqual(SELECTOR_RATING_VALUE, 'b')


if __name__ == '__main__':
    unittest.main()