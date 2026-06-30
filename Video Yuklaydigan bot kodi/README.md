# 🎬 Telegram Video Downloader Bot

Har qanday ochiq linkdan MP4 video yuklab beradigan Telegram bot.

---

## ✨ Imkoniyatlar

- 🎬 YouTube, TikTok, Instagram, Twitter/X, Facebook va 1000+ saytdan video yuklab olish
- 📢 Majburiy obuna kanallari (foydalanuvchi obuna bo'lmasa botdan foydalana olmaydi)
- 👤 Admin panel
- 📣 Barcha userlarga broadcast (ommaviy xabar) yuborish
- 📊 Statistika ko'rish

---

## 🚀 O'rnatish

### 1. Talablar
- Python 3.10+
- ffmpeg (video konvertatsiya uchun)

### 2. ffmpeg o'rnatish

**Ubuntu/Debian:**
```bash
sudo apt update && sudo apt install ffmpeg -y
```

**Windows:**
https://ffmpeg.org/download.html dan yuklab, PATH ga qo'shing.

### 3. Bot tokenini olish

1. Telegramda [@BotFather](https://t.me/BotFather) ga yozing
2. `/newbot` yuboring
3. Bot nomini va username ni kiriting
4. Token'ni nusxalab oling

### 4. Admin ID ni olish

[@userinfobot](https://t.me/userinfobot) ga `/start` yuboring — u sizning ID'ingizni ko'rsatadi.

### 5. O'rnatish va ishga tushirish

```bash
# Papkaga kiring
cd telegram_video_bot

# Virtual environment yarating (ixtiyoriy, lekin tavsiya etiladi)
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate

# Kutubxonalarni o'rnating
pip install -r requirements.txt

# .env faylini yarating
cp .env.example .env
nano .env   # yoki istalgan matn muharririda oching

# Botni ishga tushiring
python bot.py
```

---

## ⚙️ .env Konfiguratsiyasi

```env
BOT_TOKEN=1234567890:ABCDefGhIJKlmNoPQRsTUVwxyZ
ADMIN_IDS=123456789
```

Bir nechta admin:
```env
ADMIN_IDS=123456789,987654321,111222333
```

---

## 📋 Admin Panel Buyruqlari

| Buyruq | Tavsif |
|--------|--------|
| `/admin` | Admin panelni ochish |
| `/cancel` | Joriy amalni bekor qilish |

### Admin panel imkoniyatlari:

1. **📢 Broadcast** — Barcha foydalanuvchilarga xabar (matn, rasm, video) yuborish
2. **➕ Kanal qo'shish** — Majburiy obuna kanalini qo'shish
3. **📋 Kanallar ro'yxati** — Qo'shilgan kanallarni ko'rish va o'chirish
4. **📊 Statistika** — Foydalanuvchilar soni va boshqa ma'lumotlar

---

## ➕ Kanal qo'shish formati

Admin panelda "Kanal qo'shish" tugmasini bosib, quyidagi formatda yozing:

```
@kanalusername | Kanal nomi | https://t.me/kanalusername
```

**Misol:**
```
@my_channel | Mening Kanalim | https://t.me/my_channel
```

> ⚠️ Bot kanalda admin bo'lishi shart! Aks holda obunani tekshira olmaydi.

---

## 📁 Fayl Tuzilmasi

```
telegram_video_bot/
├── bot.py           # Asosiy bot kodi
├── database.py      # SQLite ma'lumotlar bazasi
├── requirements.txt # Python kutubxonalari
├── .env.example     # Konfiguratsiya namunasi
├── .env             # Sizning konfiguratsiyangiz (yarating)
└── downloads/       # Vaqtinchalik video fayllar (avtomatik yaratiladi)
```

---

## ⚠️ Muhim Eslatmalar

- Telegram 50 MB dan katta fayllarni qabul qilmaydi
- Bot kanalda **admin** bo'lishi shart (obunani tekshirish uchun)
- `downloads/` papkasi avtomatik yaratiladi va har yuklab olishdan keyin tozalanadi
- Bot faqat **ochiq** (public) linklar bilan ishlaydi

---

## 🛠 Muammolar va Yechimlar

| Muammo | Yechim |
|--------|--------|
| "ffmpeg not found" | ffmpeg o'rnating va PATH ga qo'shing |
| "File is larger than 50MB" | Telegram cheklovi, kichikroq video toping |
| "Unsupported URL" | Bu sayt qo'llab-quvvatlanmaydi |
| Bot kanal obunasini tekshirmayapti | Botni kanalga admin qiling |
