web: gunicorn --worker-class eventlet -w 1 --threads 2 --bind=0.0.0.0:$PORT --timeout=120 --access-logfile=- --error-logfile=- WEB-APP.app:app
bot: python BOT/run.py 