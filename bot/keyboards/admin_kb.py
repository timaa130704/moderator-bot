# bot/keyboards/admin_kb.py
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def get_admin_menu_keyboard():
    """Главное меню администратора"""
    rows = [
        [InlineKeyboardButton(
            text="📋 Список заявок",
            callback_data="view_applications"
        )],
        [InlineKeyboardButton(
            text="🗑 Очистить все заявки",
            callback_data="confirm_clear"
        )],
    ]
    return InlineKeyboardMarkup(inline_keyboard=rows)


def get_applications_list_keyboard(applications):
    """Список заявок — каждая отдельной кнопкой"""
    rows = []
    for app in applications:
        if app["username"]:
            label = f"@{app['username']}"
        else:
            label = f"ID {app['user_id']}"
        rows.append([InlineKeyboardButton(
            text=f"#{app['id']} | {label} | {app['created_at']}",
            callback_data=f"app_{app['id']}"
        )])
    rows.append([InlineKeyboardButton(
        text="◀️ Назад",
        callback_data="admin_panel"
    )])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def get_application_detail_keyboard(app_id):
    """Кнопки под детальным просмотром (принять/отказать/удалить)"""
    rows = [
        [
            InlineKeyboardButton(
                text="✅ Принять",
                callback_data=f"accept_{app_id}"
            ),
            InlineKeyboardButton(
                text="❌ Отказать",
                callback_data=f"reject_{app_id}"
            ),
        ],
        [
            InlineKeyboardButton(
                text="🗑 Удалить",
                callback_data=f"delete_{app_id}"
            )
        ],
        [InlineKeyboardButton(
            text="◀️ К списку заявок",
            callback_data="view_applications"
        )],
        [InlineKeyboardButton(
            text="🏠 Главное меню",
            callback_data="admin_panel"
        )],
    ]
    return InlineKeyboardMarkup(inline_keyboard=rows)


def get_confirm_delete_keyboard(app_id):
    """Подтверждение удаления конкретной заявки"""
    rows = [[
        InlineKeyboardButton(
            text="✅ Да, удалить",
            callback_data=f"confirm_delete_{app_id}"
        ),
        InlineKeyboardButton(
            text="❌ Отмена",
            callback_data=f"app_{app_id}"
        ),
    ]]
    return InlineKeyboardMarkup(inline_keyboard=rows)


def get_confirm_clear_keyboard():
    """Кнопки подтверждения очистки всех заявок"""
    rows = [[
        InlineKeyboardButton(
            text="✅ Да, удалить всё",
            callback_data="do_clear"
        ),
        InlineKeyboardButton(
            text="❌ Отмена",
            callback_data="cancel_clear"
        ),
    ]]
    return InlineKeyboardMarkup(inline_keyboard=rows)

def get_admin_menu_keyboard():
    """Главное меню администратора"""
    rows = [
        [InlineKeyboardButton(
            text="📋 Список заявок",
            callback_data="view_applications"
        )],
        [InlineKeyboardButton(
            text="📢 Рассылка",
            callback_data="broadcast_menu"
        )],
        [InlineKeyboardButton(
            text="🗑 Очистить все заявки",
            callback_data="confirm_clear"
        )],
    ]
    return InlineKeyboardMarkup(inline_keyboard=rows)