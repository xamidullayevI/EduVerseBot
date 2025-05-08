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
│   ├── templates/         # HTML shablonlar
│   ├── .env              # Web ilova sozlamalari
│   └── app.py            # Flask ilovasi
└── requirements.txt       # Kerakli kutubxonalar
```

## O'rnatish va sozlash

### 1. Kerakli dasturlar

- Python 3.8 yoki undan yuqori versiya
- MySQL server
- Git

### 2. Loyihani yuklab olish

```bash
git clone https://github.com/your-username/eduverse.git
cd eduverse
```

### 3. Virtual muhit yaratish va kutubxonalarni o'rnatish

```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac uchun
venv\Scripts\activate     # Windows uchun

pip install -r requirements.txt
```

### 4. Ma'lumotlar bazasini sozlash

1. MySQL da yangi bazani yarating:
```sql
CREATE DATABASE eduverse CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

2. `.env` fayllarini sozlang:
   - `BOT/.env` va `WEB-APP/.env` fayllarida `DATABASE_URL` ni o'zgartiring
   - `BOT_TOKEN` ni [@BotFather](https://t.me/BotFather) dan oling
   - `ADMINS` ga o'zingizning Telegram ID raqamingizni kiriting

### 5. Web ilovani sozlash

1. Web ilovani joylashtirish uchun:
   - [Heroku](https://heroku.com)
   - [PythonAnywhere](https://www.pythonanywhere.com)
   - yoki boshqa hosting xizmatidan foydalaning

2. Web ilova URL manzilini `.env` fayllarida `WEBAPP_URL` ga kiriting

### 6. Botni ishga tushirish

```bash
python main.py
```

## Bot buyruqlari

### Admin uchun:
- `/start` - Admin panelni ochish
- `/new` - Yangi mavzu kiritish
- `/confirm` - Mavzuni saqlash
- `/skip` - Rasm yoki videoni o'tkazib yuborish

### Foydalanuvchi uchun:
- `/start` - Botni ishga tushirish va contact ma'lumotlarini yuborish
- Web App tugmasi - Mavzularni ko'rish

## Web ilova funksiyalari

- Barcha mavzular ro'yxati
- Har bir mavzu uchun:
  - Tuzilma
  - Misollar
  - Rasm
  - Video
- Mobil qurilmalarga moslashgan dizayn

## Xavfsizlik

- Bot faqat admin ID dan kelgan so'rovlarni qabul qiladi
- Web ilova HTTPS orqali ishlaydi
- Foydalanuvchi ma'lumotlari xavfsiz saqlanadi

## Yordam

Agar muammolar yuzaga kelsa:
1. [Issues](https://github.com/your-username/eduverse/issues) bo'limida xabar bering
2. Telegram orqali bog'laning: [@your_username](https://t.me/your_username)

## Litsenziya

MIT License - [LICENSE](LICENSE) faylida batafsil ma'lumot 