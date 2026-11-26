# Bitrix AI Search Bot

Бот для Битрикс24, который собирает сообщения из чатов, сравнивает их с пользовательскими подписками через YandexGPT и отправляет уведомления, когда находит релевантные сообщения.

## Что нужно

- Python 3.10+
- PostgreSQL
- Входящий webhook Битрикс24 с правами на методы `im.*`, `imbot.*`, `user.*`
- Зарегистрированный чат-бот Битрикс24
- API-ключ и folder id Yandex Cloud для YandexGPT

## Установка

```bash
pip install -r requirements.txt
```

## Настройка `.env`

Создайте файл `.env` в корне проекта:

```env
BITRIX_WEBHOOK_URL=https://your-domain.bitrix24.ru/rest/1/your_webhook_key/
BITRIX_BOT_ID=123
BITRIX_BOT_CLIENT_ID=your_bot_client_id

YANDEX_API_KEY=your_yandex_api_key
YANDEX_FOLDER_ID=your_yandex_folder_id
YANDEX_OAUTH_TOKEN=your_yandex_oauth_token

DATABASE_URL=postgresql://user:password@localhost:5432/bitrix_ai_search
```

Важно : `BITRIX_WEBHOOK_URL` должен заканчиваться на `/`, потому что код добавляет к нему имена методов API.

## База данных

Создайте базу PostgreSQL:

```bash
createdb bitrix_ai_search
```

Таблицы создаются автоматически при запуске приложения:

- `messages` - сохраненные сообщения из Битрикс24
  ![Пример таблицы с сообщениями](images/massages1.png)
  ![Пример таблицы с сообщениями](images/massages2.png)
- `subscriptions` - подписки пользователей на темы
![Пример таблицы с подписками](images/subs.png)

## Запуск

Основной вариант для локальной разработки:

```bash
python3 bot.py
```

`bot.py` поднимает FastAPI-сервер и запускает фоновый worker, который раз в минуту проверяет новые сообщения.

## Webhook для Битрикс24

нужен публичный URL. Например через ngrok:

```bash
ngrok http 8000
```

В настройках бота или обработчиков событий Битрикс24 укажи:

```text
https://your-ngrok-url.ngrok-free.app/webhook
```

Сервер принимает события на:

```text
POST /webhook
```

## Как протестировать

```bash
python3 test_bot_send.py
```

Если настройки Bitrix корректные, бот отправит тестовое сообщение.

### 3. Проверить YandexGPT-фильтр

```bash
python3 yandex_client.py
```

Скрипт прогонит несколько тестовых сообщений и покажет, какие из них подходят под тему `дедлайны и обязательства`.

### 4. Собрать историю сообщений

```bash
python3 bitrix_client.py
```

Скрипт прочитает последние сообщения из доступных чатов Битрикс24 и сохранит их в PostgreSQL.

### 5. Проверить поиск по сохраненным сообщениям

```bash
python3 search.py
```

Скрипт возьмет сообщения из базы и проверит их через YandexGPT по тестовым запросам.

## Частые проблемы

- `psycopg2` не подключается к базе: проверь `DATABASE_URL` и что PostgreSQL запущен.
- Бот не отвечает: проверь `BITRIX_WEBHOOK_URL`, `BITRIX_BOT_ID`, `BITRIX_BOT_CLIENT_ID` и права webhook.
- Битрикс24 не вызывает `/webhook`: нужен публичный HTTPS URL, локальный `localhost` не подойдет.
- YandexGPT всегда возвращает ошибку: проверь `YANDEX_API_KEY`, `YANDEX_FOLDER_ID` и доступ к модели `yandexgpt-lite`.
- Нет уведомлений: сначала добавь подписку через `/subscribe <тема>`, затем убедись, что `worker.py` или `bot.py` реально запущен.

# Описание работы модулей представлены ниже:

Процесс работы состоит из двух потоков: Воркера и Веб-приложения. 
![](images/doubleflow_schema.png)

Воркер работает в режимах сбора сообщений при запуске бота и мониторинге новых сообщений (схема 1 и 2 соответственно):
![](images/get_massages_alg.png)
![](images/monitorig_schema.png)

Алгоритм интеллектуальной обработки сообщений работает по следующему алгоритму:
![](images/semant_alg.png)
