import asyncio
import logging
import sqlite3
from datetime import datetime, timedelta
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message
from aiogram.filters import CommandStart
from openai import AsyncOpenAI

# ==================== НАСТРОЙКИ ====================
BOT_TOKEN = "8535823645:AAHq8uvQWH2xd_VTcMpFsndnOOP7EzdGbV4"
GROQ_API_KEY = "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"

ai_client = AsyncOpenAI(api_key=GROQ_API_KEY, base_url="https://api.groq.com/openai/v1")
AI_MODEL = "llama-3.3-70b-versatile"
FREE_LIMIT = 10 
RESET_HOURS = 2 

logging.basicConfig(level=logging.INFO)
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# === БАЗА ДАННЫХ ===
def init_db():
    conn = sqlite3.connect("bot_users.db")
    cursor = conn.cursor()
    # start_time — время самого первого запроса
    cursor.execute("""CREATE TABLE IF NOT EXISTS users 
                      (user_id INTEGER PRIMARY KEY, count INTEGER DEFAULT 0, is_paid INTEGER DEFAULT 0, start_time TEXT)""")
    conn.commit()
    conn.close()

def get_user_data(user_id):
    conn = sqlite3.connect("bot_users.db")
    cursor = conn.cursor()
    cursor.execute("SELECT count, is_paid, start_time FROM users WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    
    if not row:
        return 0, 0, None
    
    count, is_paid, start_time = row
    
    # Проверка: прошло ли 2 часа с ПЕРВОГО запроса?
    if start_time:
        start_dt = datetime.fromisoformat(start_time)
        if datetime.now() >= start_dt + timedelta(hours=RESET_HOURS):
            cursor.execute("UPDATE users SET count = 0, start_time = NULL WHERE user_id = ?", (user_id,))
            conn.commit()
            count = 0
            start_time = None
            
    conn.close()
    return count, is_paid, start_time

def increment_count(user_id):
    conn = sqlite3.connect("bot_users.db")
    cursor = conn.cursor()
    # Если это первый запрос (count был 0), фиксируем время старта
    cursor.execute("SELECT count FROM users WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    
    if row and row[0] == 0:
        cursor.execute("UPDATE users SET count = 1, start_time = ? WHERE user_id = ?", (datetime.now().isoformat(), user_id))
    else:
        cursor.execute("UPDATE users SET count = count + 1 WHERE user_id = ?", (user_id,))
    
    conn.commit()
    conn.close()

# === ХЭНДЛЕРЫ ===
@dp.message(F.text)
async def handle_ai_request(message: Message):
    count, is_paid, start_time = get_user_data(message.from_user.id)
    
    if not is_paid and count >= FREE_LIMIT:
        await message.answer("⚠️ Твои 10 запросов закончились. Они обновятся через 2 часа с момента первого использования.")
        return

    status_message = await message.answer("🧠 Думаю...")
    try:
        response = await ai_client.chat.completions.create(
            model=AI_MODEL, messages=[{"role": "user", "content": message.text}]
        )
        increment_count(message.from_user.id)
        
        # Инфо для пользователя
        new_count, _, _ = get_user_data(message.from_user.id)
        left = max(0, FREE_LIMIT - new_count)
        
        await status_message.delete()
        await message.answer(f"{response.choices[0].message.content}\n\n📊 Осталось запросов: {left}")
    except Exception as e:
        await status_message.edit_text(f"❌ Ошибка: `{str(e)}`")

async def main():
    init_db()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
