import asyncio
import logging
import sys
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message
from aiogram.filters import CommandStart
from openai import AsyncOpenAI

# ==================== НАСТРОЙКИ ====================
BOT_TOKEN = "8535823645:AAHq8uvQWH2xd_VTcMpFsndnOOP7EzdGbV4"
GROQ_API_KEY = "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"

# Настройка клиента для Groq
ai_client = AsyncOpenAI(
    api_key=GROQ_API_KEY, 
    base_url="https://api.groq.com/openai/v1"
)

# Используем быструю и стабильную модель
AI_MODEL = "llama-3.3-70b-versatile" 
# ===================================================

logging.basicConfig(level=logging.INFO)
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

@dp.message(CommandStart())
async def cmd_start(message: Message):
    await message.answer("👋 Привет! Я готов к работе. Задавай любой вопрос!")

@dp.message(F.text)
async def handle_ai_request(message: Message):
    # Отправляем сообщение, что бот думает
    status_message = await message.answer("🧠 Пожалуйста, подождите...")
    
    try:
        response = await ai_client.chat.completions.create(
            model=AI_MODEL,
            messages=[{"role": "user", "content": message.text}],
            max_tokens=2000
        )
        ai_response = response.choices[0].message.content
        
        # Удаляем сообщение "думаю" и присылаем ответ
        await status_message.delete()
        await message.answer(ai_response)
        
    except Exception as e:
        logging.error(f"Ошибка ИИ: {e}")
        await status_message.edit_text(f"❌ Ошибка: `{str(e)}`")

async def main():
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
