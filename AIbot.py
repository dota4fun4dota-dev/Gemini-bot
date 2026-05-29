import asyncio
import logging
import sqlite3
from datetime import datetime, timedelta
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message
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

def init_db():
    conn = sqlite3.connect("bot_users.db")
    cursor = conn.cursor()
    cursor.execute("""CREATE TABLE IF NOT EXISTS users 
                      (user_id INTEGER PRIMARY KEY, count INTEGER DEFAULT 0, start_time TEXT)""")
    conn.commit()
    conn.close()

def get_status(user_id):
    conn = sqlite3.connect("bot_users.db")
    cursor = conn.cursor()
    cursor.execute("SELECT count, start_time FROM users WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    
    now = datetime.now()
    
    if not row:
        # Новый пользователь
        cursor.execute("INSERT INTO users (user_id, count, start_time) VALUES (?, 1, ?)", (user_id, now.isoformat()))
        conn.commit()
        conn.close()
        return 1, True
    
    count, start_time = row
    start_dt = datetime.fromisoformat(start_time)
    
    # Проверка таймера (прошло ли 2 часа?)
    if now >= start_dt + timedelta(hours=RESET_HOURS):
        cursor.execute("UPDATE users SET count = 1, start_time = ? WHERE user_id = ?", (now.isoformat(), user_id))
        conn.commit()
        conn.close()
        return 1, True
    
    # Если время не вышло, проверяем лимит
    if count < FREE_LIMIT:
        cursor.execute("UPDATE users SET count = count + 1 WHERE user_id = ?", (user_id,))
        conn.commit()
        conn.close()
        return count + 1, True
    
    conn.close()
    return count, False

@dp.message(F.text)
async def handle_ai_request(message: Message):
    # Проверка статуса: count - текущий номер запроса, allowed - можно ли делать запрос
    count, allowed = get_status(message.from_user.id)
    
    if not allowed:
        await message.answer("⚠️ Твои 10 запросов на 2 часа исчерпаны. Попробуй позже!")
        return

    status_message = await message.answer("🧠 Думаю...")
    try:
        response = await ai_client.chat.completions.create(
            model=AI_MODEL, messages=[{"role": "user", "content": message.text}]
        )
        left = max(0, FREE_LIMIT - count)
        await status_message.delete()
        await message.answer(f"{response.choices[0].message.content}\n\n📊 Осталось: {left}")
    except Exception as e:
        await status_message.edit_text(f"❌ Ошибка: `{str(e)}`")

async def main():
    init_db()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
