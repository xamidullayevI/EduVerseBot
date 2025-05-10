web: gunicorn --worker-class eventlet -w 1 --bind=0.0.0.0:$PORT --timeout=120 --keep-alive=65 --max-requests=1000 --max-requests-jitter=50 --log-level=info WEB-APP.app:app
bot: python BOT/run.py