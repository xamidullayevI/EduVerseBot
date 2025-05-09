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

def allowed_file(filename):
    """Fayl kengaytmasini tekshirish"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def generate_filename(filename):
    """Xavfsiz fayl nomi yaratish"""
    ext = filename.rsplit('.', 1)[1].lower()
    return f"{uuid.uuid4().hex}.{ext}"

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
                'title': t.title
            } for t in all_topics])

    except Exception as e:
        logger.error(f"Topics API xatolik: {e}")
        db.session.rollback()
        return jsonify({'error': 'Server xatolik'}), 500

# --- API: 1ta topic tafsiloti ---
@app.route('/api/topics/<int:topic_id>')
def topic_detail(topic_id):
    try:
        t = Topic.query.get_or_404(topic_id)
        return jsonify({
            'id': t.id,
            'title': t.title,
            'structure': t.structure,
            'examples': t.examples,
            'image_url': t.image_url,
            'video_url': t.video_url
        })
    except Exception as e:
        logger.error(f"Topic detail xatolik: {e}")
        return jsonify({'error': 'Server xatolik'}), 500

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
        return jsonify({'error': 'Server xatolik'}), 500

# --- HTML sahifa uchun route ---
@app.route('/')
def index():
    return render_template('index.html')

# --- Statistika endpoint ---
@app.route('/api/stats')
def stats():
    users_count = Contact.query.count()
    return jsonify({'users_count': users_count})

# --- App ishga tushishi ---
with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run(debug=True)
