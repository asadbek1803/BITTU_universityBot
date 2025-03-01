from typing import Dict, Any, Callable, Awaitable, List

from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery, TelegramObject
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.exceptions import TelegramAPIError


class SubscriptionMiddleware(BaseMiddleware):
    """
    Aiogram 3.x uchun majburiy obuna middleware
    """
    
    def __init__(self, channels: List[str]) -> None:
        """
        Middleware ni ishga tushirish
        
        :param channels: Kanallar ro'yxati, har bir kanal uchun string formatda link
        Masalan: ["channel1", "channel2"]
        """
        self.channels = channels
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
        
        # Obunalarni tekshirish
        not_subscribed = await self._check_subscriptions(user_id, data["bot"])
        
        if not not_subscribed:  # Agar barcha kanallarga obuna bo'lgan bo'lsa
            return await handler(event, data)
        else:
            # Kanallar uchun inline tugmalar yaratish
            markup = self._create_channels_markup(not_subscribed)
            
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
        Foydalanuvchi barcha kanallarga obuna bo'lganligini tekshirish
        
        :param user_id: Telegram foydalanuvchi ID si
        :param bot: Bot obyekti
        :return: Foydalanuvchi obuna bo'lmagan kanallar ro'yxati
        """
        not_subscribed = []
        
        for channel in self.channels:
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