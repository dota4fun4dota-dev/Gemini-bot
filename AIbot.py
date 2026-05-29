import asyncio
import logging
import requests
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
# Универсальный URL для популярных моделей
HF_API_URL = "https://api-inference.huggingface.co/models/runwayml/stable-diffusion-v1-5"

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# === ФУНКЦИЯ РИСОВАНИЯ ===
def query_hf_image(prompt):
    headers = {"Authorization": f"Bearer {HF_TOKEN}"}
    # Добавляем параметр wait_for_model, чтобы он сам ждал загрузки
    payload = {"inputs": prompt, "options": {"wait_for_model": True}}
    response = requests.post(HF_API_URL, headers=headers, json=payload)
    
    if response.status_code != 200:
        raise Exception(f"Ошибка {response.status_code}: {response.text}")
    return response.content

# === ХЭНДЛЕРЫ ===

@dp.message(CommandStart())
async def start(message: Message):
    await message.answer("Привет! Я готов. Пиши текст или отправь /draw [описание] для картинки.")

@dp.message(F.text.startswith("/draw"))
async def draw_handler(message: Message):
    prompt = message.text.replace("/draw", "").strip()
    if not prompt:
        await message.answer("Пришли описание, например: `/draw кот в космосе`")
        return
    
    msg = await message.answer("🎨 Генерирую изображение (это займет 10-20 сек)...")
    try:
        loop = asyncio.get_event_loop()
        image_bytes = await loop.run_in_executor(None, query_hf_image, prompt)
        
        await bot.send_photo(message.chat.id, photo=BufferedInputFile(image_bytes, filename="art.png"))
        await msg.delete()
    except Exception as e:
        await msg.edit_text(f"❌ Ошибка генерации: {str(e)[:100]}")

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
