import asyncio
import logging
import httpx
import json
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.filters import CommandStart

BOT_TOKEN = "8980453196:AAGiMgy8bohMdOM6Z3nGpmos_ysCr2W_-Us"
API_KEY = "5911714ce3ffbc56f7064a9ad0708e0c" 
API_BASE = "https://api.kie.ai/api/v1/jobs"
CHAT_API_URL = "https://api.kie.ai/gemini-3.1-pro/v1/chat/completions"

logging.basicConfig(level=logging.INFO)
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

@dp.message(CommandStart())
async def start(message: Message):
    await message.answer("Привет! Я готов. Рисую, переделываю фото или общаюсь.")

@dp.message(F.photo)
async def handle_photo(message: Message):
    msg = await message.answer("⏳ Обрабатываю изображение...")
    file = await bot.get_file(message.photo[-1].file_id)
    photo_url = f"https://api.telegram.org/file/bot{BOT_TOKEN}/{file.file_path}"
    payload = {"model": "grok-imagine/image-to-image", "input": {"prompt": message.caption or "Enhance", "image_urls": [photo_url]}}
    headers = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.post(f"{API_BASE}/createTask", json=payload, headers=headers)
            if resp.status_code != 200: return await msg.edit_text(f"Ошибка API: {resp.text}")
            task_id = resp.json().get("data", {}).get("taskId")
            for i in range(15):
                await asyncio.sleep(10)
                data = (await client.get(f"{API_BASE}/recordInfo?taskId={task_id}", headers=headers)).json().get("data", {})
                if data.get("resultJson"):
                    url = json.loads(data["resultJson"]).get("resultUrls", [None])[0]
                    if url: await message.answer_photo(photo=url, caption="✨ Готово!"); return await msg.delete()
        except Exception as e: await msg.edit_text(f"Ошибка: {str(e)}")

@dp.message(F.text)
async def handle_text(message: Message):
    if message.text.lower().startswith("нарисуй"):
        msg = await message.answer("🎨 Рисую...")
        prompt = message.text.lower().replace("нарисуй", "").strip()
        payload = {"model": "flux-2/pro-text-to-image", "input": {"prompt": prompt, "aspect_ratio": "1:1"}}
        headers = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}
        async with httpx.AsyncClient() as client:
            resp = await client.post(f"{API_BASE}/createTask", json=payload, headers=headers)
            await msg.edit_text("Задача принята. Жду результат...")
    else:
        msg = await message.answer("🤔 Думаю...")
        headers = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}
        payload = {"messages": [{"role": "user", "content": message.text}]}
        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                resp = await client.post(CHAT_API_URL, json=payload, headers=headers)
                if resp.status_code == 200:
                    answer = resp.json().get("choices", [{}])[0].get("message", {}).get("content", "Нет ответа.")
                    await msg.edit_text(answer)
                else:
                    await msg.edit_text(f"API Error {resp.status_code}: {resp.text[:100]}")
            except Exception as e:
                await msg.edit_text(f"Connection error: {type(e).__name__}: {str(e)}")

async def main(): await dp.start_polling(bot)
if __name__ == "__main__": asyncio.run(main())
