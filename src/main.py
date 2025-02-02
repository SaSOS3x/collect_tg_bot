import asyncio
import signal
import sys
from logging import info, error

from bd import init_db
from logic import bot, dp

async def on_startup():
    """Функция, которая выполняется при запуске бота."""
    info("Бот запущен")
    await init_db()  # Инициализация базы данных

async def on_shutdown():
    """Функция, которая выполняется при завершении работы бота."""
    info("Бот завершает работу...")
    await dp.storage.close()
    await bot.close()

async def main():
    """Основная асинхронная функция для запуска бота."""
    try:
        # Запуск бота с обработчиками startup и shutdown
        await dp.start_polling(
            bot,
            skip_updates=True,
            on_startup=on_startup,
            on_shutdown=on_shutdown,
        )
    except (asyncio.CancelledError, KeyboardInterrupt):
        info("Бот остановлен вручную")
    except Exception as e:
        error(f"Ошибка: {e}")
    finally:
        # Завершаем работу asyncio
        await asyncio.sleep(0.1)  # Даем время для завершения задач
        info("Бот завершил работу.")

def handle_signal(signum, frame):
    """Обработчик сигналов для graceful shutdown."""
    info(f"Получен сигнал {signum}, завершение работы...")
    # Отменяем все задачи asyncio
    for task in asyncio.all_tasks():
        task.cancel()

if __name__ == '__main__':
    # Регистрация обработчиков сигналов
    signal.signal(signal.SIGINT, handle_signal)  # Ctrl+C
    signal.signal(signal.SIGTERM, handle_signal)  # Сигнал завершения

    # Запуск асинхронной main
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        info("Бот завершил работу.")