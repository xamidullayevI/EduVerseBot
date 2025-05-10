# EduVerse - Ingliz tili o'rganish platformasi

EduVerse - bu Telegram bot va Web ilova orqali ingliz tili grammatik mavzularini o'rganish platformasi. Adminlar mavzularni rasm, video va misollar bilan kiritadi, foydalanuvchilar esa chiroyli va interaktiv tarzda o'rganishlari mumkin.

## Loyiha tuzilishi

```
eduverse/
├── BOT/                    # Telegram bot kodi
│   ├── handlers/           # Bot handerlari
│   ├── .env               # Bot sozlamalari
│   ├── bot.py             # Bot asosiy kodi
│   └── run.py             # Bot ishga tushirish
├── WEB-APP/               # Web ilova kodi
│   ├── static/            # Statik fayllar
│   │   └── uploads/       # Yuklangan fayllar
│   ├── templates/         # HTML shablonlar
│   ├── .env              # Web ilova sozlamalari
│   └── app.py            # Flask ilovasi
├── logs/                  # Log fayllar
├── .env                  # Asosiy sozlamalar
├── .gitignore           # Git ignore fayllar
├── Procfile             # Heroku sozlamalari
├── requirements.txt     # Kerakli kutubxonalar
├── runtime.txt         # Python versiyasi
└── main.py             # Asosiy ishga tushirish fayli
```

## O'rnatish va sozlash

### 1. Kerakli dasturlar

- Python 3.9 yoki undan yuqori versiya
- MySQL server 8.0 yoki undan yuqori versiya
- Git
- pip (Python paket menejeri)

### 2. Loyihani yuklab olish

```bash
git clone https://github.com/your-username/eduverse.git
cd eduverse
```

### 3. Virtual muhit yaratish va kutubxonalarni o'rnatish

```bash
# Virtual muhit yaratish
python -m venv venv

# Virtual muhitni faollashtirish
# Windows uchun:
venv\Scripts\activate
# Linux/Mac uchun:
source venv/bin/activate

# Kerakli kutubxonalarni o'rnatish
pip install -r requirements.txt
```

### 4. Ma'lumotlar bazasini sozlash

1. MySQL da yangi bazani yarating:

```sql
CREATE DATABASE eduverse CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

2. `.env` fayllarini sozlang:
   - Asosiy papkadagi `.env` faylini nusxa ko'chiring:
     ```bash
     cp .env BOT/.env
     cp .env WEB-APP/.env
     ```
   - Har bir `.env` faylida quyidagi o'zgaruvchilarni sozlang:
     ```
     # Bot sozlamalari
     BOT_TOKEN=your_bot_token_here
     ADMINS=your_telegram_id

     # Web App sozlamalari
     DATABASE_URL=mysql://username:password@localhost:3306/eduverse

     # Umumiy sozlamalar
     API_URL=http://localhost:5000
     WEBAPP_URL=http://localhost:5000

     # Xavfsizlik sozlamalari
     SECRET_KEY=your_secret_key_here
     API_KEY=your_api_key_here
     ```

### 5. Web ilovani sozlash

1. Web ilovani joylashtirish uchun quyidagi hosting xizmatlaridan birini tanlang:

   - [Heroku](https://heroku.com)
   - [PythonAnywhere](https://www.pythonanywhere.com)
   - [Railway](https://railway.app)
   - [Render](https://render.com)

2. Web ilova URL manzilini `.env` fayllarida `WEBAPP_URL` ga kiriting

### 6. Botni ishga tushirish

```bash
# Barcha komponentlarni bir vaqtda ishga tushirish
python main.py

# Yoki alohida ishga tushirish
# Bot uchun:
python BOT/run.py

# Web ilova uchun:
python WEB-APP/app.py
```

## API Documentation

### Endpoints

#### GET /api/topics
Returns list of all topics

**Response:**
```json
[
  {
    "id": 1,
    "title": "Present Simple",
    "structure": "Formatted structure text",
    "examples": "Formatted examples text"
  }
]
```

#### POST /api/topics
Creates new topic

**Request:**
```json
{
  "title": "Topic title",
  "structure": "Topic structure",
  "examples": "Topic examples",
  "image_url": "Optional image URL",
  "video_url": "Optional video URL"
}
```

#### GET /api/topics/{id}
Returns topic details

**Response:**
```json
{
  "id": 1,
  "title": "Topic title",
  "structure": "Formatted structure text",
  "examples": "Formatted examples text",
  "image_url": "Image URL",
  "video_url": "Video URL"
}
```

#### DELETE /api/topics/{id}
Deletes topic

**Response:**
```json
{
  "status": "deleted"
}
```

## Xavfsizlik

- Bot faqat admin ID dan kelgan so'rovlarni qabul qiladi
- Web ilova HTTPS orqali ishlaydi
- Foydalanuvchi ma'lumotlari xavfsiz saqlanadi
- Fayl yuklash cheklovlari mavjud
- SQL injection himoyasi
- XSS himoyasi
- CSRF himoyasi
- API key authentication
- Rate limiting
- Input validation
- Secure headers
- CORS configuration

## Yordam

Agar muammolar yuzaga kelsa:

1. [Issues](https://github.com/your-username/eduverse/issues) bo'limida xabar bering
2. Telegram orqali bog'laning: [@xamidullayev_i](https://t.me/xamidullayev_i)
3. Email orqali: ihamidullayev01@gmail.com

## Litsenziya

MIT License - [LICENSE](LICENSE) faylida batafsil ma'lumot

## Mualliflar

- Islombek Xamidullayev - [GitHub](https://github.com/xamidullayev)

## Minnatdorchilik

- [Python Telegram Bot](https://github.com/python-telegram-bot/python-telegram-bot)
- [Flask](https://github.com/pallets/flask)
- [SQLAlchemy](https://github.com/sqlalchemy/sqlalchemy)
- [Bootstrap](https://getbootstrap.com)
