# =============================================================
# main.py — Точка входа. Запускает бота с поддержкой прокси.
# =============================================================

import asyncio
import logging
import sys

from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.client.session.aiohttp import AiohttpSession

from bot.config import BOT_TOKEN, PROXY_URL
from bot.database import init_db
from bot.handlers import user, admin

# ------------------------------------------------------------------
# Настройка логирования
# ------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("bot.log", encoding="utf-8"),
    ],
)

logging.getLogger("aiosqlite").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)


async def main():
    """Основная асинхронная функция запуска бота"""
    
    # Проверяем, что токен изменён
    if BOT_TOKEN == "ВСТАВЬТЕ_ВАШ_ТОКЕН_ЗДЕСЬ":
        logger.error(
            "❌ Токен не настроен! Откройте bot/config.py и вставьте токен от @BotFather."
        )
        sys.exit(1)

    logger.info("🔧 Инициализация базы данных...")
    await init_db()

    # ============================================================
    # Создание сессии с прокси (если указан)
    # ============================================================
    if PROXY_URL:
        logger.info(f"🔄 Используется прокси: {PROXY_URL}")
        session = AiohttpSession(proxy=PROXY_URL)
    else:
        logger.info("🌐 Прокси не используется")
        session = AiohttpSession()

    # Создаём бота с установленной сессией
    bot = Bot(
        token=BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
        session=session
    )

    # Создаём диспетчер
    dp = Dispatcher(storage=MemoryStorage())

    # Подключаем роутеры (admin первым — выше приоритет)
    dp.include_router(admin.router)
    dp.include_router(user.router)

    logger.info("🚀 Бот запускается...")
    
    try:
        # Удаляем вебхук если был установлен
        await bot.delete_webhook(drop_pending_updates=True)
        
        # Запускаем поллинг
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
        
    except Exception as e:
        logger.error(f"❌ Критическая ошибка: {e}", exc_info=True)
        raise
    finally:
        await bot.session.close()
        logger.info("⛔ Бот остановлен")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("⛔ Остановлено пользователем (Ctrl+C)")