import asyncio
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message
from aiogram.filters import CommandStart
from openai import AsyncOpenAI

# === НАСТРОЙКИ ===
BOT_TOKEN = "8535823645:AAG5h7hmd97eGr1_DEBs5KDyqnMBZRUz2nA"
# Сюда нужно вставить ключ (sk-...), но лучше сделать это через переменные окружения в Railway!
OPENAI_API_KEY = "ТВОЙ_КЛЮЧ_sk-75iE8vFuJcFDIZAGErBuHOOTVvFKpTDPG6UBJhnvcweEMmTB" 

ai_client = AsyncOpenAI(api_key=OPENAI_API_KEY)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

@dp.message(F.text.startswith("/draw"))
async def draw_handler(message: Message):
    prompt = message.text.replace("/draw", "").strip()
    if not prompt:
        await message.answer("Напиши описание, например: `/draw кот в космосе`")
        return
    
    msg = await message.answer("🎨 Рисую через DALL-E...")
    try:
        # Генерация через OpenAI DALL-E 3
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
        await msg.edit_text(f"❌ Ошибка генерации: {e}")

async def main():
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
