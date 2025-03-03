from aiogram.fsm.state import State, StatesGroup


class UserIdeas(StatesGroup):
    idea = State()

class SettingsStates(StatesGroup):
    main_menu = State()
    changing_name = State()
    changing_phone = State()
    notification_settings = State()