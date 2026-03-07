# Резервное копирование и восстановление MongoDB

## 📌 Создание полного дампа базы данных

Для создания резервной копии всех баз данных MongoDB выполните команду:

```sh
mongodump --host localhost --port 27017 --out /path/to/backup
```

🔹 **Параметры:**
- `--host localhost` — указывает, что MongoDB работает локально.
- `--port 27017` — стандартный порт MongoDB.
- `--out /path/to/backup` — путь, куда сохранять дамп (например, `/backup/mongo_dump`).

---

## 🎯 Создание дампа конкретной базы данных

Если нужно сделать резервную копию только одной базы данных:

```sh
mongodump --db yourDatabase --out /path/to/backup
```

Замените `yourDatabase` на имя вашей базы данных.

---

## 🔐 Дамп с авторизацией (если требуется логин и пароль)

Если ваша база данных требует аутентификацию:

```sh
mongodump --uri="mongodb://username:password@localhost:27017/yourDatabase" --out /path/to/backup
```

Замените `username` и `password` на ваши учетные данные.

---

## 🔄 Восстановление базы данных из дампа

Чтобы восстановить базу данных из резервной копии, используйте `mongorestore`:

```sh
mongorestore --db yourDatabase /path/to/backup/yourDatabase
```

Это восстановит данные в базу `yourDatabase`.

---

## ⚡ Автоматизация резервного копирования (Shell-скрипт)

Можно создать скрипт `backup_mongo.sh` для автоматического создания бэкапа:

```sh
#!/bin/bash
TIMESTAMP=$(date +"%Y-%m-%d_%H-%M-%S")
BACKUP_DIR="/backup/mongo_backup_$TIMESTAMP"

mkdir -p "$BACKUP_DIR"
mongodump --out "$BACKUP_DIR"

echo "Backup completed at $TIMESTAMP"
```

### ✏ Дать права на выполнение:
```sh
chmod +x backup_mongo.sh
```

### 🚀 Запустить:
```sh
./backup_mongo.sh
```

---

## ⏳ Автоматизация через CRON

Если требуется автоматический бэкап каждый день в 3:00 ночи, добавьте в `crontab`:
```sh
0 3 * * * /path/to/backup_mongo.sh
```

🔹 Это обеспечит регулярное резервное копирование MongoDB без участия пользователя.

---

📌 **Готово! Теперь ваши данные в безопасности.** ✅

