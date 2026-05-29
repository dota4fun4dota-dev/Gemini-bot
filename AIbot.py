import asyncio
import logging
import sqlite3
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import CommandStart
from openai import AsyncOpenAI

# ==================== НАСТРОЙКИ ====================
BOT_TOKEN = "8535823645:AAHq8uvQWH2xd_VTcMpFsndnOOP7EzdGbV4"
GROQ_API_KEY = "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"

ai_client = AsyncOpenAI(api_key=GROQ_API_KEY, base_url="https://api.groq.com/openai/v1")
AI_MODEL = "llama-3.3-70b-versatile"
FREE_LIMIT = 5 # Лимит пробных ответов

logging.basicConfig(level=logging.INFO)
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# === БАЗА ДАННЫХ ===
def init_db():
    conn = sqlite3.connect("bot_users.db")
    cursor = conn.cursor()
    cursor.execute("""CREATE TABLE IF NOT EXISTS users 
                      (user_id INTEGER PRIMARY KEY, count INTEGER DEFAULT 0, is_paid INTEGER DEFAULT 0)""")
    conn.commit()
    conn.close()

def get_user_data(user_id):
    conn = sqlite3.connect("bot_users.db")
    cursor = conn.cursor()
    cursor.execute("SELECT count, is_paid FROM users WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    if not row:
        cursor.execute("INSERT INTO users (user_id) VALUES (?)", (user_id,))
        conn.commit()
        row = (0, 0)
    conn.close()
    return row

def increment_count(user_id):
    conn = sqlite3.connect("bot_users.db")
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET count = count + 1 WHERE user_id = ?", (user_id,))
    conn.commit()
    conn.close()

# === ХЭНДЛЕРЫ ===
@dp.message(CommandStart())
async def cmd_start(message: Message):
    await message.answer("👋 Привет! У тебя есть 5 бесплатных запросов к ИИ. После их исчерпания нужно будет купить подписку.")

@dp.message(F.text)
async def handle_ai_request(message: Message):
    count, is_paid = get_user_data(message.from_user.id)
    
    # Проверка лимитов
    if not is_paid and count >= FREE_LIMIT:
        kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="💎 Купить подписку", callback_data="buy")]])
        await message.answer("⚠️ Твои 5 бесплатных ответов закончились.\nПожалуйста, оплати подписку, чтобы продолжить!", reply_markup=kb)
        return

    status_message = await message.answer("🧠 Думаю...")
    try:
        response = await ai_client.chat.completions.create(
            model=AI_MODEL,
            messages=[{"role": "user", "content": message.text}]
        )
        increment_count(message.from_user.id)
        await status_message.delete()
        await message.answer(response.choices[0].message.content)
    except Exception as e:
        await status_message.edit_text(f"❌ Ошибка: `{str(e)}`")

async def main():
    init_db()
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
