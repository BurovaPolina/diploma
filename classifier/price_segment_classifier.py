import re
import pandas as pd
import numpy as np
from pathlib import Path
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, accuracy_score
import joblib


class PriceSegmentClassifier:
    """
    Классификатор ценовых сегментов с обучением (ML)
    """

    def __init__(self):
        # ML компоненты
        self.text_vectorizer = None  # для векторизации названий
        self.price_scaler = None  # для нормализации цен
        self.classifier = None  # модель классификации
        self.label_encoder = None  # кодирование сегментов
        self.is_trained = False

        # Пороги для разных платформ
        self.thresholds = {
            'avito': {'Бюджетный': (0, 10_000_000), 'Средний': (10_000_000, 30_000_000),
                      'Премиум': (30_000_000, 100_000_000), 'Люкс': (100_000_000, float('inf'))},
            'ozon': {'Бюджетный': (0, 50_000), 'Средний': (50_000, 150_000),
                     'Премиум': (150_000, 500_000), 'Люкс': (500_000, float('inf'))},
            'citilink': {'Бюджетный': (0, 40_000), 'Средний': (40_000, 100_000),
                         'Премиум': (100_000, 300_000), 'Люкс': (300_000, float('inf'))},
            'wildberries': {'Бюджетный': (0, 30_000), 'Средний': (30_000, 80_000),
                            'Премиум': (80_000, 200_000), 'Люкс': (200_000, float('inf'))}
        }

        # Ключевые слова для признаков (вспомогательные)
        self.keywords = {
            'Люкс': ['rtx 4090', 'rtx 5090', 'i9', 'ryzen 9', 'премиум'],
            'Премиум': ['rtx 4080', 'rtx 5080', 'i7', 'gaming', 'игровой'],
            'Бюджетный': ['бюджетный', 'эконом', 'office', 'офисный', 'celeron', 'i3']
        }

    def _extract_features(self, name, price, platform):
        """Извлекает признаки для ML модели"""
        features = {}
        # 1. Цена
        features['price'] = price if price > 0 else 0

        # 2. Платформа (one-hot кодирование)
        platforms = ['avito', 'ozon', 'citilink', 'wildberries']
        for p in platforms:
            features[f'platform_{p}'] = 1 if platform == p else 0

        # 3. Длина названия
        features['name_length'] = len(name)

        # 4. Количество цифр в названии
        features['digit_count'] = sum(c.isdigit() for c in name)

        # 5. Количество заглавных букв
        features['uppercase_count'] = sum(c.isupper() for c in name)

        # 6. Проверка, есть ли цена
        features['has_price'] = 1 if price > 0 else 0

        # 7. Признаки по ключевым словам
        name_lower = name.lower()
        for segment, words in self.keywords.items():
            features[f'keyword_{segment}'] = 1 if any(word in name_lower for word in words) else 0

        return features


    def rule_based_classify(self, price, platform, name=''):
        """Подготавливает данные для обучения"""
        # СЛУЧАЙ 1: цена не указана
        if price == 0 and name:
            name_lower = name.lower()
            # Проверка ключевых слов для каждого сегмента
            for segment, words in self.keywords.items():
                # Если хотя бы одно слово из списка есть в названии(на уверенность)
                if any(word in name_lower for word in words):
                    return segment, 0.7
            return 'Средний', 0.5

        # СЛУЧАЙ 2: цена указана
        thresholds = self.thresholds.get(platform, self.thresholds['ozon'])
        for segment, (min_price, max_price) in thresholds.items():
            if min_price <= price < max_price:
                return segment, 0.9

        return 'Средний', 0.5

    def train(self, labeled_data_path='classifier/data/labeled/labeled_data.json'):
        """
        Обучает ML модель Random Forest на размеченных данных.
        Возвращает True, если обучение успешно.
        """
        root_dir = Path(__file__).parent.parent
        full_path = root_dir / labeled_data_path

        if not full_path.exists():
            print(f"Файл с размеченными данными не найден: {full_path}")
            return False

        import json
        with open(full_path, 'r', encoding='utf-8') as f:
            labeled_items = json.load(f)

        if len(labeled_items) < 50:
            print(f"Недостаточно данных для обучения (нужно 50, есть {len(labeled_items)})")
            return False

        print(f"Обучение на {len(labeled_items)} примерах...")

        # Списки для хранения признаков и ответов
        X_features = []
        X_text = []
        y = []

        # Проходим по каждому размеченному товару
        for item in labeled_items:
            name = item.get('name', '')
            price = item.get('price', 0)
            platform = item.get('platform', 'unknown')
            segment = item.get('segment', '')

            # Если нет сегмента, пропускаем этот товар
            if not segment:
                continue

            feat = self._extract_features(name, price, platform)
            X_features.append(feat)
            X_text.append(f"{platform} {name}")
            y.append(segment)

        df_features = pd.DataFrame(X_features)

        # Векторизация текста: превращаем названия в числа
        self.text_vectorizer = TfidfVectorizer(max_features=50, ngram_range=(1, 2))
        X_text_vec = self.text_vectorizer.fit_transform(X_text).toarray()
        X_text_df = pd.DataFrame(X_text_vec, columns=[f'text_{i}' for i in range(X_text_vec.shape[1])])

        X = pd.concat([df_features, X_text_df], axis=1)

        # Нормализация цены: приводим к одному масштабу
        self.price_scaler = StandardScaler()
        if 'price' in X.columns:
            X['price'] = self.price_scaler.fit_transform(X[['price']])

        self.label_encoder = LabelEncoder()
        y_encoded = self.label_encoder.fit_transform(y)

        X_train, X_test, y_train, y_test = train_test_split(
            X, y_encoded, test_size=0.2, random_state=42, stratify=y_encoded
        )

        # Создаём и обучаем модель Random Forest (100 - решений; 10 - глубина)
        self.classifier = RandomForestClassifier(n_estimators=100, max_depth=10, random_state=42)
        self.classifier.fit(X_train, y_train)

        # Проверка качества на тестовой выборке
        y_pred = self.classifier.predict(X_test)
        accuracy = accuracy_score(y_test, y_pred)

        print(f"Точность на тестовой выборке: {accuracy:.2%}")

        # Помечаем, что модель обучена
        self.is_trained = True
        return True

    def predict(self, name, price, platform):
        """
        Предсказывает сегмент для одного товара.
        Сначала пытается использовать ML модель, если не получается - правила.
        """
        if self.is_trained and self.classifier is not None:
            try:
                features = self._extract_features(name, price, platform)
                df_features = pd.DataFrame([features])

                text = f"{platform} {name}"
                text_vec = self.text_vectorizer.transform([text]).toarray()
                text_df = pd.DataFrame(text_vec, columns=[f'text_{i}' for i in range(text_vec.shape[1])])

                X = pd.concat([df_features, text_df], axis=1)

                if 'price' in X.columns:
                    X['price'] = self.price_scaler.transform(X[['price']])

                pred_encoded = self.classifier.predict(X)[0]
                # Превращаем число обратно в слово
                segment = self.label_encoder.inverse_transform([pred_encoded])[0]

                # Получаем уверенность (вероятность от 0 до 1)
                proba = self.classifier.predict_proba(X)[0]
                confidence = max(proba)

                return segment, confidence
            except Exception as e:
                print(f"Ошибка ML предсказания: {e}")

        return self.rule_based_classify(price, platform, name)

    def classify_batch(self, items):
        """
        Классифицирует список товаров.
        Возвращает новый список, где к каждому товару добавлены сегмент и уверенность.
        """
        results = []
        for item in items:
            name = item.get('name', '')
            price = item.get('price', 0)
            platform = item.get('platform', 'unknown')

            # Предсказываем сегмент и уверенность для одного товара
            segment, confidence = self.predict(name, price, platform)

            # Копируем исходный товар и добавляем новые поля
            result = item.copy()
            result['predicted_segment'] = segment
            result['confidence'] = round(confidence, 3) # уверенность
            results.append(result)

        return results

    def save_model(self, path='classifier/models/model.pkl'):
        """
        Сохраняет обученную ML модель в файл.
        """
        if not self.is_trained:
            print("Модель не обучена")
            return False

        # Формируем полный путь к файлу
        root_dir = Path(__file__).parent.parent
        full_path = root_dir / path
        full_path.parent.mkdir(parents=True, exist_ok=True)

        # Упаковываем все компоненты модели в словарь
        model_data = {
            'text_vectorizer': self.text_vectorizer,
            'price_scaler': self.price_scaler,
            'classifier': self.classifier,
            'label_encoder': self.label_encoder,
            'thresholds': self.thresholds,
            'keywords': self.keywords,
            'is_trained': self.is_trained
        }
        joblib.dump(model_data, full_path)
        print(f"Модель сохранена в {full_path}")
        return True

    def load_model(self, path='classifier/models/model.pkl'):
        """
        Загружает обученную ML модель из файла.
        """
        root_dir = Path(__file__).parent.parent
        full_path = root_dir / path

        if full_path.exists():
            model_data = joblib.load(full_path)
            # Восстанавливаем все компоненты
            self.text_vectorizer = model_data['text_vectorizer']
            self.price_scaler = model_data['price_scaler']
            self.classifier = model_data['classifier']
            self.label_encoder = model_data['label_encoder']
            self.thresholds = model_data['thresholds']
            self.keywords = model_data['keywords']
            self.is_trained = model_data.get('is_trained', True)
            print(f"Модель загружена из {full_path}")
            return True
        return False