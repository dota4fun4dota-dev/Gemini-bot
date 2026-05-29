import asyncio
import logging
import httpx
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
        return await message.answer("Укажи описание картинки!")
    
    msg = await message.answer("⏳ Создаю задачу в Nano Banana 2...")
    
    headers = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}
    payload = {
        "model": "nano-banana-2",
        "input": {"prompt": prompt, "aspect_ratio": "auto", "resolution": "1K", "output_format": "png"}
    }
    
    async with httpx.AsyncClient() as client:
        try:
            # 1. Запрос на создание
            resp = await client.post(f"{API_BASE_URL}/api/v1/jobs/createTask", json=payload, headers=headers)
            if resp.status_code != 200:
                return await msg.edit_text(f"❌ Ошибка создания: {resp.text}")
            
            task_id = resp.json().get("data", {}).get("taskId")
            await msg.edit_text(f"🎨 Задача {task_id} принята. Ожидаю готовность...")
            
            # 2. Поллинг результата
            for i in range(30): # Ждем до 150 секунд
                await asyncio.sleep(5)
                status_resp = await client.get(f"{API_BASE_URL}/api/v1/jobs/recordInfo?taskId={task_id}", headers=headers)
                data = status_resp.json()
                
                # Логируем для отладки в Railway
                logging.info(f"DEBUG: Task {task_id} response: {data}")
                
                # Ищем статус в разных местах ответа
                job_data = data.get("data", {})
                status = job_data.get("status")
                
                if status == "success":
                    image_url = job_data.get("result", {}).get("url")
                    if image_url:
                        await message.answer_photo(photo=image_url, caption=f"Готово: {prompt}")
                        return await msg.delete()
                    else:
                        return await msg.edit_text("❌ Ошибка: Статус success, но ссылка на фото пустая.")
                
                if status == "failed":
                    return await msg.edit_text("❌ Генерация сорвалась на стороне API.")
            
            await msg.edit_text("⚠️ Превышено время ожидания. Попробуй еще раз.")
            
        except Exception as e:
            logging.error(f"Error: {e}")
            await msg.edit_text(f"⚠️ Ошибка выполнения: {str(e)}")

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
