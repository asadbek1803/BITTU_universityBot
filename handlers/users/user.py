from aiogram import Router, types
from aiogram.fsm.context import FSMContext
from datetime import datetime
import gspread
from components.functions import get_user_info, get_user_student
from components.datetime import get_tashkent_time
from environs import Env
from components.credentials import GOOGLE_CREDENTIALS, SCOPES
from states.users import SettingsStates
from google.oauth2.service_account import Credentials
from keyboards.reply.user import create_settings_keyboard, create_back_keyboard, create_main_keyboard, create_notification_settings_keyboard

router = Router()


creds = Credentials.from_service_account_info(GOOGLE_CREDENTIALS, scopes=SCOPES)
client = gspread.authorize(creds)



# User session storage
user_sessions = {}




@router.message(lambda message: message.text == "🟢 Keldim")
async def user_check_in(message: types.Message):
    worksheet = client.open("CRM").worksheet("Attends")
    telegram_id = str(message.from_user.id)
    full_name, phone = get_user_info(telegram_id)

    if not full_name:
        await message.answer("❗ Siz tizimda ro'yxatdan o'tmagansiz. Admin bilan bog'laning.")
        return
    
    if get_user_student(telegram_id=telegram_id) != True:
        await message.answer("⛔ Siz davomatga yozila olmaysiz yoki admin tasdiqlovi kutilmoqda...")
        return
    
    now = get_tashkent_time()
    today_date = now.strftime("%Y-%m-%d")  # YYYY-MM-DD format
    arrival_time = now.strftime("%H:%M")  # Current time (hour:minute)
    full_time = f"{today_date} {arrival_time}"

    # Check if user already checked in today
    all_records = worksheet.get_all_values()
    today_entry_exists = False
    
    for row in all_records:
        if row[1] == telegram_id and row[3].startswith(today_date):
            today_entry_exists = True
            break
    
    if today_entry_exists:
        await message.answer("❗ Siz bugun allaqachon kelganingizni qayd etgansiz.")
    else:
        user_sessions[telegram_id] = {"check_in": arrival_time, "check_in_time": now, "date": today_date}

        # Add to Attends worksheet
        worksheet.append_row([full_name, telegram_id, phone, full_time, ""])
        await message.answer(f"✅ Kelgan vaqtingiz saqlandi: {arrival_time}")


@router.message(lambda message: message.text == "🔴 Ketdim")
async def user_check_out(message: types.Message):
    worksheet = client.open("CRM").worksheet("Attends")
    telegram_id = str(message.from_user.id)
    now = get_tashkent_time()
    today_date = now.strftime("%Y-%m-%d")
    check_out_time = now.strftime("%H:%M")  # Current time (hour:minute)
    full_time = f"{today_date} {check_out_time}"

    # Initialize variables to avoid UnboundLocalError
    check_in_time = "00:00"  # Default value
    check_in_datetime = None
    row_number = None
    
    # Check if the user has already checked out today
    all_records = worksheet.get_all_values()
    
    for i, row in enumerate(all_records, start=1):
        if row[1] == telegram_id and row[3].startswith(today_date):
            if row[4]:  # If checkout time is already recorded
                await message.answer("❗ Siz bugun allaqachon ketganingizni qayd etgansiz.")
                return
            else:
                row_number = i
                check_in_full = row[3]  # Full timestamp "YYYY-MM-DD HH:MM"
                try:
                    # Parse the check-in datetime
                    check_in_datetime = datetime.strptime(check_in_full, "%Y-%m-%d %H:%M")
                    # Extract just the time part for comparison
                    check_in_time = check_in_full.split(" ")[1] if " " in check_in_full else "00:00"
                except (ValueError, IndexError):
                    # Fallback if format is different
                    check_in_parts = check_in_full.split(" ")
                    if len(check_in_parts) >= 2:
                        check_in_time = check_in_parts[1]
                    else:
                        check_in_time = "00:00"  # Default if parsing fails
                break
    
    if not row_number:
        await message.answer("❗ Siz bugun hali '🟢 Keldim' tugmasini bosmadingiz.")
        return

    # Calculate duration - make sure we compare actual datetime objects
    if check_in_datetime:
        # Calculate duration in hours using the actual timestamps
        tdelta = now - check_in_datetime
        duration = round(tdelta.total_seconds() / 3600, 1)  # Duration in hours
    else:
        # Fallback to time string comparison - less accurate but better than nothing
        try:
            time_format = "%H:%M"
            tdelta = datetime.strptime(check_out_time, time_format) - datetime.strptime(check_in_time, time_format)
            duration = round(tdelta.total_seconds() / 3600, 1)  # Duration in hours
            
            # If duration is negative (e.g., check-out on the next day), make it positive
            if duration < 0:
                duration += 24  # Add 24 hours
        except (ValueError, TypeError):
            # If all else fails, calculate a nominal duration
            duration = 0.5  # Default duration if calculation fails

    # Ensure duration is never zero unless truly zero
    if abs(duration) < 0.01:  # If duration is very close to zero
        if check_out_time != check_in_time:
            duration = 0.1  # Minimum duration if times differ but calculation results in 0
    
    # Update the spreadsheet
    worksheet.update(f"E{row_number}", [[full_time]])  # Use full_time format like check-in
    worksheet.update(f"F{row_number}", [[duration]])

    await message.answer(f"🚶‍♂️ Ketgan vaqtingiz saqlandi: {check_out_time}\n⏱️ Davomiylik: {duration} soat")
    
    # Remove from session if exists
    if telegram_id in user_sessions:
        del user_sessions[telegram_id]


@router.message(lambda message: message.text == "📊 Statistika")
async def user_statistics(message: types.Message):
    worksheet = client.open("CRM").worksheet("Attends")
    telegram_id = str(message.from_user.id)
    all_records = worksheet.get_all_values()
    
    # Skip header row
    data_rows = all_records[1:] if len(all_records) > 0 else []
    
    # Filter user data based on TelegramID column (column B/index 1)
    user_records = [row for row in data_rows if len(row) > 1 and row[1] == telegram_id]
    
    # Get current month and year
    current_date = get_tashkent_time()
    current_month = current_date.month
    current_year = current_date.year
    
    # Filter records for current month and year
    month_records = []
    year_records = []
    
    for row in user_records:
        try:
            if len(row) > 3 and row[3]:  # ArrivalTime column
                # Parse date from "YYYY-MM-DD HH:MM" format
                arrival_time = datetime.strptime(row[3], "%Y-%m-%d %H:%M")
                if arrival_time.year == current_year:
                    year_records.append(row)
                    if arrival_time.month == current_month:
                        month_records.append(row)
        except (ValueError, TypeError):
            pass
    
    # Calculate monthly statistics
    month_days = len(month_records)
    month_hours = 0
    
    for row in month_records:
        if len(row) > 5 and row[5]:  # Total Spending Time column
            try:
                month_hours += float(row[5])
            except (ValueError, TypeError):
                pass
    
    month_avg_duration = round(month_hours / month_days, 1) if month_days > 0 else 0
    
    # Calculate yearly statistics
    year_days = len(year_records)
    year_hours = 0
    
    for row in year_records:
        if len(row) > 5 and row[5]:  # Total Spending Time column
            try:
                year_hours += float(row[5])
            except (ValueError, TypeError):
                pass
    
    year_avg_duration = round(year_hours / year_days, 1) if year_days > 0 else 0
    
    if len(user_records) > 0:
        last_entry = user_records[-1]
        
        # Format times for display (ArrivalTime and TimeGone)
        arrival_time = last_entry[3].split(" ")[1] if len(last_entry) > 3 and " " in last_entry[3] else "N/A"
        time_gone = last_entry[4].split(" ")[1] if len(last_entry) > 4 and last_entry[4] and " " in last_entry[4] else "N/A"
        duration = last_entry[5] if len(last_entry) > 5 else "0"
        
        msg = (f"📊 Statistika:\n\n"
               f"🕒 Keldi: {arrival_time}\n"
               f"🚶‍♂️ Ketdi: {time_gone}\n"
               f"⏱️ Davomiylik: {duration} soat\n\n"
               f"📅 Bu oyda:\n"
               f"📊 Kelgan kunlar: {month_days}\n"
               f"⌛️ O'rtacha davomiylik: {month_avg_duration} soat\n\n"
               f"📅 Bu yilda:\n"
               f"📊 Kelgan kunlar: {year_days}\n"
               f"⌛️ O'rtacha davomiylik: {year_avg_duration} soat")
    else:
        msg = "📊 Siz hali biror marta kelganingizni qayd etmagansiz."
    
    await message.answer(msg)


@router.message(lambda message: message.text == "⚙️ Sozlamalar")
async def show_settings(message: types.Message, state: FSMContext):
    """Display the settings menu"""
    telegram_id = str(message.from_user.id)
    full_name, phone = get_user_info(telegram_id)
    
    if not full_name:
        await message.answer("❗ Siz tizimda ro'yxatdan o'tmagansiz. Admin bilan bog'laning.")
        return
    
    # Save current user info in state
    await state.set_state(SettingsStates.main_menu)
    await state.update_data(current_name=full_name, current_phone=phone)
    
    # Display settings menu with user's current info
    settings_keyboard = create_settings_keyboard()
    await message.answer(
        f"⚙️ Sozlamalar\n\n"
        f"👤 Ism: {full_name}\n"
        f"📱 Telefon: {phone}\n\n"
        f"O'zgartirmoqchi bo'lgan sozlamani tanlang:",
        reply_markup=settings_keyboard
    )

@router.message(SettingsStates.main_menu, lambda message: message.text == "👤 Ismni o'zgartirish")
async def change_name_request(message: types.Message, state: FSMContext):
    """Handle name change request"""
    await state.set_state(SettingsStates.changing_name)
    await message.answer(
        "Yangi ismingizni kiriting:", 
        reply_markup=types.ReplyKeyboardRemove()
    )

@router.message(SettingsStates.changing_name)
async def process_name_change(message: types.Message, state: FSMContext):
    """Process the name change"""
    new_name = message.text.strip()
    telegram_id = str(message.from_user.id)
    
    if len(new_name) < 3:
        await message.answer("❗ Ism kamida 3 ta belgidan iborat bo'lishi kerak. Qaytadan urinib ko'ring:")
        return
    
    # Update name in database or sheet
    # Find the user in the "Users" worksheet and update
    users_worksheet = client.open("CRM").worksheet("Users")
    user_cells = users_worksheet.findall(telegram_id)
    
    if user_cells:
        row = user_cells[0].row
        users_worksheet.update(f'B{row}', [[new_name]])
        
        await message.answer(f"✅ Ismingiz muvaffaqiyatli o'zgartirildi: {new_name}")
        
        # Return to settings menu
        await show_settings(message, state)
    else:
        await message.answer("❗ Foydalanuvchi ma'lumotlarini yangilashda xatolik yuz berdi. Admin bilan bog'laning.")
        await state.set_state(SettingsStates.main_menu)
        await message.answer("Asosiy menyuga qaytish uchun tugmani bosing:", reply_markup=create_main_keyboard())

@router.message(SettingsStates.main_menu, lambda message: message.text == "📱 Telefon raqamni o'zgartirish")
async def change_phone_request(message: types.Message, state: FSMContext):
    """Handle phone change request"""
    await state.set_state(SettingsStates.changing_phone)
    await message.answer(
        "Yangi telefon raqamingizni kiriting (+998XXXXXXXXX formatida):", 
        reply_markup=types.ReplyKeyboardRemove()
    )

@router.message(SettingsStates.changing_phone)
async def process_phone_change(message: types.Message, state: FSMContext):
    """Process the phone change"""
    new_phone = message.text.strip()
    telegram_id = str(message.from_user.id)
    
    # Simple validation for Uzbekistan phone numbers
    import re
    if not re.match(r'^\+998\d{9}$', new_phone):
        await message.answer(
            "❗ Telefon raqami noto'g'ri formatda kiritildi. +998XXXXXXXXX formatida kiriting:"
        )
        return
    
    # Update phone in database or sheet
    users_worksheet = client.open("CRM").worksheet("Users")
    user_cells = users_worksheet.findall(telegram_id)
    
    if user_cells:
        row = user_cells[0].row
        users_worksheet.update(f'F{row}', [[new_phone]])
        
        await message.answer(f"✅ Telefon raqamingiz muvaffaqiyatli o'zgartirildi: {new_phone}")
        
        # Return to settings menu
        await show_settings(message, state)
    else:
        await message.answer("❗ Foydalanuvchi ma'lumotlarini yangilashda xatolik yuz berdi. Admin bilan bog'laning.")
        await state.set_state(SettingsStates.main_menu)
        await message.answer("Asosiy menyuga qaytish uchun tugmani bosing:", reply_markup=create_main_keyboard())

@router.message(SettingsStates.main_menu, lambda message: message.text == "🔔 Bildirishnomalar")
async def notification_settings(message: types.Message, state: FSMContext):
    """Handle notification settings"""
    await state.set_state(SettingsStates.notification_settings)
    
    # Create notification settings keyboard
    notification_keyboard = types.ReplyKeyboardMarkup(
        keyboard=[
            [types.KeyboardButton(text="🔔 Kunlik eslatmalar")],
            [types.KeyboardButton(text="⬅️ Orqaga")]
        ],
        resize_keyboard=True
    )
    
    await message.answer(
        "🔔 Bildirishnoma sozlamalari:\n\n"
        "Quyidagi sozlamalardan birini tanlang:",
        reply_markup=notification_keyboard
    )

@router.message(SettingsStates.notification_settings, lambda message: message.text == "🔔 Kunlik eslatmalar")
async def toggle_daily_reminders(message: types.Message, state: FSMContext):
    """Toggle daily reminders"""
    telegram_id = str(message.from_user.id)
    
    # Find user settings in a separate settings worksheet or add a column to users
    users_worksheet = client.open("CRM").worksheet("Users")
    user_cells = users_worksheet.findall(telegram_id)
    
    if user_cells:
        row = user_cells[0].row
        # Column 7 corresponds to the "Reminder" column
        current_setting = users_worksheet.cell(row, 7).value
        new_setting = "0" if current_setting == "1" else "1"
        # Make sure to pass a list of lists when updating
        users_worksheet.update(f'G{row}', [[new_setting]])
        
        status = "yoqildi ✅" if new_setting == "1" else "o'chirildi ❌"
        await message.answer(f"🔔 Kunlik eslatmalar {status}")
    else:
        await message.answer("❗ Sozlamalarda xatolik yuz berdi. Admin bilan bog'laning.")
    
    # Return to notification settings
    await notification_settings(message, state)



@router.message(SettingsStates.notification_settings, lambda message: message.text == "⬅️ Orqaga")
async def back_to_settings(message: types.Message, state: FSMContext):
    """Return to main settings menu"""
    await show_settings(message, state)

@router.message(SettingsStates.main_menu, lambda message: message.text == "⬅️ Asosiy menyu")
async def back_to_main_menu(message: types.Message, state: FSMContext):
    """Return to main menu"""
    await state.clear()
    await message.answer("🏠 Asosiy menyu:", reply_markup=create_main_keyboard())