import asyncio
import logging
import httpx
import json
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message
from aiogram.filters import CommandStart

# Твои данные
BOT_TOKEN = "8980453196:AAGiMgy8bohMdOM6Z3nGpmos_ysCr2W_-Us"
API_KEY = "5911714ce3ffbc56f7064a9ad0708e0c" 
API_BASE = "https://api.kie.ai/api/v1/jobs"

logging.basicConfig(level=logging.INFO)
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

@dp.message(CommandStart())
async def start(message: Message):
    await message.answer("Привет! Напиши 'Нарисуй [описание]', и я создам картинку через Imagen4-Fast.")

@dp.message(F.text.lower().startswith("нарисуй"))
async def image_handler(message: Message):
    prompt = message.text.lower().replace("нарисуй", "").strip()
    msg = await message.answer("⏳ Запускаю Imagen4-Fast...")
    
    headers = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}
    
    # ИСПОЛЬЗУЕМ IMAGEN4-FAST
    payload = {
        "model": "imagen4-fast",
        "input": {"prompt": prompt}
    }
    
    async with httpx.AsyncClient() as client:
        try:
            # 1. Создание задачи
            resp = await client.post(f"{API_BASE}/createTask", json=payload, headers=headers)
            task_data = resp.json()
            task_id = task_data.get("taskId") or task_data.get("data", {}).get("taskId")
            
            if not task_id:
                return await msg.edit_text(f"❌ Ошибка API: {task_data}")
            
            await msg.edit_text(f"🎨 Задача принята (ID: {task_id}). Жду результат...")

            # 2. Опрос статуса
            for _ in range(40):
                await asyncio.sleep(8)
                status_resp = await client.get(f"{API_BASE}/recordInfo?taskId={task_id}", headers=headers)
                data = status_resp.json()
                
                state = data.get("state")
                logging.info(f"Статус Imagen4-Fast: {state}")
                
                if state == "success":
                    image_url = data.get("result", {}).get("url")
                    if not image_url and data.get("resultJson"):
                        image_url = json.loads(data["resultJson"]).get("url")
                    
                    if image_url:
                        await message.answer_photo(photo=image_url, caption=f"Готово: {prompt}")
                        return await msg.delete()
                    else:
                        return await msg.edit_text("❌ Успех, но сервер не прислал ссылку на картинку.")
                
                if state == "failed":
                    return await msg.edit_text("❌ Генерация не удалась.")
            
            await msg.edit_text("⚠️ Сервер долго не отвечает. Попробуй позже.")
            
        except Exception as e:
            await msg.edit_text(f"⚠️ Ошибка: {str(e)}")

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
