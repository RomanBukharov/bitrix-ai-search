import requests
import os
from dotenv import load_dotenv
from database import init_db, save_message

load_dotenv()
WEBHOOK_URL = os.getenv("BITRIX_WEBHOOK_URL")

def get_recent_chats():
    url = f"{WEBHOOK_URL}im.recent.list"
    response = requests.get(url)
    return response.json()

def collect_and_save_messages():
    """Собираем сообщения из Битрикс24 и сохраняем в БД"""
    data = get_recent_chats()
    items = data.get("result", {}).get("items", [])
    
    saved = 0
    for item in items:
        message = item.get("message", {})
        user = item.get("user", {})
        
        # Пропускаем системные сообщения и ботов
        if message.get("author_id") == 0:
            continue
        if user.get("bot"):
            continue
            
        result = save_message(
            bitrix_id  = message.get("id"),
            chat_id    = str(item.get("chat_id")),
            chat_title = item.get("title"),
            author_id  = message.get("author_id"),
            text       = message.get("text", ""),
            date       = message.get("date", "")
        )
        if result:
            saved += 1
    
    print(f"\n✅ Готово! Сохранено новых сообщений: {saved}")

def get_all_messages_from_chat(chat_id, limit=50):
    """Получаем все сообщения из конкретного чата"""
    url = f"{WEBHOOK_URL}im.dialog.messages.get"
    
    params = {
        "DIALOG_ID": chat_id,
        "LIMIT": limit
    }
    
    response = requests.get(url, params=params)
    return response.json()

def collect_all_history():
    """Собираем историю из всех чатов и сохраняем в БД"""
    data = get_recent_chats()
    items = data.get("result", {}).get("items", [])
    
    for item in items:
        # Пропускаем ботов
        if item.get("user", {}).get("bot"):
            continue
            
        chat_id    = item.get("id")        # например "chat1" или 13
        chat_title = item.get("title")
        
        print(f"\n📂 Обрабатываем чат: {chat_title}")
        
        history = get_all_messages_from_chat(chat_id)
        messages = history.get("result", {}).get("messages", [])
        
        for msg in messages:
            if msg.get("author_id") == 0:
                continue
                
            save_message(
                bitrix_id  = msg.get("id"),
                chat_id    = str(chat_id),
                chat_title = chat_title,
                author_id  = msg.get("author_id"),
                text       = msg.get("text", ""),
                date       = msg.get("date", "")
            )

if __name__ == "__main__":
    init_db()
    collect_all_history()