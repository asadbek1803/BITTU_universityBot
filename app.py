import asyncio
import gspread
from google.oauth2.service_account import Credentials
from environs import Env
from aiogram import Bot, Dispatcher
from aiogram.client.session.middlewares.request_logging import logger
from aiogram.enums import ChatType
from components.functions import get_channels
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

def setup_handlers(dispatcher: Dispatcher) -> None:
    """HANDLERS"""
    from handlers import setup_routers

    dispatcher.include_router(setup_routers())


def setup_middlewares(dispatcher: Dispatcher, bot: Bot) -> None:
    """MIDDLEWARE"""
    from middlewares.throttling import ThrottlingMiddleware
    from middlewares.SubscriptionMiddleware import SubscriptionMiddleware

    # Spamdan himoya qilish uchun klassik ichki o'rta dastur. So'rovlar orasidagi asosiy vaqtlar 0,5 soniya
    dispatcher.message.middleware(ThrottlingMiddleware(slow_mode_delay=0.5))
    # dispatcher.message.middleware(SubscriptionMiddleware(get_channels()))
    # dispatcher.callback_query.middleware(SubscriptionMiddleware(get_channels()))

def setup_filters(dispatcher: Dispatcher) -> None:
    """FILTERS"""
    from filters import ChatTypeFilter

    # Chat turini aniqlash uchun klassik umumiy filtr
    # Filtrni handlers/users/__init__ -dagi har bir routerga alohida o'rnatish mumkin
    dispatcher.message.filter(ChatTypeFilter(chat_types=[ChatType.PRIVATE]))


async def setup_aiogram(dispatcher: Dispatcher, bot: Bot) -> None:
    logger.info("Configuring aiogram")
    setup_handlers(dispatcher=dispatcher)
    setup_middlewares(dispatcher=dispatcher, bot=bot)
    setup_filters(dispatcher=dispatcher)
    logger.info("Configured aiogram")


async def database_connected():
    try:
        # Open the existing spreadsheet by ID
        spreadsheet_id = "1n0SL-MYQXhuk5AJG5U63eAHmNCFnuoT1917n_YYTwH4"
        spreadsheet = client.open_by_key(spreadsheet_id)

        # Jadval havolasini olish (Get spreadsheet URL)
        spreadsheet_url = f"https://docs.google.com/spreadsheets/d/{spreadsheet.id}"
        print(f"Jadval havolasi: {spreadsheet_url}")

        # Users, Students, Groups, Attends, Lesson Weekday Times jadvallarini yaratish
        # (Create worksheets if they don't exist)
        sheets = ["Users", "Students", "Groups", "Attends", "Lesson Weekday Times", "Ideas", "Channels"]
        existing_worksheets = [worksheet.title for worksheet in spreadsheet.worksheets()]
        
        for sheet_name in sheets:
            if sheet_name not in existing_worksheets:
                try:
                    spreadsheet.add_worksheet(title=sheet_name, rows="100", cols="20")
                    print(f"'{sheet_name}' jadvali yaratildi.")
                except gspread.exceptions.APIError as e:
                    print(f"'{sheet_name}' jadvalini yaratishda xatolik: {e}")
            else:
                print(f"'{sheet_name}' jadvali allaqachon mavjud.")

        print("Ma'lumotlar bazasi muvaffaqiyatli ochildi.")
    except Exception as e:
        print(f"Xatolik yuz berdi: {e}")



async def aiogram_on_startup_polling(dispatcher: Dispatcher, bot: Bot) -> None:
    from utils.set_bot_commands import set_default_commands
    from utils.notify_admins import on_startup_notify

    logger.info("Database connected")
    await database_connected()

    logger.info("Starting polling")
    await bot.delete_webhook(drop_pending_updates=True)
    await setup_aiogram(bot=bot, dispatcher=dispatcher)
    await on_startup_notify(bot=bot)
    await set_default_commands(bot=bot)


async def aiogram_on_shutdown_polling(dispatcher: Dispatcher, bot: Bot):
    logger.info("Stopping polling")
    await bot.session.close()
    await dispatcher.storage.close()


def main():
    """CONFIG"""
    from data.config import BOT_TOKEN
    from aiogram.enums import ParseMode
    from aiogram.fsm.storage.memory import MemoryStorage
    from aiogram.client.default import DefaultBotProperties

    bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    storage = MemoryStorage()
    dispatcher = Dispatcher(storage=storage)

    dispatcher.startup.register(aiogram_on_startup_polling)
    dispatcher.shutdown.register(aiogram_on_shutdown_polling)
    asyncio.run(dispatcher.start_polling(bot, close_bot_session=True))
    # allowed_updates=['message', 'chat_member']


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("Bot stopped!")
