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
from text import WELCOME_MESSAGE, REGISTRATION_NAME, REGISTRATION_SUCCESS, POST_MESSAGE, POST_SUCCESS, CANCEL_MESSAGE
from menu import main_menu, cancel_menu
from bd import save_user, save_post, is_user_registered, get_username, update_user
from utils import default_post_text

# Инициализация бота
bot = Bot(token=BOT_TOKEN)

# Инициализация диспетчера
dp = Dispatcher()

# Настройка логирования
logging.basicConfig(level=logging.INFO)

# Состояния для регистрации
class Registration(StatesGroup):
    name = State()
    post = State()

# Добавим новое состояние для смены имени
class ChangeName(StatesGroup):
    name = State()

# Хранение медиагрупп
media_groups = defaultdict(list)

# Флаги для отслеживания отправленных медиагрупп
sent_media_groups = set()

# Блокировка для безопасного доступа к медиагруппам
media_groups_lock = asyncio.Lock()

# Обработчик команды /start
@dp.message(Command("start")) # Команда обрабатывается после символа "/"
async def start(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    if await is_user_registered(user_id):
        await message.answer("Вы уже зарегистрированы! Что вы хотите сделать?", reply_markup=main_menu)
    else:
        await message.answer(WELCOME_MESSAGE)
        await message.answer(REGISTRATION_NAME)
        await state.set_state(Registration.name)

# Обработчик ввода имени
@dp.message(Registration.name)
async def process_name(message: types.Message, state: FSMContext):
    await state.update_data(name=message.text)

    user_id = message.from_user.id
    user_data = await state.get_data()

    await save_user(user_id, user_data['name'])

    logging.info(f"Create new user: {user_id} with name: {user_data['name']}")

    await message.answer(REGISTRATION_SUCCESS, reply_markup=main_menu)

    await state.clear()  # Очистка состояния



# Новый обработчик кнопки "Изменить имя"
@dp.message(lambda message: message.text == "Изменить имя")
async def change_name_start(message: types.Message, state: FSMContext):
    if not await is_user_registered(message.from_user.id):
        await message.answer("Сначала зарегистрируйтесь!")
        return
        
    await message.answer("Введите новое имя:", reply_markup=cancel_menu)
    await state.set_state(ChangeName.name)

# Обработчик отмены для нового состояния
@dp.message(lambda message: message.text == "Отмена", ChangeName.name)
async def cancel_name_change(message: types.Message, state: FSMContext):
    await message.answer("Изменение имени отменено", reply_markup=main_menu)
    await state.clear()

# Обработчик нового имени
@dp.message(ChangeName.name)
async def process_new_name(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    new_name = message.text
    
    # Обновляем имя в БД
    await update_user(user_id, new_name)
    
    logging.info(f"User {user_id} changed name to {new_name}")

    await message.answer(f"Имя успешно изменено на: {new_name}", reply_markup=main_menu)
    await state.clear()
    


# Обработчик кнопки "Опубликовать пост"
@dp.message(lambda message: message.text == "Опубликовать пост")
async def publish_post(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    if not await is_user_registered(user_id):
        await message.answer("Пожалуйста, завершите регистрацию, чтобы опубликовать пост.")
        return
    await message.answer(POST_MESSAGE, reply_markup=cancel_menu)
    await state.set_state(Registration.post)

# Обработчик кнопки "Отмена"
@dp.message(lambda message: message.text == "Отмена", Registration.post)
async def cancel_post(message: types.Message, state: FSMContext):
    await message.answer(CANCEL_MESSAGE, reply_markup=main_menu)
    await state.clear()  # Очистка состояния



# Обработчик текстового поста
@dp.message(Registration.post, lambda message: message.text)
async def process_post(message: types.Message, state: FSMContext):

    user_id = message.from_user.id
    user_login = message.from_user.username
    
    message_from_chat = await bot.send_message(CHANNEL_ID, await default_post_text(await get_username(user_id), user_login, message.text), parse_mode="HTML") # Отправка сообщения с обработчиком default_post_text

    logging.info(f"User {user_id} created new post in channel: {CHANNEL_ID}")

    await save_post(user_id, message.text, message_from_chat.message_id)

    await message.answer(POST_SUCCESS, reply_markup=main_menu)
    await state.clear()  # Очистка состояния



# Обработчик медиагрупп (несколько фото/видео)
@dp.message(Registration.post, lambda message: message.media_group_id)
async def process_media_group(message: types.Message, state: FSMContext):
    media_group_id = message.media_group_id
    user_id = message.from_user.id

    user_login = message.from_user.username

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
        message.caption
        # Если это первое сообщение в медиагруппе, сохраняем подпись
        if message.caption:
            media_groups[media_group_id][-1].caption = await default_post_text(await get_username(user_id), user_login, message.caption)
            media_groups[media_group_id][-1].parse_mode = "HTML"

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
                media=media_list,
            )
            
            message_from_chat = await bot.send_message(user_id, POST_SUCCESS, reply_markup=main_menu)

            await save_post(user_id, f"Медиагруппа: {len(media_list)} файлов", message_from_chat.message_id)

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