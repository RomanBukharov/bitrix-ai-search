import requests
import os
import time
from dotenv import load_dotenv
from database import init_db, init_subscriptions_table, add_subscription, get_all_subscriptions

load_dotenv()

WEBHOOK_URL = os.getenv("BITRIX_WEBHOOK_URL")
BOT_ID = int(os.getenv("BITRIX_BOT_ID"))

# Запоминаем последний обработанный ID — 
# чтобы не обрабатывать одни и те же сообщения повторно
# Было: глобальная переменная которая сбрасывается при перезапуске
last_message_id = 0

# Станет: читаем из файла чтобы помнить между перезапусками
import json
import os

STATE_FILE = "bot_state.json"

def load_last_id():
    """Загружаем последний ID из файла — чтобы не терять состояние при перезапуске"""
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE) as f:
            return json.load(f).get("last_message_id", 0)
    return 0

def save_last_id(msg_id):
    """Сохраняем последний ID в файл"""
    with open(STATE_FILE, "w") as f:
        json.dump({"last_message_id": msg_id}, f)

last_message_id = load_last_id()

def get_bot_messages():
    """
    Зачем: читаем последние сообщения из диалога с ботом.
    Каждые 5 секунд спрашиваем Битрикс — что нового написали боту?
    """
    url = f"{WEBHOOK_URL}im.dialog.messages.get"
    params = {
        "DIALOG_ID": BOT_ID,
        "LIMIT": 20
    }
    response = requests.get(url, params=params)
    return response.json()

def send_message(user_id, text):
    """
    Зачем: используем imbot.message.add вместо im.message.add —
    только этот метод отправляет сообщение от имени бота,
    а не от имени владельца вебхука.
    """
    url = f"{WEBHOOK_URL}imbot.message.add"
    params = {
        "BOT_ID": BOT_ID,
        "DIALOG_ID": BOT_ID,
        "MESSAGE": text,
        "CLIENT_ID": os.getenv("BITRIX_BOT_CLIENT_ID")
    }
    response = requests.get(url, params=params)
    result = response.json()
    print(f"  📤 Ответ отправлен: {result}")
    return result

def handle_command(text, user_id):
    """
    Зачем: разбираем команду пользователя и выполняем нужное действие.
    Каждая команда начинается с / — это стандарт для чат-ботов.
    """
    text = text.strip()
    print(f"  🔧 Обрабатываем команду: '{text}' от user_id={user_id}")

    if text.startswith("/subscribe"):
        prompt = text.replace("/subscribe", "").strip()

        if not prompt:
            send_message(user_id,
                "❌ Укажи тему подписки.\n"
                "Пример: /subscribe дедлайны и обязательства"
            )
            return

        add_subscription(user_id=str(user_id), prompt=prompt)
        send_message(user_id,
            f"✅ Подписка оформлена!\n"
            f"Буду уведомлять о сообщениях по теме:\n"
            f"«{prompt}»"
        )

    elif text.startswith("/list"):
        subs = get_all_subscriptions()
        user_subs = [s for s in subs if str(s[1]) == str(user_id)]

        if not user_subs:
            send_message(user_id,
                "У тебя пока нет подписок.\n"
                "Используй: /subscribe <тема>"
            )
        else:
            result = "📋 Твои подписки:\n\n"
            for sub in user_subs:
                result += f"• {sub[2]}\n"
            send_message(user_id, result)

    elif text.startswith("/help") or text.startswith("/start"):
        send_message(user_id,
            "🤖 AI Search Bot\n\n"
            "Я слежу за сообщениями в Битрикс24 и уведомляю "
            "тебя когда появляется что-то важное.\n\n"
            "Команды:\n"
            "/subscribe <тема> — подписаться на тему\n"
            "/list — мои подписки\n"
            "/help — помощь"
        )
    else:
        send_message(user_id,
            "Не понимаю команду. Напиши /help"
        )

def poll_bot_messages():
    """
    Зачем: главный цикл опроса.
    Читаем новые сообщения и обрабатываем только те
    у которых ID больше чем последний обработанный.
    """
    global last_message_id

    data = get_bot_messages()
    messages = data.get("result", {}).get("messages", [])

    if not messages:
        print("  Сообщений нет")
        return

    # Инициализируем last_message_id при первом запуске —
    # берём максимальный ID чтобы не обрабатывать старые сообщения
    if last_message_id == 0:
        last_message_id = max(last_message_id, msg_id)
        save_last_id(last_message_id)
        print(f"  Инициализация: последний ID = {last_message_id}")
        return

    for msg in messages:
        msg_id = msg.get("id", 0)
        print(f"  msg_id={msg_id}, author_id={msg.get('author_id')}, text={msg.get('text')[:30]}")


        # Пропускаем уже обработанные
        if msg_id <= last_message_id:
            continue

        # Пропускаем сообщения от бота и системные
        author_id = msg.get("author_id")
        if author_id == BOT_ID or author_id == 0 or str(author_id) == str(BOT_ID):
            continue

        text = msg.get("text", "")
        user_id = msg.get("author_id")

        print(f"📩 Новая команда от {user_id}: {text}")
        handle_command(text, user_id)

        last_message_id = max(last_message_id, msg_id)

def debug_send():
    """Пробуем разные форматы DIALOG_ID"""
    
    # Вариант 1 — в чат бота
    url = f"{WEBHOOK_URL}im.message.add"
    
    variants = [
        {"DIALOG_ID": 14, "MESSAGE": "тест 1 — dialog_id=14"},
        {"DIALOG_ID": "chat14", "MESSAGE": "тест 2 — chat14"},
        {"DIALOG_ID": 1, "MESSAGE": "тест 3 — dialog_id=1"},
    ]
    
    for params in variants:
        response = requests.get(url, params=params)
        print(f"DIALOG_ID={params['DIALOG_ID']}: {response.json()}")

if __name__ == "__main__":
    load_dotenv()
    debug_send()

if __name__ == "__main__":
    init_db()
    init_subscriptions_table()

    print("🤖 Бот запущен! Polling каждые 5 секунд")
    print("Напиши боту в Битрикс24: /help")
    print("Нажми Ctrl+C чтобы остановить\n")

    while True:
        try:
            poll_bot_messages()
        except Exception as e:
            print(f"⚠️ Ошибка: {e}")
        time.sleep(5)