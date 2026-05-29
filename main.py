import os
import asyncio
import logging
import httpx
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message
from aiogram.filters import CommandStart
from openai import AsyncOpenAI

# 1. Защита от системных прокси (устраняет TypeError)
for env_var in ["HTTP_PROXY", "HTTPS_PROXY", "ALL_PROXY", "http_proxy", "https_proxy", "all_proxy"]:
    if env_var in os.environ:
        del os.environ[env_var]

# 2. Конфигурация
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Получаем данные из переменных окружения Railway (это БЕЗОПАСНО)
BOT_TOKEN = os.getenv("BOT_TOKEN")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
AI_MODEL = "llama-3.3-70b-versatile"

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# Инициализация клиента Groq
client = AsyncOpenAI(
    api_key=GROQ_API_KEY, 
    base_url="https://api.groq.com/openai/v1",
    http_client=httpx.AsyncClient(proxies=None, timeout=30.0)
)

@dp.message(CommandStart())
async def cmd_start(message: Message):
    await message.answer("👋 Привет! Я снова в строю. Задавай вопросы!")

@dp.message(F.text)
async def handle_ai_request(message: Message):
    status_message = await message.answer("🧠 Думаю...")
    
    try:
        response = await client.chat.completions.create(
            model=AI_MODEL,
            messages=[{"role": "user", "content": message.text}],
            max_tokens=2000
        )
        ai_response = response.choices[0].message.content
        
        await status_message.delete()
        await message.answer(ai_response)
        
    except Exception as e:
        logger.error(f"Ошибка ИИ: {e}")
        await status_message.edit_text(f"❌ Ошибка: {str(e)[:50]}...")

async def main():
    logger.info("Бот запущен и готов к работе.")
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
