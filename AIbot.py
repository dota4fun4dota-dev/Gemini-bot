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
    await message.answer("Бот готов. Пиши 'Нарисуй [описание]'.")

@dp.message(F.text.lower().startswith("нарисуй"))
async def image_handler(message: Message):
    prompt = message.text.lower().replace("нарисуй", "").strip()
    msg = await message.answer("⏳ Создаю задачу...")
    
    headers = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}
    payload = {
        "model": "flux-2/pro-text-to-image",
        "input": {"prompt": prompt, "aspect_ratio": "1:1", "resolution": "1K"}
    }
    
    async with httpx.AsyncClient() as client:
        resp = await client.post(f"{API_BASE}/createTask", json=payload, headers=headers)
        task_id = resp.json().get("data", {}).get("TaskId")
        
        if not task_id:
            return await msg.edit_text(f"Ошибка: {resp.json()}")
        
        await msg.edit_text(f"🎨 Задача принята ({task_id}). Жду результат...")

        for i in range(20):
            await asyncio.sleep(15)
            status_resp = await client.get(f"{API_BASE}/recordInfo?taskId={task_id}", headers=headers)
            data = status_resp.json()
            
            # ВАЖНО: Смотрим, что пришло от recordInfo
            logging.info(f"ОТВЕТ RECORDINFO: {data}")
            
            # Проверяем разные варианты, где может лежать картинка
            res_data = data.get("data", {})
            url = res_data.get("result", {}).get("url") or res_data.get("output", {}).get("url")
            
            if url:
                await message.answer_photo(photo=url, caption=f"Готово: {prompt}")
                return await msg.delete()
            elif res_data.get("state") == "fail":
                return await msg.edit_text(f"Ошибка генерации: {res_data.get('failMsg')}")

        await msg.edit_text("⚠️ Сервер не прислал картинку вовремя.")

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
