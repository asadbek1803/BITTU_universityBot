

import gspread
from google.oauth2.service_account import Credentials
from environs import Env

env = Env()
env.read_env()





SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

GOOGLE_CREDENTIALS = {
    "type": env.str("TYPE"),
    "project_id": env.str("PROJECT_ID"),
    "private_key_id": env.str("PRIVATE_KEY_ID"),
    "private_key": env.str("PRIVATE_KEY"),
    "client_email": env.str("CLIENT_EMAIL"),
    "client_id": env.str("CLIENT_ID"),
    "auth_uri": env.str("AUTH_URI"),
    "token_uri": env.str("TOKEN_URI"),
    "auth_provider_x509_cert_url": env.str("AUTH_PROVIDER_X509_CERT_URL"),
    "client_x509_cert_url": env.str("CLIENT_X509_CERT_URL"),
    "universe_domain": env.str("UNIVERSE_DOMAIN")
}

creds = Credentials.from_service_account_info(GOOGLE_CREDENTIALS, scopes=SCOPES)
client = gspread.authorize(creds)
SPREADSHEET_NAME = "CRM"
worksheet = client.open(SPREADSHEET_NAME).worksheet("Users")


def get_channels():
    """
    Google Sheets CRM faylidan kanallar ro'yxatini oladi.
    Birinchi qator (sarlavha qator) tashqari barcha qatorlarni oladi.
    
    Returns:
        list: Kanallar ro'yxati
    """
    channels = client.open("CRM").worksheet("Channels")
    channels_data = channels.get_all_values()
    lists = []
    
    # Birinchi qator (indeks 0) ni tashlab, qolgan barcha qatorlarni olish
    for row in channels_data[1:]:  # 1-indeksdan boshlab oladi
        if row and row[0]:  # Bo'sh qatorlarni tekshirish
            lists.append(row[0])
    
    return lists


def check_user_exists(telegram_id):
    """Foydalanuvchi mavjudligini tekshirish"""
    users = worksheet.get_all_values()
    for row in users:
        if str(telegram_id) in row:
            return True
    return False

def check_user_status(telegram_id):
    """Foydalanuvchi mavjudligini va admin ekanligini tekshirish"""
    users = worksheet.get_all_values()
    
    for row in users:
        if str(telegram_id) == row[0]:  # Foydalanuvchi ID si birinchi ustunda
            is_admin = row[4].strip() == "True"  # Admin bo‘lsa "True" saqlanadi
            return is_admin  # True yoki False qaytaradi

    return None  # Foydalanuvchi topilmasa

def get_user_info(telegram_id):
    """Users worksheetidan foydalanuvchi ma'lumotlarini olish"""
    users_data = worksheet.get_all_values()
    
    for row in users_data:
        if row and row[0] == str(telegram_id):  # TelegramID bo'yicha qidirish
            full_name = row[1]  # FullName ustuni
            phone = row[5] if len(row) > 2 else "Noma'lum"  # Telefon raqami (agar mavjud bo'lsa)
            return full_name, phone
    return None, None


def get_user_student(telegram_id):
    """O'quvchi yoki yo'qligini tekshiramiz"""
    users_data = worksheet.get_all_values()

    for row in users_data:
        if row and row[0] == str(telegram_id):  # TelegramID bo'yicha qidirish
            if len(row) > 7 and row[7].strip():  # IsStudent ustuni mavjud va bo'sh emas
                return row[7].strip().lower() == "ha"
            return False
    return False

