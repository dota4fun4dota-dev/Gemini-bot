import asyncio
import logging
import sqlite3
import sys
from datetime import datetime, timedelta
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, PreCheckoutQuery, LabeledPrice
from aiogram.filters import CommandStart
from openai import AsyncOpenAI

# ==================== ТВОИ НАСТРОЙКИ ====================
# Твой рабочий токен бота из @BotFather
BOT_TOKEN = "8535823645:AAHq8uvQWH2xd_VTcMpFsndnOOP7EzdGbV4"

# Твой рабочий ключ OpenRouter
OPENROUTER_API_KEY = "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" 

ai_client = AsyncOpenAI(
    api_key=OPENROUTER_API_KEY, 
    base_url="https://openrouter.ai/api/v1"
)

# Актуальная бесплатная модель Gemini на OpenRouter
AI_MODEL = "google/gemini-2.5-flash:free" 
PROVIDER_TOKEN = "" 
# ========================================================

logging.basicConfig(level=logging.INFO)
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# === РАБОТА С БАЗОЙ ДАННЫХ ===
DB_PATH = "users.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            sub_until TEXT,
            free_requests_date TEXT,
            requests_count INTEGER DEFAULT 0
        )
    """)
    conn.commit()
    conn.close()

def get_user(user_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT sub_until, free_requests_date, requests_count FROM users WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    if not row:
        today = datetime.today().strftime('%Y-%m-%d')
        cursor.execute("INSERT INTO users (user_id, sub_until, free_requests_date, requests_count) VALUES (?, ?, ?, ?)",
                       (user_id, None, today, 0))
        conn.commit()
        conn.close()
        return None, today, 0
    conn.close()
    return row

def update_user_sub(user_id, days):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    until_date = datetime.now() + timedelta(days=days)
    cursor.execute("UPDATE users SET sub_until = ? WHERE user_id = ?", (until_date.strftime('%Y-%m-%d %H:%M:%S'), user_id))
    conn.commit()
    conn.close()

def increment_request(user_id, current_count):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    today = datetime.today().strftime('%Y-%m-%d')
    cursor.execute("UPDATE users SET free_requests_date = ?, requests_count = ? WHERE user_id = ?", (today, current_count + 1, user_id))
    conn.commit()
    conn.close()

# === КЛАВИАТУРЫ ===
def main_menu_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💎 Купить Подписку", callback_data="buy_sub")],
        [InlineKeyboardButton(text="📊 Мой профиль", callback_data="my_profile")]
    ])

def prices_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🌱 Неделя — 50 Stars", callback_data="pay_7")],
        [InlineKeyboardButton(text="🔥 Месяц — 150 Stars", callback_data="pay_30")],
        [InlineKeyboardButton(text="👑 Год — 500 Stars", callback_data="pay_365")]
    ])

# === ХЭНДЛЕРЫ ===
@dp.message(CommandStart())
async def cmd_start(message: Message):
    get_user(message.from_user.id)
    text = f"👋 Привет, {message.from_user.first_name}!\n\nЯ твой личный умный ИИ-помощник нового поколения.\nТы можете отправить мне любой вопрос, попросить написать реферат или код.\n\n⚠️ Без подписки тебе доступно 3 запроса в сутки.\nИспользуй кнопки ниже, чтобы проверить баланс или снять ограничения 👇"
    await message.answer(text, reply_markup=main_menu_keyboard())

@dp.callback_query(F.data == "my_profile")
async def process_profile(callback):
    sub_until, req_date, req_count = get_user(callback.from_user.id)
    today = datetime.today().strftime('%Y-%m-%d')
    
    left_reqs = 3 - req_count if req_date == today else 3
    if left_reqs < 0: left_reqs = 0
        
    status = "❌ Нет подписки"
    if sub_until:
        until_dt = datetime.strptime(sub_until, '%Y-%m-%d %H:%M:%S')
        if until_dt > datetime.now():
            status = f"🟢 Активна до {until_dt.strftime('%d.%m.%Y %H:%M')}"
            left_reqs = "♾ Безлимит"

    profile_text = f"📊 Твой профиль:\n\n👤 ID: {callback.from_user.id}\n👑 Статус подписки
