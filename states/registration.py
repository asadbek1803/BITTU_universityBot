from aiogram.fsm.state import State, StatesGroup



class RegistrationState(StatesGroup):
    waiting_for_phone = State()
    waiting_for_fullname = State()
