from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

# Создаем кнопки
button_post = KeyboardButton(text="Опубликовать пост")

button_cancel = KeyboardButton(text="Отмена")

# Создаем клавиатуру
main_menu = ReplyKeyboardMarkup(
    keyboard=[
        [button_post],  # Первый ряд с одной кнопкой
    ],
    resize_keyboard=True,  # Автоматическое изменение размера клавиатуры
)

# Создаем меню с кнопкой "Отмена"
cancel_menu = ReplyKeyboardMarkup(
    keyboard=[
        [button_cancel],  # Кнопка "Отмена"
    ],
    resize_keyboard=True,
)