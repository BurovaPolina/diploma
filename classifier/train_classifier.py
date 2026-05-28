import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from classifier.price_segment_classifier import PriceSegmentClassifier


def main():
    """
    Главная функция. Запускает обучение модели.
    """
    print("=" * 60)
    print("ОБУЧЕНИЕ МОДЕЛИ")
    print("=" * 60)

    # Создаём объект (экземпляр) классификатора
    classifier = PriceSegmentClassifier()
    # Запускаем обучение модели
    success = classifier.train()

    if success:
        classifier.save_model()
        print("\nМодель обучена и сохранена")
    else:
        print("\nОбучение не выполнено")


if __name__ == "__main__":
    main()