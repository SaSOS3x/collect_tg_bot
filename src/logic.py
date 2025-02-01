from aiogram import Bot, Dispatcher, types
from aiogram.filters.state import State, StatesGroup
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import InputMediaPhoto, InputMediaVideo, InputMediaAudio, InputMediaDocument
import logging
from collections import defaultdict
import asyncio

# Импортируем модули из текущей директории
from settings import BOT_TOKEN, CHANNEL_ID
from text import WELCOME_MESSAGE, REGISTRATION_NAME, REGISTRATION_AGE, REGISTRATION_SUCCESS, POST_MESSAGE, POST_SUCCESS, VOLUNTEER_LINK, PSYCHOLOGIST_LINK
from menu import main_menu
from bd import save_user, save_post, is_user_registered

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

# Хранение медиагрупп
media_groups = defaultdict(list)

# Флаги для отслеживания отправленных медиагрупп
sent_media_groups = set()

# Блокировка для безопасного доступа к медиагруппам
media_groups_lock = asyncio.Lock()

# Обработчик команды /start
@dp.message(Command("start"))
async def start(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    if is_user_registered(user_id):
        await message.answer("Вы уже зарегистрированы! Что вы хотите сделать?", reply_markup=main_menu)
    else:
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
        user_id = message.from_user.id
        user_data = await state.get_data()
        save_user(user_id, user_data['name'], int(message.text))
        await message.answer(REGISTRATION_SUCCESS, reply_markup=main_menu)
        await state.clear()  # Очистка состояния
    else:
        await message.answer("Пожалуйста, введите возраст от 12 до 25 лет.")

# Обработчик кнопки "Опубликовать пост"
@dp.message(lambda message: message.text == "Опубликовать пост")
async def publish_post(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    if not is_user_registered(user_id):
        await message.answer("Пожалуйста, завершите регистрацию, чтобы опубликовать пост.")
        return
    await message.answer(POST_MESSAGE)
    await state.set_state(Registration.post)

# Обработчик текстового поста
@dp.message(Registration.post, lambda message: message.text)
async def process_post(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    save_post(user_id, message.text)
    await bot.send_message(CHANNEL_ID, f"Новый пост от {message.from_user.full_name}:\n\n{message.text}")
    await message.answer(POST_SUCCESS, reply_markup=main_menu)
    await state.clear()  # Очистка состояния

# Обработчик медиагрупп (несколько фото/видео)
@dp.message(Registration.post, lambda message: message.media_group_id)
async def process_media_group(message: types.Message, state: FSMContext):
    media_group_id = message.media_group_id
    user_id = message.from_user.id

    async with media_groups_lock:
        # Если медиагруппа уже отправлена, игнорируем
        if media_group_id in sent_media_groups:
            return

        # Добавляем текущее сообщение в медиагруппу
        if message.photo:
            media_groups[media_group_id].append(
                InputMediaPhoto(media=message.photo[-1].file_id)
            )
        elif message.video:
            media_groups[media_group_id].append(
                InputMediaVideo(media=message.video.file_id)
            )
        elif message.audio:
            media_groups[media_group_id].append(
                InputMediaAudio(media=message.audio.file_id)
            )
        elif message.document:
            media_groups[media_group_id].append(
                InputMediaDocument(media=message.document.file_id)
            )

        # Если это первое сообщение в медиагруппе, сохраняем подпись
        if message.caption:
            media_groups[media_group_id][-1].caption = f"Новый пост от {message.from_user.full_name}:\n\n{message.caption}"

    # Запускаем таймер для отправки медиагруппы
    asyncio.create_task(send_media_group_after_delay(media_group_id, user_id, state))

# Функция для отправки медиагруппы после задержки
async def send_media_group_after_delay(media_group_id, user_id, state):
    # Ждем 2 секунды перед отправкой
    await asyncio.sleep(2)

    async with media_groups_lock:
        # Если медиагруппа уже отправлена, игнорируем
        if media_group_id in sent_media_groups:
            return

        # Если медиагруппа собрана, отправляем её
        if media_group_id in media_groups:
            media_list = media_groups[media_group_id]

            await bot.send_media_group(
                CHANNEL_ID,
                media=media_list
            )
            save_post(user_id, f"Медиагруппа: {len(media_list)} файлов")
            await bot.send_message(user_id, POST_SUCCESS, reply_markup=main_menu)
            await state.clear()  # Очистка состояния

            # Помечаем медиагруппу как отправленную
            sent_media_groups.add(media_group_id)

            # Удаляем медиагруппу из хранилища
            del media_groups[media_group_id]

# Обработчик одиночных фото
@dp.message(Registration.post, lambda message: message.photo and not message.media_group_id)
async def process_photo(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    photo_id = message.photo[-1].file_id  # Берем самое большое фото
    caption = message.caption if message.caption else "Фото без подписи"
    save_post(user_id, f"Фото: {caption}")
    await bot.send_photo(CHANNEL_ID, photo_id, caption=f"Новый пост от {message.from_user.full_name}:\n\n{caption}")
    await message.answer(POST_SUCCESS, reply_markup=main_menu)
    await state.clear()  # Очистка состояния

# Обработчик одиночных видео
@dp.message(Registration.post, lambda message: message.video and not message.media_group_id)
async def process_video(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    video_id = message.video.file_id
    caption = message.caption if message.caption else "Видео без подписи"
    save_post(user_id, f"Видео: {caption}")
    await bot.send_video(CHANNEL_ID, video_id, caption=f"Новый пост от {message.from_user.full_name}:\n\n{caption}")
    await message.answer(POST_SUCCESS, reply_markup=main_menu)
    await state.clear()  # Очистка состояния

# Обработчик документов
@dp.message(Registration.post, lambda message: message.document)
async def process_document(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    document_id = message.document.file_id
    caption = message.caption if message.caption else "Документ без подписи"
    save_post(user_id, f"Документ: {caption}")
    await bot.send_document(CHANNEL_ID, document_id, caption=f"Новый пост от {message.from_user.full_name}:\n\n{caption}")
    await message.answer(POST_SUCCESS, reply_markup=main_menu)
    await state.clear()  # Очистка состояния

# Обработчик голосовых сообщений
@dp.message(Registration.post, lambda message: message.voice)
async def process_voice(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    voice_id = message.voice.file_id
    caption = message.caption if message.caption else "Голосовое сообщение"
    save_post(user_id, f"Голосовое сообщение: {caption}")
    await bot.send_voice(CHANNEL_ID, voice_id, caption=f"Новый пост от {message.from_user.full_name}:\n\n{caption}")
    await message.answer(POST_SUCCESS, reply_markup=main_menu)
    await state.clear()  # Очистка состояния

# Обработчик аудио
@dp.message(Registration.post, lambda message: message.audio)
async def process_voice(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    audio_id = message.audio.file_id
    caption = message.caption if message.caption else "Музыка / Аудио"
    save_post(user_id, f"Музыка / Аудио: {caption}")
    await bot.send_audio(CHANNEL_ID, audio_id, caption=f"Новый пост от {message.from_user.full_name}:\n\n{caption}")
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