import os

# ПРИНУДИТЕЛЬНО УДАЛЯЕМ ПРОКСИ-ПЕРЕМЕННЫЕ, КОТОРЫЕ ВЫЗЫВАЮТ ОШИБКУ
if "HTTP_PROXY" in os.environ:
    del os.environ["HTTP_PROXY"]
if "HTTPS_PROXY" in os.environ:
    del os.environ["HTTPS_PROXY"]
if "ALL_PROXY" in os.environ:
    del os.environ["ALL_PROXY"]

# ... далее идет инициализация client = AsyncOpenAI(...)
import os
import asyncio
import logging
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message
from aiogram.filters import CommandStart
from openai import AsyncOpenAI

# Настройка логирования для отладки
logging.basicConfig(level=logging.INFO)

# Получаем данные из Railway Variables
BOT_TOKEN = os.getenv("BOT_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Инициализация
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
client = AsyncOpenAI(api_key=OPENAI_API_KEY)

@dp.message(CommandStart())
async def cmd_start(message: Message):
    await message.answer("Привет! Я готов. Пиши текст или используй /draw [описание] для генерации картинки.")

@dp.message(F.text.startswith("/draw"))
async def draw_handler(message: Message):
    prompt = message.text.replace("/draw", "").strip()
    if not prompt:
        await message.answer("Укажите описание: /draw кот в космосе")
        return
    
    status_msg = await message.answer("🎨 Генерирую...")
    try:
        response = await client.images.generate(
            model="dall-e-3",
            prompt=prompt,
            n=1,
            size="1024x1024"
        )
        await message.answer_photo(photo=response.data[0].url)
        await status_msg.delete()
    except Exception as e:
        await status_msg.edit_text(f"❌ Ошибка: {str(e)}")

@dp.message(F.text)
async def text_handler(message: Message):
    # Игнорируем команды
    if message.text.startswith("/"): return
    
    try:
        response = await client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": message.text}]
        )
        await message.answer(response.choices[0].message.content)
    except Exception as e:
        await message.answer(f"❌ Ошибка: {str(e)}")

async def main():
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
