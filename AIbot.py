import asyncio
import aiohttp
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, BufferedInputFile
from aiogram.filters import CommandStart
from openai import AsyncOpenAI

# === НАСТРОЙКИ ===
BOT_TOKEN = "8535823645:AAHq8uvQWH2xd_VTcMpFsndnOOP7EzdGbV4"
GROQ_API_KEY = "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"
HF_TOKEN = "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"

ai_client = AsyncOpenAI(api_key=GROQ_API_KEY, base_url="https://api.groq.com/openai/v1")
AI_MODEL = "llama-3.3-70b-versatile"
# Сменим модель на более стабильную для API
HF_API_URL = "https://api-inference.huggingface.co/models/black-forest-labs/FLUX.1-schnell"

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# === АСИНХРОННЫЙ ЗАПРОС ===
async def query_hf_image(prompt):
    async with aiohttp.ClientSession() as session:
        headers = {"Authorization": f"Bearer {HF_TOKEN}"}
        # Включаем wait_for_model, чтобы API сам ждал загрузки
        payload = {"inputs": prompt, "options": {"wait_for_model": True}}
        
        async with session.post(HF_API_URL, headers=headers, json=payload, timeout=120) as response:
            if response.status == 200:
                return await response.read()
            else:
                error_text = await response.text()
                raise Exception(f"API Error {response.status}: {error_text[:50]}")

@dp.message(F.text.startswith("/draw"))
async def draw_handler(message: Message):
    prompt = message.text.replace("/draw", "").strip()
    if not prompt:
        await message.answer("Пришли описание, например: `/draw кот`")
        return
    
    msg = await message.answer("🎨 Рисую... это может занять до 30 секунд.")
    try:
        image_bytes = await query_hf_image(prompt)
        await bot.send_photo(message.chat.id, photo=BufferedInputFile(image_bytes, filename="art.png"))
        await msg.delete()
    except Exception as e:
        await msg.edit_text(f"❌ Ошибка: {str(e)}")

@dp.message(F.text)
async def text_handler(message: Message):
    if message.text.startswith("/"): return 
    await message.answer("🧠 Думаю...")
    try:
        response = await ai_client.chat.completions.create(
            model=AI_MODEL,
            messages=[{"role": "user", "content": message.text}]
        )
        await message.answer(response.choices[0].message.content)
    except Exception as e:
        await message.answer(f"❌ Ошибка: {e}")

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
