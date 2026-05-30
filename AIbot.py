import asyncio
import logging
import httpx
import json
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
    await message.answer("Бот готов. Пиши 'Нарисуй [описание]'.")

@dp.message(F.text.lower().startswith("нарисуй"))
async def image_handler(message: Message):
    prompt = message.text.lower().replace("нарисуй", "").strip()
    if not prompt:
        return await message.answer("Укажите, что нарисовать.")
    
    msg = await message.answer("⏳ Создаю задачу...")
    
    headers = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}
    payload = {
        "model": "flux-2/pro-text-to-image",
        "input": {"prompt": prompt, "aspect_ratio": "1:1", "resolution": "1K"}
    }
    
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.post(f"{API_BASE}/createTask", json=payload, headers=headers)
            data_resp = resp.json()
            task_id = data_resp.get("data", {}).get("taskId")
            
            if not task_id:
                return await msg.edit_text(f"Ошибка: {data_resp}")
            
            await msg.edit_text(f"🎨 Задача принята. Жду результат...")

            for i in range(20):
                await asyncio.sleep(15)
                status_resp = await client.get(f"{API_BASE}/recordInfo?taskId={task_id}", headers=headers)
                data = status_resp.json().get("data", {})
                
                # Обработка resultJson из логов
                result_json_str = data.get("resultJson")
                url = None
                
                if result_json_str:
                    try:
                        res_obj = json.loads(result_json_str)
                        # Извлекаем из ключа resultUrls, который мы увидели в логах
                        urls = res_obj.get("resultUrls")
                        if urls and isinstance(urls, list):
                            url = urls[0]
                    except Exception as e:
                        logging.error(f"Ошибка парсинга JSON: {e}")
                
                if url:
                    await message.answer_photo(photo=url, caption=f"Готово: {prompt}")
                    return await msg.delete()
                elif data.get("state") == "fail":
                    return await msg.edit_text("❌ Ошибка генерации.")

            await msg.edit_text("⚠️ Время вышло.")
        except Exception as e:
            logging.error(f"Ошибка: {e}")
            await msg.edit_text(f"⚠️ Ошибка выполнения.")

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
