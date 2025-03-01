from datetime import datetime, timedelta
import calendar
from aiogram import Router
from aiogram.filters.callback_data import CallbackData
from aiogram import types
from aiogram.filters import Command
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardButton, InlineKeyboardMarkup
from datetime import datetime
import gspread
from components.functions import  check_user_status
from environs import Env
from aiogram.fsm.context import FSMContext
from components.datetime import get_tashkent_time
from components.credentials import GOOGLE_CREDENTIALS, SCOPES
from aiogram.fsm.state import State, StatesGroup
from loader import bot
from keyboards.reply.admin import admin_buttons
from google.oauth2.service_account import Credentials

router = Router()


SPREADSHEET_ID = "1n0SL-MYQXhuk5AJG5U63eAHmNCFnuoT1917n_YYTwH4"

creds = Credentials.from_service_account_info(GOOGLE_CREDENTIALS, scopes=SCOPES)
client = gspread.authorize(creds)



# Define callback data factories
class CalendarCallback(CallbackData, prefix="calendar"):
    action: str
    year: int
    month: int
    day: int = 0



def get_crm_link():
    """Google Sheets ID'dan CRM havolasini yaratish"""
    return f"https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/"


@router.message(lambda message: message.text == "🗂️ CRM baza linkini olish")
async def get_crm_link_handler(message: types.Message):
    """Foydalanuvchiga CRM bazasi havolasini yuborish"""
    crm_link = get_crm_link()
    
    if crm_link:
        await message.answer(f"🔗 CRM bazasiga kirish: [Google Sheets]({crm_link})", parse_mode="Markdown")
    else:
        await message.answer("❌ CRM havolasi topilmadi. Iltimos, administrator bilan bog‘laning.")



class ChannelAddState(StatesGroup):
    waiting_for_channel = State()

@router.message(lambda message: message.text == "🔗 Kanal qo'shish")  # "/add_channel" buyrug‘i bilan ishga tushadi
async def add_channel_command(message: types.Message, state: FSMContext):
    await message.answer(
        "🌐 Kanal username'ini yuboring (Masalan: `@YourChannel`)\n\n"
        "⚠️ *Diqqat!* Kanalni qo‘shishdan oldin botni admin qiling!"
        
    )
    await state.set_state(ChannelAddState.waiting_for_channel)

@router.message(ChannelAddState.waiting_for_channel)
async def process_channel_username(message: types.Message, state: FSMContext):
    channel_username = message.text.strip()
    channels_worksheet = client.open("CRM").worksheet("Channels")
    if not channel_username.startswith("@"):
        await message.answer("❌ Iltimos, kanal username'ini to‘g‘ri formatda yuboring! Masalan: `@YourChannel`")
        return

    try:
        # Google Sheets'ga qo‘shish
        channels_worksheet.append_row([channel_username])

        await message.answer("✅ Kanal muvaffaqiyatli qo‘shildi!")
        await state.clear()

    except Exception as e:
        await message.answer(f"❌ Xatolik yuz berdi: {e}")
        await state.clear()

# Handler for University Statistics
@router.message(lambda message: message.text == "📊 Universited statistikasi")

async def university_statistics(message: types.Message):
    worksheet = client.open("CRM").worksheet("Attends")
    if check_user_status(telegram_id=message.from_user.id) != True:
        await message.answer("❌ Kechirasiz, bu funksiyadan foydalanish uchun sizda administrator huquqi yo'q.")
        return

    all_records = worksheet.get_all_values()
    data_rows = all_records[1:] if len(all_records) > 0 else []
    
    # Get current date
    current_date = get_tashkent_time()
    
    # Calculate statistics
    today_count = 0
    weekly_count = 0
    monthly_count = 0
    
    # Get start of week (Monday)
    week_start = current_date - timedelta(days=current_date.weekday())
    week_start = datetime(week_start.year, week_start.month, week_start.day)
    
    # Get start of month
    month_start = datetime(current_date.year, current_date.month, 1)
    
    # Count attendances
    unique_users_today = set()
    unique_users_week = set()
    unique_users_month = set()
    
    for row in data_rows:
        if len(row) > 3 and row[3]:  # ArrivalTime column
            try:
                arrival_time = datetime.strptime(row[3], "%Y-%m-%d %H:%M")
                user_id = row[1]  # TelegramID column
                
                # Check if today
                if arrival_time.date() == current_date.date():
                    unique_users_today.add(user_id)
                
                # Check if this week
                if arrival_time >= week_start:
                    unique_users_week.add(user_id)
                
                # Check if this month
                if arrival_time >= month_start:
                    unique_users_month.add(user_id)
                    
            except (ValueError, TypeError):
                pass
    
    today_count = len(unique_users_today)
    weekly_count = len(unique_users_week)
    monthly_count = len(unique_users_month)
    
    # Create message
    msg = (f"📊 Universitet davomat statistikasi:\n\n"
           f"📅 Bugun: {today_count} o'quvchi\n"
           f"📅 Shu hafta: {weekly_count} o'quvchi\n"
           f"📅 Shu oy: {monthly_count} o'quvchi")
    
    # Create inline keyboard for daily statistics
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📆 Kunlik statistikani ko'rish", callback_data=CalendarCallback(action="month", year=current_date.year, month=current_date.month).pack())]
        ]
    )
    
    await message.answer(msg, reply_markup=keyboard)

# Create calendar 
async def create_calendar(year, month):
    keyboard = []
    
    # Add header row with month and year
    month_name = calendar.month_name[month]
    keyboard.append([
        InlineKeyboardButton(text="<<", callback_data=CalendarCallback(action="month", year=year if month > 1 else year - 1, month=month - 1 if month > 1 else 12).pack()),
        InlineKeyboardButton(text=f"{month_name} {year}", callback_data="ignore"),
        InlineKeyboardButton(text=">>", callback_data=CalendarCallback(action="month", year=year if month < 12 else year + 1, month=month + 1 if month < 12 else 1).pack())
    ])
    
    # Add days of week header
    days_of_week = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    keyboard.append([InlineKeyboardButton(text=day, callback_data="ignore") for day in days_of_week])
    
    # Get the calendar for the month
    month_calendar = calendar.monthcalendar(year, month)
    
    # Add calendar days
    for week in month_calendar:
        row = []
        for day in week:
            if day == 0:
                row.append(InlineKeyboardButton(text=" ", callback_data="ignore"))
            else:
                row.append(InlineKeyboardButton(
                    text=str(day),
                    callback_data=CalendarCallback(action="day", year=year, month=month, day=day).pack()
                ))
        keyboard.append(row)
    
    # Add close button
    keyboard.append([InlineKeyboardButton(text="❌ Yopish", callback_data="close_calendar")])
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

# Handler for calendar callbacks
@router.callback_query(CalendarCallback.filter())
async def calendar_callback_handler(call: types.CallbackQuery, callback_data: CalendarCallback):
    worksheet = client.open("CRM").worksheet("Attends")
    action = callback_data.action
    year = callback_data.year
    month = callback_data.month
    day = callback_data.day
    
    # Process different actions
    if action == "month":
        calendar_markup = await create_calendar(year, month)
        await call.message.edit_text("📆 Kunni tanlang:", reply_markup=calendar_markup)
    
    elif action == "day":
        # Get selected date
        selected_date = datetime(year, month, day)
        
        # Get attendance for the selected date
        all_records = worksheet.get_all_values()
        data_rows = all_records[1:] if len(all_records) > 0 else []
        
        # Filter records for the selected date
        day_records = []
        for row in data_rows:
            if len(row) > 3 and row[3]:  # ArrivalTime column
                try:
                    arrival_time = datetime.strptime(row[3], "%Y-%m-%d %H:%M")
                    if arrival_time.date() == selected_date.date():
                        day_records.append(row)
                except (ValueError, TypeError):
                    pass
        
        # Format date for display
        formatted_date = selected_date.strftime("%Y-%m-%d")
        
        # Check if any records found
        if not day_records:
            await call.message.edit_text(
                f"📅 {formatted_date} kuni hech kim kelmagan.",
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="◀️ Orqaga", callback_data=CalendarCallback(action="month", year=year, month=month).pack())]
                ])
            )
            return
        
        # Prepare for pagination
        total_records = len(day_records)
        pages = (total_records + 9) // 10  # Calculate number of pages (10 items per page)
        
        # Show first page
        await show_attendance_page(call.message, day_records, 1, pages, year, month, day, formatted_date)
    
    await call.answer()

# Handler for close calendar button
@router.callback_query(lambda c: c.data == "close_calendar")
async def close_calendar(call: types.CallbackQuery):
    await call.message.delete()
    await call.answer()

# Function to show paginated attendance
async def show_attendance_page(message, records, page, total_pages, year, month, day, formatted_date):
    # Calculate start and end indices for current page
    start_idx = (page - 1) * 10
    end_idx = min(start_idx + 10, len(records))
    
    # Create message text
    text = f"📅 {formatted_date} kungi davomat:\n\n"
    
    for i, record in enumerate(records[start_idx:end_idx], start=start_idx + 1):
        name = record[0]  # FullName column
        arrival = record[3].split(" ")[1] if len(record) > 3 and " " in record[3] else "N/A"
        departure = record[4].split(" ")[1] if len(record) > 4 and record[4] and " " in record[4] else "N/A"
        duration = record[5] if len(record) > 5 else "0"
        
        text += f"{i}. {name}\n   🕒 {arrival} - {departure} ({duration} soat)\n\n"
    
    text += f"Sahifa: {page}/{total_pages}"
    
    # Create navigation buttons
    keyboard = []
    nav_row = []
    
    if page > 1:
        nav_row.append(InlineKeyboardButton(text="◀️ Oldingi", callback_data=f"page_{year}_{month}_{day}_{page-1}"))
    
    if page < total_pages:
        nav_row.append(InlineKeyboardButton(text="Keyingi ▶️", callback_data=f"page_{year}_{month}_{day}_{page+1}"))
    
    if nav_row:
        keyboard.append(nav_row)
    
    # Add back button
    keyboard.append([InlineKeyboardButton(text="◀️ Orqaga", callback_data=CalendarCallback(action="month", year=year, month=month).pack())])
    
    # Edit message with new content
    await message.edit_text(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard))

# Handler for pagination callbacks
@router.callback_query(lambda c: c.data.startswith("page_"))
async def pagination_callback(call: types.CallbackQuery):
    worksheet = client.open("CRM").worksheet("Attends")
    # Parse callback data
    _, year, month, day, page = call.data.split("_")
    year, month, day, page = int(year), int(month), int(day), int(page)
    
    # Get the date
    selected_date = datetime(year, month, day)
    formatted_date = selected_date.strftime("%Y-%m-%d")
    
    # Get records for the selected date
    all_records = worksheet.get_all_values()
    data_rows = all_records[1:] if len(all_records) > 0 else []
    
    day_records = []
    for row in data_rows:
        if len(row) > 3 and row[3]:
            try:
                arrival_time = datetime.strptime(row[3], "%Y-%m-%d %H:%M")
                if arrival_time.date() == selected_date.date():
                    day_records.append(row)
            except (ValueError, TypeError):
                pass
    
    # Calculate total pages
    total_pages = (len(day_records) + 9) // 10
    
    # Show the requested page
    await show_attendance_page(call.message, day_records, page, total_pages, year, month, day, formatted_date)
    await call.answer()

# Add the handlers for other admin buttons



# Define states for the conversation
class AdminStates(StatesGroup):
    waiting_for_message = State()
    confirm_message = State()
    waiting_for_admin_id = State()
    confirm_admin = State()

# Handler for sending message to all users
@router.message(lambda message: message.text == "📨 Xabar yuborish")
async def send_message_command(message: types.Message, state: FSMContext):
    users_worksheet = client.open("CRM").worksheet("Users")
    # Check if the user is an admin
    telegram_id = str(message.from_user.id)
    all_users = users_worksheet.get_all_values()
    
    # Skip header row
    users_data = all_users[1:] if len(all_users) > 0 else []
    
    # Find user
    user_row = None
    for i, row in enumerate(users_data, start=1):
        if len(row) > 1 and row[1] == telegram_id:
            user_row = row
            break
    
    # Check if user is admin
    if check_user_status(telegram_id=telegram_id) != True:
        await message.answer("❌ Kechirasiz, bu funksiyadan foydalanish uchun sizda administrator huquqi yo'q.")
        return
    
    # User is admin, proceed with message sending
    await message.answer("📝 Barcha foydalanuvchilarga yubormoqchi bo'lgan xabaringizni kiriting:")
    await state.set_state(AdminStates.waiting_for_message)

# Handler for receiving the message to send
@router.message(AdminStates.waiting_for_message)
async def process_message_to_send(message: types.Message, state: FSMContext):
    # Save the message text
    await state.update_data(message_text=message.text)
    
    # Ask for confirmation
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="✅ Yuborish"), KeyboardButton(text="❌ Bekor qilish")]
        ],
        resize_keyboard=True
    )
    
    preview_text = message.text
    if len(preview_text) > 100:
        preview_text = preview_text[:97] + "..."
    
    await message.answer(
        f"📩 Quyidagi xabarni barcha foydalanuvchilarga yuborilsinmi?\n\n{preview_text}",
        reply_markup=keyboard
    )
    await state.set_state(AdminStates.confirm_message)

# Handler for message confirmation
@router.message(AdminStates.confirm_message)
async def confirm_sending_message(message: types.Message, state: FSMContext):
    users_worksheet = client.open("CRM").worksheet("Users")
    if message.text == "✅ Yuborish":
        # Get the message to send
        user_data = await state.get_data()
        message_text = user_data.get("message_text", "")
        
        # Get all users
        all_users = users_worksheet.get_all_values()
        users_data = all_users[1:] if len(all_users) > 0 else []
        
        # Count successful and failed sends
        sent_count = 0
        failed_count = 0
        
        # Send message to all users
        await message.answer("📤 Xabar yuborilmoqda...")
        
        for row in users_data:
            if len(row) > 1:  # Make sure the row has a TelegramID
                try:
                    user_id = int(row[0])
                    await bot.send_message(user_id, f"📢 Admindan xabar:\n\n{message_text}")
                    sent_count += 1
                except Exception:
                    failed_count += 1
        
        # Restore original keyboard
       
        
        # Send summary
        await message.answer(
            f"✅ Xabar yuborildi!\n\n"
            f"📤 Yuborildi: {sent_count} foydalanuvchi\n"
            f"❌ Xatolik: {failed_count} foydalanuvchi",
            reply_markup=admin_buttons
        )
    else:
        # Cancelled
        
        
        await message.answer("❌ Xabar yuborish bekor qilindi.", reply_markup=admin_buttons)
    
    # Reset state
    await state.clear()

# Handler for adding a new admin
@router.message(lambda message: message.text == "➕ Admin qo'shish")
async def add_admin_command(message: types.Message, state: FSMContext):
    users_worksheet = client.open("CRM").worksheet("Users")
    # Check if the user is an admin
    telegram_id = str(message.from_user.id)
    all_users = users_worksheet.get_all_values()
    
    # Skip header row
    users_data = all_users[1:] if len(all_users) > 0 else []
    
    # Find user
    user_row = None
    user_row_index = -1
    for i, row in enumerate(users_data, start=1):
        if len(row) > 1 and row[1] == telegram_id:
            user_row = row
            user_row_index = i
            break
    
    # Check if user is admin
    if check_user_status(telegram_id=telegram_id) != True:
        await message.answer("❌ Kechirasiz, bu funksiyadan foydalanish uchun sizda administrator huquqi yo'q.")
        return
    
    # User is admin, proceed with adding new admin
    await message.answer("👤 Yangi administrator qilmoqchi bo'lgan foydalanuvchining Telegram ID raqamini kiriting:")
    await state.set_state(AdminStates.waiting_for_admin_id)

# Handler for receiving the admin ID
@router.message(AdminStates.waiting_for_admin_id)
async def process_admin_id(message: types.Message, state: FSMContext):
    new_admin_id = message.text.strip()
    users_worksheet = client.open("CRM").worksheet("Users")
    # Validate if the input is a valid ID
    if not new_admin_id.isdigit():
        await message.answer("❌ Noto'g'ri format. Iltimos, raqamlardan iborat Telegram ID kiriting:")
        return
    
    # Save the ID
    await state.update_data(new_admin_id=new_admin_id)
    
    # Check if user exists in the worksheet
    all_users = users_worksheet.get_all_values()
    users_data = all_users[1:] if len(all_users) > 0 else []
    
    # Find user
    user_exists = False
    user_row_index = -1
    user_name = ""
    
    for i, row in enumerate(users_data, start=1):
        if len(row) > 1 and row[0] == new_admin_id:
            user_exists = True
            user_row_index = i + 1  # Adding 1 because we skipped the header row
            user_name = row[0] if len(row) > 0 else "Noma'lum foydalanuvchi"
            break
    
    if not user_exists:
        await message.answer("❌ Bunday Telegram ID raqamli foydalanuvchi topilmadi. Iltimos, qayta tekshiring.")
        await state.clear()
        return
    
    # Check if user is already an admin
    is_already_admin = False
    if check_user_status(telegram_id=new_admin_id) == "True":
        is_already_admin = True
    
    if is_already_admin:
        await message.answer(f"⚠️ {user_name} allaqachon administrator huquqiga ega.")
        await state.clear()
        return
    
    # Save user info
    await state.update_data(user_row_index=user_row_index, user_name=user_name)
    
    # Ask for confirmation
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="✅ Tasdiqlash"), KeyboardButton(text="❌ Bekor qilish")]
        ],
        resize_keyboard=True
    )
    
    await message.answer(
        f"👤 {user_name} (ID: {new_admin_id}) foydalanuvchisiga administrator huquqi berilsinmi?",
        reply_markup=keyboard
    )
    await state.set_state(AdminStates.confirm_admin)

# Handler for admin confirmation
@router.message(AdminStates.confirm_admin)
async def confirm_add_admin(message: types.Message, state: FSMContext):
    if message.text == "✅ Tasdiqlash":
        users_worksheet = client.open("CRM").worksheet("Users")
        # Get user data
        user_data = await state.get_data()
        user_row_index = user_data.get("user_row_index", -1)
        user_name = user_data.get("user_name", "")
        new_admin_id = user_data.get("new_admin_id", "")
        
        if user_row_index > 0:
            try:
                # Update the IsAdmin field to True
                users_worksheet.update_cell(user_row_index, 5, "'True")  # Column E is 5th column (IsAdmin)
                
                # Try to notify the user about their new admin status
                try:
                    await bot.send_message(
                        int(new_admin_id),
                        "🎉 Tabriklaymiz! Sizga administrator huquqi berildi."
                    )
                except Exception:
                    # Couldn't send message to the user, but admin status was still updated
                    pass
                
                # Restore original keyboard
                
                await message.answer(
                    f"✅ {user_name} (ID: {new_admin_id}) foydalanuvchisiga administrator huquqi berildi.",
                    reply_markup=admin_buttons
                )
            except Exception as e:
                await message.answer(f"❌ Xatolik yuz berdi: {str(e)}")
        else:
            await message.answer("❌ Xatolik yuz berdi: Foydalanuvchi ma'lumotlari topilmadi.")
    else:
        # Cancelled
        
        
        await message.answer("❌ Administrator qo'shish bekor qilindi.", reply_markup=admin_buttons)
    
    # Reset state
    await state.clear()