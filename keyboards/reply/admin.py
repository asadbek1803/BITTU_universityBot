from aiogram.types import ReplyKeyboardMarkup, KeyboardButton


buttons = [
    [KeyboardButton(text = "📊 Universited statistikasi")],
    [KeyboardButton(text="📨 Xabar yuborish"), KeyboardButton(text="➕ Admin qo'shish")],
    [KeyboardButton(text="🗂️ CRM baza linkini olish"), KeyboardButton(text= "🔗 Kanal qo'shish")],
    [KeyboardButton(text="🗑️ Kanal o'chirish")]
]

admin_buttons = ReplyKeyboardMarkup(keyboard=buttons,
                                    resize_keyboard=True,
                                    input_field_placeholder="Admin tanlamalari: ",
                                    )