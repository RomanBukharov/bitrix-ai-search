import sqlite3
from datetime import datetime

DB_PATH = "messages.db"

def init_db():
    """Создаём таблицу если её ещё нет"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            bitrix_id   INTEGER UNIQUE,
            chat_id     TEXT,
            chat_title  TEXT,
            author_id   INTEGER,
            text        TEXT,
            date        TEXT,
            created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    conn.commit()
    conn.close()
    print("✅ База данных готова")

def save_message(bitrix_id, chat_id, chat_title, author_id, text, date):
    """Сохраняем одно сообщение. UNIQUE на bitrix_id защищает от дублей"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            INSERT OR IGNORE INTO messages 
            (bitrix_id, chat_id, chat_title, author_id, text, date)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (bitrix_id, chat_id, chat_title, author_id, text, date))
        
        conn.commit()
        
        if cursor.rowcount > 0:
            print(f"💾 Сохранено: [{chat_title}] {text[:50]}...")
            return True
        else:
            print(f"⏭️  Уже есть в БД: {bitrix_id}")
            return False
            
    finally:
        conn.close()

def get_all_messages():
    """Читаем все сообщения из БД"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT bitrix_id, chat_title, author_id, text, date 
        FROM messages 
        ORDER BY date DESC
    """)
    
    rows = cursor.fetchall()
    conn.close()
    return rows

def init_subscriptions_table():
    """Создаём таблицу подписок — здесь храним промпты пользователей"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS subscriptions (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id    TEXT,
            prompt     TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    conn.commit()
    conn.close()

def add_subscription(user_id, prompt):
    """Сохраняем подписку пользователя на определённый промпт"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("""
        INSERT INTO subscriptions (user_id, prompt)
        VALUES (?, ?)
    """, (user_id, prompt))
    
    conn.commit()
    conn.close()
    print(f"✅ Подписка добавлена: '{prompt}'")

def get_all_subscriptions():
    """Получаем все подписки всех пользователей"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("SELECT id, user_id, prompt FROM subscriptions")
    rows = cursor.fetchall()
    conn.close()
    return rows

def get_last_message_id():
    """Запоминаем ID последнего сообщения — чтобы потом знать что появилось нового"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("SELECT MAX(bitrix_id) FROM messages")
    result = cursor.fetchone()[0]
    conn.close()
    return result or 0

def get_new_messages(since_id):
    """Получаем только те сообщения которые появились после последней проверки"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT bitrix_id, chat_title, author_id, text, date
        FROM messages
        WHERE bitrix_id > ?
        ORDER BY bitrix_id ASC
    """, (since_id,))
    
    rows = cursor.fetchall()
    conn.close()
    return rows

if __name__ == "__main__":
    init_db()
    print("\nТекущие сообщения в БД:")
    messages = get_all_messages()
    if not messages:
        print("  (пока пусто)")
    for msg in messages:
        print(f"  [{msg[1]}] {msg[3][:60]}")