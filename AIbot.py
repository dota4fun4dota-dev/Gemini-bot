import asyncio
import logging
import httpx
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message
from aiogram.filters import CommandStart

BOT_TOKEN = "8980453196:AAGiMgy8bohMdOM6Z3nGpmos_ysCr2W_-Us"
API_KEY = "5911714ce3ffbc56f7064a9ad0708e0c" 
API_BASE = "https://api.kie.ai/api/v1/jobs"

logging.basicConfig(level=logging.INFO)
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

@dp.message(CommandStart())
async def start(message: Message):
    await message.answer("Бот готов! Пиши 'Нарисуй [описание]'.")

@dp.message(F.text.lower().startswith("нарисуй"))
async def image_handler(message: Message):
    prompt = message.text.lower().replace("нарисуй", "").strip()
    if not prompt:
        return await message.answer("Пожалуйста, напиши описание.")
    
    msg = await message.answer("⏳ Отправляю запрос во Flux-2 Pro...")
    
    headers = {
        "Authorization": f"Bearer {API_KEY}", 
        "Content-Type": "application/json"
    }
    
    # ФИНАЛЬНАЯ СТРУКТУРА ДЛЯ FLUX-2
    payload = {
        "model": "flux-2/pro-text-to-image",
        "input": {
            "prompt": prompt,
            "aspect_ratio": "1:1",
            "resolution": "1K"
        }
    }
    
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.post(f"{API_BASE}/createTask", json=payload, headers=headers)
            task_json = resp.json()
            logging.info(f"Ответ сервера: {task_json}")
            
            task_id = task_json.get("data", {}).get("taskId")
            if not task_id:
                return await msg.edit_text(f"❌ Ошибка создания: {task_json.get('msg')}")
            
            await msg.edit_text(f"🎨 Задача принята ({task_id}). Жду генерацию...")

            # Опрос статуса
            for i in range(25):
                await asyncio.sleep(15)
                status_resp = await client.get(f"{API_BASE}/recordInfo?taskId={task_id}", headers=headers)
                data = status_resp.json().get("data", {})
                
                state = data.get("state")
                if state == "success":
                    url = data.get("result", {}).get("url")
                    if url:
                        await message.answer_photo(photo=url, caption=f"Готово: {prompt}")
                        return await msg.delete()
                elif state == "fail":
                    return await msg.edit_text(f"❌ Ошибка генерации: {data.get('failMsg')}")
            
            await msg.edit_text("⚠️ Время ожидания вышло.")
        except Exception as e:
            await msg.edit_text(f"⚠️ Ошибка: {str(e)}")

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
