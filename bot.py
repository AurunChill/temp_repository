import asyncio
from pathlib import Path
from collections import defaultdict

from aiogram import Bot, Dispatcher, F
from aiogram.fsm.context import FSMContext
from aiogram.client.default import DefaultBotProperties
from aiogram.fsm.state import StatesGroup, State
from aiogram.filters import Command
from aiogram.types import (
    Message,
    CallbackQuery,
    FSInputFile,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    ReplyKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardRemove,
    InputMediaPhoto,
)

API_TOKEN = '7083557118:AAHBdNxqMrP89ayO9ZUWwbKCQ1Sd4umSDgk'
GROUP_CHAT_ID = '-1002152922264'
IMAGE_FOLDER = Path(__file__).parent / 'images'
IMAGES = {
    'start_image': IMAGE_FOLDER / 'image1.png',
    'button1': IMAGE_FOLDER / 'image2.png',
    'button2': IMAGE_FOLDER / 'image3.png',
    'button3': IMAGE_FOLDER / 'image4.png',
    'button4': IMAGE_FOLDER / 'image5.png',
    'button5': IMAGE_FOLDER / 'image6.png',
}

# Инициализация бота и диспетчера
bot = Bot(API_TOKEN, default=DefaultBotProperties(parse_mode='html'))
dp = Dispatcher(bot=bot)


class UserStates(StatesGroup):
    """Состояния для FSM."""
    waiting_for_message = State()
    waiting_for_phone = State()


# Словарь для хранения истории состояний пользователей
user_history = defaultdict(list)

# Словарь для хранения данных пользователей
user_data = defaultdict(lambda: {
    'username': '',
    'actions': [],
    'current_context': None,
    'group_message_id': None,  # Добавлено для хранения ID сообщения в группе
})


def get_start_keyboard() -> InlineKeyboardMarkup:
    """Функция для создания начальной клавиатуры."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text='Кнопка 1', callback_data='button1')],
            [InlineKeyboardButton(text='Кнопка 2', callback_data='button2')],
            [InlineKeyboardButton(text='Кнопка 3', callback_data='button3')],
        ]
    )


def get_button1_keyboard() -> InlineKeyboardMarkup:
    """Функция для создания клавиатуры при нажатии Кнопки 1."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text='Кнопка 4', callback_data='button4')],
            [InlineKeyboardButton(text='Кнопка 5', callback_data='button5')],
            [InlineKeyboardButton(text='Назад', callback_data='back')],
        ]
    )


def get_back_keyboard() -> InlineKeyboardMarkup:
    """Функция для создания клавиатуры "Назад"."""
    return InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text='Назад', callback_data='back')]]
    )


share_phone_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text='Поделиться номером телефона', request_contact=True)]
    ],
    resize_keyboard=True,
    one_time_keyboard=True,
)


def get_user_display_name(user) -> str:
    """Возвращает отображаемое имя пользователя."""
    if user.username:
        return f'@{user.username}'
    else:
        return f'<a href="tg://openmessage?user_id={user.id}">{user.full_name}</a>'


async def update_group_message(user_id: int):
    """Обновляет сообщение в группе с текущими данными пользователя."""
    user_info = user_data[user_id]
    actions_list = '\n'.join(user_info['actions'])
    phone = user_info.get('phone', 'Не предоставлен')
    message_text = (
        f'<b>Новая заявка от пользователя:</b> {user_info["username"]}\n'
        f'<b>Номер телефона:</b> {phone}\n\n'
        f'<b>Выбранные опции:</b>\n{actions_list}'
    )
    group_message_id = user_info.get('group_message_id')
    if group_message_id:
        try:
            await bot.edit_message_text(
                chat_id=GROUP_CHAT_ID,
                message_id=group_message_id,
                text=message_text
            )
        except Exception as e:
            print(f'Ошибка при редактировании сообщения: {e}')
    else:
        try:
            sent_message = await bot.send_message(
                chat_id=GROUP_CHAT_ID,
                text=message_text
            )
            user_info['group_message_id'] = sent_message.message_id
        except Exception as e:
            print(f'Ошибка при отправке сообщения: {e}')


@dp.message(Command('start'))
async def send_welcome(message: Message, state: FSMContext):
    """Обработчик команды /start."""
    user_id = message.from_user.id
    user = message.from_user
    display_name = get_user_display_name(user)
    print(f'Пользователь {user_id} нажал /start')

    # Инициализируем историю и данные для пользователя
    user_history[user_id] = []
    user_data[user_id]['username'] = display_name

    # Отправляем сообщение в группу и сохраняем его ID
    try:
        group_message = await bot.send_message(
            chat_id=GROUP_CHAT_ID,
            text=f'Зарегистрился новый пользователь: {display_name}'
        )
        user_data[user_id]['group_message_id'] = group_message.message_id
    except Exception as e:
        print(f'Ошибка при отправке сообщения в группу: {e}')

    # Отправляем пользователю приветственное сообщение с клавиатурой
    await message.answer_photo(
        photo=FSInputFile(path=IMAGES.get('start_image')),
        caption='Привет! Выберите один из вариантов ниже:',
        reply_markup=get_start_keyboard(),
    )

    # Обновляем сообщение в группе
    await update_group_message(user_id)


@dp.callback_query(F.data == 'button1')
async def handle_button1(callback: CallbackQuery, state: FSMContext):
    """Обработчик нажатия Кнопки 1."""
    user_id = callback.from_user.id
    print(f'Пользователь {user_id} нажал Кнопку 1')

    # Сохраняем текущее состояние в истории
    user_history[user_id].append('start')

    # Устанавливаем текущий контекст и добавляем действие в историю действий
    user_data[user_id]['current_context'] = 'Кнопка 1'
    user_data[user_id]['actions'].append('Нажато "Кнопка 1"')

    media = InputMediaPhoto(
        media=FSInputFile(IMAGES.get('button1')),
        caption='Вы выбрали Кнопку 1.',
    )
    await callback.message.edit_media(media=media, reply_markup=get_button1_keyboard())

    # Обновляем сообщение в группе
    await update_group_message(user_id)

    await callback.answer()


@dp.callback_query(F.data == 'button2')
async def handle_button2(callback: CallbackQuery, state: FSMContext):
    """Обработчик нажатия Кнопки 2."""
    user_id = callback.from_user.id
    print(f'Пользователь {user_id} нажал Кнопку 2')

    # Сохраняем текущее состояние в истории
    user_history[user_id].append('start')

    # Сбрасываем текущий контекст и добавляем действие в историю действий
    user_data[user_id]['current_context'] = None
    user_data[user_id]['actions'].append('Нажато "Кнопка 2"')

    media = InputMediaPhoto(
        media=FSInputFile(IMAGES.get('button2')),
        caption='Пожалуйста, введите сообщение.',
    )
    await callback.message.edit_media(media=media, reply_markup=get_back_keyboard())

    await state.set_state(UserStates.waiting_for_message)

    # Обновляем сообщение в группе
    await update_group_message(user_id)

    await callback.answer()


@dp.callback_query(F.data == 'button3')
async def handle_button3(callback: CallbackQuery, state: FSMContext):
    """Обработчик нажатия Кнопки 3."""
    user_id = callback.from_user.id
    print(f'Пользователь {user_id} нажал Кнопку 3')

    # Сохраняем текущее состояние в истории
    user_history[user_id].append('start')

    # Сбрасываем текущий контекст и добавляем действие в историю действий
    user_data[user_id]['current_context'] = None
    user_data[user_id]['actions'].append('Нажато "Кнопка 3"')

    media = InputMediaPhoto(
        media=FSInputFile(IMAGES.get('button3')),
        caption='Пожалуйста, введите сообщение.',
    )
    await callback.message.edit_media(media=media, reply_markup=get_back_keyboard())

    await state.set_state(UserStates.waiting_for_message)

    # Обновляем сообщение в группе
    await update_group_message(user_id)

    await callback.answer()


@dp.callback_query(F.data == 'button4')
async def handle_button4(callback: CallbackQuery, state: FSMContext):
    """Обработчик нажатия Кнопки 4."""
    user_id = callback.from_user.id
    print(f'Пользователь {user_id} нажал Кнопку 4')

    # Сохраняем текущее состояние в истории
    user_history[user_id].append('button1')

    # Добавляем действие в историю действий с указанием контекста
    context = user_data[user_id]['current_context']
    action = f'Нажато "{context}-4"' if context else 'Нажато "Кнопка 4"'
    user_data[user_id]['actions'].append(action)

    media = InputMediaPhoto(
        media=FSInputFile(IMAGES.get('button4')),
        caption='Пожалуйста, введите сообщение.',
    )
    await callback.message.edit_media(media=media, reply_markup=get_back_keyboard())

    await state.set_state(UserStates.waiting_for_message)

    # Обновляем сообщение в группе
    await update_group_message(user_id)

    await callback.answer()


@dp.callback_query(F.data == 'button5')
async def handle_button5(callback: CallbackQuery, state: FSMContext):
    """Обработчик нажатия Кнопки 5."""
    user_id = callback.from_user.id
    print(f'Пользователь {user_id} нажал Кнопку 5')

    # Сохраняем текущее состояние в истории
    user_history[user_id].append('button1')

    # Добавляем действие в историю действий с указанием контекста
    context = user_data[user_id]['current_context']
    action = f'Нажато "{context}-5"' if context else 'Нажато "Кнопка 5"'
    user_data[user_id]['actions'].append(action)

    media = InputMediaPhoto(
        media=FSInputFile(IMAGES.get('button5')),
        caption='Пожалуйста, введите сообщение.',
    )
    await callback.message.edit_media(media=media, reply_markup=get_back_keyboard())

    await state.set_state(UserStates.waiting_for_message)

    # Обновляем сообщение в группе
    await update_group_message(user_id)

    await callback.answer()


@dp.callback_query(F.data == 'back')
async def handle_back(callback: CallbackQuery, state: FSMContext):
    """Обработчик нажатия кнопки "Назад"."""
    user_id = callback.from_user.id
    user_data[user_id]['actions'].append('Нажато "Назад"')

    if not user_history[user_id]:
        # Если истории нет, возвращаемся к начальной клавиатуре
        media = InputMediaPhoto(
            media=FSInputFile(IMAGES.get('start_image')),
            caption='Привет! Выберите один из вариантов ниже:',
        )
        await callback.message.edit_media(media=media, reply_markup=get_start_keyboard())
    else:
        # Возвращаемся к предыдущему состоянию
        previous_state = user_history[user_id].pop()
        if previous_state == 'start':
            media = InputMediaPhoto(
                media=FSInputFile(IMAGES.get('start_image')),
                caption='Привет! Выберите один из вариантов ниже:',
            )
            await callback.message.edit_media(media=media, reply_markup=get_start_keyboard())
        elif previous_state == 'button1':
            media = InputMediaPhoto(
                media=FSInputFile(IMAGES.get('button1')),
                caption='Вы выбрали Кнопку 1.',
            )
            await callback.message.edit_media(
                media=media, reply_markup=get_button1_keyboard()
            )

    # Обновляем сообщение в группе
    await update_group_message(user_id)

    await state.clear()
    await callback.answer()


@dp.message(UserStates.waiting_for_message)
async def handle_message_input(message: Message, state: FSMContext):
    """Обработчик сообщения пользователя."""
    user_id = message.from_user.id
    print(f'Пользователь {user_id} отправил сообщение: {message.text}')

    # Добавляем сообщение в историю действий пользователя
    user_data[user_id]['actions'].append(f'Сообщение: {message.text}')

    # Отправляем запрос на номер телефона
    await message.answer(
        'Пожалуйста, поделитесь своим номером телефона.',
        reply_markup=share_phone_keyboard,
    )
    await state.set_state(UserStates.waiting_for_phone)

    # Обновляем сообщение в группе
    await update_group_message(user_id)


@dp.message(UserStates.waiting_for_phone, F.contact)
async def handle_phone_input(message: Message, state: FSMContext):
    """Обработчик получения номера телефона."""
    user_id = message.from_user.id
    phone_number = message.contact.phone_number
    print(f'Пользователь {user_id} отправил номер телефона: {phone_number}')

    # Сохраняем номер телефона в данных пользователя
    user_data[user_id]['phone'] = phone_number
    user_data[user_id]['actions'].append('Номер телефона предоставлен')

    # Обновляем сообщение в группе
    await update_group_message(user_id)

    # Сообщаем пользователю об успешной отправке заявки
    await message.answer(
        'Спасибо! Ваши данные были отправлены. Мы свяжемся с вами в ближайшее время.',
        reply_markup=ReplyKeyboardRemove(),
    )

    # Отправляем пользователю начальное сообщение с клавиатурой
    await message.answer_photo(
        photo=FSInputFile(path=IMAGES.get('start_image')),
        caption='Привет! Выберите один из вариантов ниже:',
        reply_markup=get_start_keyboard(),
    )

    # Обновляем сообщение в группе
    await update_group_message(user_id)

    # Очищаем состояние пользователя
    await state.clear()


if __name__ == '__main__':
    print('Запускаем бота...')
    asyncio.run(dp.start_polling(bot))
