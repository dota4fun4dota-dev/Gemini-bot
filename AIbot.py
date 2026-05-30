import asyncio
import logging
import httpx
import json
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message
from aiogram.filters import CommandStart

BOT_TOKEN = "8980453196:AAGiMgy8bohMdOM6Z3nGpmos_ysCr2W_-Us"
API_KEY = "5911714ce3ffbc56f7064a9ad0708e0c" 
API_BASE = "https://api.kie.ai/api/v1/jobs"
CHAT_API_URL = "https://api.kie.ai/gemini-3.1-pro/v1/chat/completions"

logging.basicConfig(level=logging.INFO)
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

@dp.startup()
async def on_startup():
    await bot.delete_webhook(drop_pending_updates=True)

async def send_long_message(message: Message, text: str):
    for i in range(0, len(text), 4000):
        await message.answer(text[i:i+4000])

@dp.message(CommandStart())
async def start(message: Message):
    await message.answer("Привет! Я готов к работе.")

@dp.message(F.photo)
async def handle_photo(message: Message):
    msg = await message.answer("⏳...")
    file = await bot.get_file(message.photo[-1].file_id)
    photo_url = f"https://api.telegram.org/file/bot{BOT_TOKEN}/{file.file_path}"
    payload = {"model": "grok-imagine/image-to-image", "input": {"prompt": message.caption or "Enhance", "image_urls": [photo_url]}}
    headers = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}
    
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.post(f"{API_BASE}/createTask", json=payload, headers=headers)
            if resp.status_code != 200 or not resp.json(): return await msg.edit_text("Ошибка сервера.")
            
            task_id = resp.json().get("data", {}).get("taskId")
            for i in range(20):
                await asyncio.sleep(15)
                res = await client.get(f"{API_BASE}/recordInfo?taskId={task_id}", headers=headers)
                data = res.json()
                if data and data.get("data", {}).get("resultJson"):
                    url = json.loads(data["data"]["resultJson"]).get("resultUrls", [None])[0]
                    if url: await message.answer_photo(photo=url); return await msg.delete()
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
            data = resp.json()
            if not data or "data" not in data: return await msg.edit_text("Ошибка API.")
            
            task_id = data["data"].get("taskId")
            await msg.edit_text("Ожидайте...")
            for i in range(20):
                await asyncio.sleep(15)
                res = await client.get(f"{API_BASE}/recordInfo?taskId={task_id}", headers=headers)
                res_data = res.json()
                if res_data and res_data.get("data", {}).get("resultJson"):
                    url = json.loads(res_data["data"]["resultJson"]).get("resultUrls", [None])[0]
                    if url: await message.answer_photo(photo=url); return await msg.delete()
            await msg.edit_text("Время вышло.")
    else:
        msg = await message.answer("🤔...")
        headers = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}
        payload = {"messages": [{"role": "user", "content": message.text}]}
        async with httpx.AsyncClient(timeout=60.0) as client:
            try:
                resp = await client.post(CHAT_API_URL, json=payload, headers=headers)
                data = resp.json()
                if data and "choices" in data:
                    answer = data["choices"][0]["message"]["content"]
                    await msg.delete()
                    await send_long_message(message, answer)
            except Exception as e: await msg.edit_text(f"Ошибка: {str(e)}")

async def main(): await dp.start_polling(bot)
if __name__ == "__main__": asyncio.run(main())
