from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

@app.post("/webhook")
async def handle_webhook(request: Request):
    """
    Зачем: Битрикс24 отправляет данные в формате form-data,
    а не JSON. Поэтому читаем через request.form() а не request.json()
    """
    try:
        # Пробуем form-data (так Битрикс отправляет вебхуки)
        form_data = await request.form()
        data = dict(form_data)
        print(f"📩 Получено (form): {data}")
    except Exception:
        try:
            data = await request.json()
            print(f"📩 Получено (json): {data}")
        except Exception as e:
            print(f"⚠️ Ошибка парсинга: {e}")
            return JSONResponse({"status": "ok"})
    
    # Достаём данные из вебхука Битрикс24
    event = data.get("event", "")
    user_id = data.get("data[USER][ID]") or data.get("data[PARAMS][FROM_USER_ID]")
    message_text = data.get("data[PARAMS][MESSAGE]") or data.get("data[MESSAGE]", "")
    
    print(f"  Событие: {event}, user_id: {user_id}, текст: {message_text}")
    
    if message_text and message_text.startswith("/"):
        handle_command(message_text, user_id)
    
    return JSONResponse({"status": "ok"})