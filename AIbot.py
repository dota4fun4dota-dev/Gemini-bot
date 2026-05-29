# -*- coding: utf-8 -*-
import os
import sys
import io

# Глобальная настройка кодировки до запуска всего остального
os.environ["PYTHONIOENCODING"] = "UTF-8"
sys.stdin = io.TextIOWrapper(sys.stdin.buffer, encoding='utf-8')
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

import asyncio
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message
from aiogram.filters import CommandStart
from openai import AsyncOpenAI

# Получаем переменные из Railway
BOT_TOKEN = os.getenv("BOT_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

ai_client = AsyncOpenAI(api_key=OPENAI_API_KEY)
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

@dp.message(CommandStart())
async def cmd_start(message: Message):
    await message.answer("Привет! Я готов. Пиши /draw [описание] для генерации.")

import unicodedata

@dp.message(F.text.startswith("/draw"))
async def draw_handler(message: Message):
    prompt = message.text.replace("/draw", "").strip()
    if not prompt:
        await message.answer("Укажите описание.")
        return
    
    msg = await message.answer("🎨 Генерирую...")
    try:
        # Пытаемся нормализовать строку, удаляя спецсимволы, 
        # которые могли бы вызвать конфликт кодировок
        clean_prompt = unicodedata.normalize('NFKC', prompt)
        
        response = await ai_client.images.generate(
            model="dall-e-3",
            prompt=clean_prompt,
            n=1,
            size="1024x1024"
        )
        image_url = response.data[0].url
        await message.answer_photo(photo=image_url)
        await msg.delete()
    except Exception as e:
        # Если ошибка сохраняется, выводим её максимально подробно
        await msg.edit_text(f"❌ Ошибка: {type(e).__name__}: {str(e)}")
@dp.message(F.text)
async def text_handler(message: Message):
    if message.text.startswith("/"): return
    await message.answer("🧠 Думаю...")
    try:
        response = await ai_client.chat.completions.create(
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
