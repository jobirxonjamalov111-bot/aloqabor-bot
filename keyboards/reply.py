from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

main_menu = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="📝 Murojaat yuborish")],
        [KeyboardButton(text="ℹ️ Ma'lumot")]
    ],
    resize_keyboard=True
)
