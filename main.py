import time
import threading
from database import (
    init_db, init_subscriptions_table,
    get_all_subscriptions, get_last_message_id,
    get_new_messages
)
from yandex_client import is_message_relevant
from bitrix_client import collect_and_save_messages
from bitrix_bot import poll_bot_messages, send_message, BOT_ID

def monitor_loop():
    """
    Зачем: отдельный поток который следит за новыми сообщениями.
    Работает параллельно с ботом — не мешает обработке команд.
    Каждые 30 секунд проверяет новые сообщения и сравнивает с подписками.
    """
    print("👀 Мониторинг запущен")
    
    while True:
        try:
            last_id = get_last_message_id()
            collect_and_save_messages()
            new_messages = get_new_messages(since_id=last_id)
            
            if new_messages:
                subscriptions = get_all_subscriptions()
                
                for msg in new_messages:
                    bitrix_id, chat_title, author_id, text, date = msg
                    
                    for sub in subscriptions:
                        sub_id, user_id, prompt = sub
                        
                        if is_message_relevant(text, prompt):
                            # Отправляем уведомление боту в чат
                            notification = (
                                f"🔔 Найдено новое сообщение!\n\n"
                                f"📌 Твой промпт: «{prompt}»\n"
                                f"💬 Чат: {chat_title}\n"
                                f"📝 Сообщение: {text}\n"
                                f"🕐 Дата: {date}"
                            )
                            send_message(user_id, notification)
                            print(f"🔔 Уведомление отправлено пользователю {user_id}")
        
        except Exception as e:
            print(f"⚠️ Ошибка мониторинга: {e}")
        
        time.sleep(30)  # проверяем каждые 30 секунд

def bot_loop():
    """
    Зачем: отдельный поток для бота.
    Каждые 5 секунд читает новые команды от пользователей.
    """
    print("🤖 Бот запущен")
    
    while True:
        try:
            poll_bot_messages()
        except Exception as e:
            print(f"⚠️ Ошибка бота: {e}")
        time.sleep(5)

if __name__ == "__main__":
    init_db()
    init_subscriptions_table()
    
    print("🚀 Запускаем систему...")
    print("=" * 50)
    
    # Запускаем два потока параллельно
    # Thread — это как два работника которые делают разные задачи одновременно
    bot_thread = threading.Thread(target=bot_loop, daemon=True)
    monitor_thread = threading.Thread(target=monitor_loop, daemon=True)
    
    bot_thread.start()
    monitor_thread.start()
    
    print("✅ Система работает!")
    print("Напиши боту /subscribe <тема> в Битрикс24")
    print("Нажми Ctrl+C чтобы остановить\n")
    
    # Держим главный поток живым
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n👋 Останавливаем систему...")