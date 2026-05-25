import pandas as pd
import json
from datetime import datetime
from pathlib import Path

import sys

sys.path.insert(0, str(Path(__file__).parent))

from utils import load_all_data
from classifier import PriceSegmentClassifier


def main():
    print("=" * 70)
    print("КЛАССИФИКАТОР ЦЕНОВЫХ СЕГМЕНТОВ")
    print("=" * 70)

    classifier = PriceSegmentClassifier()
    print("\nКлассификатор загружен")

    print("\nЗагрузка данных...")
    all_data = load_all_data()

    if not all_data:
        print("\nНет данных для классификации")
        print("Убедитесь, что в папках avito, ozon, wildberries есть JSON файлы")
        return

    print(f"\nКлассификация {len(all_data)} записей...")
    results = classifier.classify_batch(all_data)

    results_dir = Path('classifier/data/results')
    results_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    json_path = results_dir / f'classified_{timestamp}.json'
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"\nJSON сохранен: {json_path}")

    df = pd.DataFrame(results)
    excel_path = results_dir / f'classified_{timestamp}.xlsx'

    with pd.ExcelWriter(excel_path, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name='Данные', index=False)

        if 'predicted_segment' in df.columns:
            stats = df['predicted_segment'].value_counts().to_frame('Количество')
            stats['Процент'] = (stats['Количество'] / len(df) * 100).round(1)
            stats.to_excel(writer, sheet_name='Статистика')

    print(f"Excel сохранен: {excel_path}")

    print("\n" + "=" * 70)
    print("РЕЗУЛЬТАТЫ")
    print("=" * 70)
    print(f"\nВсего обработано: {len(df)} записей")

    if 'predicted_segment' in df.columns:
        print("\nРаспределение по сегментам:")
        for segment, count in df['predicted_segment'].value_counts().items():
            percentage = count / len(df) * 100
            print(f"  {segment}: {count} ({percentage:.1f}%)")

    print("\nГОТОВО")


if __name__ == "__main__":
    main()