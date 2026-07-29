"""
application.py
---------------
"Murojaat va Konsultatsiya" bo'limining yuragi — FSM orqali mijozdan
zayavka (ariza) yig'ish va uni Admin'ga yuborish jarayoni.

Oqim quyidagicha:
    1) F.I.Sh so'raladi
    2) Telefon raqami so'raladi (kontakt ulashish orqali)
    3) Qiziqayotgan xizmat turi so'raladi
    4) Qo'shimcha izoh/savol so'raladi
    5) Yig'ilgan ma'lumotlar tasdiqlash uchun ko'rsatiladi
    6) Tasdiqlansa — Admin'ga chiroyli formatda yuboriladi
"""

import re

from aiogram import Router, F, Bot
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery

from config import config
from states.application_states import ApplicationForm
from keyboards.reply import (
    main_menu_keyboard,
    phone_share_keyboard,
    service_type_keyboard,
    confirm_keyboard,
    BTN_CONSULTATION,
    BTN_SERVICE_CALLCENTER,
    BTN_SERVICE_BOT,
    BTN_SERVICE_BOTH,
    BTN_CONFIRM,
    BTN_RESTART,
    BTN_CANCEL,
)
from keyboards.inline import CB_START_APPLICATION

router = Router(name="application")


# Telefon raqamini yengil tekshirish uchun oddiy regex
# (+998901234567, 998901234567, 90 123 45 67 kabi variantlarni qabul qiladi)
PHONE_REGEX = re.compile(r"^\+?\d[\d\s\-]{6,14}\d$")


# ==========================================================
# ZAYAVKA JARAYONINI BOSHLASH (2 xil kirish nuqtasi)
# ==========================================================

async def _start_application(message_or_callback, state: FSMContext):
    """
    Zayavka formasini boshlash uchun umumiy funksiya.
    Reply tugma orqali ham, Inline tugma orqali ham shu funksiya chaqiriladi.
    """
    await state.clear()
    await state.set_state(ApplicationForm.full_name)

    text = (
        "📝 <b>Ajoyib! Ariza qoldirish jarayonini boshlaymiz.</b>\n\n"
        "Jarayon atigi 4 ta qisqa qadamdan iborat va 1 daqiqadan "
        "kam vaqt oladi.\n\n"
        "1️⃣ Avvalo, <b>F.I.Sh</b>ingizni to'liq kiriting:"
    )

    if isinstance(message_or_callback, CallbackQuery):
        # Inline tugma bosilganda - avvalgi xabarni tahrirlab bo'lmaydi,
        # chunki reply keyboard kerak, shu sababli yangi xabar yuboramiz
        await message_or_callback.message.answer(text, reply_markup=_cancel_only_kb())
        await message_or_callback.answer()  # loading holatini olib tashlash
    else:
        await message_or_callback.answer(text, reply_markup=_cancel_only_kb())


def _cancel_only_kb():
    """F.I.Sh va Izoh bosqichlarida faqat 'Bekor qilish' tugmasi chiqishi uchun."""
    from aiogram.utils.keyboard import ReplyKeyboardBuilder

    builder = ReplyKeyboardBuilder()
    builder.button(text=BTN_CANCEL)
    return builder.as_markup(resize_keyboard=True)


@router.message(F.text == BTN_CONSULTATION)
async def start_application_from_menu(message: Message, state: FSMContext):
    """Asosiy menyudagi '📞 Murojaat va Konsultatsiya' tugmasi orqali kirish."""
    await _start_application(message, state)


@router.callback_query(F.data == CB_START_APPLICATION)
async def start_application_from_inline(callback: CallbackQuery, state: FSMContext):
    """Ma'lumot bo'limlari ostidagi '✍️ Ariza qoldirish' inline tugmasi orqali kirish."""
    await _start_application(callback, state)


# ==========================================================
# 1-QADAM: F.I.Sh
# ==========================================================

@router.message(ApplicationForm.full_name, F.text.len() >= 3)
async def process_full_name(message: Message, state: FSMContext):
    """F.I.Sh qabul qilinadi va keyingi qadamga o'tiladi."""
    await state.update_data(full_name=message.text.strip())
    await state.set_state(ApplicationForm.phone_number)

    await message.answer(
        "2️⃣ Rahmat! Endi <b>telefon raqamingizni</b> quyidagi tugma orqali "
        "ulashing (yoki qo'lda kiriting):",
        reply_markup=phone_share_keyboard(),
    )


@router.message(ApplicationForm.full_name)
async def process_full_name_invalid(message: Message):
    """Agar F.I.Sh juda qisqa yoki bo'sh kiritilsa."""
    await message.answer(
        "⚠️ Iltimos, F.I.Sh to'liq va kamida 3 ta harfdan iborat bo'lsin. "
        "Qaytadan kiriting:"
    )


# ==========================================================
# 2-QADAM: TELEFON RAQAMI
# ==========================================================

@router.message(ApplicationForm.phone_number, F.contact)
async def process_phone_contact(message: Message, state: FSMContext):
    """Foydalanuvchi kontaktni tugma orqali ulashganda."""
    await state.update_data(phone_number=message.contact.phone_number)
    await _ask_service_type(message, state)


@router.message(ApplicationForm.phone_number, F.text)
async def process_phone_text(message: Message, state: FSMContext):
    """Foydalanuvchi telefon raqamini qo'lda yozib yuborganda."""
    phone_candidate = message.text.strip()

    if not PHONE_REGEX.match(phone_candidate):
        await message.answer(
            "⚠️ Telefon raqami noto'g'ri formatda. Masalan: "
            "<code>+998901234567</code>\n\n"
            "Yoki pastdagi 📱 tugma orqali raqamingizni ulashing:"
        )
        return

    await state.update_data(phone_number=phone_candidate)
    await _ask_service_type(message, state)


async def _ask_service_type(message: Message, state: FSMContext):
    """3-qadamga o'tish: qiziqayotgan xizmat turini so'rash."""
    await state.set_state(ApplicationForm.service_type)
    await message.answer(
        "3️⃣ Qaysi xizmat turiga qiziqmoqdasiz?",
        reply_markup=service_type_keyboard(),
    )


# ==========================================================
# 3-QADAM: XIZMAT TURI
# ==========================================================

@router.message(
    ApplicationForm.service_type,
    F.text.in_({BTN_SERVICE_CALLCENTER, BTN_SERVICE_BOT, BTN_SERVICE_BOTH}),
)
async def process_service_type(message: Message, state: FSMContext):
    """Xizmat turi ro'yxatdagi variantlardan tanlanganda."""
    await state.update_data(service_type=message.text)
    await state.set_state(ApplicationForm.comment)

    await message.answer(
        "4️⃣ Va nihoyat, <b>qo'shimcha izoh yoki savolingiz</b> bo'lsa yozing.\n"
        "Agar bo'lmasa, shunchaki \"-\" belgisini yuboring:",
        reply_markup=_cancel_only_kb(),
    )


@router.message(ApplicationForm.service_type)
async def process_service_type_invalid(message: Message):
    """Foydalanuvchi ro'yxatdan tashqari matn yozsa."""
    await message.answer(
        "⚠️ Iltimos, quyidagi tugmalardan birini tanlang 👇",
        reply_markup=service_type_keyboard(),
    )


# ==========================================================
# 4-QADAM: IZOH
# ==========================================================

@router.message(ApplicationForm.comment, F.text)
async def process_comment(message: Message, state: FSMContext):
    """Izoh qabul qilinadi va yakuniy tasdiqlash bosqichiga o'tiladi."""
    await state.update_data(comment=message.text.strip())
    await state.set_state(ApplicationForm.confirm)

    data = await state.get_data()
    summary = _build_summary_text(data)

    await message.answer(
        f"✅ <b>Ma'lumotlaringizni tekshiring:</b>\n\n{summary}\n\n"
        "Barchasi to'g'ri bo'lsa, <b>Tasdiqlash</b> tugmasini bosing.",
        reply_markup=confirm_keyboard(),
    )


def _build_summary_text(data: dict) -> str:
    """Yig'ilgan ma'lumotlardan chiroyli xulosaviy matn tuzish."""
    return (
        f"👤 <b>F.I.Sh:</b> {data.get('full_name')}\n"
        f"📱 <b>Telefon:</b> {data.get('phone_number')}\n"
        f"🛠 <b>Xizmat turi:</b> {data.get('service_type')}\n"
        f"💬 <b>Izoh:</b> {data.get('comment')}"
    )


# ==========================================================
# YAKUN: TASDIQLASH VA ADMINGA YUBORISH
# ==========================================================

@router.message(ApplicationForm.confirm, F.text == BTN_CONFIRM)
async def confirm_and_send(message: Message, state: FSMContext, bot: Bot):
    """Foydalanuvchi ma'lumotlarni tasdiqlaganda - Admin'ga yuboriladi."""
    data = await state.get_data()
    user = message.from_user

    admin_text = (
        "🆕 <b>Yangi zayavka — AloqaBor</b>\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        f"👤 <b>F.I.Sh:</b> {data.get('full_name')}\n"
        f"📱 <b>Telefon:</b> {data.get('phone_number')}\n"
        f"🛠 <b>Xizmat turi:</b> {data.get('service_type')}\n"
        f"💬 <b>Izoh:</b> {data.get('comment')}\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        f"🔗 <b>Telegram:</b> @{user.username if user.username else 'mavjud emas'}\n"
        f"🆔 <b>User ID:</b> <code>{user.id}</code>"
    )

    # Adminga yuborishga harakat qilamiz. Agar admin botni bloklagan bo'lsa
    # yoki ID noto'g'ri kiritilgan bo'lsa - dastur yiqilib qolmasligi kerak.
    try:
        await bot.send_message(chat_id=config.admin_id, text=admin_text)
    except Exception as error:  # noqa: BLE001 - adminga yetkazishda har qanday xatoni ushlaymiz
        # Bu yerda logging kutubxonasi orqali xatoni loglash tavsiya etiladi
        print(f"[XATOLIK] Adminga zayavka yuborilmadi: {error}")

    await state.clear()
    await message.answer(
        "🎉 <b>Rahmat! Arizangiz muvaffaqiyatli qabul qilindi.</b>\n\n"
        "Tez orada AloqaBor mutaxassisi siz bilan bog'lanadi. "
        "Ishonchli hamkorligimizga umid qilamiz! 🤝",
        reply_markup=main_menu_keyboard(),
    )


@router.message(ApplicationForm.confirm, F.text == BTN_RESTART)
async def restart_application(message: Message, state: FSMContext):
    """Foydalanuvchi ma'lumotlarni qaytadan kiritmoqchi bo'lsa."""
    await _start_application(message, state)


@router.message(ApplicationForm.confirm)
async def process_confirm_invalid(message: Message):
    """Tasdiqlash bosqichida noto'g'ri matn kiritilsa."""
    await message.answer(
        "⚠️ Iltimos, quyidagi tugmalardan birini tanlang 👇",
        reply_markup=confirm_keyboard(),
    )
