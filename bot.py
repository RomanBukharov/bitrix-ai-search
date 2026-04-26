import requests
import os
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from dotenv import load_dotenv
from database import init_db, init_subscriptions_table, add_subscription, get_all_subscriptions, delete_subscription
from contextlib import asynccontextmanager
import threading
from worker import check_and_notify
import time
import json

load_dotenv()

WEBHOOK_URL = os.getenv("BITRIX_WEBHOOK_URL")
BOT_ID = int(os.getenv("BITRIX_BOT_ID"))
CLIENT_ID = os.getenv("BITRIX_BOT_CLIENT_ID")

def run_worker():
    """Запускаем мониторинг в фоновом потоке параллельно с веб-сервером"""
    init_db()
    init_subscriptions_table()
    print("👀 Worker запущен в фоне")
    while True:
        try:
            print("🔄 Проверяем новые сообщения...")
            check_and_notify()
        except Exception as e:
            print(f"⚠️ Ошибка worker: {e}")
        time.sleep(60)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """При старте сервера — создаём БД и запускаем фоновый мониторинг"""
    init_db()
    init_subscriptions_table()
    worker_thread = threading.Thread(target=run_worker, daemon=True)
    worker_thread.start()
    yield

app = FastAPI(lifespan=lifespan)


def send_message(user_id, text, dialog_id=None, chat_id=None, keyboard=None):
    url = f"{WEBHOOK_URL}imbot.message.add"
    
    # Собираем params как обычный словарь без json.dumps
    params = {
        "BOT_ID": BOT_ID,
        "CLIENT_ID": CLIENT_ID,
        "DIALOG_ID": f"chat{chat_id}" if chat_id else BOT_ID,
        "MESSAGE": text
    }
    
    if keyboard:
        params["KEYBOARD"] = keyboard  # передаём как есть, без json.dumps
    
    print(f"  📤 Отправляем в DIALOG_ID={params['DIALOG_ID']}")
    # Используем GET с params вместо POST с json
    response = requests.get(url, params=params)
    result = response.json()
    print(f"  📤 Ответ: {result}")
    return result

def handle_command(text, user_id, dialog_id=None, chat_id=None):
    """Обрабатываем команды пользователя"""
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
            for i, sub in enumerate(user_subs, 1):
                result += f"{i}. {sub[2]}\n"
            send_message(user_id, result, dialog_id, chat_id)

    elif text.startswith("/delete"):
        parts = text.split()

        if len(parts) == 1:
            subs = get_all_subscriptions()
            user_subs = [s for s in subs if str(s[1]) == str(user_id)]

            if not user_subs:
                send_message(user_id, "У тебя нет подписок для удаления.", dialog_id, chat_id)
                return

            result = "📋 Выбери номер для удаления:\n\n"
            for i, sub in enumerate(user_subs, 1):
                result += f"{i}. {sub[2]}\n"
            result += "\nНапиши: /delete <номер>\nНапример: /delete 1"
            send_message(user_id, result, dialog_id, chat_id)

        elif len(parts) == 2 and parts[1].isdigit():
            index = int(parts[1]) - 1
            subs = get_all_subscriptions()
            user_subs = [s for s in subs if str(s[1]) == str(user_id)]

            if index < 0 or index >= len(user_subs):
                send_message(user_id, "❌ Неверный номер.\nНапиши /delete чтобы увидеть список.", dialog_id, chat_id)
                return

            sub_to_delete = user_subs[index]
            delete_subscription(sub_to_delete[0])
            send_message(user_id, f"✅ Подписка удалена:\n«{sub_to_delete[2]}»", dialog_id, chat_id)

        else:
            send_message(user_id, "❌ Неверный формат.\nИспользуй: /delete <номер>", dialog_id, chat_id)

    elif text.startswith("/help") or text.startswith("/start"):
        send_message(user_id,
            "🤖 AI Search Bot\n\n"
            "Я слежу за сообщениями в Битрикс24 и уведомляю тебя когда появляется что-то важное.\n\n"
            "Нажми на команду:\n"
            "[send=/list]📋 Мои подписки[/send]\n"
            "[send=/delete]🗑 Удалить подписку[/send]\n"
            "[send=/subscribe ]➕ Подписаться на тему[/send]",
            dialog_id, chat_id
        )

    else:
        send_message(user_id, "Не понимаю команду. Напиши /help", dialog_id, chat_id)

@app.post("/webhook")
async def handle_webhook(request: Request):
    try:
        form_data = await request.form()
        data = dict(form_data)
    except Exception as e:
        print(f"⚠️ Ошибка парсинга: {e}")
        return JSONResponse({"status": "ok"})

    event = data.get("event", "")
    message_text = data.get("data[PARAMS][MESSAGE]", "")
    user_id = data.get("data[PARAMS][FROM_USER_ID]")
    dialog_id = data.get("data[PARAMS][DIALOG_ID]")
    chat_id = data.get("data[PARAMS][TO_CHAT_ID]")

    # Пользователь впервые открыл чат с ботом
    if event == "ONIMBOTJOINCHAT":
        user_id = data.get("data[PARAMS][USER_ID]")
        chat_id = data.get("data[PARAMS][CHAT_ID]")
        send_message(user_id,
            "👋 Привет! Я AI Search Bot.\n\n"
            "Слежу за сообщениями в Битрикс24 и уведомляю тебя когда появляется что-то важное.\n\n"
            "Напиши [send=/help]/help[/send] чтобы посмотреть список команд.",
            None, chat_id
        )

    elif message_text and message_text.startswith("/"):
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