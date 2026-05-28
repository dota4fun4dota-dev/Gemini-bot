import asyncio
import logging
import sqlite3
import sys
from datetime import datetime, timedelta
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, PreCheckoutQuery, LabeledPrice
from aiogram.filters import CommandStart
from openai import AsyncOpenAI # Официальный клиент для работы с DeepSeek API

# ==================== ТВОИ НАСТРОЙКИ ====================
BOT_TOKEN = "8535823645:AAEnS_30By0LIIZtOAx220JNZ5bkXf90aJU"
PROVIDER_TOKEN = "" # Для Telegram Stars оставляем пустым

# Твой официальный токен DeepSeek
DEEPSEEK_API_KEY = "sk-b7303ecad65245d094f328633a6a5843" 

# Подключаем официальный сервер DeepSeek
ai_client = AsyncOpenAI(
    api_key=DEEPSEEK_API_KEY, 
    base_url="https://api.deepseek.com/v1"
)
AI_MODEL = "deepseek-chat" # Официальное название модели DeepSeek-V3
# ========================================================

logging.basicConfig(level=logging.INFO)
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# === РАБОТА С БАЗОЙ ДАННЫХ ===
def init_db():
    conn = sqlite3.connect("users.db")
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
    conn = sqlite3.connect("users.db")
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
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    until_date = datetime.now() + timedelta(days=days)
    cursor.execute("UPDATE users SET sub_until = ? WHERE user_id = ?", (until_date.strftime('%Y-%m-%d %H:%M:%S'), user_id))
    conn.commit()
    conn.close()

def increment_request(user_id, current_count):
    conn = sqlite3.connect("users.db")
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
    await message.answer(
        f"👋 Привет, {message.from_user.first_name}!\n\n"
        "Я твой личный умный ИИ-помощник нового поколения.\n"
        "Ты можешь отправить мне любой вопрос, попросить написать реферат или код.\n\n"
        "⚠️ Без подписки тебе доступно **3 запроса в сутки**.\n"
        "Используй кнопки ниже, чтобы
