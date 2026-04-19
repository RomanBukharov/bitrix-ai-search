import requests
import os
from dotenv import load_dotenv

load_dotenv()

WEBHOOK_URL = os.getenv("BITRIX_WEBHOOK_URL")
BOT_ID = os.getenv("BITRIX_BOT_ID")
CLIENT_ID = os.getenv("BITRIX_BOT_CLIENT_ID")

def get_last_user_message_id():
    """Получаем ID последнего сообщения пользователя боту"""
    url = f"{WEBHOOK_URL}im.dialog.messages.get"
    params = {"DIALOG_ID": BOT_ID, "LIMIT": 1}
    response = requests.get(url, params=params)
    messages = response.json().get("result", {}).get("messages", [])
    if messages:
        return messages[0].get("id")
    return None

# Получаем ID последнего сообщения
message_id = get_last_user_message_id()
print(f"Последнее сообщение ID: {message_id}")

url = f"{WEBHOOK_URL}imbot.message.add"
params = {
    "BOT_ID": BOT_ID,
    "CLIENT_ID": CLIENT_ID,
    "DIALOG_ID": BOT_ID,
    "MESSAGE": "тест от имени бота",
    "MESSAGE_ID": message_id  # отвечаем на конкретное сообщение
}

response = requests.get(url, params=params)
print(response.json())

