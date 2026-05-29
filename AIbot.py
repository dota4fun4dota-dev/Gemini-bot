# -*- coding: utf-8 -*-
import asyncio
import os
import sys
import io
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message
from aiogram.filters import CommandStart
from openai import AsyncOpenAI

# Принудительная установка кодировки UTF-8 для вывода в консоль
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Получаем ключи из настроек Railway (Variables)
BOT_TOKEN = os.getenv("BOT_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Инициализация клиентов
ai_client = AsyncOpenAI(api_key=OPENAI_API_KEY)
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

@dp.message(CommandStart())
async def cmd_start(message: Message):
    await message.answer("Привет! Пиши мне текст или используй /draw [описание] для генерации картинки.")

@dp.message(F.text.startswith("/draw"))
async def draw_handler(message: Message):
    prompt = message.text.replace("/draw", "").strip()
    if not prompt:
        await message.answer("Пожалуйста, напиши описание. Например: /draw кот в космосе")
        return
    
    msg = await message.answer("🎨 Генерирую изображение...")
    try:
        response = await ai_client.images.generate(
            model="dall-e-3",
            prompt=prompt,
            n=1,
            size="1024x1024"
        )
        image_url = response.data[0].url
        await message.answer_photo(photo=image_url)
        await msg.delete()
    except Exception as e:
        await msg.edit_text(f"❌ Ошибка генерации: {str(e)}")

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
    # Очистка очереди (убирает конфликт экземпляров)
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
