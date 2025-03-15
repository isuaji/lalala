import sqlite3
import logging
from datetime import datetime

def init_database():
    try:
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()

        # Создание таблицы пользователей
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')

        # Создание таблицы профилей
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS profiles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            full_name TEXT,
            phone TEXT,
            address TEXT,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
        ''')

        # Создание таблицы сообщений
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            message_text TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
        ''')

        # Создание таблицы настроек
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS settings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            notification_enabled BOOLEAN DEFAULT TRUE,
            theme TEXT DEFAULT 'light',
            language TEXT DEFAULT 'ru',
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
        ''')

        # Добавление тестовых данных
        cursor.execute('''
        INSERT OR IGNORE INTO users (username, email) 
        VALUES 
            ('test_user', 'test@example.com'),
            ('admin', 'admin@example.com')
        ''')

        conn.commit()
        logging.info("База данных успешно инициализирована")
        
    except sqlite3.Error as e:
        logging.error(f"Ошибка при инициализации базы данных: {e}")
        raise
    
    finally:
        conn.close()

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    init_database() 