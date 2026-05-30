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
    "imagen": "google/imagen4-fast"
}

def get_menu():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Flux-2 Pro (Высокое качество)", callback_data="set_flux")],
        [InlineKeyboardButton(text="Imagen 4 (Быстрый стиль)", callback_data="set_imagen")]
    ])

@dp.message(CommandStart())
async def start(message: Message):
    user_models[message.from_user.id] = MODELS["flux"]
    welcome_text = (
        "🤖 **Добро пожаловать в AI Art Bot!**\n\n"
        "Я умею превращать твои текстовые описания в уникальные изображения с помощью продвинутых нейросетей.\n\n"
        "**Как пользоваться:**\n"
        "1. Выбери модель в меню ниже.\n"
        "2. Напиши 'Нарисуй [твое описание]', например: *Нарисуй кота в космосе*.\n"
        "3. Подожди немного, пока я генерирую арт!\n\n"
        "**Мои возможности:**\n"
        "• Генерация фотореалистичных и художественных изображений.\n"
        "• Поддержка нескольких мощных моделей ИИ."
    )
    await message.answer(welcome_text, reply_markup=get_menu(), parse_mode="Markdown")

@dp.callback_query(F.data.startswith("set_"))
async def set_model(callback: CallbackQuery):
    model_key = callback.data.split("_")[1]
    user_models[callback.from_user.id] = MODELS.get(model_key, MODELS["flux"])
    await callback.message.answer(f"✅ Модель успешно изменена на: **{model_key.upper()}**", parse_mode="Markdown")
    await callback.answer()

@dp.message(F.text.lower().startswith("нарисуй"))
async def image_handler(message: Message):
    prompt = message.text.lower().replace("нарисуй", "").strip()
    if not prompt:
        return await message.answer("Пожалуйста, напиши описание после команды 'Нарисуй'.")
        
    model = user_models.get(message.from_user.id, MODELS["flux"])
    msg = await message.answer(f"⏳ Генерирую изображение через {model}...")
    
    headers = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}
    payload = {
        "model": model,
        "input": {"prompt": prompt, "aspect_ratio": "1:1", "resolution": "1K"}
    }
    
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.post(f"{API_BASE}/createTask", json=payload, headers=headers)
            task_data = resp.json()
            task_id = task_data.get("data", {}).get("taskId")
            
            if not task_id:
                return await msg.edit_text(f"❌ Ошибка: {task_data.get('msg')}")
            
            await msg.edit_text(f"🎨 Задача принята. Ожидайте...")

            for i in range(20):
                await asyncio.sleep(15)
                status_resp = await client.get(f"{API_BASE}/recordInfo?taskId={task_id}", headers=headers)
                data = status_resp.json().get("data", {})
                
                url = None
                if data.get("resultJson"):
                    res_obj = json.loads(data["resultJson"])
                    url = res_obj.get("resultUrls", [None])[0]
                
                if url:
                    await message.answer_photo(photo=url, caption=f"✨ Готово: {prompt}")
                    return await msg.delete()
                elif data.get("state") == "fail":
                    return await msg.edit_text("❌ Ошибка при генерации.")
            
            await msg.edit_text("⚠️ Превышено время ожидания.")
        except Exception as e:
            await msg.edit_text(f"⚠️ Ошибка: {str(e)}")

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
