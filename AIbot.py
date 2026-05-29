import os
import sys
import asyncio
import logging
import httpx
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message
from aiogram.filters import CommandStart
from openai import AsyncOpenAI

# 1. Принудительная очистка переменных окружения ДО импорта OpenAI
for env_var in ["HTTP_PROXY", "HTTPS_PROXY", "ALL_PROXY", "http_proxy", "https_proxy", "all_proxy"]:
    if env_var in os.environ:
        del os.environ[env_var]

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 2. Инициализация переменных
BOT_TOKEN = os.getenv("BOT_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

if not BOT_TOKEN or not OPENAI_API_KEY:
    logger.error("Ключи не заданы!")
    sys.exit(1)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# 3. Использование чистого транспорта для httpx
# Это гарантирует, что прокси не будут использованы
transport = httpx.AsyncHTTPTransport(verify=True)
client = AsyncOpenAI(
    api_key=OPENAI_API_KEY,
    http_client=httpx.AsyncClient(transport=transport, timeout=60.0)
)

@dp.message(CommandStart())
async def cmd_start(message: Message):
    await message.answer("👋 Бот активен и готов к работе!")

@dp.message(F.text.startswith("/draw"))
async def draw_handler(message: Message):
    prompt = message.text.replace("/draw", "").strip()
    if not prompt:
        await message.answer("Введите описание для рисунка.")
        return
    
    msg = await message.answer("🎨 Генерирую...")
    try:
        response = await client.images.generate(
            model="dall-e-3",
            prompt=prompt,
            n=1,
            size="1024x1024"
        )
        await message.answer_photo(photo=response.data[0].url)
        await msg.delete()
    except Exception as e:
        logger.error(f"Generation Error: {e}")
        await msg.edit_text("❌ Ошибка генерации.")

async def main():
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
