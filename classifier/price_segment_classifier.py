import re
from pathlib import Path
import joblib


class PriceSegmentClassifier:
    def __init__(self):
        self.is_trained = False

        # Пороги для разных платформ
        self.thresholds = {
            'avito': {
                'Бюджетный': (0, 10_000_000),
                'Средний': (10_000_000, 30_000_000),
                'Премиум': (30_000_000, 100_000_000),
                'Люкс': (100_000_000, float('inf'))
            },
            'ozon': {
                'Бюджетный': (0, 50_000),
                'Средний': (50_000, 150_000),
                'Премиум': (150_000, 500_000),
                'Люкс': (500_000, float('inf'))
            },
            'citilink': {
                'Бюджетный': (0, 40_000),
                'Средний': (40_000, 100_000),
                'Премиум': (100_000, 300_000),
                'Люкс': (300_000, float('inf'))
            },
            'wildberries': {
                'Бюджетный': (0, 30_000),
                'Средний': (30_000, 80_000),
                'Премиум': (80_000, 200_000),
                'Люкс': (200_000, float('inf'))
            }
        }

        # Ключевые слова для определения сегмента
        self.keywords = {
            'Люкс': ['rtx 4090', 'rtx 5090', 'i9', 'ryzen 9', 'премиум', 'luxury'],
            'Премиум': ['rtx 4080', 'rtx 5080', 'i7', 'gaming', 'игровой'],
            'Бюджетный': ['бюджетный', 'эконом', 'office', 'офисный', 'celeron', 'pentium', 'i3']
        }

    def rule_based_classify(self, price, platform, name=''):
        """Классификация на основе правил"""
        if price == 0 and name:
            name_lower = name.lower()
            for segment, words in self.keywords.items():
                if any(word in name_lower for word in words):
                    return segment, 0.7
            return 'Средний', 0.5

        thresholds = self.thresholds.get(platform, self.thresholds['ozon'])
        for segment, (min_price, max_price) in thresholds.items():
            if min_price <= price < max_price:
                return segment, 0.9

        return 'Средний', 0.5

    def predict(self, name, price, platform):
        """Предсказание сегмента"""
        return self.rule_based_classify(price, platform, name)

    def classify_batch(self, items):
        """Классификация списка товаров"""
        results = []
        for item in items:
            name = item.get('name', '')
            price = item.get('price', 0)
            platform = item.get('platform', 'unknown')

            segment, confidence = self.predict(name, price, platform)

            result = item.copy()
            result['predicted_segment'] = segment
            result['confidence'] = round(confidence, 3)
            results.append(result)

        return results

    def save_model(self, path='classifier/models/model.pkl'):
        """Сохраняет модель"""
        if not self.is_trained:
            print("Модель не обучена")
            return

        root_dir = Path(__file__).parent.parent
        full_path = root_dir / path
        full_path.parent.mkdir(parents=True, exist_ok=True)
        joblib.dump({}, full_path)
        print(f"Модель сохранена")

    def load_model(self, path='classifier/models/model.pkl'):
        """Загружает модель"""
        root_dir = Path(__file__).parent.parent
        full_path = root_dir / path

        if full_path.exists():
            self.is_trained = True
            print(f"Модель загружена")
            return True
        return False