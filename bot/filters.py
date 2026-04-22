from aiogram.filters import BaseFilter
from bot.config import ADMIN_IDS


class IsAdmin(BaseFilter):
    """Пропускает только администраторов из ADMIN_IDS"""
    async def __call__(self, event) -> bool:
        return event.from_user.id in ADMIN_IDS
