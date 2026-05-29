import asyncio
import logging
import httpx
import json
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message
from aiogram.filters import CommandStart

# === КОНФИГУРАЦИЯ ===
BOT_TOKEN = "8980453196:AAGiMgy8bohMdOM6Z3nGpmos_ysCr2W_-Us"
API_KEY = "5911714ce3ffbc56f7064a9ad0708e0c" 
API_BASE = "https://api.kie.ai/api/v1/jobs"

logging.basicConfig(level=logging.INFO)
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

@dp.message(CommandStart())
async def start(message: Message):
    await message.answer("Привет! Напиши 'Нарисуй [описание]', и я приступлю к работе.")

@dp.message(F.text.lower().startswith("нарисуй"))
async def image_handler(message: Message):
    prompt = message.text.lower().replace("нарисуй", "").strip()
    if not prompt:
        return await message.answer("Пожалуйста, напиши описание после слова 'Нарисуй'.")
    
    msg = await message.answer("⏳ Отправляю запрос на генерацию...")
    
    headers = {
        "Authorization": f"Bearer {API_KEY}", 
        "Content-Type": "application/json"
    }
    
    # ФИНАЛЬНАЯ СТРУКТУРА:
    # 1. Используем точное имя модели
    # 2. Передаем "prompt" (на английском!), как требует API
    payload = {
        "model": "google/imagen4-fast",
        "input": {
            "prompt": prompt
        }
    }
    
    async with httpx.AsyncClient() as client:
        try:
            # 1. Создание задачи
            resp = await client.post(f"{API_BASE}/createTask", json=payload, headers=headers)
            task_data = resp.json()
            
            # Логируем, если пришла ошибка на этапе создания
            if resp.status_code != 200:
                return await msg.edit_text(f"❌ Ошибка API ({resp.status_code}): {task_data.get('msg', 'Неизвестная ошибка')}")
            
            task_id = task_data.get("data", {}).get("taskId")
            if not task_id:
                return await msg.edit_text(f"❌ API не вернуло taskId. Ответ: {task_data}")
            
            await msg.edit_text(f"🎨 Задача принята (ID: {task_id}). Жду результат...")

            # 2. Опрос статуса
            for i in range(40):
                await asyncio.sleep(10)
                status_resp = await client.get(f"{API_BASE}/recordInfo?taskId={task_id}", headers=headers)
                data = status_resp.json()
                
                state = data.get("state")
                logging.info(f"Статус Imagen4 (попытка {i+1}): {state}")
                
                if state == "success":
                    image_url = data.get("result", {}).get("url")
                    # Если URL нет в result, пробуем достать из resultJson
                    if not image_url and data.get("resultJson"):
                        try:
                            image_url = json.loads(data["resultJson"]).get("url")
                        except:
                            pass
                    
                    if image_url:
                        await message.answer_photo(photo=image_url, caption=f"Готово: {prompt}")
                        return await msg.delete()
                    else:
                        return await msg.edit_text("❌ Задача выполнена, но ссылка на фото пустая.")
                
                elif state == "failed":
                    return await msg.edit_text("❌ Ошибка генерации на стороне сервера.")
            
            await msg.edit_text("⚠️ Время вышло. Попробуй еще раз чуть позже.")
            
        except Exception as e:
            logging.error(f"Ошибка в боте: {e}")
            await msg.edit_text(f"⚠️ Ошибка: {str(e)}")

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
