from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

# Создаем inline-кнопки
async def inline_kb_full_example(user_login, example_url):

    button1 = [InlineKeyboardButton(text="Подробнее", url=f"{example_url}")] # Кнопка с ссылкой
    button2 = [InlineKeyboardButton(text="Связаться", url=f"https://t.me/{user_login}")] # Кнопка с ссылкой на Telegram

    if example_url == "":
        call_keyboard = InlineKeyboardMarkup(inline_keyboard=[button2])
    elif user_login == "":
        call_keyboard = InlineKeyboardMarkup(inline_keyboard=[button1])
    elif example_url == "" and user_login == "":
        call_keyboard = None
    else:
        call_keyboard = InlineKeyboardMarkup(inline_keyboard=[
            button1,
            button2
        ])

    return call_keyboard