from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

# Создаем кнопки
button_post = KeyboardButton(text="Опубликовать пост")
button_change_name = KeyboardButton(text="Изменить имя")  # Новая кнопка
button_cancel = KeyboardButton(text="Отмена")

# Создаем клавиатуру
main_menu = ReplyKeyboardMarkup(
    keyboard=[
        [button_post],
        [button_change_name],  # Добавляем новый ряд с кнопкой
    ],
    resize_keyboard=True,
)

# Создаем меню с кнопкой "Отмена"
cancel_menu = ReplyKeyboardMarkup(
    keyboard=[
        [button_cancel],
    ],
    resize_keyboard=True,
)