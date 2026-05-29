import asyncio
import os
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message
from aiogram.filters import CommandStart
from openai import AsyncOpenAI

# Берем ключи из переменных среды (безопасно)
BOT_TOKEN = os.getenv("BOT_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

ai_client = AsyncOpenAI(api_key=OPENAI_API_KEY)
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

@dp.message(CommandStart())
async def cmd_start(message: Message):
    await message.answer("Привет! Пиши текст для общения или /draw [описание] для генерации картинки.")

@dp.message(F.text.startswith("/draw"))
async def draw_handler(message: Message):
    # Убираем команду и очищаем от лишних пробелов
    prompt = message.text.replace("/draw", "").strip()
    
    if not prompt:
        await message.answer("Напиши описание, например: `/draw кот в космосе`")
        return
    
    msg = await message.answer("🎨 Генерирую изображение через DALL-E 3...")
    
    try:
        # OpenAI API автоматически понимает UTF-8, 
        # но если ошибка вылезает до него — значит, мы неверно формируем данные
        response = await ai_client.images.generate(
            model="dall-e-3",
            prompt=prompt.encode('utf-8').decode('utf-8'), # Принудительная работа с UTF-8
            n=1,
            size="1024x1024"
        )
        image_url = response.data[0].url
        await message.answer_photo(photo=image_url)
        await msg.delete()
    except Exception as e:
        # Выводим ошибку, чтобы понять, на каком этапе она падает
        await msg.edit_text(f"❌ Ошибка генерации: {str(e)}")

@dp.message(F.text)
async def text_handler(message: Message):
    if message.text.startswith("/"): return
    await message.answer("🧠 Думаю...")
    try:
        response = await ai_client.chat.completions.create(
            model="gpt-3.5-turbo", # Или gpt-4o
            messages=[{"role": "user", "content": message.text}]
        )
        await message.answer(response.choices[0].message.content)
    except Exception as e:
        await message.answer(f"❌ Ошибка: {e}")

async def main():
    # Очистка очереди убирает TelegramConflictError
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
