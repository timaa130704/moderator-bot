# bot/keyboards/user_kb.py
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def get_start_keyboard(is_admin=False):
    """Кнопка на стартовом сообщении"""
    if is_admin:
        rows = [[InlineKeyboardButton(
            text="🔧 Панель администратора",
            callback_data="admin_panel"
        )]]
    else:
        rows = [[InlineKeyboardButton(
            text="📝 Подать заявку",
            callback_data="apply"
        )]]
    return InlineKeyboardMarkup(inline_keyboard=rows)


def get_cancel_keyboard():
    """Кнопка отмены во время анкеты"""
    rows = [[InlineKeyboardButton(
        text="❌ Отменить заполнение",
        callback_data="cancel_form"
    )]]
    return InlineKeyboardMarkup(inline_keyboard=rows)


# ✅ ОБНОВЛЕНО: TikTok вместо YouTube
def get_platform_keyboard():
    """Выбор платформы (Twitch или TikTok)"""
    rows = [
        [
            InlineKeyboardButton(text="🎵 TikTok", callback_data="platform_tiktok"),
            InlineKeyboardButton(text="📱 Twitch", callback_data="platform_twitch")
        ],
        [InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_form")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=rows)