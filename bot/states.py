from aiogram.fsm.state import State, StatesGroup


class ApplicationForm(StatesGroup):
    """Шаги анкеты на должность модератора"""
    waiting_for_platform = State()  # ✅ Новое: выбор платформы
    waiting_for_name = State()
    waiting_for_age = State()
    waiting_for_adequacy = State()
    waiting_for_help = State()
    waiting_for_experience = State()


class AdminActions(StatesGroup):
    """Состояния для действий администратора"""
    waiting_for_clear_confirm = State()
    waiting_for_reject_reason = State()
    waiting_for_broadcast = State()