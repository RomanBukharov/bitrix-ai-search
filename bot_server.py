from fastapi import FastAPI, Request
from database import init_db, init_subscriptions_table, add_subscription
from search import search_messages
import uvicorn

app = FastAPI()

@app.post("/webhook")
async def handle_webhook(request: Request):
    """
    Сюда Битрикс24 будет присылать все события —
    новые сообщения боту, команды пользователей и т.д.
    """
    data = await request.json()
    print(f"📩 Входящий запрос: {data}")
    return {"status": "ok"}

@app.get("/")
async def root():
    return {"status": "сервер работает"}

if __name__ == "__main__":
    init_db()
    init_subscriptions_table()
    uvicorn.run(app, host="0.0.0.0", port=8000)