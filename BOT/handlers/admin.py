from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo, KeyboardButton, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import ContextTypes
import aiohttp
import os
import logging
from logging.handlers import RotatingFileHandler
from typing import Optional, Dict, Any
import re
import json
from functools import wraps
import traceback
import asyncio
import time
from datetime import datetime, timedelta

# Log yozish sozlamalari
if not os.path.exists('logs'):
    os.makedirs('logs')

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[
        RotatingFileHandler('logs/bot.log', maxBytes=10240, backupCount=10),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Sozlamalar
ADMINS = [int(x) for x in os.getenv("ADMINS", "").split(",") if x.strip()]
API_URL = os.getenv("API_URL", "http://localhost:5000")
WEBAPP_URL = os.getenv("WEBAPP_URL", "http://localhost:5000")
API_KEY = os.getenv("API_KEY")

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
DELETE_TOPIC_BTN = "🗑 Mavzuni o'chirish"

TOPIC_STEPS = ['title', 'structure', 'examples', 'image', 'video']

# Rate limiting settings
RATE_LIMIT = 30  # max requests per second
RATE_WINDOW = 1  # seconds
RETRY_COUNT = 3
RETRY_DELAY = 1  # seconds

class RateLimiter:
    def __init__(self, rate=RATE_LIMIT, per=RATE_WINDOW):
        self.rate = rate
        self.per = per
        self.allowance = rate
        self.last_check = time.time()

    def is_allowed(self):
        current = time.time()
        time_passed = current - self.last_check
        self.last_check = current
        self.allowance += time_passed * (self.rate / self.per)
        
        if self.allowance > self.rate:
            self.allowance = self.rate
            
        if self.allowance < 1:
            return False
            
        self.allowance -= 1
        return True

rate_limiter = RateLimiter()

def handle_rate_limit(func):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        for attempt in range(RETRY_COUNT):
            if rate_limiter.is_allowed():
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    if "Too Many Requests" in str(e) and attempt < RETRY_COUNT - 1:
                        await asyncio.sleep(RETRY_DELAY * (attempt + 1))
                        continue
                    raise
            await asyncio.sleep(RETRY_DELAY)
        return await func(*args, **kwargs)
    return wrapper

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

async def handle_error(update: Update, context: ContextTypes.DEFAULT_TYPE, error: Exception):
    """Xatoliklarni boshqarish"""
    logger.error(f"Xatolik yuz berdi: {str(error)}")
    logger.error(traceback.format_exc())
    
    # Asosiy menyuga qaytish
    keyboard = [
        [KeyboardButton("🌐 Webapp", web_app=WebAppInfo(url=WEBAPP_URL))],
        [KeyboardButton("📊 Statistika")],
        [KeyboardButton(NEW_TOPIC_BTN)],
        [KeyboardButton(DELETE_TOPIC_BTN)]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=False)
    
    error_message = "Xatolik yuz berdi. Iltimos, keyinroq qaytadan urinib ko'ring."
    if update.effective_message:
        await update.effective_message.reply_text(error_message, reply_markup=reply_markup)
    elif update.callback_query:
        await update.callback_query.message.reply_text(error_message, reply_markup=reply_markup)

@handle_rate_limit
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start buyrug'i"""
    try:
        user_id = update.message.from_user.id
        if is_admin(user_id):
            keyboard = [
                [KeyboardButton("🌐 Webapp", web_app=WebAppInfo(url=WEBAPP_URL))],
                [KeyboardButton("📊 Statistika")],
                [KeyboardButton(NEW_TOPIC_BTN)],
                [KeyboardButton(DELETE_TOPIC_BTN)]
            ]
            reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=False)
            await update.message.reply_text(
                "Admin panelga xush kelibsiz! Yangi mavzu qo'shish yoki o'chirish uchun tugmani bosing.",
                reply_markup=reply_markup
            )
        else:
            # Foydalanuvchini bazadan tekshirish
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{API_URL}/api/contacts/{user_id}") as resp:
                    if resp.status == 200:
                        keyboard = [[KeyboardButton("🌐 Web App", web_app=WebAppInfo(url=WEBAPP_URL))]]
                        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=False)
                        await update.message.reply_text(
                            "Xush kelibsiz! Mavzularni ko'rish uchun Web App tugmasini bosing:",
                            reply_markup=reply_markup
                        )
                        return
            keyboard = [[KeyboardButton("📱 Contact yuborish", request_contact=True)]]
            reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
            await update.message.reply_text(
                "EduVerse botiga xush kelibsiz! Davom etish uchun contact ma'lumotlaringizni yuboring.",
                reply_markup=reply_markup
            )
    except Exception as e:
        logger.error(f"Start xatolik: {e}")
        await update.message.reply_text("Xatolik yuz berdi. Iltimos, qaytadan urinib ko'ring.")

@handle_rate_limit
async def new_topic_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info("Yangi mavzu tugmasi bosildi")
    print("Yangi mavzu tugmasi bosildi")
    if not is_admin(update.message.from_user.id):
        return
    context.user_data['topic'] = {}
    context.user_data['topic_step'] = 0
    await ask_next_topic_step(update, context)

async def ask_next_topic_step(update, context):
    try:
        step_idx = context.user_data.get('topic_step', 0)
        if step_idx >= len(TOPIC_STEPS):
            # Barcha bosqichlar tugaganda
            keyboard = [
                [KeyboardButton(SAVE_BTN)],
                [KeyboardButton(CANCEL_BTN)]
            ]
            reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=False)
            await update.message.reply_text(
                "Barcha ma'lumotlar qabul qilindi. Saqlash uchun tugmani bosing:",
                reply_markup=reply_markup
            )
            return

        step = TOPIC_STEPS[step_idx]
        logger.info(f"Keyingi bosqich: {step}")

        # Har bir bosqich uchun tegishli keyboard
        if step in ['title', 'structure', 'examples']:
            # Matn kiritish uchun
            keyboard = [[KeyboardButton(CANCEL_BTN)]]
            message = {
                'title': "Mavzu nomini kiriting:",
                'structure': "Mavzu tuzilmasini kiriting:",
                'examples': "Misollarni kiriting:"
            }[step]
        elif step == 'image':
            # Rasm yuklash uchun
            keyboard = [
                [KeyboardButton(SKIP_BTN)],
                [KeyboardButton(CANCEL_BTN)]
            ]
            message = "Rasm yuboring yoki o'tkazib yuborish uchun tugmani bosing:"
        elif step == 'video':
            # Video yuklash uchun
            keyboard = [
                [KeyboardButton(SKIP_BTN)],
                [KeyboardButton(CANCEL_BTN)]
            ]
            message = "Video yuboring yoki video havolasini kiriting (YouTube yoki boshqa video havolasi).\nO'tkazib yuborish uchun tugmani bosing:"

        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        await update.message.reply_text(message, reply_markup=reply_markup)

    except Exception as e:
        logger.error(f"ask_next_topic_step xatolik: {e}")
        # Xatolik yuz berganda asosiy menyuga qaytish
        keyboard = [
            [KeyboardButton("🌐 Webapp", web_app=WebAppInfo(url=WEBAPP_URL))],
            [KeyboardButton("📊 Statistika")],
            [KeyboardButton(NEW_TOPIC_BTN)],
            [KeyboardButton(DELETE_TOPIC_BTN)]
        ]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=False)
        await update.message.reply_text(
            "Xatolik yuz berdi. Asosiy menyuga qaytdingiz.",
            reply_markup=reply_markup
        )
        context.user_data.pop('topic', None)
        context.user_data.pop('topic_step', None)

@handle_rate_limit
async def topic_text_step(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        if not is_admin(update.message.from_user.id):
            return

        if 'topic_step' not in context.user_data:
            return

        step_idx = context.user_data['topic_step']
        text = update.message.text

        # Cancel tugmasi bosilganda
        if text == CANCEL_BTN:
            # Barcha ma'lumotlarni tozalash
            context.user_data.pop('topic', None)
            context.user_data.pop('topic_step', None)
            
            # Asosiy menyuga qaytish
            keyboard = [
                [KeyboardButton("🌐 Webapp", web_app=WebAppInfo(url=WEBAPP_URL))],
                [KeyboardButton("📊 Statistika")],
                [KeyboardButton(NEW_TOPIC_BTN)],
                [KeyboardButton(DELETE_TOPIC_BTN)]
            ]
            reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=False)
            await update.message.reply_text(
                "Mavzu yaratish bekor qilindi. Asosiy menyuga qaytdingiz.",
                reply_markup=reply_markup
            )
            return

        # Save tugmasi bosilganda
        if text == SAVE_BTN and step_idx >= len(TOPIC_STEPS):
            await save_topic_handler(update, context)
            return

        if step_idx >= len(TOPIC_STEPS):
            return

        step = TOPIC_STEPS[step_idx]

        # Skip tugmasi bosilganda
        if text == SKIP_BTN:
            if step == 'image':
                context.user_data['topic']['image_url'] = None
                logger.info("Rasm o'tkazib yuborildi")
            elif step == 'video':
                context.user_data['topic']['video_url'] = None
                logger.info("Video o'tkazib yuborildi")
            
            # Keyingi bosqichga o'tish
            context.user_data['topic_step'] += 1
            await ask_next_topic_step(update, context)
            return

        # Matn kiritilganda
        if step in ['title', 'structure', 'examples']:
            if not validate_text(text):
                await update.message.reply_text(
                    "Matn noto'g'ri formatda. Iltimos, qaytadan kiriting:",
                    reply_markup=ReplyKeyboardMarkup([[KeyboardButton(CANCEL_BTN)]], resize_keyboard=True)
                )
                return

            context.user_data['topic'][step] = text
            context.user_data['topic_step'] += 1
            await ask_next_topic_step(update, context)
            return

        # Video havolasi kiritilganda
        if step == 'video' and text:
            if validate_youtube_url(text) or validate_url(text):
                context.user_data['topic']['video_url'] = text
                context.user_data['topic_step'] += 1
                await ask_next_topic_step(update, context)
            else:
                keyboard = [
                    [KeyboardButton(SKIP_BTN)],
                    [KeyboardButton(CANCEL_BTN)]
                ]
                await update.message.reply_text(
                    "Noto'g'ri video havolasi. Iltimos, to'g'ri havola kiriting yoki o'tkazib yuborish tugmasini bosing:",
                    reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
                )
            return

    except Exception as e:
        logger.error(f"topic_text_step xatolik: {e}")
        # Xatolik yuz berganda asosiy menyuga qaytish
        keyboard = [
            [KeyboardButton("🌐 Webapp", web_app=WebAppInfo(url=WEBAPP_URL))],
            [KeyboardButton("📊 Statistika")],
            [KeyboardButton(NEW_TOPIC_BTN)],
            [KeyboardButton(DELETE_TOPIC_BTN)]
        ]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=False)
        await update.message.reply_text(
            "Xatolik yuz berdi. Asosiy menyuga qaytdingiz.",
            reply_markup=reply_markup
        )
        context.user_data.pop('topic', None)
        context.user_data.pop('topic_step', None)

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
    try:
        if not is_admin(update.message.from_user.id):
            return

        if 'topic_step' not in context.user_data:
            return

        step_idx = context.user_data['topic_step']
        if step_idx >= len(TOPIC_STEPS):
            return

        step = TOPIC_STEPS[step_idx]
        if update.message.text and update.message.text.strip() == SKIP_BTN:
            logger.info(f"Skip tugmasi bosildi: {step} bosqichida")
            
            if step == 'image':
                context.user_data['topic']['image_url'] = None
                logger.info("Rasm o'tkazib yuborildi")
            elif step == 'video':
                context.user_data['topic']['video_url'] = None
                logger.info("Video o'tkazib yuborildi")
            
            # Keyingi bosqichga o'tish
            context.user_data['topic_step'] += 1
            await ask_next_topic_step(update, context)
            return

    except Exception as e:
        logger.error(f"skip_handler xatolik: {e}")
        # Xatolik yuz berganda asosiy menyuga qaytish
        keyboard = [
            [KeyboardButton("🌐 Webapp", web_app=WebAppInfo(url=WEBAPP_URL))],
            [KeyboardButton("📊 Statistika")],
            [KeyboardButton(NEW_TOPIC_BTN)],
            [KeyboardButton(DELETE_TOPIC_BTN)]
        ]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=False)
        await update.message.reply_text(
            "Xatolik yuz berdi. Asosiy menyuga qaytdingiz.",
            reply_markup=reply_markup
        )
        context.user_data.pop('topic', None)
        context.user_data.pop('topic_step', None)

async def video_handler_topic(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.message.from_user.id):
        return
    if context.user_data.get('topic_step', 0) == TOPIC_STEPS.index('video'):
        text = update.message.text
        # 1. Video fayl
        if update.message.video:
            video = update.message.video
            if video.file_size > MAX_VIDEO_SIZE:
                await update.message.reply_text(f"Video hajmi {MAX_VIDEO_SIZE/1024/1024}MB dan oshmasligi kerak.")
                return
            file = await video.get_file()
            context.user_data['topic']['video_url'] = file.file_path
            context.user_data['topic_step'] += 1
            await ask_next_topic_step(update, context)
        # 2. YouTube havolasi
        elif text and validate_youtube_url(text):
            context.user_data['topic']['video_url'] = text
            context.user_data['topic_step'] += 1
            await ask_next_topic_step(update, context)
        # 3. Boshqa video havolasi
        elif text and validate_url(text):
            context.user_data['topic']['video_url'] = text
            context.user_data['topic_step'] += 1
            await ask_next_topic_step(update, context)
        # 4. Skip yoki cancel
        elif text == SKIP_BTN:
            context.user_data['topic']['video_url'] = None
            context.user_data['topic_step'] += 1
            await ask_next_topic_step(update, context)
        elif text == CANCEL_BTN:
            context.user_data.pop('topic', None)
            context.user_data.pop('topic_step', None)
            # Show main admin menu after cancel
            keyboard = [
                [KeyboardButton("🌐 Webapp", web_app=WebAppInfo(url=WEBAPP_URL))],
                [KeyboardButton("📊 Statistika")],
                [KeyboardButton(NEW_TOPIC_BTN)],
                [KeyboardButton(DELETE_TOPIC_BTN)]
            ]
            reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=False)
            await update.message.reply_text("Mavzu yaratish bekor qilindi.", reply_markup=reply_markup)
        # 5. Noto'g'ri format
        else:
            await update.message.reply_text(
                "Video yoki video havolasini yuboring yoki o'tkazib yuborish uchun tugmani bosing:",
                reply_markup=ReplyKeyboardMarkup([[KeyboardButton(SKIP_BTN)], [KeyboardButton(CANCEL_BTN)]], resize_keyboard=True)
            )

async def save_topic_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
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
                        # Barcha ma'lumotlarni tozalash
                        context.user_data.pop('topic', None)
                        context.user_data.pop('topic_step', None)

                        # Asosiy menyuga qaytish
                        keyboard = [
                            [KeyboardButton("🌐 Webapp", web_app=WebAppInfo(url=WEBAPP_URL))],
                            [KeyboardButton("📊 Statistika")],
                            [KeyboardButton(NEW_TOPIC_BTN)],
                            [KeyboardButton(DELETE_TOPIC_BTN)]
                        ]
                        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=False)
                        await update.message.reply_text(
                            "Mavzu saqlandi! Asosiy menyuga qaytdingiz.",
                            reply_markup=reply_markup
                        )
                    else:
                        error_text = await resp.text()
                        logger.error(f"Topic saqlash xatolik: {error_text}")
                        await update.message.reply_text(
                            "Mavzuni saqlashda