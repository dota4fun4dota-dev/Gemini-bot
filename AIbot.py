import asyncio
import logging
import httpx
import json
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message
from aiogram.filters import CommandStart

# === КОНФИГУРАЦИЯ ===
BOT_TOKEN = "8980453196:AAGiMgy8bohMdOM6Z3nGpmos_ysCr2W_-Us"
API_BASE_URL = "https://api.kie.ai" 
API_KEY = "5911714ce3ffbc56f7064a9ad0708e0c" 

logging.basicConfig(level=logging.INFO)
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

@dp.message(CommandStart())
async def start(message: Message):
    await message.answer("Привет! Напиши 'Нарисуй [описание]', и я создам картинку.")

@dp.message(F.text.lower().startswith("нарисуй"))
async def image_handler(message: Message):
    prompt = message.text.lower().replace("нарисуй", "").strip()
    if not prompt:
        return await message.answer("Пожалуйста, напиши что нарисовать.")
    
    msg = await message.answer("⏳ Отправляю задачу в нейросеть...")
    
    headers = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}
    payload = {
        "model": "nano-banana-2",
        "input": {"prompt": prompt, "aspect_ratio": "1:1", "resolution": "1K", "output_format": "png"}
    }
    
    async with httpx.AsyncClient() as client:
        try:
            # 1. Создание задачи
            resp = await client.post(f"{API_BASE_URL}/api/v1/jobs/createTask", json=payload, headers=headers)
            if resp.status_code != 200:
                return await msg.edit_text(f"❌ Ошибка создания задачи: {resp.text}")
            
            task_id = resp.json()["data"]["taskId"]
            await msg.edit_text(f"🎨 Задача {task_id} принята. Рисую...")
            
            # 2. Опрос статуса
            for i in range(30):
                await asyncio.sleep(10)
                status_resp = await client.get(f"{API_BASE_URL}/api/v1/jobs/recordInfo?taskId={task_id}", headers=headers)
                data = status_resp.json().get("data", {})
                
                # Проверяем состояние
                state = data.get("state")
                
                if state == "success":
                    # Пытаемся достать URL из result, если пусто - из resultJson
                    image_url = data.get("result", {}).get("url")
                    if not image_url and data.get("resultJson"):
                        image_url = json.loads(data["resultJson"]).get("url")
                    
                    if image_url:
                        await message.answer_photo(photo=image_url, caption=f"Готово: {prompt}")
                        return await msg.delete()
                    else:
                        return await msg.edit_text("❌ Ошибка: статус success, но ссылка на изображение не найдена.")
                
                elif state == "failed":
                    return await msg.edit_text("❌ Ошибка: Генерация не удалась (failed).")
            
            await msg.edit_text("⚠️ Время ожидания вышло. Сервер всё ещё обрабатывает запрос.")
        except Exception as e:
            logging.error(f"Error: {e}")
            await msg.edit_text(f"⚠️ Произошла ошибка: {str(e)}")

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
