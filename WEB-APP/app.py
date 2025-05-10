from flask import Flask, jsonify, render_template, request, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from flask_caching import Cache
from flask_socketio import SocketIO, emit
import os
from sqlalchemy import create_engine, text
from sqlalchemy_utils import database_exists, create_database
from dotenv import load_dotenv
import pymysql
import logging
from logging.handlers import RotatingFileHandler
from werkzeug.utils import secure_filename
import uuid
from datetime import datetime
import traceback
import re
from functools import wraps
import eventlet

# Load environment variables
load_dotenv()
pymysql.install_as_MySQLdb()

# App initialization
app = Flask(__name__)

# Database configuration
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    'pool_size': 10,
    'pool_timeout': 30,
    'pool_recycle': 1800,
    'max_overflow': 2
}

# Cache configuration
cache = Cache(app, config={
    'CACHE_TYPE': 'simple',
    'CACHE_DEFAULT_TIMEOUT': 300
})

# CORS configuration
CORS(app)

# WebSocket configuration
socketio = SocketIO(
    app,
    async_mode='eventlet',
    ping_timeout=60,
    ping_interval=25,
    cors_allowed_origins="*",
    max_http_buffer_size=10e6
)

# Static files configuration
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
UPLOAD_FOLDER = os.path.join(app.static_folder, 'uploads')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Ensure upload directory exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Logging configuration
if not os.path.exists('logs'):
    os.makedirs('logs')

logging.basicConfig(
    handlers=[
        RotatingFileHandler(
            'logs/webapp.log',
            maxBytes=10485760,  # 10MB
            backupCount=5
        ),
        logging.StreamHandler()
    ],
    level=logging.INFO,
    format='%(asctime)s %(levelname)s: %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize database
db = SQLAlchemy(app)

# --- Baza avtomatik yaratiladi ---
db_url = app.config['SQLALCHEMY_DATABASE_URI']
engine = create_engine(db_url)
if not database_exists(engine.url):
    create_database(engine.url)
    logger.info(f"Baza yaratildi: {engine.url}")
else:
    logger.info(f"Baza allaqachon mavjud: {engine.url}")

# --- Modellar ---
class Contact(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.BigInteger, unique=True)
    first_name = db.Column(db.String(255))
    last_name = db.Column(db.String(255))
    phone_number = db.Column(db.String(32))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Topic(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255))
    structure = db.Column(db.Text)
    examples = db.Column(db.Text)
    image_url = db.Column(db.String(255))
    video_url = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class News(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255))
    content = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Feedback(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.BigInteger, nullable=True)
    user_name = db.Column(db.String(255), nullable=True)
    topic_id = db.Column(db.Integer)
    comment = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

def allowed_file(filename):
    """Fayl kengaytmasini tekshirish"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in {'png', 'jpg', 'jpeg', 'gif', 'mp4', 'mov'}

def generate_filename(filename):
    """Xavfsiz fayl nomi yaratish"""
    ext = filename.rsplit('.', 1)[1].lower()
    return f"{uuid.uuid4().hex}.{ext}"

def format_sentences(text):
    if not text:
        return ""
    sentences = re.split(r'(?<=[.!?:])(?:\s*|\n+)', text.strip())
    formatted = []
    auto_num = 1
    for sentence in sentences:
        sentence = sentence.strip()
        if not sentence:
            continue
        if sentence.endswith(':'):
            main = sentence[:-1].strip()
            out = f'<b>{main}</b>:'
        else:
            sentence = re.sub(r'^\d+\.\s*', '', sentence)
            out = f'{auto_num}. {sentence}'
            auto_num += 1
        formatted.append(out)
    return '\n'.join(formatted)

# API key tekshiruv
def require_api_key(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        api_key = request.headers.get('X-API-Key')
        if not api_key or api_key != os.getenv('API_KEY'):
            return jsonify({'error': 'Invalid API key'}), 401
        return f(*args, **kwargs)
    return decorated

@app.after_request
def add_header(response):
    """Add headers to optimize caching and performance."""
    if 'Cache-Control' not in response.headers:
        if request.path.startswith('/static/'):
            response.headers['Cache-Control'] = 'public, max-age=31536000'
        else:
            response.headers['Cache-Control'] = 'public, max-age=300'
    response.headers['Vary'] = 'Accept-Encoding'
    return response

@app.errorhandler(404)
def not_found_error(error):
    return jsonify({'error': 'Not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    logger.error(f"Server Error: {error}")
    return jsonify({'error': 'Internal server error'}), 500

@app.errorhandler(Exception)
def handle_exception(e):
    logger.error(f"Unhandled Exception: {str(e)}")
    logger.error(traceback.format_exc())
    return jsonify({'error': 'Internal server error'}), 500

# Health check endpoint
@app.route('/health')
@cache.cached(timeout=60)
def health_check():
    try:
        db.session.execute('SELECT 1')
        db.session.commit()
        return jsonify({
            'status': 'healthy',
            'database': 'connected',
            'timestamp': str(datetime.now())
        })
    except Exception as e:
        logger.error(f'Health check failed: {e}')
        return jsonify({
            'status': 'unhealthy',
            'error': str(e)
        }), 500

# --- API: contact saqlash ---
@app.route('/api/contacts', methods=['POST'])
def save_contact():
    try:
        data = request.json
        if not data:
            logger.error("Contact saqlash: Ma'lumotlar yo'q")
            return jsonify({'error': 'Ma\'lumotlar yo\'q'}), 400

        user_id = data.get('user_id')
        first_name = data.get('first_name')
        last_name = data.get('last_name')
        phone_number = data.get('phone_number')

        logger.info(f"Contact saqlash so'rovi: user_id={user_id}, first_name={first_name}, phone={phone_number}")

        if not all([user_id, first_name, phone_number]):
            missing_fields = []
            if not user_id: missing_fields.append('user_id')
            if not first_name: missing_fields.append('first_name')
            if not phone_number: missing_fields.append('phone_number')
            
            error_msg = f"Majburiy maydonlar to'ldirilmagan: {', '.join(missing_fields)}"
            logger.error(f"Contact saqlash: {error_msg}")
            return jsonify({'error': error_msg}), 400

        try:
            db.session.execute(text('SELECT 1'))
            logger.info("Baza ulanishi muvaffaqiyatli")

            contact = Contact.query.filter_by(user_id=user_id).first()
            if not contact:
                contact = Contact(
                    user_id=user_id,
                    first_name=first_name,
                    last_name=last_name,
                    phone_number=phone_number
                )
                db.session.add(contact)
                logger.info(f"Yangi contact qo'shildi: {user_id}")
            else:
                contact.first_name = first_name
                contact.last_name = last_name
                contact.phone_number = phone_number
                logger.info(f"Contact yangilandi: {user_id}")

            db.session.commit()
            logger.info("Contact muvaffaqiyatli saqlandi")
            return jsonify({'status': 'ok'})

        except Exception as db_error:
            logger.error(f"Baza xatolik: {str(db_error)}")
            db.session.rollback()
            return jsonify({
                'error': 'Ma\'lumotlar bazasi xatolik',
                'details': str(db_error)
            }), 500

    except Exception as e:
        logger.error(f"Contact saqlash xatolik: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({
            'error': 'Server xatolik',
            'details': str(e)
        }), 500

# --- API: barcha topics ---
@app.route('/api/topics', methods=['GET', 'POST'])
def topics():
    try:
        if request.method == 'POST':
            data = request.json
            if not data:
                return jsonify({'error': 'Ma\'lumotlar yo\'q'}), 400

            if not all([data.get('title'), data.get('structure'), data.get('examples')]):
                return jsonify({'error': 'Majburiy maydonlar to\'ldirilmagan'}), 400

            topic = Topic(
                title=data.get('title'),
                structure=data.get('structure'),
                examples=data.get('examples'),
                image_url=data.get('image_url'),
                video_url=data.get('video_url')
            )
            db.session.add(topic)
            db.session.commit()
            logger.info(f"Yangi mavzu qo'shildi: {topic.title}")
            return jsonify({'status': 'ok'})
        else:
            all_topics = Topic.query.order_by(Topic.created_at.desc()).all()
            return jsonify([{
                'id': t.id,
                'title': t.title,
                'structure': format_sentences(t.structure),
                'examples': format_sentences(t.examples),
            } for t in all_topics])

    except Exception as e:
        logger.error(f"Topics API xatolik: {e}")
        logger.error(traceback.format_exc())
        db.session.rollback()
        return jsonify({'error': 'Server xatolik', 'details': str(e)}), 500

# --- API: 1ta topic tafsiloti ---
@app.route('/api/topics/<int:topic_id>')
def topic_detail(topic_id):
    try:
        t = Topic.query.get_or_404(topic_id)
        return jsonify({
            'id': t.id,
            'title': t.title,
            'structure': format_sentences(t.structure),
            'examples': format_sentences(t.examples),
            'image_url': t.image_url,
            'video_url': t.video_url
        })
    except Exception as e:
        logger.error(f"Topic detail xatolik: {e}")
        logger.error(traceback.format_exc())
        return jsonify({'error': 'Server xatolik', 'details': str(e)}), 500

# --- API: topic o'chirish ---
@app.route('/api/topics/<int:topic_id>', methods=['DELETE'])
def delete_topic(topic_id):
    try:
        topic = Topic.query.get_or_404(topic_id)
        db.session.delete(topic)
        db.session.commit()
        return jsonify({'status': 'deleted'})
    except Exception as e:
        db.session.rollback()
        logger.error(f"Topic o'chirish xatolik: {e}")
        logger.error(traceback.format_exc())
        return jsonify({'error': str(e)}), 500

# --- Fayl yuklash endpoint ---
@app.route('/api/upload', methods=['POST'])
def upload_file():
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'Fayl yuborilmagan'}), 400

        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'Fayl nomi yo\'q'}), 400

        if not allowed_file(file.filename):
            return jsonify({'error': 'Ruxsat etilmagan fayl turi'}), 400

        filename = generate_filename(file.filename)
        save_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(save_path)
        url = f"/static/uploads/{filename}"
        
        logger.info(f"Fayl yuklandi: {filename}")
        return jsonify({'url': url})

    except Exception as e:
        logger.error(f"Fayl yuklash xatolik: {e}")
        logger.error(traceback.format_exc())
        return jsonify({'error': 'Server xatolik', 'details': str(e)}), 500

# --- HTML sahifa uchun route ---
@app.route('/')
def index():
    return render_template('index.html', topic=None)

# --- Statistika endpoint ---
@app.route('/api/stats')
def stats():
    users_count = Contact.query.count()
    stats_data = {'users_count': users_count}
    socketio.emit('stats_update', stats_data)
    return jsonify(stats_data)

# --- API: contact mavjudligini tekshirish ---
@app.route('/api/contacts/<int:user_id>')
def get_contact(user_id):
    contact = Contact.query.filter_by(user_id=user_id).first()
    if contact:
        return jsonify({'status': 'ok'})
    return jsonify({'error': 'Not found'}), 404

# --- API: barcha yangiliklar ---
@app.route('/api/news', methods=['GET', 'POST'])
def get_news():
    try:
        if request.method == 'POST':
            data = request.json
            if not data or not data.get('title'):
                return jsonify({'error': 'Sarlavha kiritilmagan'}), 400
            
            news = News(
                title=data.get('title'),
                content=data.get('content', '')
            )
            db.session.add(news)
            db.session.commit()
            
            # Emit socket event for new news
            socketio.emit('news_update', {
                'id': news.id,
                'title': news.title,
                'content': news.content,
                'created_at': news.created_at.strftime('%Y-%m-%d')
            })
            
            logger.info(f"Yangi yangilik qo'shildi: {news.title}")
            return jsonify({'status': 'ok'})
        else:
            news = News.query.order_by(News.created_at.desc()).limit(5).all()
            return jsonify([
                {
                    'id': n.id,
                    'title': n.title,
                    'content': n.content,
                    'created_at': n.created_at.strftime('%Y-%m-%d')
                } for n in news
            ])
    except Exception as e:
        logger.error(f"News API xatolik: {e}")
        logger.error(traceback.format_exc())
        db.session.rollback()
        return jsonify({'error': 'Server xatolik', 'details': str(e)}), 500

# --- API: yangilikni o'chirish ---
@app.route('/api/news/<int:news_id>', methods=['DELETE'])
def delete_news(news_id):
    try:
        news = News.query.get_or_404(news_id)
        db.session.delete(news)
        db.session.commit()
        return jsonify({'status': 'deleted'})
    except Exception as e:
        db.session.rollback()
        logger.error(f"Yangilik o'chirish xatolik: {e}")
        logger.error(traceback.format_exc())
        return jsonify({'error': str(e)}), 500

# --- API: barcha feedbacklar va yangi sharh qabul qilish ---
@app.route('/api/feedback', methods=['GET', 'POST'])
def feedback():
    if request.method == 'POST':
        data = request.json
        print('FEEDBACK POST DATA:', data)
        user_id = data.get('user_id')
        topic_id = data.get('topic_id')
        comment = data.get('comment')
        user_name = None
        try:
            user_id_int = int(user_id)
            user_id = user_id_int
        except Exception:
            user_name = user_id
            user_id = None
        try:
            topic_id_int = int(topic_id)
            topic_id = topic_id_int
        except Exception:
            print('FEEDBACK ERROR: topic_id not integer')
            return jsonify({'error': "Mavzu ID noto'g'ri"}), 400
        if not all([topic_id, comment]) or (not user_id and not user_name):
            print('FEEDBACK ERROR: Majburiy maydonlar yo\'q')
            return jsonify({'error': 'Majburiy maydonlar toldirilmagan'}), 400
        try:
            fb = Feedback(user_id=user_id, user_name=user_name, topic_id=topic_id, comment=comment)
            db.session.add(fb)
            db.session.commit()
            
            # Emit socket event for new feedback
            socketio.emit('feedback_update', {
                'id': fb.id,
                'user': user_name or (Contact.query.filter_by(user_id=user_id).first().first_name if user_id else 'Foydalanuvchi'),
                'topic': Topic.query.get(topic_id).title,
                'comment': comment,
                'created_at': fb.created_at.strftime('%Y-%m-%d')
            })
            
            print('FEEDBACK SUCCESS')
            return jsonify({'status': 'ok'})
        except Exception as e:
            import traceback
            db.session.rollback()
            print('FEEDBACK ERROR:', e)
            print(traceback.format_exc())
            logger.error(f'FEEDBACK ERROR: {e}')
            logger.error(traceback.format_exc())
            return jsonify({'error': 'Sharh saqlanmadi', 'details': str(e)}), 500
    else:
        feedbacks = Feedback.query.order_by(Feedback.created_at.desc()).limit(5).all()
        result = []
        for f in feedbacks:
            if f.user_id:
                user = Contact.query.filter_by(user_id=f.user_id).first()
                user_display = user.first_name if user else 'Foydalanuvchi'
            else:
                user_display = f.user_name or 'Foydalanuvchi'
            topic = Topic.query.filter_by(id=f.topic_id).first()
            result.append({
                'id': f.id,
                'user': user_display,
                'topic': topic.title if topic else 'Mavzu',
                'comment': f.comment,
                'created_at': f.created_at.strftime('%Y-%m-%d')
            })
        return jsonify(result)

# WebSocket handlers
@socketio.on('connect')
def handle_connect():
    logger.info("Client connected")
    emit('connected', {'data': 'Connected'})

@socketio.on('disconnect')
def handle_disconnect():
    logger.info("Client disconnected")

# --- App ishga tushishi ---
with app.app_context():
    db.create_all()

if __name__ == '__main__':
    socketio.run(app, debug=False)
