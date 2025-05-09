from telegram.ext import Application, CommandHandler, MessageHandler, filters
from telegram import Update
from handlers import admin
import os
from dotenv import load_dotenv

# Fayl yo‘lini aniq ko‘rsatamiz
dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
load_dotenv(dotenv_path)

async def start_bot(token: str):
    application = Application.builder().token(token).build()

    application.add_handler(CommandHandler("start", admin.start))
    application.add_handler(CommandHandler("confirm", admin.confirm_topic))
    application.add_handler(CommandHandler("skip", admin.skip))
    application.add_handler(CommandHandler("new", admin.new_topic))

    # Statistika tugmasi uchun handler
    application.add_handler(MessageHandler(filters.Regex("Statistika"), admin.stats_handler))
    # Yangi mavzu tugmasi
    application.add_handler(MessageHandler(filters.Regex("^➕ Yangi mavzu qo'shish$"), admin.new_topic_button))
    # Topic bosqichlari uchun text handler (faqat topic yaratish jarayonida)
    application.add_handler(MessageHandler(
        filters.TEXT & ~filters.COMMAND,
        admin.topic_text_step
    ))
    # Topic uchun photo handler
    application.add_handler(MessageHandler(filters.PHOTO, admin.photo_handler_topic))
    # Topic uchun video handler
    application.add_handler(MessageHandler(filters.VIDEO, admin.video_handler_topic))
    # Topic uchun skip tugmasi
    application.add_handler(MessageHandler(filters.Regex("^⏭ O'tkazib yuborish$"), admin.skip_handler))
    # Topic uchun saqlash tugmasi
    application.add_handler(MessageHandler(filters.Regex("^✅ Saqlash$"), admin.save_topic_handler))

    # Foydalanuvchi uchun umumiy handlerlar (topic yaratish jarayonida bo'lmagan paytda)
    # Ushbu handlerlarni topic yaratish bosqichida ishlatmaslik uchun, admin.py dagi handlerlarda
    # context.user_data['topic_step'] mavjudligini tekshirish kerak.
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, admin.video_handler))
    application.add_handler(MessageHandler(filters.PHOTO, admin.photo_handler))
    application.add_handler(MessageHandler(filters.VIDEO, admin.video_handler))
    application.add_handler(MessageHandler(filters.CONTACT, admin.contact_handler))

    print("Bot started...")
    await application.run_polling(allowed_updates=Update.ALL_TYPES)
