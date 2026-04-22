# bot/handlers/user.py
import logging
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext

from bot.states import ApplicationForm
from bot.database import save_application, check_existing_application, add_user
from bot.config import ADMIN_IDS, CHAT_NAME
from bot.keyboards.user_kb import get_start_keyboard, get_cancel_keyboard, get_platform_keyboard

logger = logging.getLogger(__name__)
router = Router()


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    """Приветствие при команде /start"""
    await state.clear()
    
    user = message.from_user
    await add_user(
        user_id=user.id,
        username=user.username,
        first_name=user.first_name,
        last_name=user.last_name
    )
    
    name = user.full_name

    if user.id in ADMIN_IDS:
        await message.answer(
            f"👋 Привет, <b>Администратор {name}</b>!\n\n"
            "Используйте /admin для панели управления.",
            parse_mode="HTML",
            reply_markup=get_start_keyboard(is_admin=True)
        )
        return

    await message.answer(
        f"👋 Привет, <b>{name}</b>!\n\n"
        f"Это бот для подачи заявок на должность <b>модератора</b> {CHAT_NAME}.\n\n"
        "📋 Тебе предстоит ответить на <b>5 вопросов</b>.\n"
        "Заявка будет рассмотрена администрацией.\n\n"
        "Готов начать? 👇",
        parse_mode="HTML",
        reply_markup=get_start_keyboard(is_admin=False)
    )
    logger.info(f"Пользователь {user.id} запустил бота")


@router.callback_query(F.data == "apply")
async def start_application(callback: CallbackQuery, state: FSMContext):
    """Начало заполнения анкеты - выбор платформы"""
    uid = callback.from_user.id

    if await check_existing_application(uid):
        await callback.answer("⚠️ Вы уже подавали заявку!", show_alert=True)
        await callback.message.edit_text(
            "❌ <b>Вы уже подали заявку ранее.</b>\n\n"
            "Администрация рассмотрит её в ближайшее время.",
            parse_mode="HTML"
        )
        return

    # ✅ ВЫБОР ПЛАТФОРМЫ
    await callback.message.edit_text(
        "📱 <b>Выберите платформу:</b>\n\n"
        "На какой платформе вы хотите стать модератором?",
        parse_mode="HTML",
        reply_markup=get_platform_keyboard()
    )
    await callback.answer()


# ✅ ОБРАБОТЧИК ВЫБОРА ПЛАТФОРМЫ
@router.callback_query(F.data.startswith("platform_"))
async def select_platform(callback: CallbackQuery, state: FSMContext):
    """Обрабатывает выбор платформы"""
    platform = callback.data.split("_")[1].upper()  # twitch или youtube
    
    await state.set_state(ApplicationForm.waiting_for_name)
    await state.update_data(platform=platform)
    
    await callback.message.edit_text(
        "📝 <b>Анкета на должность модератора</b>\n\n"
        f"📱 <b>Платформа: {platform}</b>\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "❓ <b>Вопрос 1 из 5</b>\n\n"
        "Как тебя зовут?\n\n"
        "<i>Пример: Иван</i>",
        parse_mode="HTML",
        reply_markup=get_cancel_keyboard()
    )
    await callback.answer()
    logger.info(f"Пользователь {callback.from_user.id} выбрал платформу: {platform}")


@router.message(ApplicationForm.waiting_for_name)
async def q1_name(message: Message, state: FSMContext):
    """Ответ на вопрос 1 — имя"""
    await state.update_data(name=message.text)
    await state.set_state(ApplicationForm.waiting_for_age)
    
    data = await state.get_data()
    platform = data.get("platform", "")
    
    await message.answer(
        "✅ Отлично!\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "❓ <b>Вопрос 2 из 5</b>\n\n"
        "Сколько тебе лет?\n\n"
        "<i>Пример: 18</i>",
        parse_mode="HTML",
        reply_markup=get_cancel_keyboard()
    )


@router.message(ApplicationForm.waiting_for_age)
async def q2_age(message: Message, state: FSMContext):
    """Ответ на вопрос 2 — возраст"""
    await state.update_data(age=message.text)
    await state.set_state(ApplicationForm.waiting_for_adequacy)
    await message.answer(
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "❓ <b>Вопрос 3 из 5</b>\n\n"
        "Оцени свой уровень адекватности (от 1 до 10):\n\n"
        "<i>Пример: 8</i>\n"
        "<i>1 - совсем неадекватный, 10 - полностью адекватный</i>",
        parse_mode="HTML",
        reply_markup=get_cancel_keyboard()
    )


@router.message(ApplicationForm.waiting_for_adequacy)
async def q3_adequacy(message: Message, state: FSMContext):
    """Ответ на вопрос 3 — адекватность"""
    await state.update_data(adequacy=message.text)
    await state.set_state(ApplicationForm.waiting_for_help)
    await message.answer(
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "❓ <b>Вопрос 4 из 5</b>\n\n"
        "Готов ли ты помогать стримеру и отвечать на вопросы зрителей, если стример не смог ответить? (если да, то каким образом?)\n\n"
        "<i>Ответь: Да/Нет</i>",
        parse_mode="HTML",
        reply_markup=get_cancel_keyboard()
    )


@router.message(ApplicationForm.waiting_for_help)
async def q4_help(message: Message, state: FSMContext):
    """Ответ на вопрос 4 — готовность помогать"""
    await state.update_data(help_ready=message.text)
    await state.set_state(ApplicationForm.waiting_for_experience)
    await message.answer(
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "❓ <b>Вопрос 5 из 5</b>\n\n"
        "Есть ли у тебя опыт модерирования?\n\n"
        "<i>Пример: Да, я модерировал чат 6 месяцев</i>\n"
        "<i>или: Нет, но я готов учиться</i>",
        parse_mode="HTML",
        reply_markup=get_cancel_keyboard()
    )


@router.message(ApplicationForm.waiting_for_experience)
async def q5_experience(message: Message, state: FSMContext):
    """Финальный ответ — опыт модератора"""
    data = await state.get_data()
    user = message.from_user
    
    try:
        app_id = await save_application(
            user_id=user.id,
            username=user.username,
            platform=data["platform"],  # ✅ ДОБАВЛЕНО
            name=data["name"],
            age=data["age"],
            adequacy=data["adequacy"],
            help_ready=data["help_ready"],
            experience=message.text,
        )
        await state.clear()
        await message.answer(
            "🎉 <b>Анкета отправлена!</b>\n\n"
            "✅ Ваша заявка принята и будет рассмотрена администрацией.\n\n"
            f"📌 Номер заявки: <b>#{app_id}</b>\n\n"
            "Мы свяжемся с вами в ближайшее время. Спасибо! 🙏",
            parse_mode="HTML"
        )
        logger.info(f"Заявка #{app_id} ({data['platform']}) от {user.id} сохранена")
    except Exception as e:
        logger.error(f"Ошибка сохранения заявки: {e}")
        await state.clear()
        await message.answer(
            "❌ Ошибка при сохранении заявки. Попробуйте позже."
        )


@router.callback_query(F.data == "cancel_form")
async def cancel_form(callback: CallbackQuery, state: FSMContext):
    """Отмена заполнения анкеты"""
    await state.clear()
    await callback.message.edit_text(
        "❌ <b>Заполнение анкеты отменено.</b>\n\n"
        "Чтобы начать заново — /start",
        parse_mode="HTML"
    )
    await callback.answer("Отменено")
    logger.info(f"Пользователь {callback.from_user.id} отменил анкету")