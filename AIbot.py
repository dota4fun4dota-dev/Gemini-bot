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
CHAT_API_URL = "https://api.kie.ai/gemini-3.1-pro/v1/chat/completions"

logging.basicConfig(level=logging.INFO)
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

@dp.startup()
async def on_startup():
    await bot.delete_webhook(drop_pending_updates=True)

@dp.message(CommandStart())
async def start(message: Message):
    await message.answer("Я снова в строю! Могу рисовать (начни с 'нарисуй...') или общаться.")

@dp.message(F.text)
async def handle_all_messages(message: Message):
    # Логика РИСОВАНИЯ
    if message.text.lower().startswith("нарисуй"):
        msg = await message.answer("🎨 Генерирую...")
        prompt = message.text.lower().replace("нарисуй", "").strip()
        payload = {"model": "flux-2/pro-text-to-image", "input": {"prompt": prompt, "aspect_ratio": "1:1"}}
        headers = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}
        
        async with httpx.AsyncClient() as client:
            try:
                resp = await client.post(f"{API_BASE}/createTask", json=payload, headers=headers)
                data = resp.json()
                # Безопасное извлечение taskId
                task_id = data.get("data", {}).get("taskId") if isinstance(data, dict) else None
                
                if not task_id:
                    return await msg.edit_text("Ошибка: API не вернуло ID задачи.")

                await msg.edit_text("Задача в очереди, жду результат...")
                for i in range(20):
                    await asyncio.sleep(10)
                    res = await client.get(f"{API_BASE}/recordInfo?taskId={task_id}", headers=headers)
                    res_data = res.json()
                    # Безопасное извлечение URL
                    result_json_str = res_data.get("data", {}).get("resultJson") if isinstance(res_data, dict) else None
                    if result_json_str:
                        url = json.loads(result_json_str).get("resultUrls", [None])[0]
                        if url: await message.answer_photo(photo=url, caption="✨ Готово!"); return await msg.delete()
                await msg.edit_text("Время вышло.")
            except Exception as e:
                await msg.edit_text(f"Ошибка рисования: {str(e)}")

    # Логика ОБЩЕНИЯ
    else:
        msg = await message.answer("🤔 Думаю...")
        headers = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}
        payload = {"messages": [{"role": "user", "content": message.text}]}
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            try:
                resp = await client.post(CHAT_API_URL, json=payload, headers=headers)
                data = resp.json()
                if isinstance(data, dict) and "choices" in data:
                    answer = data["choices"][0]["message"]["content"]
                    await msg.delete()
                    await message.answer(answer)
                else:
                    await msg.edit_text("Не удалось получить ответ от модели.")
            except Exception as e:
                await msg.edit_text(f"Ошибка чата: {str(e)}")

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
