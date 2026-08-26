# Telegram Kontent Bot

Kuniga 3-7 marta kanal yoki guruhga avtomatik rasm + matnli post yuboradigan bot.
Foydalanuvchi xabarlariga javob bermaydi, faqat post qiladi.

## 1. Telegram bot yaratish

1. Telegram'da **@BotFather** ga yozing
2. `/newbot` buyrug'ini yuboring, nom va username bering
3. Sizga token beriladi (masalan `123456:ABC-DEF...`) — buni saqlab qo'ying,
   **hech kimga va hech qanday chatga yozmang**

## 2. Botni kanal/guruhga admin qilish

1. Kanal yoki guruhingiz sozlamalariga o'ting
2. **Administrators** → botingizni qo'shing
3. Kamida "Post messages" (kanalda) yoki "Send messages" (guruhda) huquqini bering

### TARGET_CHAT_ID ni topish

- Ochiq kanal/guruh bo'lsa: `@kanal_username` shaklida yozsa bo'ladi
- Yopiq bo'lsa: kanalga bitta xabar yuboring, keyin
  `https://api.telegram.org/bot<TOKEN>/getUpdates` manzilini brauzerda oching —
  javobda `"chat":{"id": -100...}` ko'rinadi, shu raqam TARGET_CHAT_ID bo'ladi

## 3. Gemini API kalitini olish

https://aistudio.google.com/apikey saytiga kirib, yangi API kalit yarating.

## 4. Railway'da joylashtirish

1. https://railway.com ga kiring, **New Project** → **Deploy from GitHub repo**
   (avval shu papkani o'z GitHub repo'ingizga yuklang)
2. Loyiha yaratilgach, **Variables** bo'limiga o'ting va quyidagilarni qo'shing:

   | Nomi | Qiymati |
   |---|---|
   | `TELEGRAM_BOT_TOKEN` | BotFather'dan olingan token |
   | `GEMINI_API_KEY` | Google AI Studio'dan olingan kalit |
   | `TARGET_CHAT_ID` | Kanal/guruh ID yoki @username |
   | `MIN_POSTS_PER_DAY` | 3 (ixtiyoriy) |
   | `MAX_POSTS_PER_DAY` | 7 (ixtiyoriy) |
   | `ACTIVE_HOUR_START` | 9 (ixtiyoriy) |
   | `ACTIVE_HOUR_END` | 22 (ixtiyoriy) |

3. Railway avtomatik `Dockerfile`ni topib, botni build va deploy qiladi
4. **Deployments** bo'limidan loglarni kuzatib, "Bot ishga tushdi: @..." xabarini kutasiz

## Botning ishlash tartibi

- Har kuni tasodifiy `MIN_POSTS_PER_DAY`–`MAX_POSTS_PER_DAY` orasida son tanlanadi
- Shuncha son postlar `ACTIVE_HOUR_START`–`ACTIVE_HOUR_END` oralig'ida
  tasodifiy vaqtlarga taqsimlanadi
- Har bir post uchun mavzu ro'yxatidan (`src/content_generator.py` ichida
  `TOPICS`) tasodifiy tanlanadi, Gemini matn va rasm generatsiya qiladi
- Post kanalga bot nomidan emas, kanal identiteti bilan chiqadi (agar kanal
  bo'lsa) — "kimdan yuborilgani" ko'rsatilmaydi
- Bot foydalanuvchi xabarlariga hech qanday tarzda javob bermaydi

## Mavzularni o'zgartirish

`src/content_generator.py` faylidagi `TOPICS` ro'yxatini o'zingiz xohlagan
mavzular bilan tahrirlashingiz mumkin.

## Video postlar haqida

Gemini hozircha video generatsiya qilmaydi — faqat rasm. Video qo'shish
uchun alohida video-generatsiya xizmati (masalan Higgsfield) kerak bo'ladi;
buni keyingi bosqichda qo'shib berishim mumkin.
