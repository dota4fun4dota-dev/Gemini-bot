import os
import asyncio
import logging
import httpx
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message
from aiogram.filters import CommandStart
from openai import AsyncOpenAI

# 1. Принудительная очистка прокси-переменных
for env_var in ["HTTP_PROXY", "HTTPS_PROXY", "ALL_PROXY", "http_proxy", "https_proxy", "all_proxy"]:
    if env_var in os.environ:
        del os.environ[env_var]

# 2. Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# 3. Инициализация клиентов
BOT_TOKEN = os.getenv("BOT_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

if not BOT_TOKEN or not OPENAI_API_KEY:
    raise ValueError("Missing required environment variables: BOT_TOKEN or OPENAI_API_KEY")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
# Явное отключение прокси через httpx
ai_client = AsyncOpenAI(
    api_key=OPENAI_API_KEY,
    http_client=httpx.AsyncClient(proxies=None, timeout=30.0)
)

@dp.message(CommandStart())
async def cmd_start(message: Message):
    await message.answer("Система готова. Используй /draw для генерации или пиши текст для общения.")

@dp.message(F.text.startswith("/draw"))
async def draw_handler(message: Message):
    prompt = message.text.replace("/draw", "").strip()
    if not prompt:
        return await message.answer("Укажите описание для генерации.")
    
    status_msg = await message.answer("🎨 Генерирую изображение...")
    try:
        response = await ai_client.images.generate(
            model="dall-e-3",
            prompt=prompt,
            n=1,
            size="1024x1024"
        )
        await message.answer_photo(photo=response.data[0].url)
        await status_msg.delete()
    except Exception as e:
        logger.error(f"DALL-E Error: {e}")
        await status_msg.edit_text("❌ Ошибка при генерации изображения. Попробуйте позже.")

@dp.message(F.text)
async def text_handler(message: Message):
    if message.text.startswith("/"): return
    
    try:
        response = await ai_client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": message.text}]
        )
        await message.answer(response.choices[0].message.content)
    except Exception as e:
        logger.error(f"GPT Error: {e}")
        await message.answer("❌ Ошибка при ответе ИИ.")

async def main():
    logger.info("Запуск бота...")
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
