import os
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

def get_conn():
    # Получаем соединение с PostgreSQL
    return psycopg2.connect(DATABASE_URL)

def init_db():
    # Создаём таблицу сообщений
    conn = get_conn()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            id          SERIAL PRIMARY KEY,
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
    print("База данных готова")

def init_subscriptions_table():
    conn = get_conn()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS subscriptions (
            id         SERIAL PRIMARY KEY,
            user_id    TEXT,
            chat_id    TEXT,
            prompt     TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()

def save_message(bitrix_id, chat_id, chat_title, author_id, text, date):
    # Сохраняем сообщение без дублей
    conn = get_conn()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT INTO messages (bitrix_id, chat_id, chat_title, author_id, text, date)
            VALUES (%s, %s, %s, %s, %s, %s)
            ON CONFLICT (bitrix_id) DO NOTHING
        """, (bitrix_id, chat_id, chat_title, author_id, text, date))
        conn.commit()
        if cursor.rowcount > 0:
            print(f" + Сохранено: [{chat_title}] {text[:50]}...")
            return True
        else:
            print(f" - Уже есть в БД: {bitrix_id}")
            return False
    finally:
        conn.close()

def get_all_messages():
    # Все сообщения из БД
    conn = get_conn()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT bitrix_id, chat_title, author_id, text, date
        FROM messages ORDER BY date DESC
    """)
    rows = cursor.fetchall()
    conn.close()
    return rows

def get_last_message_id():
    # ID последнего сообщения
    conn = get_conn()
    cursor = conn.cursor()
    cursor.execute("SELECT MAX(bitrix_id) FROM messages")
    result = cursor.fetchone()[0]
    conn.close()
    return result or 0

def get_new_messages(since_id):
    # Сообщения новее чем since_id
    conn = get_conn()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT bitrix_id, chat_title, author_id, text, date
        FROM messages WHERE bitrix_id > %s
        ORDER BY bitrix_id ASC
    """, (since_id,))
    rows = cursor.fetchall()
    conn.close()
    return rows
def add_subscription(user_id, prompt, chat_id):
    conn = get_conn()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO subscriptions (user_id, chat_id, prompt)
        VALUES (%s, %s, %s)
    """, (user_id, chat_id, prompt))
    conn.commit()
    conn.close()
    print(f"Подписка добавлена: '{prompt}'")

def get_all_subscriptions():
    conn = get_conn()
    cursor = conn.cursor()
    cursor.execute("SELECT id, user_id, chat_id, prompt FROM subscriptions")
    rows = cursor.fetchall()
    conn.close()
    return rows

def delete_subscription(sub_id):
    # Удаляем подписку по ID
    conn = get_conn()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM subscriptions WHERE id = %s", (sub_id,))
    conn.commit()
    conn.close()
    print(f"Подписка {sub_id} удалена")