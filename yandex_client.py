import requests
import os
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("YANDEX_API_KEY")
FOLDER_ID = os.getenv("YANDEX_FOLDER_ID")

def ask_yandex_gpt(prompt):
    """Отправляем запрос к YandexGPT и возвращаем текст ответа"""
    url = "https://llm.api.cloud.yandex.net/foundationModels/v1/completion"
    
    headers = {
        "Authorization": f"Api-Key {API_KEY}",
        "Content-Type": "application/json"
    }
    
    body = {
        "modelUri": f"gpt://{FOLDER_ID}/yandexgpt-lite",
        "completionOptions": {
            "stream": False,
            "temperature": 0.1,
            "maxTokens": 500
        },
        "messages": [
            {"role": "user", "text": prompt}
        ]
    }
    
    response = requests.post(url, headers=headers, json=body)
    data = response.json()
    
    # Достаём только текст из ответа
    return data["result"]["alternatives"][0]["message"]["text"]


def is_message_relevant(message_text, user_prompt):
    """
    Спрашиваем GPT: подходит ли сообщение под запрос пользователя?
    Возвращает True или False
    """
    prompt = f"""Ты помощник для фильтрации сообщений. 
Пользователь ищет сообщения по теме: "{user_prompt}"

Сообщение: "{message_text}"

Ответь ТОЛЬКО одним словом: ДА (если сообщение подходит) или НЕТ (если не подходит)."""

    answer = ask_yandex_gpt(prompt)
    return "ДА" in answer.upper()


if __name__ == "__main__":
    # Тестируем поиск
    test_messages = [
        "Иванов обязался сдать документы к понедельнику",
        "Нужно подготовить отчёт до 15 числа",
        "Встреча по проекту перенесена на пятницу",
        "Как дела у всех сегодня?",
        "Сделаю до 14!"
    ]
    
    user_prompt = "дедлайны и обязательства"
    
    print(f"🔍 Ищем сообщения по теме: '{user_prompt}'\n")
    print("=" * 50)
    
    for msg in test_messages:
        relevant = is_message_relevant(msg, user_prompt)
        icon = "✅" if relevant else "❌"
        print(f"{icon} {msg}")