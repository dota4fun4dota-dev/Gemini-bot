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
CHAT_API_URL = "https://api.kie.ai/gemini-3.1-pro/v1/chat/completions" # Новый URL для чата

logging.basicConfig(level=logging.INFO)
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

user_models = {}
MODELS = {
    "flux": "flux-2/pro-text-to-image",
    "imagen": "google/imagen4-fast",
    "grok_img": "grok-imagine/image-to-image"
}

# --- Логика авто-определения ---
@dp.message(F.photo)
async def handle_photo(message: Message):
    # ПУНКТ 2: Переделка фото (Img2Img)
    file = await bot.get_file(message.photo[-1].file_id)
    photo_url = f"https://api.telegram.org/file/bot{BOT_TOKEN}/{file.file_path}"
    prompt = message.caption or "Enhance this image"
    
    msg = await message.answer("⏳ Обрабатываю фото через Grok...")
    payload = {"model": "grok-imagine/image-to-image", "input": {"prompt": prompt, "image_urls": [photo_url]}}
    headers = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}
    
    async with httpx.AsyncClient() as client:
        resp = await client.post(f"{API_BASE}/createTask", json=payload, headers=headers)
        task_id = resp.json().get("data", {}).get("taskId")
        
        for i in range(15):
            await asyncio.sleep(15)
            data = (await client.get(f"{API_BASE}/recordInfo?taskId={task_id}", headers=headers)).json().get("data", {})
            if data.get("resultJson"):
                url = json.loads(data["resultJson"]).get("resultUrls", [None])[0]
                if url:
                    await message.answer_photo(photo=url, caption="✨ Готово!")
                    return await msg.delete()
        await msg.edit_text("⚠️ Ошибка или время вышло.")

@dp.message(F.text)
async def handle_text(message: Message):
    # ПУНКТ 1: Рисование по тексту
    if message.text.lower().startswith("нарисуй"):
        prompt = message.text.lower().replace("нарисуй", "").strip()
        model = user_models.get(message.from_user.id, MODELS["flux"])
        msg = await message.answer(f"🎨 Рисую через {model}...")
        
        headers = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}
        payload = {"model": model, "input": {"prompt": prompt, "aspect_ratio": "1:1"}}
        
        async with httpx.AsyncClient() as client:
            resp = await client.post(f"{API_BASE}/createTask", json=payload, headers=headers)
            task_id = resp.json().get("data", {}).get("taskId")
            # ... (логика ожидания как раньше, сокращено для краткости)
            # Вставь сюда цикл ожидания из нашего "золотого" кода
            await message.answer("Задача принята, ожидайте результат.")
            
    # ПУНКТ 3: Умный чат (Gemini)
    else:
        msg = await message.answer("🤔 Думаю...")
        headers = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}
        payload = {
            "messages": [{"role": "user", "content": [{"type": "text", "text": message.text}]}]
        }
        async with httpx.AsyncClient() as client:
            resp = await client.post(CHAT_API_URL, json=payload, headers=headers)
            answer = resp.json().get("choices", [{}])[0].get("message", {}).get("content", "Не удалось получить ответ.")
            await msg.edit_text(answer)

# ... (остальной код: start, main, и т.д.)
