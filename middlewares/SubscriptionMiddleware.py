from typing import Dict, Any, Callable, Awaitable, List

from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery, TelegramObject
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.exceptions import TelegramAPIError


class SubscriptionMiddleware(BaseMiddleware):
    """
    Aiogram 3.x uchun majburiy obuna middleware.
    Ochiq va yopiq kanallar uchun mo'ljallangan.
    Maxfiy havolalar (https://t.me/+...) bilan yaratilgan guruh/kanallar uchun ham ishlaydi.
    """
    
    def __init__(self, channels: List[str]) -> None:
        """
        Middleware ni ishga tushirish
        
        :param channels: Kanallar ro'yxati, har bir kanal uchun string formatda link
        Masalan: ["channel1", "channel2", "https://t.me/+oyS8L2a4eblhZGRi"]
        """
        self.channels = channels
        # Maxfiy havola va oddiy kanallar/guruhlar uchun alohida ro'yxatlar
        self.private_links = [c for c in channels if c.startswith("https://t.me/+")]
        self.regular_channels = [c for c in channels if not c.startswith("https://t.me/+")]
        super().__init__()
    
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:
        # Start buyrug'i uchun tekshirilmaydi
        if isinstance(event, Message) and event.text and event.text.startswith('/start'):
            return await handler(event, data)
        
        # Foydalanuvchi ID sini olish
        if isinstance(event, Message):
            user_id = event.from_user.id
        elif isinstance(event, CallbackQuery):
            user_id = event.from_user.id
        else:
            # Agar event Message yoki CallbackQuery bo'lmasa, handler ni chaqirish
            return await handler(event, data)
        
        # Oddiy kanal/guruhlar uchun obunalarni tekshirish
        not_subscribed_channels = await self._check_subscriptions(user_id, data["bot"])
        
        # Barcha kanallar (oddiy va maxfiy) ro'yxatini yaratish
        all_not_subscribed = not_subscribed_channels + self.private_links
        
        if not all_not_subscribed:  # Agar barcha kanallarga obuna bo'lgan bo'lsa
            return await handler(event, data)
        else:
            # Kanallar uchun inline tugmalar yaratish
            markup = self._create_channels_markup(all_not_subscribed)
            
            # Obuna haqida xabar yuborish
            if isinstance(event, Message):
                await event.answer(
                    "⚠️ Botdan foydalanish uchun quyidagi kanallarga obuna bo'ling:",
                    reply_markup=markup
                )
            elif isinstance(event, CallbackQuery):
                await event.message.edit_text(
                    "⚠️ Botdan foydalanish uchun quyidagi kanallarga obuna bo'ling:",
                    reply_markup=markup
                )
                await event.answer()
            
            # Handler ni chaqirmaslik
            return None
    
    async def _check_subscriptions(self, user_id: int, bot) -> List[str]:
        """
        Foydalanuvchi barcha oddiy kanallarga obuna bo'lganligini tekshirish.
        
        :param user_id: Telegram foydalanuvchi ID si
        :param bot: Bot obyekti
        :return: Foydalanuvchi obuna bo'lmagan kanallar ro'yxati
        """
        not_subscribed = []
        
        for channel in self.regular_channels:
            try:
                # Kanalning username qismini olish
                channel_username = channel
                if '@' in channel:
                    channel_username = channel.replace('@', '')
                
                # Bot member status ni tekshirishi uchun to'liq kanal ID
                chat_id = f"@{channel_username}" if not channel_username.startswith('@') else channel_username
                
                member = await bot.get_chat_member(chat_id, user_id)
                # Agar foydalanuvchi kanalda bo'lmasa yoki chiqib ketgan bo'lsa
                if member.status in ['left', 'kicked', 'restricted']:
                    not_subscribed.append(channel)
                # Agar foydalanuvchi admin tomonidan tasdiqlanishi kutilayotgan bo'lsa (yopiq kanal/guruh)
                elif member.status == 'pending':
                    not_subscribed.append(channel)
            except TelegramAPIError:
                # Agar bot a'zolikni tekshira olmasa, obuna bo'lmagan deb hisoblanadi
                not_subscribed.append(channel)
        
        return not_subscribed
    
    def _create_channels_markup(self, channels: List[str]) -> InlineKeyboardMarkup:
        """
        Kanallar uchun inline tugmalar yaratish
        
        :param channels: Kanallar ro'yxati
        :return: InlineKeyboardMarkup
        """
        markup_buttons = []
        counter = 1
        for channel in channels:
            # Maxfiy havola tekshirish
            if channel.startswith("https://t.me/+"):
                button = InlineKeyboardButton(
                    text=f"📢 Maxfiy guruhga a'zo bo'lish {counter}",
                    url=channel
                )
                markup_buttons.append([button])
            else:
                # Kanalning username qismini olish
                channel_username = channel
                if '@' in channel:
                    channel_username = channel.replace('@', '')
                
                button = InlineKeyboardButton(
                    text=f"📢 A'zo bo'lish {counter}",
                    url=f"https://t.me/{channel_username}"
                )
                markup_buttons.append([button])
            counter += 1
        
        # Tekshirish tugmasini qo'shish
        markup_buttons.append([
            InlineKeyboardButton(
                text="✅ Tekshirish",
                callback_data="check_subscription"
            )
        ])
        
        return InlineKeyboardMarkup(inline_keyboard=markup_buttons)
    
    # Maxfiy havolalar uchun obuna tekshirish metodi
    # Bu metod "check_subscription" callback_data orqali chaqiriladi
    async def check_private_subscription(self, user_id: int, bot):
        """
        "Tekshirish" tugmasi bosilganda chaqiriladigan metod.
        Ushbu metodda maxfiy havolalar uchun yangi tekshirish logikasini qo'shish mumkin.
        
        :param user_id: Foydalanuvchi ID si
        :param bot: Bot obyekti
        :return: Foydalanuvchi maxfiy kanallarga obuna bo'lgan yoki yo'qligi
        """
        # Bu metodni o'zingizga moslashtiring
        # Hozircha bu holda maxfiy kanallarga obuna tekshirib bo'lmaydi
        # Foydalanuvchi tekshirish tugmasini bosishi bilan maxfiy kanallar ro'yxatdan o'chiriladi
        
        # Bu yerda odatda foydalanuvchi maxfiy kanallarga obuna bo'lgandan so'ng,
        # Tekshirish tugmasini bosganda, endi maxfiy kanallarni ro'yxatdan chiqarib tashlash mantiqini qo'shish kerak
        self.private_links = []
        return True
    
    async def request_access(self, user_id: int, bot, channel: str) -> bool:
        """
        Yopiq kanal/guruhga qo'shilish uchun so'rov yuborish funksiyasi
        
        :param user_id: Foydalanuvchi ID si
        :param bot: Bot obyekti
        :param channel: Kanal yoki guruh username/ID si
        :return: So'rov muvaffaqiyatli yuborilgan bo'lsa True, aks holda False
        """
        try:
            # Maxfiy havola tekshirish
            if channel.startswith("https://t.me/+"):
                # Maxfiy havolalar uchun so'rov yuborish imkoni yo'q
                return False
                
            # Kanalning username qismini olish
            channel_username = channel
            if '@' in channel:
                channel_username = channel.replace('@', '')
            
            # Bot member status ni tekshirishi uchun to'liq kanal ID
            chat_id = f"@{channel_username}" if not channel_username.startswith('@') else channel_username
            
            # Foydalanuvchining kanal/guruhga qo'shilganligini tekshirish
            member = await bot.get_chat_member(chat_id, user_id)
            
            # Agar foydalanuvchi allaqachon so'rov yuborgan bo'lsa yoki a'zo bo'lsa
            if member.status in ['member', 'administrator', 'creator', 'pending']:
                return True
            
            # Yopiq kanal/guruhga qo'shilish uchun so'rov yuborish
            # Bu funksiya faqat bot kanal/guruh administratori bo'lsagina ishlaydi
            invite_link = await bot.create_chat_invite_link(chat_id)
            return True
        except TelegramAPIError as e:
            # Xatolik yuz bergan bo'lsa False qaytarish
            return False
    
    async def is_closed_channel(self, bot, channel: str) -> bool:
        """
        Kanal yoki guruh yopiq ekanligini tekshirish
        
        :param bot: Bot obyekti
        :param channel: Kanal yoki guruh username/ID si
        :return: Yopiq bo'lsa True, aks holda False
        """
        # Maxfiy havola tekshirish
        if channel.startswith("https://t.me/+"):
            # Maxfiy havolalar har doim yopiq hisoblanadi
            return True
            
        try:
            # Kanalning username qismini olish
            channel_username = channel
            if '@' in channel:
                channel_username = channel.replace('@', '')
            
            # Bot member status ni tekshirishi uchun to'liq kanal ID
            chat_id = f"@{channel_username}" if not channel_username.startswith('@') else channel_username
            
            # Kanal/guruh haqida ma'lumot olish
            chat_info = await bot.get_chat(chat_id)
            
            # Kanal/guruh yopiq ekanligini tekshirish
            if hasattr(chat_info, 'join_by_request') and chat_info.join_by_request:
                return True
            if hasattr(chat_info, 'is_restricted') and chat_info.is_restricted:
                return True
                
            return False
        except TelegramAPIError:
            # Xatolik yuz bergan bo'lsa, yopiq deb hisoblaymiz
            return True