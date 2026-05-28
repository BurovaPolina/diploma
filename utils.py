import json
from pathlib import Path


def load_all_data():
    all_data = []
    root_dir = Path(__file__).parent

    # Список папок, где могут лежать JSON-файлы с данными
    search_paths = [
        (root_dir / 'avito', 'avito'),
        (root_dir / 'ozon', 'ozon'),
        (root_dir / 'wildberries', 'wildberries'),
        (root_dir / 'selenium' / 'electronics-stores', 'citilink'),
    ]

    print("Поиск JSON файлов...")

    # Проходим по каждой папке из списка
    for folder, platform in search_paths:
        if not folder.exists():
            continue

        json_files = list(folder.glob('*.json'))
        res_folder = folder / 'res'
        if res_folder.exists():
            json_files.extend(res_folder.glob('*.json'))

        for json_file in json_files:
            if 'labeled' in json_file.name or 'classified' in json_file.name:
                continue

            print(f"  Загрузка: {json_file.name}")

            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    # Проверка, является ли загруженные данные списком
                    if isinstance(data, list):
                        for item in data:
                            item['platform'] = platform
                            all_data.append(item)
            except Exception as e:
                print(f"    Ошибка: {e}")

    print(f"\nЗагружено {len(all_data)} записей")
    return all_data

# Функция сохраняет размеченные данные в файл
def save_labeled_data(data, filename='classifier/data/labeled/labeled_data.json'):
    root_dir = Path(__file__).parent
    full_path = root_dir / filename
    full_path.parent.mkdir(parents=True, exist_ok=True)

    with open(full_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"Сохранено {len(data)} записей")


def load_labeled_data(filename='classifier/data/labeled/labeled_data.json'):
    root_dir = Path(__file__).parent
    full_path = root_dir / filename

    if full_path.exists():
        with open(full_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    return []