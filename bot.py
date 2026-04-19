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

def send_message(user_id, text, dialog_id=None, chat_id=None):
    url = f"{WEBHOOK_URL}imbot.message.add"
    params = {
        "BOT_ID": BOT_ID,
        "CLIENT_ID": CLIENT_ID,
        "DIALOG_ID": f"chat{chat_id}" if chat_id else BOT_ID,  # используем chat_id
        "MESSAGE": text
    }
    print(f"  📤 Отправляем в DIALOG_ID={params['DIALOG_ID']}")
    response = requests.get(url, params=params)
    result = response.json()
    print(f"  📤 Ответ: {result}")
    return result

def handle_command(text, user_id, dialog_id=None, chat_id=None):
    text = text.strip()
    print(f"  🔧 Команда: '{text}' от {user_id}, dialog={dialog_id}")

    if text.startswith("/subscribe"):
        prompt = text.replace("/subscribe", "").strip()
        if not prompt:
            send_message(user_id, "❌ Укажи тему. Пример:\n/subscribe дедлайны и обязательства", dialog_id, chat_id)
            return
        add_subscription(user_id=str(user_id), prompt=prompt)
        send_message(user_id, f"✅ Подписка оформлена!\nБуду уведомлять о сообщениях по теме:\n«{prompt}»", dialog_id, chat_id)

    elif text.startswith("/list"):
        subs = get_all_subscriptions()
        user_subs = [s for s in subs if str(s[1]) == str(user_id)]
        if not user_subs:
            send_message(user_id, "У тебя пока нет подписок.\nИспользуй: /subscribe <тема>", dialog_id, chat_id)
        else:
            result = "📋 Твои подписки:\n\n"
            for sub in user_subs:
                result += f"• {sub[2]}\n"
            send_message(user_id, result, dialog_id, chat_id)

    elif text.startswith("/help") or text.startswith("/start"):
        send_message(user_id,
            "🤖 AI Search Bot\n\n"
            "Команды:\n"
            "/subscribe <тема> — подписаться\n"
            "/list — мои подписки\n"
            "/help — помощь",
            dialog_id, chat_id
        )
    else:
        send_message(user_id, "Не понимаю команду. Напиши /help", dialog_id, chat_id)

@app.post("/webhook")
async def handle_webhook(request: Request):
    try:
        form_data = await request.form()
        data = dict(form_data)
        print(f"📩 Получено: {data}")
    except Exception as e:
        print(f"⚠️ Ошибка парсинга: {e}")
        return JSONResponse({"status": "ok"})

    message_text = data.get("data[PARAMS][MESSAGE]", "")
    user_id = data.get("data[PARAMS][FROM_USER_ID]")
    
    # Используем DIALOG_ID из вебхука — это правильный чат
    dialog_id = data.get("data[PARAMS][DIALOG_ID]")
    chat_id = data.get("data[PARAMS][TO_CHAT_ID]")

    print(f"  user_id={user_id}, dialog_id={dialog_id}, chat_id={chat_id}, текст={message_text}")

    if message_text and message_text.startswith("/"):
        handle_command(message_text, user_id, dialog_id, chat_id)

    return JSONResponse({"status": "ok"})

@app.get("/")
async def root():
    return {"status": "alive", "message": "Bitrix AI Search Bot работает!"}

if __name__ == "__main__":
    import uvicorn
    init_db()
    init_subscriptions_table()
    uvicorn.run(app, host="0.0.0.0", port=8000)