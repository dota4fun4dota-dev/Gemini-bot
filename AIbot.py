def increment_count(user_id):
    conn = sqlite3.connect("bot_users.db")
    cursor = conn.cursor()
    
    # Сначала проверяем, есть ли пользователь и какой у него сейчас count
    cursor.execute("SELECT count, start_time FROM users WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    
    if row:
        current_count, start_time = row
        # Если это первый запрос (count 0), фиксируем время
        if current_count == 0 or not start_time:
            cursor.execute("UPDATE users SET count = 1, start_time = ? WHERE user_id = ?", 
                           (datetime.now().isoformat(), user_id))
        else:
            # Иначе просто увеличиваем
            cursor.execute("UPDATE users SET count = count + 1 WHERE user_id = ?", (user_id,))
    else:
        # Если пользователя вдруг нет, создаем его
        cursor.execute("INSERT INTO users (user_id, count, start_time) VALUES (?, ?, ?)", 
                       (user_id, 1, datetime.now().isoformat()))
        
    conn.commit()
    conn.close()
