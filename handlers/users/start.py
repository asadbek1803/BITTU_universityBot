from aiogram import Router, types, F
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from loader import bot
from keyboards.reply.user import user_menu
from keyboards.reply.admin import admin_buttons
from components.credentials import GOOGLE_CREDENTIALS, SCOPES
import gspread
from components.datetime import get_tashkent_time
from components.functions import check_user_exists, check_user_status
from states.registration import RegistrationState
from google.oauth2.service_account import Credentials


router = Router()


creds = Credentials.from_service_account_info(GOOGLE_CREDENTIALS, scopes=SCOPES)
client = gspread.authorize(creds)
SPREADSHEET_NAME = "CRM"
worksheet = client.open(SPREADSHEET_NAME).worksheet("Users")




@router.message(CommandStart())
async def do_start(message: types.Message, state: FSMContext):
    telegram_id = message.from_user.id

    if check_user_exists(telegram_id):
        if check_user_status(telegram_id=telegram_id):
            await message.answer(f"Assalomu alaykum Admin! Quyidagi menulardan birini tanlang 👇👇", reply_markup=admin_buttons)
        else:
            await message.answer(f"Assalomu alaykum <b> {message.from_user.full_name} </b>! <i> Innovator klubiga </i> xush kelibsiz. Siz bilan ushbu bot orqali bog'lanib malumotlarni berib boramiz! \n\n Quyidagi menulardan birini tanlang👇👇", reply_markup=user_menu)
    else:
        keyboard = ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="📱 Telefon raqamni yuborish", request_contact=True)]
            ],
            resize_keyboard=True,
            one_time_keyboard=True
        )
        await message.answer("Iltimos, telefon raqamingizni yuboring 📲", reply_markup=keyboard)
        await state.set_state(RegistrationState.waiting_for_phone)


@router.message(RegistrationState.waiting_for_phone, F.contact)
async def phone_received(message: types.Message, state: FSMContext):
    phone_number = message.contact.phone_number

    # Telefon raqamini vaqtincha saqlash
    await state.update_data(phone_number=phone_number)

    await message.answer("Endi ism-familiyangizni kiriting ✍️")
    await state.set_state(RegistrationState.waiting_for_fullname)
    

@router.message(RegistrationState.waiting_for_fullname)
async def fullname_received(message: types.Message, state: FSMContext):
    telegram_id = message.from_user.id
    username = message.from_user.username or "Noma'lum"
    full_name = message.text
    created_at = get_tashkent_time().strftime("%Y-%m-%d %H:%M:%S")  # Datetime obyektini string formatga o‘tkazamiz
    is_admin = "False"

    # Oldindan saqlangan telefon raqamini olish
    user_data = await state.get_data()
    phone_number = user_data["phone_number"]

    # Yangi foydalanuvchini Google Sheets’ga qo‘shish
    worksheet.append_row([telegram_id, full_name, username, created_at, is_admin, phone_number])

    await message.answer("Siz muvaffaqiyatli ro‘yxatdan o‘tdingiz! ✅", reply_markup=types.ReplyKeyboardRemove())
    await bot.send_message(chat_id=telegram_id, text=f"Bizning botga xush kelibsiz 😊 Quyidagi menulardan birini tanlang 👇👇", reply_markup=user_menu)
    
    # State ni tozalash
    await state.clear()
