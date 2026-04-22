# bot/handlers/admin.py
import logging
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext

from bot.filters import IsAdmin
from bot.states import AdminActions
from bot.database import (
    get_all_applications,
    get_application_by_id,
    clear_all_applications,
    accept_application,
    reject_application,
    delete_application,
    get_all_user_ids  # ✅ ДОБАВЛЕНО
)
from bot.keyboards.admin_kb import (
    get_admin_menu_keyboard,
    get_applications_list_keyboard,
    get_application_detail_keyboard,
    get_confirm_clear_keyboard,
    get_confirm_delete_keyboard
)

logger = logging.getLogger(__name__)

router = Router()
router.message.filter(IsAdmin())
router.callback_query.filter(IsAdmin())


@router.message(Command("admin"))
async def cmd_admin(message: Message, state: FSMContext):
    """Открывает панель администратора"""
    await state.clear()
    await message.answer(
        f"🔧 <b>Панель администратора</b>\n\n"
        f"👤 {message.from_user.full_name}\n\n"
        "Выберите действие:",
        parse_mode="HTML",
        reply_markup=get_admin_menu_keyboard()
    )
    logger.info(f"Администратор {message.from_user.id} открыл панель")


@router.callback_query(F.data == "admin_panel")
async def cb_admin_panel(callback: CallbackQuery, state: FSMContext):
    """Возврат в главное меню администратора"""
    await state.clear()
    await callback.message.edit_text(
        "🔧 <b>Панель администратора</b>\n\nВыберите действие:",
        parse_mode="HTML",
        reply_markup=get_admin_menu_keyboard()
    )
    await callback.answer()


@router.callback_query(F.data == "view_applications")
async def cb_view_applications(callback: CallbackQuery):
    """Показывает список всех заявок"""
    apps = await get_all_applications()
    if not apps:
        await callback.message.edit_text(
            "📭 <b>Список заявок пуст.</b>\n\n"
            "Пока никто не подавал заявки.",
            parse_mode="HTML",
            reply_markup=get_admin_menu_keyboard()
        )
        await callback.answer()
        return
    await callback.message.edit_text(
        f"📋 <b>Список заявок</b>\n\n"
        f"Всего: <b>{len(apps)}</b>\n\n"
        "Нажмите на заявку для просмотра:",
        parse_mode="HTML",
        reply_markup=get_applications_list_keyboard(apps)
    )
    await callback.answer()


@router.callback_query(F.data.startswith("app_"))
async def cb_view_detail(callback: CallbackQuery, state: FSMContext):
    """Детальный просмотр заявки"""
    await state.clear()
    app_id = int(callback.data.split("_")[1])
    app = await get_application_by_id(app_id)
    if not app:
        await callback.answer("Заявка не найдена!", show_alert=True)
        return

    uid   = app["user_id"]
    uname = app["username"]
    if uname:
        link    = f"https://t.me/{uname}"
        display = f"@{uname}"
    else:
        link    = f"tg://user?id={uid}"
        display = f"ID: {uid}"

    status_text = f"<b>Статус:</b> {app['status']}\n\n" if app.get('status') else ""

    text = (
        f"📄 <b>Заявка #{app['id']}</b>  |  {app['created_at']}\n\n"
        f"👤 <b>Пользователь:</b> {display}\n"
        f"🔗 <a href=\"{link}\">Открыть профиль</a>\n\n"
        f"━━━━━━━━━━━━━━━━━━\n\n"
        f"{status_text}"
        f"👤 <b>Имя:</b>\n{app['name']}\n\n"
        f"🎂 <b>Возраст:</b>\n{app['age']}\n\n"
        f"😊 <b>Уровень адекватности (1-10):</b>\n{app['adequacy']}\n\n"
        f"🤝 <b>Готов помогать стримеру:</b>\n{app['help_ready']}\n\n"
        f"💼 <b>Опыт модерирования:</b>\n{app['experience']}"
    )
    await callback.message.edit_text(
        text,
        parse_mode="HTML",
        reply_markup=get_application_detail_keyboard(app_id),
        disable_web_page_preview=True
    )
    await callback.answer()
    logger.info(f"Администратор {callback.from_user.id} открыл заявку #{app_id}")


@router.callback_query(F.data.startswith("accept_"))
async def cb_accept_application(callback: CallbackQuery):
    """Принимает заявку"""
    app_id = int(callback.data.split("_")[1])
    app = await get_application_by_id(app_id)
    
    if not app:
        await callback.answer("Заявка не найдена!", show_alert=True)
        return
    
    await accept_application(app_id)
    
    try:
        await callback.bot.send_message(
            chat_id=app["user_id"],
            text=f"🎉 <b>Поздравляем!</b>\n\n"
                 f"✅ Ваша заявка на должность модератора <b>принята</b>!\n\n"
                 f"📌 Номер заявки: <b>#{app_id}</b>\n\n"
                 f"Администрация свяжется с вами в ближайшее время.",
            parse_mode="HTML"
        )
        logger.info(f"Пользователю {app['user_id']} отправлено сообщение о принятии заявки #{app_id}")
    except Exception as e:
        logger.error(f"Ошибка отправки сообщения пользователю: {e}")
    
    await callback.message.edit_text(
        f"✅ <b>Заявка #{app_id} принята!</b>\n\n"
        f"Пользователю отправлено сообщение о принятии.",
        parse_mode="HTML",
        reply_markup=get_admin_menu_keyboard()
    )
    await callback.answer("Заявка принята!", show_alert=True)


@router.callback_query(F.data.startswith("reject_"))
async def cb_reject_ask_reason(callback: CallbackQuery, state: FSMContext):
    """Запрашивает причину отказа"""
    app_id = int(callback.data.split("_")[1])
    app = await get_application_by_id(app_id)
    
    if not app:
        await callback.answer("Заявка не найдена!", show_alert=True)
        return
    
    await state.set_state(AdminActions.waiting_for_reject_reason)
    await state.update_data(reject_app_id=app_id)
    
    await callback.message.edit_text(
        f"❌ <b>Отказ в заявке #{app_id}</b>\n\n"
        f"Напишите причину отказа:\n\n"
        f"<i>Например: «Недостаточно опыта»</i>",
        parse_mode="HTML"
    )
    await callback.answer()


@router.message(AdminActions.waiting_for_reject_reason)
async def process_reject_reason(message: Message, state: FSMContext):
    """Обрабатывает причину отказа"""
    data = await state.get_data()
    app_id = data["reject_app_id"]
    reason = message.text.strip()
    
    await state.clear()
    
    app = await get_application_by_id(app_id)
    if not app:
        await message.answer("⚠️ Заявка не найдена.")
        return
    
    await reject_application(app_id)
    
    try:
        await message.bot.send_message(
            chat_id=app["user_id"],
            text=f"😔 <b>К сожалению...</b>\n\n"
                 f"❌ Ваша заявка на должность модератора <b>отклонена</b>.\n\n"
                 f"📌 Номер заявки: <b>#{app_id}</b>\n"
                 f"📝 Причина: <b>{reason}</b>\n\n"
                 f"Спасибо за попытку! Можете подать новую заявку позже.",
            parse_mode="HTML"
        )
        logger.info(f"Пользователю {app['user_id']} отправлено сообщение об отклонении заявки #{app_id}")
    except Exception as e:
        logger.error(f"Ошибка отправки сообщения пользователю: {e}")
    
    await message.answer(
        f"❌ <b>Заявка #{app_id} отклонена!</b>\n\n"
        f"Причина: {reason}\n"
        f"Пользователю отправлено уведомление.",
        parse_mode="HTML",
        reply_markup=get_admin_menu_keyboard()
    )


@router.callback_query(F.data.startswith("delete_"))
async def cb_delete_confirm(callback: CallbackQuery):
    """Запрос подтверждения удаления"""
    app_id = int(callback.data.split("_")[1])
    app = await get_application_by_id(app_id)
    
    if not app:
        await callback.answer("Заявка не найдена!", show_alert=True)
        return
    
    await callback.message.edit_text(
        f"🗑 <b>Удалить заявку #{app_id}?</b>\n\n"
        f"Это действие <b>необратимо</b>!\n\n"
        f"Вы уверены?",
        parse_mode="HTML",
        reply_markup=get_confirm_delete_keyboard(app_id)
    )
    await callback.answer()


@router.callback_query(F.data.startswith("confirm_delete_"))
async def cb_delete_application(callback: CallbackQuery):
    """Выполняет удаление заявки"""
    app_id = int(callback.data.split("_")[2])
    app = await get_application_by_id(app_id)
    
    if not app:
        await callback.answer("Заявка не найдена!", show_alert=True)
        return
    
    await delete_application(app_id)
    
    await callback.message.edit_text(
        f"🗑 <b>Заявка #{app_id} удалена!</b>\n\n"
        f"Пользователь: @{app['username'] or 'ID ' + str(app['user_id'])}",
        parse_mode="HTML",
        reply_markup=get_admin_menu_keyboard()
    )
    await callback.answer("Заявка удалена!", show_alert=True)
    logger.info(f"Администратор {callback.from_user.id} удалил заявку #{app_id}")


# ✅ РАССЫЛКА СООБЩЕНИЙ (BROADCAST)
@router.callback_query(F.data == "broadcast_menu")
async def cb_broadcast_menu(callback: CallbackQuery, state: FSMContext):
    """Открывает меню рассылки"""
    await state.set_state(AdminActions.waiting_for_broadcast)
    
    await callback.message.edit_text(
        "📢 <b>Режим рассылки</b>\n\n"
        "Напишите сообщение для рассылки всем пользователям:\n\n"
        "<i>Можно использовать:</i>\n"
        "• <b>Жирный текст</b>\n"
        "• <i>Наклонный текст</i>\n"
        "• <u>Подчеркивание</u>\n\n"
        "Отправьте 'отмена' чтобы выйти из режима рассылки.",
        parse_mode="HTML"
    )
    await callback.answer()


@router.message(Command("broadcast"))
async def cmd_broadcast(message: Message, state: FSMContext):
    """Запускает режим рассылки через команду"""
    await state.clear()
    await state.set_state(AdminActions.waiting_for_broadcast)
    
    await message.answer(
        "📢 <b>Режим рассылки</b>\n\n"
        "Напишите сообщение для рассылки всем пользователям:\n\n"
        "<i>Можно использовать:</i>\n"
        "• <b>Жирный текст</b>\n"
        "• <i>Наклонный текст</i>\n"
        "• <u>Подчеркивание</u>\n\n"
        "Отправьте 'отмена' чтобы выйти из режима рассылки.",
        parse_mode="HTML"
    )
    logger.info(f"Администратор {message.from_user.id} начал рассылку")


@router.message(AdminActions.waiting_for_broadcast)
async def process_broadcast(message: Message, state: FSMContext):
    """Обрабатывает сообщение для рассылки"""
    
    # Проверяем отмену
    if message.text.lower() == "отмена":
        await state.clear()
        await message.answer(
            "❌ <b>Рассылка отменена.</b>",
            parse_mode="HTML",
            reply_markup=get_admin_menu_keyboard()
        )
        return
    
    broadcast_text = message.text
    
    # Получаем всех пользователей
    user_ids = await get_all_user_ids()
    
    if not user_ids:
        await state.clear()
        await message.answer(
            "❌ <b>Нет пользователей для рассылки.</b>",
            parse_mode="HTML",
            reply_markup=get_admin_menu_keyboard()
        )
        return
    
    # Отправляем сообщение всем
    success_count = 0
    failed_count = 0
    
    for user_id in user_ids:
        try:
            await message.bot.send_message(
                chat_id=user_id,
                text=broadcast_text,
                parse_mode="HTML",
                disable_web_page_preview=True
            )
            success_count += 1
        except Exception as e:
            failed_count += 1
            logger.warning(f"Не удалось отправить сообщение пользователю {user_id}: {e}")
    
    await state.clear()
    
    # Отправляем отчет администратору
    await message.answer(
        f"✅ <b>Рассылка завершена!</b>\n\n"
        f"📊 Статистика:\n"
        f"✅ Успешно отправлено: <b>{success_count}</b>\n"
        f"❌ Ошибок: <b>{failed_count}</b>\n"
        f"👥 Всего пользователей: <b>{len(user_ids)}</b>\n\n"
        f"📝 Текст рассылки:\n{broadcast_text}",
        parse_mode="HTML",
        reply_markup=get_admin_menu_keyboard()
    )
    
    logger.info(f"Администратор {message.from_user.id} завершил рассылку. "
                f"Успешно: {success_count}, Ошибок: {failed_count}")


@router.callback_query(F.data == "confirm_clear")
async def cb_confirm_clear(callback: CallbackQuery, state: FSMContext):
    """Запрос подтверждения перед очисткой"""
    apps = await get_all_applications()
    await state.set_state(AdminActions.waiting_for_clear_confirm)
    await callback.message.edit_text(
        f"⚠️ <b>Подтверждение удаления всех заявок</b>\n\n"
        f"Будет удалено заявок: <b>{len(apps)}</b>\n\n"
        "❗ Действие <b>необратимо!</b>\n\nВы уверены?",
        parse_mode="HTML",
        reply_markup=get_confirm_clear_keyboard()
    )
    await callback.answer()


@router.callback_query(F.data == "do_clear", AdminActions.waiting_for_clear_confirm)
async def cb_do_clear(callback: CallbackQuery, state: FSMContext):
    """Выполняет очистку всех заявок"""
    try:
        deleted = await clear_all_applications()
        await state.clear()
        await callback.message.edit_text(
            f"✅ <b>Список очищен!</b>\n\nУдалено заявок: <b>{deleted}</b>",
            parse_mode="HTML",
            reply_markup=get_admin_menu_keyboard()
        )
        await callback.answer("Удалено!", show_alert=True)
        logger.info(f"Администратор {callback.from_user.id} удалил {deleted} заявок")
    except Exception as e:
        logger.error(f"Ошибка очистки: {e}")
        await callback.answer("Ошибка при очистке!", show_alert=True)


@router.callback_query(F.data == "cancel_clear")
async def cb_cancel_clear(callback: CallbackQuery, state: FSMContext):
    """Отмена очистки"""
    await state.clear()
    await callback.message.edit_text(
        "❌ <b>Очистка отменена.</b>",
        parse_mode="HTML",
        reply_markup=get_admin_menu_keyboard()
    )
    await callback.answer("Отменено")