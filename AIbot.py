# === ОБРАБОТКА ТЕКСТОВЫХ ЗАПРОСОВ К ИИ ===
@dp.message(F.text)
async def handle_ai_request(message: Message):
    user_id = message.from_user.id
    sub_until, req_date, req_count = get_user(user_id)
    
    has_sub = False
    if sub_until:
        until_dt = datetime.strptime(sub_until, '%Y-%m-%d %H:%M:%S')
        if until_dt > datetime.now():
            has_sub = True

    if not has_sub:
        today = datetime.today().strftime('%Y-%m-%d')
        current_count = req_count if req_date == today else 0
        
        if current_count >= 3:
            limit_text = "⚠️ Лимит бесплатных запросов на сегодня исчерпан (3 из 3).\n\nЧтобы продолжить общаться с ИИ без ограничений, оформите подписку."
            await message.answer(limit_text, reply_markup=main_menu_keyboard())
            return
        else:
            increment_request(user_id, current_count)

    status_message = await message.answer("🧠 *ИИ генерирует ответ... Пожалуйста, подождите.*")
    
    try:
        response = await ai_client.chat.completions.create(
            model=AI_MODEL,
            messages=[
                {"role": "system", "content": "Ты — полезный и умный ИИ-ассистент. Отвечай четко, структурировано и на русском языке."},
                {"role": "user", "content": message.text}
            ],
            max_tokens=1500
        )
        ai_response = response.choices[0].message.content
        
        await status_message.delete()
        await message.answer(ai_response)
        
    except Exception as e:
        # Выводим реальный текст ошибки в логи сервера
        logging.error(f"Критическая ошибка ИИ: {e}")
        # Выводим ошибку прямо в Телеграм, чтобы сразу понять в чем косяк
        await status_message.edit_text(f"❌ **Ошибка при обращении к ИИ:**\n`{str(e)}` \n\nПроверьте баланс и статус ключа на сайте openrouter.ai")
