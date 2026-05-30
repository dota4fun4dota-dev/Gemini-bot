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

logging.basicConfig(level=logging.INFO)
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

user_models = {}
MODELS = {
    "flux": "flux-2/pro-text-to-image",
    "imagen": "google/imagen4-fast",
    "grok_img": "grok-imagine/image-to-image" # Добавили модель для Img2Img
}

def get_menu():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Flux-2 Pro", callback_data="set_flux")],
        [InlineKeyboardButton(text="Imagen 4", callback_data="set_imagen")],
        [InlineKeyboardButton(text="Grok Img2Img", callback_data="set_grok_img")]
    ])

@dp.message(CommandStart())
async def start(message: Message):
    user_models[message.from_user.id] = MODELS["flux"]
    await message.answer("Бот готов! Выбери модель и пиши 'Нарисуй [описание]'.\nДля переделки фото — просто отправь фото с подписью.", reply_markup=get_menu())

@dp.callback_query(F.data.startswith("set_"))
async def set_model(callback: CallbackQuery):
    model_key = callback.data.split("_")[1]
    user_models[callback.from_user.id] = MODELS.get(model_key, MODELS["flux"])
    await callback.message.answer(f"✅ Модель установлена: {model_key.upper()}")
    await callback.answer()

# --- ПУНКТ 1: Текстовая генерация ---
@dp.message(F.text.lower().startswith("нарисуй"))
async def image_handler(message: Message):
    prompt = message.text.lower().replace("нарисуй", "").strip()
    model = user_models.get(message.from_user.id, MODELS["flux"])
    msg = await message.answer(f"⏳ Генерирую через {model}...")
    
    headers = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}
    payload = {"model": model, "input": {"prompt": prompt, "aspect_ratio": "1:1", "resolution": "1K"}}
    
    async with httpx.AsyncClient() as client:
        resp = await client.post(f"{API_BASE}/createTask", json=payload, headers=headers)
        task_id = resp.json().get("data", {}).get("taskId")
        if not task_id: return await msg.edit_text("Ошибка создания задачи.")
        
        for i in range(20):
            await asyncio.sleep(15)
            status_resp = await client.get(f"{API_BASE}/recordInfo?taskId={task_id}", headers=headers)
            data = status_resp.json().get("data", {})
            if data.get("resultJson"):
                res_obj = json.loads(data["resultJson"])
                url = res_obj.get("resultUrls", [None])[0]
                if url:
                    await message.answer_photo(photo=url, caption=f"Готово: {prompt}")
                    return await msg.delete()
        await msg.edit_text("⚠️ Ошибка или время вышло.")

# --- ПУНКТ 2: Обработка фото (Img2Img) ---
@dp.message(F.photo)
async def image_to_image_handler(message: Message):
    # ВАЖНО: Сейчас мы используем URL фото из Telegram, если Kie.ai поддерживает прямые ссылки
    file_id = message.photo[-1].file_id
    file = await bot.get_file(file_id)
    photo_url = f"https://api.telegram.org/file/bot{BOT_TOKEN}/{file.file_path}"
    
    prompt = message.caption or "Recreate this image"
    msg = await message.answer("⏳ Переделываю фото...")
    
    headers = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}
    payload = {
        "model": "grok-imagine/image-to-image",
        "input": {"prompt": prompt, "image_urls": [photo_url]}
    }
    
    async with httpx.AsyncClient() as client:
        resp = await client.post(f"{API_BASE}/createTask", json=payload, headers=headers)
        task_id = resp.json().get("data", {}).get("taskId")
        if not task_id: return await msg.edit_text(f"Ошибка Img2Img: {resp.json().get('msg')}")
        
        for i in range(20):
            await asyncio.sleep(15)
            status_resp = await client.get(f"{API_BASE}/recordInfo?taskId={task_id}", headers=headers)
            data = status_resp.json().get("data", {})
            if data.get("resultJson"):
                res_obj = json.loads(data["resultJson"])
                url = res_obj.get("resultUrls", [None])[0]
                if url:
                    await message.answer_photo(photo=url, caption="✨ Готово!")
                    return await msg.delete()
        await msg.edit_text("⚠️ Ошибка переделки.")

async def main(): await dp.start_polling(bot)
if __name__ == "__main__": asyncio.run(main())
