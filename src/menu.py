from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

# Создаем кнопки
button_post = KeyboardButton(text="Опубликовать пост")
button_contact = KeyboardButton(text="Связь с проектом")
button_volunteer = KeyboardButton(text="Стать волонтёром/психологом")

# Создаем клавиатуру
main_menu = ReplyKeyboardMarkup(
    keyboard=[
        [button_post],  # Первый ряд с одной кнопкой
        [button_contact],  # Второй ряд с одной кнопкой
        [button_volunteer],  # Третий ряд с одной кнопкой
    ],
    resize_keyboard=True,  # Автоматическое изменение размера клавиатуры
)