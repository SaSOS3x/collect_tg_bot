from aiogram import Bot, Dispatcher, types
from aiogram.filters.state import State, StatesGroup
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
import logging

# Импортируем модули из текущей директории
from settings import BOT_TOKEN, CHANNEL_ID
from text import WELCOME_MESSAGE, REGISTRATION_NAME, REGISTRATION_AGE, REGISTRATION_SUCCESS, POST_MESSAGE, POST_SUCCESS, VOLUNTEER_LINK, PSYCHOLOGIST_LINK
from menu import main_menu
from bd import save_user, save_post

# Инициализация бота
bot = Bot(token=BOT_TOKEN)

# Инициализация диспетчера
dp = Dispatcher()

# Настройка логирования
logging.basicConfig(level=logging.INFO)

# Состояния для регистрации
class Registration(StatesGroup):
    name = State()
    age = State()
    post = State()

# Обработчик команды /start
@dp.message(Command("start"))
async def start(message: types.Message, state: FSMContext):
    await message.answer(WELCOME_MESSAGE)
    await message.answer(REGISTRATION_NAME)
    await state.set_state(Registration.name)

# Обработчик ввода имени
@dp.message(Registration.name)
async def process_name(message: types.Message, state: FSMContext):
    await state.update_data(name=message.text)
    await message.answer(REGISTRATION_AGE)
    await state.set_state(Registration.age)

# Обработчик ввода возраста
@dp.message(Registration.age)
async def process_age(message: types.Message, state: FSMContext):
    if message.text.isdigit() and 12 <= int(message.text) <= 25:
        await state.update_data(age=int(message.text))
        user_data = await state.get_data()
        user_id = save_user(user_data['name'], user_data['age'])
        await state.update_data(user_id=user_id)  # Сохраняем user_id в состоянии
        await message.answer(REGISTRATION_SUCCESS, reply_markup=main_menu)
        await state.set_state(None)  # Сбрасываем состояние
    else:
        await message.answer("Пожалуйста, введите возраст от 12 до 25 лет.")

# Обработчик кнопки "Опубликовать пост"
@dp.message(lambda message: message.text == "Опубликовать пост")
async def publish_post(message: types.Message, state: FSMContext):
    user_data = await state.get_data()
    if 'user_id' not in user_data:
        await message.answer("Пожалуйста, завершите регистрацию, чтобы опубликовать пост.")
        return
    await message.answer(POST_MESSAGE)
    await state.set_state(Registration.post)

# Обработчик ввода поста
@dp.message(Registration.post)
async def process_post(message: types.Message, state: FSMContext):
    user_data = await state.get_data()
    if 'user_id' not in user_data:
        await message.answer("Ошибка: данные пользователя не найдены. Пожалуйста, начните с команды /start.")
        return

    save_post(user_data['user_id'], message.text)
    await bot.send_message(CHANNEL_ID, f"Новый пост от {user_data['name']}:\n\n{message.text}")
    await message.answer(POST_SUCCESS, reply_markup=main_menu)
    await state.clear()  # Очистка состояния

# Обработчик кнопки "Связь с проектом"
@dp.message(lambda message: message.text == "Связь с проектом")
async def contact_project(message: types.Message):
    await message.answer(VOLUNTEER_LINK)

# Обработчик кнопки "Стать волонтёром/психологом"
@dp.message(lambda message: message.text == "Стать волонтёром/психологом")
async def become_volunteer(message: types.Message):
    await message.answer(PSYCHOLOGIST_LINK)

