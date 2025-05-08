from flask import Flask, jsonify, render_template, request
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
import os
from sqlalchemy import create_engine
from sqlalchemy_utils import database_exists, create_database
from dotenv import load_dotenv  # 👉 .env faylni o‘qish uchun kerak
import pymysql

load_dotenv()  # 👉 .env fayldagi o‘zgaruvchilarni yuklaydi
pymysql.install_as_MySQLdb()

app = Flask(__name__)

# --- Bazani sozlash ---
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'mysql://user:password@localhost:3306/eduverse')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# --- Baza avtomatik yaratiladi ---
db_url = app.config['SQLALCHEMY_DATABASE_URI']
engine = create_engine(db_url)
if not database_exists(engine.url):
    create_database(engine.url)
    print(f"Baza yaratildi: {engine.url}")
else:
    print(f"Baza allaqachon mavjud: {engine.url}")

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

class Topic(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255))
    structure = db.Column(db.Text)
    examples = db.Column(db.Text)
    image_url = db.Column(db.String(255))
    video_url = db.Column(db.String(255))

# --- API: contact saqlash ---
@app.route('/api/contacts', methods=['POST'])
def save_contact():
    data = request.json
    user_id = data.get('user_id')
    first_name = data.get('first_name')
    last_name = data.get('last_name')
    phone_number = data.get('phone_number')

    contact = Contact.query.filter_by(user_id=user_id).first()
    if not contact:
        contact = Contact(user_id=user_id, first_name=first_name, last_name=last_name, phone_number=phone_number)
        db.session.add(contact)
    else:
        contact.first_name = first_name
        contact.last_name = last_name
        contact.phone_number = phone_number
    db.session.commit()
    return jsonify({'status': 'ok'})

# --- API: barcha topics ---
@app.route('/api/topics', methods=['GET', 'POST'])
def topics():
    if request.method == 'POST':
        data = request.json
        topic = Topic(
            title=data.get('title'),
            structure=data.get('structure'),
            examples=data.get('examples'),
            image_url=data.get('image_url'),
            video_url=data.get('video_url')
        )
        db.session.add(topic)
        db.session.commit()
        return jsonify({'status': 'ok'})
    else:
        all_topics = Topic.query.all()
        return jsonify([{
            'id': t.id,
            'title': t.title
        } for t in all_topics])

# --- API: 1ta topic tafsiloti ---
@app.route('/api/topics/<int:topic_id>')
def topic_detail(topic_id):
    t = Topic.query.get_or_404(topic_id)
    return jsonify({
        'id': t.id,
        'title': t.title,
        'structure': t.structure,
        'examples': t.examples,
        'image_url': t.image_url,
        'video_url': t.video_url
    })

# --- HTML sahifa uchun route ---
@app.route('/')
def index():
    return render_template('index.html')

# --- App ishga tushishi ---
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
