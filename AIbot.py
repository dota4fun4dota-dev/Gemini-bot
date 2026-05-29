import asyncio
import logging
import httpx
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message
from aiogram.filters import CommandStart

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
    msg = await message.answer("⏳ Отправляю задачу...")
    
    headers = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}
    payload = {
        "model": "nano-banana-2",
        "input": {"prompt": prompt, "aspect_ratio": "auto", "resolution": "1K", "output_format": "png"}
    }
    
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.post(f"{API_BASE_URL}/api/v1/jobs/createTask", json=payload, headers=headers)
            task_id = resp.json().get("data", {}).get("taskId")
            await msg.edit_text(f"🎨 Задача {task_id} принята. Жду результат...")
            
            # УВЕЛИЧИЛИ ВРЕМЯ: 40 попыток по 10 секунд = до 400 секунд ожидания
            for i in range(40):
                await asyncio.sleep(10)
                status_resp = await client.get(f"{API_BASE_URL}/api/v1/jobs/recordInfo?taskId={task_id}", headers=headers)
                data = status_resp.json()
                
                # ВЫВОДИМ В ЛОГИ ВСЁ, ЧТО ПРИШЛО
                logging.info(f"ОТВЕТ СЕРВЕРА: {data}")
                
                # Проверка по разным возможным ключам
                job_data = data.get("data", {})
                status = job_data.get("status")
                
                if status == "success":
                    image_url = job_data.get("result", {}).get("url")
                    await message.answer_photo(photo=image_url, caption=f"Готово: {prompt}")
                    return await msg.delete()
                elif status == "failed":
                    return await msg.edit_text(f"❌ Ошибка API: {job_data.get('error', 'неизвестно')}")
            
            await msg.edit_text("⚠️ Время вышло. Сервер всё ещё обрабатывает запрос.")
        except Exception as e:
            await msg.edit_text(f"⚠️ Ошибка: {str(e)}")

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
    
