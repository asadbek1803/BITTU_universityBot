from aiogram import types




kb = [
         
            [types.KeyboardButton(text="🟢 Keldim"), types.KeyboardButton(text="🔴 Ketdim")],
            [types.KeyboardButton(text="📊 Statistika")],
            [types.KeyboardButton(text="⚙️ Sozlamalar")]
        
    ]

user_menu = types.ReplyKeyboardMarkup(
        resize_keyboard=True,
        input_field_placeholder="Quyidagi menuni tanlang: ",
        keyboard=kb)


def create_main_keyboard():
    """Create keyboard for main menu with attendance buttons and settings"""
    return types.ReplyKeyboardMarkup(
        keyboard=[
            [types.KeyboardButton(text="🟢 Keldim"), types.KeyboardButton(text="🔴 Ketdim")],
            [types.KeyboardButton(text="📊 Statistika")],
            [types.KeyboardButton(text="⚙️ Sozlamalar")]
        ],
        resize_keyboard=True
    )

def create_settings_keyboard():
    """Create keyboard for settings menu"""
    return types.ReplyKeyboardMarkup(
        keyboard=[
            [types.KeyboardButton(text="👤 Ismni o'zgartirish")],
            [types.KeyboardButton(text="📱 Telefon raqamni o'zgartirish")],
            [types.KeyboardButton(text="🔔 Bildirishnomalar")],
            [types.KeyboardButton(text="⬅️ Asosiy menyu")]
        ],
        resize_keyboard=True
    )

def create_notification_settings_keyboard():
    """Create keyboard for notification settings"""
    return types.ReplyKeyboardMarkup(
        keyboard=[
            [types.KeyboardButton(text="🔔 Kunlik eslatmalar")],
            [types.KeyboardButton(text="⬅️ Orqaga")]
        ],
        resize_keyboard=True
    )

def create_back_keyboard():
    """Create a simple keyboard with just a back button"""
    return types.ReplyKeyboardMarkup(
        keyboard=[
            [types.KeyboardButton(text="⬅️ Orqaga")]
        ],
        resize_keyboard=True
    )