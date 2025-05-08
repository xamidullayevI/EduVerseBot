from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo, KeyboardButton, ReplyKeyboardMarkup
from telegram.ext import ContextTypes
import aiohttp
import os

ADMINS = [int(x) for x in os.getenv("ADMINS", "").split(",") if x.strip()]
API_URL = os.getenv("API_URL", "http://localhost:5000")
WEBAPP_URL = os.getenv("WEBAPP_URL", "http://localhost:5000")

def is_admin(user_id):
    return user_id in ADMINS

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if is_admin(update.message.from_user.id):
        await update.message.reply_text(
            "Admin panelga xush kelibsiz! /new bilan yangi mavzu boshlang.\n\n"
            f"Web App: {WEBAPP_URL}"
        )
    else:
        # Contact so'rash uchun tugma yaratamiz
        keyboard = [[KeyboardButton("📱 Contact yuborish", request_contact=True)]]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        
        await update.message.reply_text(
            "EduVerse botiga xush kelibsiz! Davom etish uchun contact ma'lumotlaringizni yuboring.",
            reply_markup=reply_markup
        )

async def new_topic(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.message.from_user.id):
        await update.message.reply_text("Sizda bu buyruqni ishlatish huquqi yo'q!")
        return
    
    # Agar allaqachon mavzu yaratish jarayoni bor bo'lsa
    if 'topic' in context.user_data and context.user_data['topic']:
        await update.message.reply_text(
            "Sizda allaqachon mavzu yaratish jarayoni bor. "
            "Agar yangi mavzu boshlashni xohlasangiz, /confirm yoki /skip buyrug'ini bosing."
        )
        return
        
    context.user_data['topic'] = {}
    await update.message.reply_text("Mavzu nomini yuboring:")

async def text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.message.from_user.id):
        await update.message.reply_text("Sizda bu buyruqni ishlatish huquqi yo'q!")
        return
    if 'topic' not in context.user_data:
        await update.message.reply_text("Iltimos, /new bilan boshlang.")
        return
    topic = context.user_data['topic']
    if 'title' not in topic:
        topic['title'] = update.message.text
        await update.message.reply_text("Mavzu strukturasi (matn)ni yuboring:")
    elif 'structure' not in topic:
        topic['structure'] = update.message.text
        await update.message.reply_text("Misollarni yuboring:")
    elif 'examples' not in topic:
        topic['examples'] = update.message.text
        await update.message.reply_text("Endi rasm yuboring (ixtiyoriy, o'tkazib yuborish uchun /skip):")
    else:
        await update.message.reply_text("Rasm yoki video kutilyapti yoki /confirm bosing.")

async def photo_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.message.from_user.id):
        await update.message.reply_text("Sizda bu buyruqni ishlatish huquqi yo'q!")
        return
    if 'topic' not in context.user_data:
        await update.message.reply_text("Iltimos, /new bilan boshlang.")
        return
    photo = update.message.photo[-1]
    file = await photo.get_file()
    context.user_data['topic']['image_url'] = file.file_path
    await update.message.reply_text("Endi video yuboring (ixtiyoriy, o'tkazib yuborish uchun /skip):")

async def video_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.message.from_user.id):
        await update.message.reply_text("Sizda bu buyruqni ishlatish huquqi yo'q!")
        return
    if 'topic' not in context.user_data:
        await update.message.reply_text("Iltimos, /new bilan boshlang.")
        return
    video = update.message.video
    file = await video.get_file()
    context.user_data['topic']['video_url'] = file.file_path
    await update.message.reply_text("Barcha ma'lumotlar qabul qilindi. /confirm bosing.")

async def skip(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.message.from_user.id):
        await update.message.reply_text("Sizda bu buyruqni ishlatish huquqi yo'q!")
        return
    if 'topic' not in context.user_data:
        await update.message.reply_text("Iltimos, /new bilan boshlang.")
        return
    
    topic = context.user_data['topic']
    if 'image_url' not in topic:
        topic['image_url'] = None
        await update.message.reply_text("Rasm o'tkazib yuborildi. Video yuboring (ixtiyoriy, o'tkazib yuborish uchun /skip):")
    elif 'video_url' not in topic:
        topic['video_url'] = None
        await update.message.reply_text("Video o'tkazib yuborildi. /confirm bosing.")
    else:
        await update.message.reply_text("Barcha bosqichlar tugadi. /confirm bosing.")
        # Mavzu ma'lumotlarini tozalaymiz
        context.user_data['topic'] = {}

async def confirm_topic(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.message.from_user.id):
        await update.message.reply_text("Sizda bu buyruqni ishlatish huquqi yo'q!")
        return
    topic = context.user_data.get('topic')
    if not topic or 'title' not in topic or 'structure' not in topic or 'examples' not in topic:
        await update.message.reply_text("Ma'lumotlar to'liq emas.")
        return
    async with aiohttp.ClientSession() as session:
        async with session.post(f"{API_URL}/api/topics", json=topic) as resp:
            if resp.status == 200:
                await update.message.reply_text("Mavzu saqlandi!")
                # Mavzu ma'lumotlarini tozalaymiz
                context.user_data['topic'] = {}
            else:
                await update.message.reply_text("Xatolik yuz berdi.")

async def contact_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Contact handler admin uchun emas, hamma uchun ishlaydi
    contact = update.message.contact
    data = {
        'user_id': update.effective_user.id,  # Telegram user ID
        'first_name': contact.first_name,
        'last_name': contact.last_name,
        'phone_number': contact.phone_number
    }
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(f"{API_URL}/api/contacts", json=data) as resp:
                if resp.status == 200:
                    # Contact tugmasini olib tashlaymiz va Web App tugmasini qo'shamiz
                    keyboard = [[KeyboardButton("🌐 Web App", web_app=WebAppInfo(url=WEBAPP_URL))]]
                    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=False)
                    
                    await update.message.reply_text(
                        "Contact ma'lumotlari saqlandi! Mavzularni ko'rish uchun Web App tugmasini bosing:",
                        reply_markup=reply_markup
                    )
                else:
                    error_text = await resp.text()
                    print(f"Contact saqlashda xatolik: {error_text}")
                    await update.message.reply_text(
                        "Contact saqlashda xatolik yuz berdi. Iltimos, qaytadan urinib ko'ring.\n"
                        "Agar muammo davom etsa, administrator bilan bog'laning."
                    )
    except Exception as e:
        print(f"Contact saqlashda xatolik: {e}")
        await update.message.reply_text(
            "Server bilan bog'lanishda xatolik yuz berdi. Iltimos, keyinroq qaytadan urinib ko'ring.\n"
            "Agar muammo davom etsa, administrator bilan bog'laning."
        ) 