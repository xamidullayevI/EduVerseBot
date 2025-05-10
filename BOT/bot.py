from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackQueryHandler
from telegram import Update
from handlers import admin
import os
from dotenv import load_dotenv
import logging
from logging.handlers import RotatingFileHandler
import sys
import traceback
import json
from datetime import datetime

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[
        RotatingFileHandler('logs/bot.log', maxBytes=10240, backupCount=10),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Load environment variables
dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
load_dotenv(dotenv_path)

async def error_handler(update: object, context: object) -> None:
    """Log Errors caused by Updates."""
    error_details = {
        'severity': 'error',
        'timestamp': datetime.utcnow().isoformat(),
        'message': str(context.error),
        'update': update.to_dict() if isinstance(update, Update) else str(update),
        'trace': ''.join(traceback.format_tb(sys.exc_info()[2]))
    }
    
    logger.error(json.dumps(error_details, indent=2, ensure_ascii=False))
    
    # If critical error, notify admins
    if isinstance(context.error, Exception):
        await context.bot.send_message(
            chat_id=os.getenv("ADMINS").split(",")[0],
            text=f"❌ Critical error:\n{context.error}\n\nCheck logs for details."
        )

async def start_bot(token: str):
    try:
        application = Application.builder().token(token).build()

        # Error handler
        application.add_error_handler(error_handler)

        # Command handlers
        application.add_handler(CommandHandler("start", admin.start))

        # Admin handlers  
        application.add_handler(MessageHandler(filters.Regex("^📊 Statistika$"), admin.stats_handler))
        application.add_handler(MessageHandler(filters.Regex("^➕ Yangi mavzu qo'shish$"), admin.new_topic_button))
        application.add_handler(MessageHandler(filters.Regex("^🗑 Mavzuni o'chirish$"), admin.delete_topic_button))
        application.add_handler(CallbackQueryHandler(admin.delete_topic_callback, pattern=r"^delete_topic_\d+$"))

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

        logger.info("Bot started successfully")
        await application.run_polling(allowed_updates=Update.ALL_TYPES)
        
    except Exception as e:
        error_details = {
            'severity': 'critical',
            'timestamp': datetime.utcnow().isoformat(),
            'message': str(e),
            'trace': traceback.format_exc()
        }
        logger.critical(json.dumps(error_details, indent=2, ensure_ascii=False))
        raise
