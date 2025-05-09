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
    application.add_handler(CommandHandler("new", admin.new_topic))
    application.add_handler(CommandHandler("confirm", admin.confirm_topic))
    application.add_handler(CommandHandler("skip", admin.skip))

    # Avval video handlerlar
    application.add_handler(MessageHandler(filters.VIDEO, admin.video_handler))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, admin.video_handler))

    # Keyin photo va boshqa textlar
    application.add_handler(MessageHandler(filters.PHOTO, admin.photo_handler))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, admin.text_handler))

    application.add_handler(MessageHandler(filters.CONTACT, admin.contact_handler))

    print("Bot started...")
    await application.run_polling(allowed_updates=Update.ALL_TYPES)
