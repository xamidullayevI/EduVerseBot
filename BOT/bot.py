from telegram.ext import Application, CommandHandler, MessageHandler, filters
from telegram import Update
from handlers import admin
import os
from dotenv import load_dotenv

# Fayl yo'lini aniq ko'rsatamiz
dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
load_dotenv(dotenv_path)

async def start_bot(token: str):
    application = Application.builder().token(token).build()

    # Start command handler
    application.add_handler(CommandHandler("start", admin.start))

    # Admin handlers
    application.add_handler(MessageHandler(filters.Regex("^📊 Statistika$"), admin.stats_handler))
    application.add_handler(MessageHandler(filters.Regex("^➕ Yangi mavzu qo'shish$"), admin.new_topic_button))
    
    # Topic creation handlers
    application.add_handler(MessageHandler(
        filters.TEXT & ~filters.COMMAND & ~filters.UpdateType.EDITED_MESSAGE,
        admin.topic_text_step
    ))
    application.add_handler(MessageHandler(filters.PHOTO, admin.photo_handler_topic))
    application.add_handler(MessageHandler(filters.VIDEO, admin.video_handler_topic))
    application.add_handler(MessageHandler(filters.Regex("^⏭ O'tkazib yuborish$"), admin.skip_handler))
    application.add_handler(MessageHandler(filters.Regex("^✅ Saqlash$"), admin.save_topic_handler))

    # User handlers
    application.add_handler(MessageHandler(filters.CONTACT, admin.contact_handler))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, admin.video_handler))
    application.add_handler(MessageHandler(filters.PHOTO, admin.photo_handler))
    application.add_handler(MessageHandler(filters.VIDEO, admin.video_handler))

    print("Bot started...")
    await application.run_polling(allowed_updates=Update.ALL_TYPES)
