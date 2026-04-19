import requests
import os
from dotenv import load_dotenv

load_dotenv()

WEBHOOK_URL = os.getenv("BITRIX_WEBHOOK_URL")

def register_bot():
    """
    Зачем: регистрируем бота программно через API.
    Только так бот получает право отправлять сообщения от своего имени.
    Бота созданного через интерфейс Битрикс24 такого права не имеет.
    """
    url = f"{WEBHOOK_URL}imbot.register"
    
    params = {
        "CODE": "ai_search_bot",
        "TYPE": "B",  # B = чат-бот
        "EVENT_MESSAGE_ADD": "http://localhost",  # заглушка, polling не нужен
        "EVENT_WELCOME_MESSAGE": "http://localhost",
        "PROPERTIES": {
            "NAME": "AI Search Bot",
            "LAST_NAME": "",
            "COLOR": "GREEN",
            "EMAIL": "",
            "PERSONAL_BIRTHDAY": "",
            "WORK_POSITION": "AI-поиск по сообщениям",
            "PERSONAL_WWW": "",
            "PERSONAL_PHOTO": "",
        }
    }
    
    response = requests.post(url, json=params)
    result = response.json()
    print(result)
    return result

if __name__ == "__main__":
    result = register_bot()
    if "result" in result:
        print(f"\n✅ Бот зарегистрирован!")
        print(f"BOT_ID = {result['result']}")
        print(f"\nДобавь в .env:")
        print(f"BITRIX_BOT_ID={result['result']}")
    else:
        print(f"\n❌ Ошибка: {result}")