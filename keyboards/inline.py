from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def get_confirm_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Tasdiqlash", callback_data="confirm_send"),
                InlineKeyboardButton(text="❌ Bekor qilish", callback_data="cancel_send")
            ]
        ]
    )
