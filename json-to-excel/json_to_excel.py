import pandas as pd
import json


def json_to_excel(json_file, excel_file):
    with open(json_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # Если данные — список словарей
    if isinstance(data, list):
        df = pd.DataFrame(data)
    # Если данные — словарь с вложенными структурами
    elif isinstance(data, dict):
        # Преобразуем словарь в табличную форму (ключи - строки)
        df = pd.json_normalize(data)
    else:
        raise ValueError("JSON не является ни списком, ни словарём.")

    df.to_excel(excel_file, index=False, engine='openpyxl')
    print(f"✅ Успешно сохранено в {excel_file}")

# Пример использования
if __name__ == "__main__":
    json_to_excel('res/wildberries_pc 2025-04-17 16_44.json', 'output/output.xlsx')
