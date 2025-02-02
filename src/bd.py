import aiosqlite

async def init_db():
    async with aiosqlite.connect('bot.db') as conn:
        cursor = await conn.cursor()
        await cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL UNIQUE,
                name TEXT NOT NULL
            )
        ''')
        await cursor.execute('''
            CREATE TABLE IF NOT EXISTS posts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                message TEXT NOT NULL,
                message_id INTEGER NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            )
        ''')
        await conn.commit()

async def save_user(user_id, name):
    async with aiosqlite.connect('bot.db') as conn:
        cursor = await conn.cursor()
        await cursor.execute('INSERT INTO users (user_id, name) VALUES (?, ?)', (user_id, name))
        await conn.commit()

async def save_post(user_id, message, message_id):
    async with aiosqlite.connect('bot.db') as conn:
        cursor = await conn.cursor()
        await cursor.execute('INSERT INTO posts (user_id, message, message_id) VALUES (?, ?, ?)', (user_id, message, 0))
        await conn.commit()

async def is_user_registered(user_id):
    async with aiosqlite.connect('bot.db') as conn:
        cursor = await conn.cursor()
        await cursor.execute('SELECT user_id FROM users WHERE user_id = ?', (user_id,))
        result = await cursor.fetchone()
        return result is not None

async def get_username(user_id):
    async with aiosqlite.connect('bot.db') as conn:
        cursor = await conn.cursor()
        await cursor.execute('SELECT name FROM users WHERE user_id = ?', (user_id,))
        result = await cursor.fetchone()
        return result[0] if result else None
    
async def update_user(user_id, new_name):
    async with aiosqlite.connect('bot.db') as conn:
        cursor = await conn.cursor()
        await cursor.execute('UPDATE users SET name = ? WHERE user_id = ?', (new_name, user_id))
        await conn.commit()