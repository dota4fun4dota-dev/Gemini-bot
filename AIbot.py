import asyncio
import logging
import httpx
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message
from aiogram.filters import CommandStart
from openai import AsyncOpenAI
from gigachat import GigaChat

# === КОНФИГУРАЦИЯ ===
BOT_TOKEN = "8980453196:AAGiMgy8bohMdOM6Z3nGpmos_ysCr2W_-Us"
GROQ_API_KEY = "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"
OPENAI_API_KEY = "sk-cdrG1z0hioUqEzu05GgMPmEunV4KYjQaSM3JSBZSjgHeJzrP"
GIGA_CLIENT_ID = "019e7399-aee8-7446-8aa8-543af102e074"
GIGA_CLIENT_SECRET = "30338f1b-829d-41df-a2b2-1d8995196355"

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Инициализация клиентов
client_groq = AsyncOpenAI(api_key=GROQ_API_KEY, base_url="https://api.groq.com/openai/v1", http_client=httpx.AsyncClient(timeout=60.0))
client_openai = AsyncOpenAI(api_key=OPENAI_API_KEY)
giga = GigaChat(credentials=f"{GIGA_CLIENT_ID}:{GIGA_CLIENT_SECRET}", verify_ssl_certs=False, scope="GIGACHAT_API_PERS")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

@dp.message(CommandStart())
async def cmd_start(message: Message):
    await message.answer("✅ Бот готов!\n\nМои функции:\n1. Просто текст -> Groq (Llama 3.3)\n2. /giga [текст] -> GigaChat\n3. 'Нарисуй [текст]' -> DALL-E 3")

# Обработка картинок (DALL-E 3)
@dp.message(F.text.lower().contains("нарисуй"))
async def image_handler(message: Message):
    prompt = message.text.lower().replace("нарисуй", "").strip()
    msg = await message.answer("🎨 Рисую через DALL-E 3...")
    try:
        response = await client_openai.images.generate(model="dall-e-3", prompt=prompt, n=1, size="1024x1024")
        await message.answer_photo(photo=response.data[0].url)
        await msg.delete()
    except Exception as e:
        await msg.edit_text(f"❌ Ошибка генерации: {e}")

# Обработка GigaChat
@dp.message(F.text.startswith("/giga"))
async def giga_handler(message: Message):
    prompt = message.text.replace("/giga", "").strip()
    msg = await message.answer("🌌 GigaChat думает...")
    try:
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(None, lambda: giga.chat(prompt))
        await msg.delete()
        await message.answer(f"GigaChat: {response.choices[0].message.content}")
    except Exception as e:
        await msg.edit_text(f"❌ Ошибка GigaChat: {e}")

# Обработка Groq (основной чат)
@dp.message(F.text)
async def groq_handler(message: Message):
    msg = await message.answer("🧠 Groq думает...")
    try:
        response = await client_groq.chat.completions.create(model="llama-3.3-70b-versatile", messages=[{"role": "user", "content": message.text}])
        await msg.delete()
        await message.answer(f"Groq: {response.choices[0].message.content}")
    except Exception as e:
        await msg.edit_text("❌ Ошибка Groq.")

async def main():
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
