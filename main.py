import subprocess
import sys
import os
import shutil
from threading import Thread
import time
from dotenv import load_dotenv
import signal
import atexit

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
processes = []

def cleanup():
    """Cleanup function to terminate all processes"""
    for process in processes:
        if process and process.poll() is None:
            process.terminate()
            process.wait()

def signal_handler(signum, frame):
    """Handle termination signals"""
    print("\n⚠️ Dastur to'xtatilmoqda...")
    cleanup()
    sys.exit(0)

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
    print("📥 Kerakli kutubxonalar o'rnatilmoqda...")
    subprocess.run([pip_path, 'install', '-r', os.path.join(BASE_DIR, 'requirements.txt')])
    print("✅ Barcha kutubxonalar o'rnatildi!")

def run_bot(python_path):
    try:
        print("🚀 Bot ishga tushmoqda...")
        process = subprocess.Popen([python_path, 'run.py'], cwd=os.path.join(BASE_DIR, 'BOT'))
        processes.append(process)
        return process
    except Exception as e:
        print(f"❌ Bot ishga tushirishda xatolik: {e}")
        return None

def run_webapp(python_path):
    try:
        print("🌐 Web app ishga tushmoqda...")
        process = subprocess.Popen([python_path, 'app.py'], cwd=os.path.join(BASE_DIR, 'WEB-APP'))
        processes.append(process)
        return process
    except Exception as e:
        print(f"❌ Web app ishga tushirishda xatolik: {e}")
        return None

if __name__ == '__main__':
    try:
        # Signal handlers
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        atexit.register(cleanup)

        python_path, pip_path = setup_virtual_env()
        check_directories()
        setup_env()
        install_requirements(pip_path)

        bot_process = run_bot(python_path)
        if not bot_process:
            raise Exception("Bot ishga tushirilmadi!")

        time.sleep(2)  # Bot ishga tushishi uchun kutish

        web_process = run_webapp(python_path)
        if not web_process:
            raise Exception("Web app ishga tushirilmadi!")

        # Monitor processes
        while True:
            if bot_process.poll() is not None:
                print("❌ Bot to'xtadi!")
                break
            if web_process.poll() is not None:
                print("❌ Web app to'xtadi!")
                break
            time.sleep(1)

    except Exception as e:
        print(f"❌ Umumiy xatolik yuz berdi: {e}")
        cleanup()
        sys.exit(1)
