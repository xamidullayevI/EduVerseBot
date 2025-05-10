import subprocess
import sys
import os
import shutil
from threading import Thread
import time
from dotenv import load_dotenv
import signal
import atexit
import logging
from logging.handlers import RotatingFileHandler

# Log yozish sozlamalari
if not os.path.exists('logs'):
    os.makedirs('logs')

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[
        RotatingFileHandler('logs/main.log', maxBytes=10240, backupCount=10),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
processes = []

def cleanup():
    """Cleanup function to terminate all processes"""
    logger.info("Cleaning up processes...")
    for process in processes:
        if process and process.poll() is None:
            logger.info(f"Terminating process {process.pid}")
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                logger.warning(f"Process {process.pid} did not terminate gracefully, killing...")
                process.kill()
                process.wait()

def signal_handler(signum, frame):
    """Handle termination signals"""
    logger.info(f"Received signal {signum}, shutting down...")
    cleanup()
    sys.exit(0)

def setup_virtual_env():
    """Virtual environment setup"""
    venv_name = os.path.join(BASE_DIR, "venv")
    if not os.path.exists(venv_name):
        logger.info("Creating virtual environment...")
        subprocess.run([sys.executable, '-m', 'venv', venv_name], check=True)
        logger.info("Virtual environment created successfully")
    
    if sys.platform == "win32":
        python_path = os.path.join(venv_name, "Scripts", "python.exe")
        pip_path = os.path.join(venv_name, "Scripts", "pip.exe")
    else:
        python_path = os.path.join(venv_name, "bin", "python")
        pip_path = os.path.join(venv_name, "bin", "pip")
    
    return python_path, pip_path

def check_directories():
    """Check required directories"""
    required_dirs = ['BOT', 'WEB-APP', 'logs']
    for dir_name in required_dirs:
        dir_path = os.path.join(BASE_DIR, dir_name)
        if not os.path.exists(dir_path):
            os.makedirs(dir_path)
            logger.info(f"Created directory: {dir_path}")

def setup_env():
    """Setup environment files"""
    logger.info("Setting up environment files...")
    env_source = os.path.join(BASE_DIR, '.env')
    bot_env_path = os.path.join(BASE_DIR, 'BOT', '.env')
    web_env_path = os.path.join(BASE_DIR, 'WEB-APP', '.env')

    if not os.path.exists(env_source):
        raise FileNotFoundError("Main .env file not found!")

    shutil.copy(env_source, bot_env_path)
    shutil.copy(env_source, web_env_path)
    logger.info("Environment files set up successfully")

def install_requirements(pip_path):
    """Install required packages"""
    logger.info("Installing requirements...")
    try:
        subprocess.run([pip_path, 'install', '-r', os.path.join(BASE_DIR, 'requirements.txt')], check=True)
        logger.info("Requirements installed successfully")
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to install requirements: {e}")
        raise

def run_process(name, command, cwd):
    """Run a process with proper error handling"""
    try:
        logger.info(f"Starting {name}...")
        process = subprocess.Popen(
            command,
            cwd=cwd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True
        )
        processes.append(process)
        return process
    except Exception as e:
        logger.error(f"Failed to start {name}: {e}")
        raise

def monitor_process(process, name, command, cwd):
    """Monitor a process and restart if it fails"""
    while True:
        if process.poll() is not None:
            logger.error(f"{name} stopped unexpectedly with code {process.returncode}")
            logger.info(f"Restarting {name}...")
            # Restart process
            new_process = run_process(name, command, cwd)
            process = new_process
        time.sleep(5)

if __name__ == '__main__':
    try:
        # Signal handlers
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        atexit.register(cleanup)

        # Setup
        python_path, pip_path = setup_virtual_env()
        check_directories()
        setup_env()
        install_requirements(pip_path)

        # Start processes
        bot_command = [python_path, 'run.py']
        bot_cwd = os.path.join(BASE_DIR, 'BOT')
        bot_process = run_process("Bot", bot_command, bot_cwd)
        time.sleep(2)  # Wait for bot to start
        web_command = [python_path, 'app.py']
        web_cwd = os.path.join(BASE_DIR, 'WEB-APP')
        web_process = run_process("Web App", web_command, web_cwd)

        # Start monitoring threads
        Thread(target=monitor_process, args=(bot_process, "Bot", bot_command, bot_cwd), daemon=True).start()
        Thread(target=monitor_process, args=(web_process, "Web App", web_command, web_cwd), daemon=True).start()

        # Keep main thread alive
        while True:
            time.sleep(1)

    except Exception as e:
        logger.error(f"Fatal error: {e}")
        cleanup()
        sys.exit(1)
