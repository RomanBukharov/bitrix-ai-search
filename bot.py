from fastapi import FastAPI, Request
from database import init_db, init_subscriptions_table, add_subscription, get_all_subscriptions
import requests
import os
from dotenv import load_dotenv

load_dotenv()

WEBHOOK_URL = os.getenv("BITRIX_WEBHOOK_URL")

app = FastAPI()

def send_message(dialog_id, text):
    """Отправляем сообщение пользователю в чат Битрикс24"""
    url = f"{WEBHOOK_URL}im.message.add"
    params = {
        "DIALOG_ID": dialog_id,
        "MESSAGE": text
    }
    requests.get(url, params=params)

@app.post("/webhook")
async def handle_webhook(request: Request):
    """
    Этот endpoint принимает все события от Битрикс24.
    Когда пользователь пишет боту — Битрикс присылает 
    запрос сюда с данными о сообщении.
    """
    data = await request.json()
    print(f"📩 Получено событие: {data}")
    
    # Достаём текст сообщения и ID диалога
    message_text = data.get("data", {}).get("PARAMS", {}).get("MESSAGE", "")
    dialog_id = data.get("data", {}).get("PARAMS", {}).get("FROM_USER_ID", "")
    
    if not message_text:
        return {"status": "ok"}
    
    print(f"💬 Сообщение: {message_text} от {dialog_id}")
    
    # Обрабатываем команды
    if message_text.startswith("/subscribe"):
        # Пример: /subscribe дедлайны и обязательства
        prompt = message_text.replace("/subscribe", "").strip()
        
        if not prompt:
            send_message(dialog_id, "❌ Укажи тему подписки. Пример:\n/subscribe дедлайны и обязательства")
            return {"status": "ok"}
        
        add_subscription(user_id=str(dialog_id), prompt=prompt)
        send_message(dialog_id, f"✅ Подписка оформлена!\nБуду уведомлять о сообщениях по теме: '{prompt}'")
    
    elif message_text.startswith("/list"):
        # Показываем все подписки пользователя
        subs = get_all_subscriptions()
        user_subs = [s for s in subs if str(s[1]) == str(dialog_id)]
        
        if not user_subs:
            send_message(dialog_id, "У тебя пока нет подписок.\nИспользуй /subscribe <тема>")
        else:
            text = "📋 Твои подписки:\n"
            for sub in user_subs:
                text += f"• {sub[2]}\n"
            send_message(dialog_id, text)
    
    elif message_text.startswith("/help"):
        send_message(dialog_id, 
            "🤖 Команды бота:\n\n"
            "/subscribe <тема> — подписаться на тему\n"
            "/list — список твоих подписок\n"
            "/help — помощь"
        )
    
    return {"status": "ok"}

@app.get("/")
async def root():
    """Просто проверяем что сервер живой"""
    return {"status": "alive", "message": "Bitrix AI Search Bot работает!"}

if __name__ == "__main__":
    import uvicorn
    init_db()
    init_subscriptions_table()
    uvicorn.run(app, host="0.0.0.0", port=8000)