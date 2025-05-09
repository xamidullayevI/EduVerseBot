from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo, KeyboardButton, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import ContextTypes
import aiohttp
import os
import logging
from typing import Optional, Dict, Any
import re

# Log yozish sozlamalari
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    filename='bot.log'
)
logger = logging.getLogger(__name__)

# Sozlamalar
ADMINS = [int(x) for x in os.getenv("ADMINS", "").split(",") if x.strip()]
API_URL = os.getenv("API_URL", "http://localhost:5000")
WEBAPP_URL = os.getenv("WEBAPP_URL", "http://localhost:5000")

# Rasm formatlari
ALLOWED_IMAGE_TYPES = ['image/jpeg', 'image/png', 'image/gif']
MAX_IMAGE_SIZE = 5 * 1024 * 1024  # 5MB

# Video formatlari
ALLOWED_VIDEO_TYPES = ['video/mp4', 'video/quicktime']
MAX_VIDEO_SIZE = 50 * 1024 * 1024  # 50MB

def is_admin(user_id: int) -> bool:
    """Admin tekshiruv"""
    return user_id in ADMINS

def validate_text(text: str, max_length: int = 1000) -> bool:
    """Matn tekshiruv"""
    return bool(text and len(text) <= max_length)

def validate_url(url: str) -> bool:
    """URL tekshiruv"""
    url_pattern = re.compile(
        r'^https?://'  # http:// yoki https://
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain
        r'localhost|'  # localhost
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # IP
        r'(?::\d+)?'  # port
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)
    return bool(url_pattern.match(url))

def validate_youtube_url(url: str) -> bool:
    """YouTube havolasini tekshirish"""
    youtube_pattern = re.compile(
        r'(https?://)?(www\.)?'
        r'(youtube|youtu|youtube-nocookie)\.(com|be)/'
        r'(watch\?v=|embed/|v/|.+\?v=)?([^&=%\?]{11})'
    )
    return bool(youtube_pattern.match(url))

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start buyrug'i"""
    try:
        user_id = update.message.from_user.id
        if is_admin(user_id):
            keyboard = [[KeyboardButton("🌐 Webapp", web_app=WebAppInfo(url=WEBAPP_URL))]]
            reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=False)
            await update.message.reply_text(
                "Admin panelga xush kelibsiz! /new bilan yangi mavzu boshlang.",
                reply_markup=reply_markup
            )
        else:
            keyboard = [[KeyboardButton("📱 Contact yuborish", request_contact=True)]]
            reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
            await update.message.reply_text(
                "EduVerse botiga xush kelibsiz! Davom etish uchun contact ma'lumotlaringizni yuboring.",
                reply_markup=reply_markup
            )
    except Exception as e:
        logger.error(f"Start xatolik: {e}")
        await update.message.reply_text("Xatolik yuz berdi. Iltimos, qaytadan urinib ko'ring.")

async def new_topic(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Yangi mavzu yaratish"""
    try:
        if not is_admin(update.message.from_user.id):
            await update.message.reply_text("Sizda bu buyruqni ishlatish huquqi yo'q!")
            return
        
        if 'topic' in context.user_data and context.user_data['topic']:
            await update.message.reply_text(
                "Sizda allaqachon mavzu yaratish jarayoni bor. "
                "Agar yangi mavzu boshlashni xohlasangiz, /confirm yoki /skip buyrug'ini bosing."
            )
            return
            
        context.user_data['topic'] = {}
        await update.message.reply_text("Mavzu nomini yuboring:")
    except Exception as e:
        logger.error(f"New topic xatolik: {e}")
        await update.message.reply_text("Xatolik yuz berdi. Iltimos, qaytadan urinib ko'ring.")

async def text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Matn qabul qilish"""
    try:
        if not is_admin(update.message.from_user.id):
            await update.message.reply_text("Sizda bu buyruqni ishlatish huquqi yo'q!")
            return

        if 'topic' not in context.user_data:
            await update.message.reply_text("Iltimos, /new bilan boshlang.")
            return

        if not validate_text(update.message.text):
            await update.message.reply_text("Matn noto'g'ri formatda yoki juda uzun.")
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
    except Exception as e:
        logger.error(f"Text handler xatolik: {e}")
        await update.message.reply_text("Xatolik yuz berdi. Iltimos, qaytadan urinib ko'ring.")

async def photo_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Rasm qabul qilish"""
    try:
        if not is_admin(update.message.from_user.id):
            await update.message.reply_text("Sizda bu buyruqni ishlatish huquqi yo'q!")
            return

        if 'topic' not in context.user_data:
            await update.message.reply_text("Iltimos, /new bilan boshlang.")
            return

        photo = update.message.photo[-1]
        if photo.file_size > MAX_IMAGE_SIZE:
            await update.message.reply_text(f"Rasm hajmi {MAX_IMAGE_SIZE/1024/1024}MB dan oshmasligi kerak.")
            return

        file = await photo.get_file()
        context.user_data['topic']['image_url'] = file.file_path
        await update.message.reply_text("Endi video yuboring (ixtiyoriy, o'tkazib yuborish uchun /skip):")
    except Exception as e:
        logger.error(f"Photo handler xatolik: {e}")
        await update.message.reply_text("Rasm yuklashda xatolik yuz berdi. Iltimos, qaytadan urinib ko'ring.")

async def video_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Video qabul qilish"""
    try:
        if not is_admin(update.message.from_user.id):
            await update.message.reply_text("Sizda bu buyruqni ishlatish huquqi yo'q!")
            return

        if 'topic' not in context.user_data:
            await update.message.reply_text("Iltimos, /new bilan boshlang.")
            return

        # Agar video fayl yuborilsa
        if update.message.video:
            video = update.message.video
            if video.file_size > MAX_VIDEO_SIZE:
                await update.message.reply_text(f"Video hajmi {MAX_VIDEO_SIZE/1024/1024}MB dan oshmasligi kerak.")
                return
            file = await video.get_file()
            context.user_data['topic']['video_url'] = file.file_path
        # Agar YouTube havolasi yuborilsa
        elif update.message.text and validate_youtube_url(update.message.text):
            context.user_data['topic']['video_url'] = update.message.text
        # Agar boshqa havola yuborilsa
        elif update.message.text and validate_url(update.message.text):
            context.user_data['topic']['video_url'] = update.message.text
        else:
            await update.message.reply_text(
                "Video fayl yoki havola yuboring:\n"
                "- Telegram orqali video fayl\n"
                "- YouTube havolasi\n"
                "- Boshqa video havolasi"
            )
            return

        await update.message.reply_text("Barcha ma'lumotlar qabul qilindi. /confirm bosing.")
    except Exception as e:
        logger.error(f"Video handler xatolik: {e}")
        await update.message.reply_text("Video yuklashda xatolik yuz berdi. Iltimos, qaytadan urinib ko'ring.")

async def skip(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """O'tkazib yuborish"""
    try:
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
            context.user_data['topic'] = {}
    except Exception as e:
        logger.error(f"Skip xatolik: {e}")
        await update.message.reply_text("Xatolik yuz berdi. Iltimos, qaytadan urinib ko'ring.")

async def confirm_topic(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Mavzuni saqlash"""
    try:
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
                    context.user_data['topic'] = {}
                else:
                    error_text = await resp.text()
                    logger.error(f"Topic saqlash xatolik: {error_text}")
                    await update.message.reply_text("Mavzuni saqlashda xatolik yuz berdi. Iltimos, qaytadan urinib ko'ring.")
    except Exception as e:
        logger.error(f"Confirm topic xatolik: {e}")
        await update.message.reply_text("Xatolik yuz berdi. Iltimos, qaytadan urinib ko'ring.")

async def contact_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Contact ma'lumotlarini qabul qilish"""
    try:
        contact = update.message.contact
        if not contact:
            await update.message.reply_text("Contact ma'lumotlari topilmadi. Iltimos, qaytadan urinib ko'ring.")
            return

        data = {
            'user_id': update.effective_user.id,
            'first_name': contact.first_name,
            'last_name': contact.last_name,
            'phone_number': contact.phone_number
        }
        
        logger.info(f"Contact ma'lumotlari yuborilmoqda: {data}")
        
        async with aiohttp.ClientSession() as session:
            async with session.post(f"{API_URL}/api/contacts", json=data) as resp:
                response_text = await resp.text()
                logger.info(f"Server javobi: {response_text}")
                
                if resp.status == 200:
                    keyboard = [[KeyboardButton("🌐 Web App", web_app=WebAppInfo(url=WEBAPP_URL))]]
                    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=False)
                    
                    await update.message.reply_text(
                        "Contact ma'lumotlari saqlandi! Mavzularni ko'rish uchun Web App tugmasini bosing:",
                        reply_markup=reply_markup
                    )
                else:
                    logger.error(f"Contact saqlash xatolik: Status={resp.status}, Response={response_text}")
                    await update.message.reply_text(
                        f"Contact saqlashda xatolik yuz berdi (Status: {resp.status}).\n"
                        "Iltimos, qaytadan urinib ko'ring.\n"
                        "Agar muammo davom etsa, administrator bilan bog'laning."
                    )
    except aiohttp.ClientError as e:
        logger.error(f"API ulanish xatolik: {e}")
        await update.message.reply_text(
            "Server bilan bog'lanishda xatolik yuz berdi. Iltimos, keyinroq qaytadan urinib ko'ring.\n"
            "Agar muammo davom etsa, administrator bilan bog'laning."
        )
    except Exception as e:
        logger.error(f"Contact handler xatolik: {e}")
        await update.message.reply_text(
            "Kutilmagan xatolik yuz berdi. Iltimos, keyinroq qaytadan urinib ko'ring.\n"
            "Agar muammo davom etsa, administrator bilan bog'laning."
        ) 