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

# Хранилище моделей пользователей
user_models = {}

# Список доступных моделей
MODELS = {
    "flux": "flux-2/pro-text-to-image",
    "imagen": "google/imagen4-fast"
}

def get_menu():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Flux-2 Pro", callback_data="set_flux")],
        [InlineKeyboardButton(text="Imagen 4", callback_data="set_imagen")]
    ])

@dp.message(CommandStart())
async def start(message: Message):
    user_models[message.from_user.id] = MODELS["flux"] # По умолчанию
    await message.answer("Привет! Выбери модель для генерации:", reply_markup=get_menu())

@dp.callback_query(F.data.startswith("set_"))
async def set_model(callback: CallbackQuery):
    model_key = callback.data.split("_")[1]
    user_models[callback.from_user.id] = MODELS.get(model_key, MODELS["flux"])
    await callback.message.answer(f"✅ Модель установлена: {model_key.upper()}")
    await callback.answer()

@dp.message(F.text.lower().startswith("нарисуй"))
async def image_handler(message: Message):
    prompt = message.text.lower().replace("нарисуй", "").strip()
    model = user_models.get(message.from_user.id, MODELS["flux"])
    
    msg = await message.answer(f"⏳ Генерирую через {model}...")
    
    headers = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}
    payload = {
        "model": model,
        "input": {"prompt": prompt, "aspect_ratio": "1:1", "resolution": "1K"}
    }
    
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.post(f"{API_BASE}/createTask", json=payload, headers=headers)
            task_id = resp.json().get("data", {}).get("taskId")
            
            if not task_id:
                return await msg.edit_text(f"Ошибка API: {resp.json().get('msg')}")
            
            for i in range(20):
                await asyncio.sleep(15)
                status_resp = await client.get(f"{API_BASE}/recordInfo?taskId={task_id}", headers=headers)
                data = status_resp.json().get("data", {})
                
                url = None
                if data.get("resultJson"):
                    res_obj = json.loads(data["resultJson"])
                    url = res_obj.get("resultUrls", [None])[0]
                
                if url:
                    await message.answer_photo(photo=url, caption=f"Готово: {prompt} ({model})")
                    return await msg.delete()
        except Exception as e:
            await msg.edit_text(f"⚠️ Ошибка: {str(e)}")

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
