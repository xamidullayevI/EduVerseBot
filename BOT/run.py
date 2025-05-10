import os
from dotenv import load_dotenv
import nest_asyncio
import asyncio
from bot import start_bot

# Fayl yo'lini aniq ko'rsatamiz
dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
print("DOTENV PATH:", dotenv_path)
print("EXISTS:", os.path.exists(dotenv_path))

load_dotenv(dotenv_path)
print("ADMINS ENV:", os.getenv("ADMINS"))
BOT_TOKEN = os.getenv("BOT_TOKEN")

import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Asyncio loop'ni sozlaymiz
nest_asyncio.apply()

if __name__ == "__main__":
    try:
        if not BOT_TOKEN:
            logger.error("BOT_TOKEN .env faylida topilmadi! Bot ishga tushmaydi.")
            exit(1)
        # Botni ishga tushirish
        asyncio.run(start_bot(BOT_TOKEN))
    except KeyboardInterrupt:
        logger.info("Bot to'xtatildi!")
    except Exception as e:
        logger.error(f"Xatolik yuz berdi: {e}")
