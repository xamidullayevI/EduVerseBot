import subprocess
import sys
import os
import shutil
from threading import Thread
import time
from dotenv import load_dotenv

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

def setup_virtual_env():
    venv_name = os.path.join(BASE_DIR, "venv")
    if not os.path.exists(venv_name):
        print("📦 Virtual muhit yaratilmoqda...")
        subprocess.run([sys.executable, '-m', 'venv', venv_name])
        print("✅ Virtual muhit yaratildi!")
    
    if sys.platform == "win32":
        python_path = os.path.join(venv_name, "Scripts", "python.exe")
        pip_path = os.path.join(venv_name, "Scripts", "pip.exe")
    else:
        python_path = os.path.join(venv_name, "bin", "python")
        pip_path = os.path.join(venv_name, "bin", "pip")
    
    return python_path, pip_path

def check_directories():
    if not os.path.exists(os.path.join(BASE_DIR, 'BOT')):
        raise FileNotFoundError("❌ BOT papkasi topilmadi!")
    if not os.path.exists(os.path.join(BASE_DIR, 'WEB-APP')):
        raise FileNotFoundError("❌ WEB-APP papkasi topilmadi!")

def setup_env():
    print("🌍 .env fayllar ulanyapti...")
    env_source = os.path.join(BASE_DIR, '.env')
    bot_env_path = os.path.join(BASE_DIR, 'BOT', '.env')
    web_env_path = os.path.join(BASE_DIR, 'WEB-APP', '.env')

    if not os.path.exists(env_source):
        raise FileNotFoundError("❌ Asosiy papkada .env fayl topilmadi!")

    shutil.copy(env_source, bot_env_path)
    shutil.copy(env_source, web_env_path)

    print("✅ .env fayllar sozlandi.")

def install_requirements(pip_path):
    print("📥 Kerakli kutubxonalar o‘rnatilmoqda...")
    subprocess.run([pip_path, 'install', '-r', os.path.join(BASE_DIR, 'requirements.txt')])
    print("✅ Barcha kutubxonalar o‘rnatildi!")

def run_bot(python_path):
    try:
        print("🚀 Bot ishga tushmoqda...")
        subprocess.run([python_path, 'run.py'], cwd=os.path.join(BASE_DIR, 'BOT'))
    except Exception as e:
        print(f"❌ Bot ishga tushirishda xatolik: {e}")

def run_webapp(python_path):
    try:
        print("🌐 Web app ishga tushmoqda...")
        subprocess.run([python_path, 'app.py'], cwd=os.path.join(BASE_DIR, 'WEB-APP'))
    except Exception as e:
        print(f"❌ Web app ishga tushirishda xatolik: {e}")

if __name__ == '__main__':
    try:
        python_path, pip_path = setup_virtual_env()
        check_directories()
        setup_env()
        install_requirements(pip_path)

        bot_thread = Thread(target=run_bot, args=(python_path,))
        web_thread = Thread(target=run_webapp, args=(python_path,))

        bot_thread.start()
        time.sleep(2)
        web_thread.start()

        bot_thread.join()
        web_thread.join()

    except Exception as e:
        print(f"❌ Umumiy xatolik yuz berdi: {e}")
        sys.exit(1)
