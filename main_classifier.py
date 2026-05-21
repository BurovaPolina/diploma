import pandas as pd
import json
from datetime import datetime
from pathlib import Path

# Добавляем путь к проекту
import sys

sys.path.insert(0, str(Path(__file__).parent))

from utils import load_all_data
from classifier import PriceSegmentClassifier


def main():
    print("=" * 70)
    print("КЛАССИФИКАТОР ЦЕНОВЫХ СЕГМЕНТОВ")
    print("=" * 70)

    # Создаем классификатор
    classifier = PriceSegmentClassifier()
    print("\n Классификатор загружен (rule-based режим)")

    # Загружаем данные
    print("\n Загрузка данных...")
    all_data = load_all_data()

    if not all_data:
        print("\n НЕТ ДАННЫХ ДЛЯ КЛАССИФИКАЦИИ!")
        print("\nЧто делать:")
        print("1. Убедитесь, что в папках avito/, ozon/, wildberries/ есть JSON файлы")
        print("2. Или создайте тестовый файл classifier/data/raw/test.json")
        return

    # Классификация
    print(f"\n Классификация {len(all_data)} записей...")
    results = classifier.classify_batch(all_data)

    # Сохраняем результаты
    results_dir = Path('classifier/data/results')
    results_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # Сохраняем JSON
    json_path = results_dir / f'classified_{timestamp}.json'
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"\n JSON сохранен: {json_path}")

    # Сохраняем Excel
    df = pd.DataFrame(results)
    excel_path = results_dir / f'classified_{timestamp}.xlsx'

    with pd.ExcelWriter(excel_path, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name='Классифицированные данные', index=False)

        # Статистика по сегментам
        if 'predicted_segment' in df.columns:
            stats = df['predicted_segment'].value_counts().to_frame('Количество')
            stats['Процент'] = (stats['Количество'] / len(df) * 100).round(1)
            stats.to_excel(writer, sheet_name='Статистика')

    print(f"Excel сохранен: {excel_path}")

    # Вывод статистики
    print("\n" + "=" * 70)
    print("РЕЗУЛЬТАТЫ КЛАССИФИКАЦИИ")
    print("=" * 70)
    print(f"\nВсего обработано: {len(df)} записей")

    if 'predicted_segment' in df.columns:
        print("\nРаспределение по сегментам:")
        for segment, count in df['predicted_segment'].value_counts().items():
            percentage = count / len(df) * 100
            bar = '█' * int(percentage / 2)
            print(f"  {segment:10} | {bar:20} {count:4} ({percentage:5.1f}%)")

    print("\n КЛАССИФИКАЦИЯ ЗАВЕРШЕНА!")


if __name__ == "__main__":
    main()