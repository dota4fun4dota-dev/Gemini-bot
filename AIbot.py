import sys
import asyncio
import logging
import httpx
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message
from aiogram.filters import CommandStart
from openai import AsyncOpenAI

# === КОНФИГУРАЦИЯ ===
BOT_TOKEN = "8980453196:AAGiMgy8bohMdOM6Z3nGpmos_ysCr2W_-Us"
GROQ_API_KEY = "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"

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Инициализация клиента для Groq
# base_url указывает, что мы работаем через Groq, а не через OpenAI
transport = httpx.AsyncHTTPTransport(verify=True)
http_client = httpx.AsyncClient(transport=transport, timeout=60.0)

client = AsyncOpenAI(
    api_key=GROQ_API_KEY,
    base_url="https://api.groq.com/openai/v1",
    http_client=http_client
)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

@dp.message(CommandStart())
async def cmd_start(message: Message):
    await message.answer("✅ Бот запущен и подключен к Groq Llama 3.3!")

@dp.message(F.text)
async def handle_message(message: Message):
    msg = await message.answer("🧠 Думаю...")
    try:
        response = await client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": message.text}]
        )
        await msg.delete()
        await message.answer(response.choices[0].message.content)
    except Exception as e:
        logger.error(f"Groq Error: {e}")
        await msg.edit_text("❌ Ошибка при обращении к ИИ.")

async def main():
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
