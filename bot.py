import requests
import os
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from dotenv import load_dotenv
from database import init_db, init_subscriptions_table, add_subscription, get_all_subscriptions

load_dotenv()

WEBHOOK_URL = os.getenv("BITRIX_WEBHOOK_URL")
BOT_ID = int(os.getenv("BITRIX_BOT_ID"))
CLIENT_ID = os.getenv("BITRIX_BOT_CLIENT_ID")

app = FastAPI()

def send_message(user_id, text):
    """Отправляем сообщение от имени бота"""
    url = f"{WEBHOOK_URL}imbot.message.add"
    params = {
        "BOT_ID": BOT_ID,
        "CLIENT_ID": CLIENT_ID,
        "DIALOG_ID": BOT_ID,
        "MESSAGE": text
    }
    response = requests.get(url, params=params)
    result = response.json()
    print(f"  📤 Ответ: {result}")
    return result

def handle_command(text, user_id):
    """Обрабатываем команды пользователя"""
    text = text.strip()
    print(f"  🔧 Команда: '{text}' от {user_id}")

    if text.startswith("/subscribe"):
        prompt = text.replace("/subscribe", "").strip()
        if not prompt:
            send_message(user_id, "❌ Укажи тему. Пример:\n/subscribe дедлайны и обязательства")
            return
        add_subscription(user_id=str(user_id), prompt=prompt)
        send_message(user_id, f"✅ Подписка оформлена!\nБуду уведомлять о сообщениях по теме:\n«{prompt}»")

    elif text.startswith("/list"):
        subs = get_all_subscriptions()
        user_subs = [s for s in subs if str(s[1]) == str(user_id)]
        if not user_subs:
            send_message(user_id, "У тебя пока нет подписок.\nИспользуй: /subscribe <тема>")
        else:
            result = "📋 Твои подписки:\n\n"
            for sub in user_subs:
                result += f"• {sub[2]}\n"
            send_message(user_id, result)

    elif text.startswith("/help") or text.startswith("/start"):
        send_message(user_id,
            "🤖 AI Search Bot\n\n"
            "Команды:\n"
            "/subscribe <тема> — подписаться\n"
            "/list — мои подписки\n"
            "/help — помощь"
        )
    else:
        send_message(user_id, "Не понимаю команду. Напиши /help")

@app.post("/webhook")
async def handle_webhook(request: Request):
    """
    Зачем: принимаем вебхук от Битрикс24.
    Битрикс отправляет данные в form-data формате.
    """
    try:
        form_data = await request.form()
        data = dict(form_data)
        print(f"📩 Получено: {data}")
    except Exception as e:
        print(f"⚠️ Ошибка парсинга: {e}")
        return JSONResponse({"status": "ok"})

    event = data.get("event", "")
    user_id = data.get("data[USER][ID]") or data.get("data[PARAMS][FROM_USER_ID]")
    message_text = data.get("data[PARAMS][MESSAGE]", "")

    print(f"  Событие: {event}, user_id: {user_id}, текст: {message_text}")

    if message_text and message_text.startswith("/"):
        handle_command(message_text, user_id)

    return JSONResponse({"status": "ok"})

@app.get("/")
async def root():
    return {"status": "alive", "message": "Bitrix AI Search Bot работает!"}

if __name__ == "__main__":
    import uvicorn
    init_db()
    init_subscriptions_table()
    uvicorn.run(app, host="0.0.0.0", port=8000)