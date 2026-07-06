import sqlite3
import random

DB_NAME = 'bot.db'

def get_conn():
    return sqlite3.connect(DB_NAME)

def init_db():
    conn = get_conn()
    c = conn.cursor()
    # Таблица пользователей
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            telegram_id INTEGER UNIQUE,
            username TEXT,
            score_correct INTEGER DEFAULT 0,
            score_incorrect INTEGER DEFAULT 0,
            current_level TEXT DEFAULT 'A'
        )
    ''')
    # Таблица слов
    c.execute('''
        CREATE TABLE IF NOT EXISTS words (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            english TEXT NOT NULL,
            russian TEXT NOT NULL,
            level TEXT NOT NULL CHECK(level IN ('A','B','C'))
        )
    ''')
    # Проверка и вставка слов если таблица пуста
    c.execute("SELECT COUNT(*) FROM words")
    if c.fetchone()[0] == 0:
        words = [
            # Level A (25)
            ('apple', 'яблоко', 'A'),
            ('book', 'книга', 'A'),
            ('cat', 'кот', 'A'),
            ('dog', 'собака', 'A'),
            ('sun', 'солнце', 'A'),
            ('table', 'стол', 'A'),
            ('car', 'машина', 'A'),
            ('house', 'дом', 'A'),
            ('water', 'вода', 'A'),
            ('phone', 'телефон', 'A'),
            ('pen', 'ручка', 'A'),
            ('school', 'школа', 'A'),
            ('boy', 'мальчик', 'A'),
            ('girl', 'девочка', 'A'),
            ('milk', 'молоко', 'A'),
            ('bread', 'хлеб', 'A'),
            ('mother', 'мама', 'A'),
            ('father', 'папа', 'A'),
            ('window', 'окно', 'A'),
            ('door', 'дверь', 'A'),
            ('tree', 'дерево', 'A'),
            ('chair', 'стул', 'A'),
            ('cup', 'чашка', 'A'),
            ('hand', 'рука', 'A'),
            ('food', 'еда', 'A'),

            # Level B (20)
            ('challenge', 'вызов', 'B'),
            ('improve', 'улучшать', 'B'),
            ('develop', 'развивать', 'B'),
            ('experience', 'опыт', 'B'),
            ('opinion', 'мнение', 'B'),
            ('reason', 'причина', 'B'),
            ('prefer', 'предпочитать', 'B'),
            ('comfortable', 'комфортный', 'B'),
            ('opportunity', 'возможность', 'B'),
            ('advice', 'совет', 'B'),
            ('promise', 'обещать', 'B'),
            ('solution', 'решение', 'B'),
            ('prepare', 'готовить', 'B'),
            ('difficult', 'сложный', 'B'),
            ('impossible', 'невозможный', 'B'),
            ('management', 'управление', 'B'),
            ('support', 'поддержка', 'B'),
            ('interview', 'интервью', 'B'),
            ('provide', 'обеспечивать', 'B'),
            ('successful', 'успешный', 'B'),

            # Level C (20)
            ('profound', 'глубокий', 'C'),
            ('ubiquitous', 'вездесущий', 'C'),
            ('exacerbate', 'усугублять', 'C'),
            ('notwithstanding', 'несмотря на', 'C'),
            ('convoluted', 'запутанный', 'C'),
            ('ameliorate', 'улучшать', 'C'),
            ('detrimental', 'вредный', 'C'),
            ('disseminate', 'распространять', 'C'),
            ('perfunctory', 'поверхностный', 'C'),
            ('juxtaposition', 'сопоставление', 'C'),
            ('parsimonious', 'скаредный', 'C'),
            ('ineffable', 'невыразимый', 'C'),
            ('superfluous', 'избыточный', 'C'),
            ('ephemeral', 'мимолётный', 'C'),
            ('obfuscate', 'запутывать', 'C'),
            ('idiosyncrasy', 'особенность', 'C'),
            ('equanimity', 'хладнокровие', 'C'),
            ('serendipity', 'интуитивная прозорливость', 'C'),
            ('loquacious', 'говорливый', 'C'),
            ('magnanimous', 'великодушный', 'C')
        ]
        c.executemany("INSERT INTO words (english, russian, level) VALUES (?, ?, ?)", words)
    conn.commit()
    conn.close()

def set_user_level(telegram_id, level):
    conn = get_conn()
    c = conn.cursor()
    c.execute('''
        INSERT INTO users (telegram_id, current_level) 
        VALUES (?, ?)
        ON CONFLICT(telegram_id) DO UPDATE SET current_level=excluded.current_level
    ''', (telegram_id, level))
    conn.commit()
    conn.close()

def get_user_level(telegram_id):
    conn = get_conn()
    c = conn.cursor()
    c.execute('SELECT current_level FROM users WHERE telegram_id=?', (telegram_id,))
    res = c.fetchone()
    conn.close()
    if res:
        return res[0]
    else:
        # По умолчанию 'A'
        set_user_level(telegram_id, 'A')
        return 'A'

def get_random_word_by_level(level):
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT id, english, russian FROM words WHERE level=? ORDER BY RANDOM() LIMIT 1", (level,))
    row = c.fetchone()
    conn.close()
    if row:
        return {'id': row[0], 'english': row[1], 'russian': row[2]}
    return None

def get_wrong_options_by_level(correct_word_id, level):
    conn = get_conn()
    c = conn.cursor()
    c.execute("""
        SELECT russian FROM words 
        WHERE level=? AND id!=? 
        ORDER BY RANDOM() LIMIT 3
    """, (level, correct_word_id))
    results = [row[0] for row in c.fetchall()]
    conn.close()
    return results

def update_user_stats(telegram_id, is_correct):
    conn = get_conn()
    c = conn.cursor()
    # Если пользователя нет, создаём
    c.execute("SELECT id FROM users WHERE telegram_id=?", (telegram_id,))
    exists = c.fetchone()
    if not exists:
        c.execute("INSERT INTO users (telegram_id, score_correct, score_incorrect) VALUES (?, 0, 0)", (telegram_id,))
    if is_correct:
        c.execute("UPDATE users SET score_correct = score_correct + 1 WHERE telegram_id=?", (telegram_id,))
    else:
        c.execute("UPDATE users SET score_incorrect = score_incorrect + 1 WHERE telegram_id=?", (telegram_id,))
    conn.commit()
    conn.close()

# Инициализация базы при старте
init_db()