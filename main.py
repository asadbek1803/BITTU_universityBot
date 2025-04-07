from aiogram import Bot,Dispatcher
from aiogram.types import Message,URLInputFile
from aiogram.filters import Command,CommandStart
import asyncio
import requests
api='https://full-media-downloader-pro-zfkrvjl323.onrender.com/instagramdownloader'
api_token='QXowf53aI7b9KvLQuBqFsBtdhidooix12QRRbkwsZLuqyYnFVqQ80qWW7bMT8UULEL5lWzcLGCaIDbboGNjrOSfweAhqF6Y8LKmp'
bot=Bot(token='7641176490:AAHd7zLUiJj7MSPRdGscpdvClby90BlAYQg')
dp=Dispatcher()
@dp.message(CommandStart())
async def start(msg:Message):
    await msg.answer("""👋 Salom!
Men sizga musiqa topishga yordam beraman 🎶 menga quyidagilardan birini yuboring:

🎵 Qo'shiq yoki ijrochi nomi
🔤 Qo'shiq matni
🎙 Musiqa bilan ovozli xabar
📹 Musiqa bilan video
🔊 Audioyozuv
🎥 Musiqa bilan video xabar
🔗 Instagram, Tik-Tok, YouTube va boshqa saytlarga video havola Admin bot:
@Allah_I_believe_in_You
🕺 Rohatlaning""")

@dp.message()
async def solve(msg:Message):
    url=f"{api}?url={msg.text}&token={api_token}"
    jvb=requests.get(url).json()
    await msg.answer_video(video=jvb['url'])
async def main():
    await dp.start_polling(bot)
if __name__ == '__main__':
    asyncio.run(main())
