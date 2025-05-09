from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo, KeyboardButton, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import ContextTypes
import aiohttp
import os
import logging
from typing import Optional, Dict, Any
import re
import json

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

# --- Yangi mavzu qo'shish uchun tugmalar ---
NEW_TOPIC_BTN = "➕ Yangi mavzu qo'shish"
SKIP_BTN = "⏭ O'tkazib yuborish"
CANCEL_BTN = "❌ Bekor qilish"
SAVE_BTN = "✅ Saqlash"

TOPIC_STEPS = ['title', 'structure', 'examples', 'image', 'video']

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
            keyboard = [
                [KeyboardButton("🌐 Webapp", web_app=WebAppInfo(url=WEBAPP_URL))],
                [KeyboardButton("📊 Statistika")],
                [KeyboardButton(NEW_TOPIC_BTN)]
            ]
            reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=False)
            await update.message.reply_text(
                "Admin panelga xush kelibsiz! Yangi mavzu qo'shish uchun tugmani bosing.",
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

async def new_topic_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info("Yangi mavzu tugmasi bosildi")
    print("Yangi mavzu tugmasi bosildi")
    if not is_admin(update.message.from_user.id):
        return
    context.user_data['topic'] = {}
    context.user_data['topic_step'] = 0
    await ask_next_topic_step(update, context)

async def ask_next_topic_step(update, context):
    step_idx = context.user_data.get('topic_step', 0)
    if step_idx >= len(TOPIC_STEPS):
        await update.message.reply_text(
            "Barcha ma'lumotlar qabul qilindi. Saqlash uchun tugmani bosing:",
            reply_markup=ReplyKeyboardMarkup([[KeyboardButton(SAVE_BTN)], [KeyboardButton(CANCEL_BTN)]], resize_keyboard=True)
        )
        return
    step = TOPIC_STEPS[step_idx]
    if step == 'title':
        await update.message.reply_text("Mavzu nomini kiriting:", reply_markup=ReplyKeyboardMarkup([[KeyboardButton(CANCEL_BTN)]], resize_keyboard=True))
    elif step == 'structure':
        await update.message.reply_text("Mavzu tuzilmasini kiriting:", reply_markup=ReplyKeyboardMarkup([[KeyboardButton(CANCEL_BTN)]], resize_keyboard=True))
    elif step == 'examples':
        await update.message.reply_text("Misollarni kiriting:", reply_markup=ReplyKeyboardMarkup([[KeyboardButton(CANCEL_BTN)]], resize_keyboard=True))
    elif step == 'image':
        await update.message.reply_text(
            "Rasm yuboring yoki o'tkazib yuborish uchun tugmani bosing:",
            reply_markup=ReplyKeyboardMarkup([[KeyboardButton(SKIP_BTN)], [KeyboardButton(CANCEL_BTN)]], resize_keyboard=True)
        )
    elif step == 'video':
        await update.message.reply_text(
            "Video yuboring yoki o'tkazib yuborish uchun tugmani bosing:",
            reply_markup=ReplyKeyboardMarkup([[KeyboardButton(SKIP_BTN)], [KeyboardButton(CANCEL_BTN)]], resize_keyboard=True)
        )

async def topic_text_step(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.message.from_user.id):
        return
    if 'topic_step' not in context.user_data:
        return
    step_idx = context.user_data['topic_step']
    if step_idx >= len(TOPIC_STEPS):
        return
    step = TOPIC_STEPS[step_idx]
    text = update.message.text
    if text == CANCEL_BTN:
        context.user_data.pop('topic', None)
        context.user_data.pop('topic_step', None)
        await update.message.reply_text("Mavzu yaratish bekor qilindi.", reply_markup=ReplyKeyboardRemove())
        return
    if step in ['title', 'structure', 'examples']:
        context.user_data['topic'][step] = text
        context.user_data['topic_step'] += 1
        await ask_next_topic_step(update, context)
    elif step == 'image':
        await update.message.reply_text(
            "Rasm yuboring yoki o'tkazib yuborish uchun tugmani bosing:",
            reply_markup=ReplyKeyboardMarkup([[KeyboardButton(SKIP_BTN)], [KeyboardButton(CANCEL_BTN)]], resize_keyboard=True)
        )
    elif step == 'video':
        await update.message.reply_text(
            "Video yuboring yoki o'tkazib yuborish uchun tugmani bosing:",
            reply_markup=ReplyKeyboardMarkup([[KeyboardButton(SKIP_BTN)], [KeyboardButton(CANCEL_BTN)]], resize_keyboard=True)
        )

async def photo_handler_topic(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.message.from_user.id):
        return
    if context.user_data.get('topic_step', 0) == TOPIC_STEPS.index('image'):
        photo = update.message.photo[-1]
        if photo.file_size > MAX_IMAGE_SIZE:
            await update.message.reply_text(f"Rasm hajmi {MAX_IMAGE_SIZE/1024/1024}MB dan oshmasligi kerak.")
            return
        file = await photo.get_file()
        context.user_data['topic']['image_url'] = file.file_path
        context.user_data['topic_step'] += 1
        await ask_next_topic_step(update, context)

async def skip_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.message.from_user.id):
        return
    if 'topic_step' not in context.user_data:
        return
    step_idx = context.user_data['topic_step']
    if step_idx >= len(TOPIC_STEPS):
        return
    step = TOPIC_STEPS[step_idx]
    if update.message.text == SKIP_BTN:
        if step == 'image':
            context.user_data['topic']['image_url'] = None
        elif step == 'video':
            context.user_data['topic']['video_url'] = None
        context.user_data['topic_step'] += 1
        await ask_next_topic_step(update, context)

async def video_handler_topic(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.message.from_user.id):
        return
    if context.user_data.get('topic_step', 0) == TOPIC_STEPS.index('video'):
        if update.message.video:
            video = update.message.video
            if video.file_size > MAX_VIDEO_SIZE:
                await update.message.reply_text(f"Video hajmi {MAX_VIDEO_SIZE/1024/1024}MB dan oshmasligi kerak.")
                return
            file = await video.get_file()
            context.user_data['topic']['video_url'] = file.file_path
            context.user_data['topic_step'] += 1
            await ask_next_topic_step(update, context)
        elif update.message.text and validate_youtube_url(update.message.text):
            context.user_data['topic']['video_url'] = update.message.text
            context.user_data['topic_step'] += 1
            await ask_next_topic_step(update, context)
        elif update.message.text and validate_url(update.message.text):
            context.user_data['topic']['video_url'] = update.message.text
            context.user_data['topic_step'] += 1
            await ask_next_topic_step(update, context)
        elif update.message.text == SKIP_BTN:
            context.user_data['topic']['video_url'] = None
            context.user_data['topic_step'] += 1
            await ask_next_topic_step(update, context)
        elif update.message.text == CANCEL_BTN:
            context.user_data.pop('topic', None)
            context.user_data.pop('topic_step', None)
            await update.message.reply_text("Mavzu yaratish bekor qilindi.", reply_markup=ReplyKeyboardRemove())
        else:
            await update.message.reply_text(
                "Video yuboring yoki o'tkazib yuborish uchun tugmani bosing:",
                reply_markup=ReplyKeyboardMarkup([[KeyboardButton(SKIP_BTN)], [KeyboardButton(CANCEL_BTN)]], resize_keyboard=True)
            )

async def save_topic_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.message.from_user.id):
        return
    if context.user_data.get('topic_step', 0) == len(TOPIC_STEPS) and update.message.text == SAVE_BTN:
        topic = context.user_data.get('topic')
        if not topic or 'title' not in topic or 'structure' not in topic or 'examples' not in topic:
            await update.message.reply_text("Ma'lumotlar to'liq emas.")
            return
        async with aiohttp.ClientSession() as session:
            async with session.post(f"{API_URL}/api/topics", json=topic) as resp:
                if resp.status == 200:
                    await update.message.reply_text("Mavzu saqlandi!", reply_markup=ReplyKeyboardRemove())
                    context.user_data['topic'] = {}
                    context.user_data['topic_step'] = None
                else:
                    error_text = await resp.text()
                    logger.error(f"Topic saqlash xatolik: {error_text}")
                    await update.message.reply_text("Mavzuni saqlashda xatolik yuz berdi. Iltimos, qaytadan urinib ko'ring.")

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
        logger.info(f"API URL: {API_URL}")
        
        async with aiohttp.ClientSession() as session:
            try:
                async with session.post(f"{API_URL}/api/contacts", json=data) as resp:
                    response_text = await resp.text()
                    logger.info(f"Server javobi: Status={resp.status}, Response={response_text}")
                    
                    if resp.status == 200:
                        keyboard = [[KeyboardButton("🌐 Web App", web_app=WebAppInfo(url=WEBAPP_URL))]]
                        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=False)
                        
                        await update.message.reply_text(
                            "Contact ma'lumotlari saqlandi! Mavzularni ko'rish uchun Web App tugmasini bosing:",
                            reply_markup=reply_markup
                        )
                    else:
                        error_msg = f"Contact saqlashda xatolik yuz berdi (Status: {resp.status}).\n"
                        try:
                            error_data = json.loads(response_text)
                            if 'details' in error_data:
                                error_msg += f"Xatolik tafsiloti: {error_data['details']}\n"
                        except:
                            error_msg += f"Server javobi: {response_text}\n"
                        
                        error_msg += "Iltimos, qaytadan urinib ko'ring.\n"
                        error_msg += "Agar muammo davom etsa, administrator bilan bog'laning."
                        
                        logger.error(error_msg)
                        await update.message.reply_text(error_msg)
            except aiohttp.ClientError as e:
                error_msg = f"API ulanish xatolik: {str(e)}"
                logger.error(error_msg)
                await update.message.reply_text(
                    "Server bilan bog'lanishda xatolik yuz berdi. Iltimos, keyinroq qaytadan urinib ko'ring.\n"
                    "Agar muammo davom etsa, administrator bilan bog'laning."
                )
    except Exception as e:
        error_msg = f"Contact handler xatolik: {str(e)}"
        logger.error(error_msg)
        await update.message.reply_text(
            "Kutilmagan xatolik yuz berdi. Iltimos, keyinroq qaytadan urinib ko'ring.\n"
            "Agar muammo davom etsa, administrator bilan bog'laning."
        )

async def stats_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.message.from_user.id):
        await update.message.reply_text("Siz admin emassiz!")
        return
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{API_URL}/api/stats") as resp:
                data = await resp.json()
                await update.message.reply_text(
                    f"📊 Statistika:\nJami foydalanuvchilar: {data.get('users_count', 0)}"
                )
    except Exception as e:
        logger.error(f"Statistika olishda xatolik: {e}")
        await update.message.reply_text("Statistika olishda xatolik yuz berdi.")

async def video_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Foydalanuvchi uchun: topic yaratish jarayonida emas
    if 'topic_step' in context.user_data:
        return
    await update.message.reply_text("Video yoki havola uchun bu botda faqat adminlar uchun maxsus bo'lim mavjud.")

async def photo_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Foydalanuvchi uchun: topic yaratish jarayonida emas
    if 'topic_step' in context.user_data:
        return
    await update.message.reply_text("Rasm yuborish adminlar uchun mo'ljallangan.") 