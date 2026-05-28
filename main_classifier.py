import pandas as pd
import json
from datetime import datetime
from pathlib import Path

import sys

# Добавляем папку с проектом в путь поиска модулей
sys.path.insert(0, str(Path(__file__).parent))

from utils import load_all_data
from classifier import PriceSegmentClassifier


def main():
    print("=" * 70)
    print("КЛАССИФИКАТОР ЦЕНОВЫХ СЕГМЕНТОВ")
    print("=" * 70)

    # Создаём объект классификатора
    classifier = PriceSegmentClassifier()
    print("\nКлассификатор загружен")

    print("\nЗагрузка данных...")
    # Загружаем все JSON-файлы из папок парсеров
    all_data = load_all_data()

    # Проверка: сколько данных загружено
    print(f"\nЗагружено товаров: {len(all_data)}")

    # Если данные есть, показываем пример первого товара для проверки
    if len(all_data) > 0:
        print(f"Пример первого товара: {all_data[0]}")
    else:
        # Если данных нет, выводим сообщение и выходим
        print("\nНет данных для классификации")
        print("Убедитесь, что в папках avito, wildberries, selenium/electronics-stores есть JSON файлы")
        return

    print(f"\nКлассификация {len(all_data)} записей...")

    # Запускаем классификацию для всех товаров
    # Возвращает новый список с добавленными полями predicted_segment и confidence
    results = classifier.classify_batch(all_data)

    # Создаём объект Path с путём к папке для результатов
    results_dir = Path('classifier/data/results')
    # Создаём папку (и все промежуточные), если её нет
    results_dir.mkdir(parents=True, exist_ok=True)

    # Получаем текущую дату и время для уникального имени файла
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # Сохраняем результаты в JSON
    json_path = results_dir / f'classified_{timestamp}.json'
    with open(json_path, 'w', encoding='utf-8') as f:
        # Сохраняем список results в JSON-файл
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"\nJSON сохранен: {json_path}")

    # Преобразуем результаты в таблицу pandas для сохранения в Excel
    df = pd.DataFrame(results)
    excel_path = results_dir / f'classified_{timestamp}.xlsx'

    with pd.ExcelWriter(excel_path, engine='openpyxl') as writer:
        # Сохраняем таблицу на лист
        df.to_excel(writer, sheet_name='Данные', index=False)

        # Проверяем, есть ли в таблице колонка 'predicted_segment'
        if 'predicted_segment' in df.columns:
            # Считаем количество товаров в каждом сегменте
            stats = df['predicted_segment'].value_counts().to_frame('Количество')
            # Добавляем колонку с процентами
            stats['Процент'] = (stats['Количество'] / len(df) * 100).round(1)
            # Сохраняем статистику на отдельный лист
            stats.to_excel(writer, sheet_name='Статистика')

            # ВЫВОД СТАТИСТИКИ В КОНСОЛЬ
            print("\n" + "=" * 70)
            print("РЕЗУЛЬТАТЫ КЛАССИФИКАЦИИ")
            print("=" * 70)
            print(f"\nВсего обработано: {len(df)} записей")
            print("\nРаспределение по сегментам:")
            for segment, count in stats['Количество'].items():
                percent = stats.loc[segment, 'Процент']
                print(f"  {segment}: {count} ({percent}%)")

    print(f"\nExcel сохранен: {excel_path}")
    print("\nГОТОВО")


if __name__ == "__main__":
    main()