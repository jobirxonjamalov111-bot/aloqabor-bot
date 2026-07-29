from aiogram import Router, F
from aiogram.types import Message

router = Router()

@router.message(F.text == "ℹ️ Ma'lumot")
async def info_handler(message: Message):
    await message.answer(
        "<b>Aloqa Boti</b>\n\n"
        "Ushbu bot orqali siz o'z murojaat va arizalaringizni yuborishingiz mumkin.\n"
        "Barcha xabarlar ma'muriyatga yetkaziladi.",
        parse_mode="HTML"
    )
