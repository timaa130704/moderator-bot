# bot/database.py
import aiosqlite
import logging
from datetime import datetime
from bot.config import DB_PATH

logger = logging.getLogger(__name__)


async def init_db():
    """Создаёт таблицу заявок при первом запуске"""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS applications (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id         INTEGER NOT NULL,
                username        TEXT,
                name            TEXT NOT NULL,
                age             TEXT NOT NULL,
                adequacy        TEXT NOT NULL,
                help_ready      TEXT NOT NULL,
                experience      TEXT NOT NULL,
                created_at      TEXT NOT NULL,
                status          TEXT DEFAULT 'новая'
            )
        """)
        await db.commit()
    logger.info("БД инициализирована")


async def save_application(user_id, username, name, age, adequacy, help_ready, experience):
    """Сохраняет заявку, возвращает её ID"""
    now = datetime.now().strftime("%d.%m.%Y %H:%M")
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute(
            "INSERT INTO applications "
            "(user_id,username,name,age,adequacy,help_ready,experience,created_at,status)"
            " VALUES (?,?,?,?,?,?,?,?,?)",
            (user_id, username, name, age, adequacy, help_ready, experience, now, "новая")
        )
        await db.commit()
        logger.info(f"Заявка #{cur.lastrowid} сохранена")
        return cur.lastrowid


async def get_all_applications():
    """Все заявки, новые сверху"""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute(
            "SELECT * FROM applications ORDER BY id DESC"
        )
        rows = await cur.fetchall()
        return [dict(r) for r in rows]


async def get_application_by_id(app_id):
    """Одна заявка по ID"""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute(
            "SELECT * FROM applications WHERE id=?", (app_id,)
        )
        row = await cur.fetchone()
        return dict(row) if row else None


async def accept_application(app_id):
    """Принимает заявку (меняет статус на 'принята')"""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE applications SET status=? WHERE id=?",
            ("принята", app_id)
        )
        await db.commit()
        logger.info(f"Заявка #{app_id} принята")


async def reject_application(app_id):
    """Отклоняет заявку (меняет статус на 'отклонена')"""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE applications SET status=? WHERE id=?",
            ("отклонена", app_id)
        )
        await db.commit()
        logger.info(f"Заявка #{app_id} отклонена")


async def clear_all_applications():
    """Удаляет все заявки, возвращает кол-во"""
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute("SELECT COUNT(*) FROM applications")
        row = await cur.fetchone()
        count = row[0] if row else 0
        await db.execute("DELETE FROM applications")
        await db.commit()
        return count


async def check_existing_application(user_id):
    """True если пользователь уже подавал заявку"""
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute(
            "SELECT id FROM applications WHERE user_id=?", (user_id,)
        )
        return (await cur.fetchone()) is not None

        # В конец файла bot/database.py добавьте:

async def delete_application(app_id: int):
    """Удаляет конкретную заявку по ID"""
    try:
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute("DELETE FROM applications WHERE id=?", (app_id,))
            await db.commit()
            logger.info(f"Заявка #{app_id} удалена")
    except Exception as e:
        logger.error(f"Ошибка удаления заявки #{app_id}: {e}")
        raise

# В конец файла bot/database.py добавьте:

# В bot/database.py найдите функцию get_all_user_ids() и замените её:

async def get_all_user_ids():
    """Возвращает список всех user_id, кто когда-либо запускал бота"""
    try:
        async with aiosqlite.connect(DB_PATH) as db:
            # Создаём таблицу для отслеживания пользователей если её нет
            await db.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY,
                    username TEXT,
                    first_name TEXT,
                    last_name TEXT,
                    first_seen TEXT
                )
            """)
            await db.commit()
            
            # Получаем всех пользователей
            cur = await db.execute(
                "SELECT DISTINCT user_id FROM users"
            )
            rows = await cur.fetchall()
            return [row[0] for row in rows]
    except Exception as e:
        logger.error(f"Ошибка получения списка пользователей: {e}")
        return []


async def add_user(user_id: int, username: str = None, first_name: str = None, last_name: str = None):
    """Добавляет или обновляет пользователя в таблицу users"""
    try:
        from datetime import datetime
        now = datetime.now().strftime("%d.%m.%Y %H:%M")
        
        async with aiosqlite.connect(DB_PATH) as db:
            # Создаём таблицу если её нет
            await db.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY,
                    username TEXT,
                    first_name TEXT,
                    last_name TEXT,
                    first_seen TEXT
                )
            """)
            
            # Проверяем, есть ли уже этот пользователь
            cur = await db.execute(
                "SELECT user_id FROM users WHERE user_id = ?",
                (user_id,)
            )
            exists = await cur.fetchone()
            
            if exists:
                # Обновляем существующего пользователя
                await db.execute(
                    "UPDATE users SET username=?, first_name=?, last_name=? WHERE user_id=?",
                    (username, first_name, last_name, user_id)
                )
            else:
                # Добавляем нового пользователя
                await db.execute(
                    "INSERT INTO users (user_id, username, first_name, last_name, first_seen) "
                    "VALUES (?, ?, ?, ?, ?)",
                    (user_id, username, first_name, last_name, now)
                )
            
            await db.commit()
            logger.info(f"Пользователь {user_id} добавлен/обновлен в таблицу users")
    except Exception as e:
        logger.error(f"Ошибка добавления пользователя: {e}")