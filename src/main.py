from bd import init_db
from logic import dp, bot

if __name__ == '__main__':
    init_db()
    # Запуск бота
    dp.run_polling(bot)