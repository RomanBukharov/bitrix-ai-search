import requests
import os
from dotenv import load_dotenv

load_dotenv()

WEBHOOK_URL = os.getenv("BITRIX_WEBHOOK_URL")

url = f"{WEBHOOK_URL}im.recent.list"
response = requests.get(url)
data = response.json()
items = data.get("result", {}).get("items", [])

for item in items:
    msg = item.get("message", {})
    print(f"Чат: {item.get('title')}, последнее сообщение ID: {msg.get('id')}, текст: {msg.get('text', '')[:50]}")