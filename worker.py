import time
import requests
import os
from dotenv import load_dotenv
from database import (
    init_db, init_subscriptions_table,
    get_all_subscriptions, get_last_message_id,
    get_new_messages
)
from yandex_client import is_message_relevant
from bitrix_client import collect_and_save_messages

load_dotenv()

WEBHOOK_URL = os.getenv("BITRIX_WEBHOOK_URL")
BOT_ID = os.getenv("BITRIX_BOT_ID")
CLIENT_ID = os.getenv("BITRIX_BOT_CLIENT_ID")
CHECK_INTERVAL = 60  # проверяем каждую минуту

def send_notification(user_id, chat_title, text, prompt, date, author_name, chat_id="20"):
    """Отправляем уведомление с именем отправителя и временем"""
    url = f"{WEBHOOK_URL}imbot.message.add"
    message = (
        f"🔔 Найдено новое сообщение!\n\n"
        f"📌 Твой промпт: «{prompt}»\n"
        f"💬 Чат: {chat_title}\n"
        f"👤 Отправитель: {author_name}\n"
        f"📝 Сообщение: {text}\n"
        f"🕐 Время: {date}"
    )
    params = {
        "BOT_ID": BOT_ID,
        "CLIENT_ID": CLIENT_ID,
        "DIALOG_ID": f"chat{chat_id}",
        "MESSAGE": message
    }
    response = requests.get(url, params=params)
    print(f"  📤 Уведомление отправлено: {response.json()}")

def get_user_name(user_id):
    """Получаем имя пользователя по его ID"""
    url = f"{WEBHOOK_URL}user.get"
    params = {"ID": user_id}
    response = requests.get(url, params=params)
    data = response.json()
    users = data.get("result", [])
    if users:
        user = users[0]
        return f"{user.get('NAME', '')} {user.get('LAST_NAME', '')}".strip()
    return f"Пользователь {user_id}"

def check_and_notify():
    last_id = get_last_message_id()
    collect_and_save_messages()
    new_messages = get_new_messages(since_id=last_id)

    if not new_messages:
        print("  Новых сообщений нет")
        return

    print(f"  Новых сообщений: {len(new_messages)}")
    subscriptions = get_all_subscriptions()

    if not subscriptions:
        print("  Подписок нет")
        return

    for msg in new_messages:
        bitrix_id, chat_title, author_id, text, date = msg
        
        # Получаем имя автора
        author_name = get_user_name(author_id)

        for sub in subscriptions:
            sub_id, user_id, prompt = sub

            print(f"  Проверяем: '{text[:30]}' vs '{prompt}'")
            if is_message_relevant(text, prompt):
                print(f"  ✅ Совпадение! Уведомляем {user_id}")
                send_notification(user_id, chat_title, text, prompt, date, author_name)

if __name__ == "__main__":
    init_db()
    init_subscriptions_table()

    print("👀 Worker запущен!")
    print(f"⏱️  Проверка каждые {CHECK_INTERVAL} секунд")

    while True:
        print(f"\n🔄 Проверяем новые сообщения...")
        try:
            check_and_notify()
        except Exception as e:
            print(f"⚠️ Ошибка: {e}")
        time.sleep(CHECK_INTERVAL)