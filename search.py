from database import get_all_messages, init_db
from yandex_client import is_message_relevant

def search_messages(user_prompt):
    """Ищем подходящие сообщения из БД по промпту пользователя"""
    
    messages = get_all_messages()
    
    if not messages:
        print("❌ База данных пуста. Сначала запусти bitrix_client.py")
        return []
    
    print(f"🔍 Ищем по запросу: '{user_prompt}'")
    print(f"📊 Всего сообщений в БД: {len(messages)}")
    print("=" * 50)
    
    results = []
    
    for msg in messages:
        bitrix_id, chat_title, author_id, text, date = msg
        
        # Пропускаем пустые сообщения
        if not text.strip():
            continue
        
        relevant = is_message_relevant(text, user_prompt)
        
        if relevant:
            results.append({
                "chat": chat_title,
                "text": text,
                "date": date
            })
            print(f"✅ [{chat_title}] {text}")
        else:
            print(f"❌ [{chat_title}] {text}")
    
    print("=" * 50)
    print(f"\n🎯 Найдено подходящих: {len(results)} из {len(messages)}")
    
    return results


if __name__ == "__main__":
    init_db()
    
    # Пробуем разные запросы
    print("\n--- Запрос 1 ---")
    search_messages("дедлайны и обязательства")
    
    print("\n--- Запрос 2 ---")
    search_messages("перенос встречи")