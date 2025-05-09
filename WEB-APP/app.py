from flask import Flask, jsonify, render_template, request, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
import os
from sqlalchemy import create_engine, text
from sqlalchemy_utils import database_exists, create_database
from dotenv import load_dotenv
import pymysql
import logging
from werkzeug.utils import secure_filename
import uuid
from datetime import datetime
import traceback
import re

# Log yozish sozlamalari
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    filename='webapp.log'
)
logger = logging.getLogger(__name__)

load_dotenv()
pymysql.install_as_MySQLdb()

app = Flask(__name__)

# Fayl yuklash sozlamalari
UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), 'static', 'uploads')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'mp4', 'mov'}
MAX_CONTENT_LENGTH = 50 * 1024 * 1024  # 50MB

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = MAX_CONTENT_LENGTH

# --- Bazani sozlash ---
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'mysql://user:password@localhost:3306/eduverse')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# --- Baza avtomatik yaratiladi ---
db_url = app.config['SQLALCHEMY_DATABASE_URI']
engine = create_engine(db_url)
if not database_exists(engine.url):
    create_database(engine.url)
    logger.info(f"Baza yaratildi: {engine.url}")
else:
    logger.info(f"Baza allaqachon mavjud: {engine.url}")

# --- Baza ulanishi ---
db = SQLAlchemy(app)
CORS(app)

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
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def generate_filename(filename):
    """Xavfsiz fayl nomi yaratish"""
    ext = filename.rsplit('.', 1)[1].lower()
    return f"{uuid.uuid4().hex}.{ext}"

def format_sentences(text):
    if not text:
        return ""
    # . ! ? : dan keyin yangi qator yoki bo'shliq bo'lsa ham bo'lib yuboradi
    sentences = re.split(r'(?<=[.!?:])(?:\s*|\n+)', text.strip())
    formatted = []
    auto_num = 1
    for sentence in sentences:
        sentence = sentence.strip()
        if not sentence:
            continue
        # Qalin qilish: oxirida : bo'lsa, oxirgi : oldini qalin qilamiz va raqam ham qo'shilmaydi
        if sentence.endswith(':'):
            main = sentence[:-1].strip()
            out = f'<b>{main}</b>:'
        else:
            # Gap boshida raqam va nuqta bo'lsa, olib tashlaymiz
            sentence = re.sub(r'^\d+\.\s*', '', sentence)
            out = f'{auto_num}. {sentence}'
            auto_num += 1
        formatted.append(out)
    return '\n'.join(formatted)

@app.errorhandler(Exception)
def handle_exception(e):
    logger.error(f"Unhandled Exception: {str(e)}")
    logger.error(traceback.format_exc())
    # Foydalanuvchiga to'liq xatolikni ko'rsatish (faqat test uchun!)
    return f"<pre>{traceback.format_exc()}</pre>", 500

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
            # Baza ulanishini tekshirish
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
    return jsonify({'users_count': users_count})

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
        # user_id ni int ga o'gir
        try:
            user_id_int = int(user_id)
            user_id = user_id_int
        except Exception:
            user_name = user_id
            user_id = None
        # topic_id ni int ga o'gir
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

# --- App ishga tushishi ---
with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run(debug=True)
