import nest_asyncio
nest_asyncio.apply()
import os
import json
import shutil
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext, CallbackQueryHandler

# Конфигурация
CHANNEL_ID = "@your_channel"  # Замените на username или ID вашего канала
TEMPLATE_FILE = "template.html"  # Файл шаблона сайта
BASE_URL = "bio.69.mu"  # Базовый URL для сайтов

# Загрузка базы данных
def load_database():
    if os.path.exists('database.json'):
        with open('database.json', 'r') as f:
            return json.load(f)
    return {}

# Сохранение базы данных
def save_database(data):
    with open('database.json', 'w') as f:
        json.dump(data, f, indent=4)

# Создание папки пользователя и копирование шаблона
def setup_user_folder(username: str):
    user_folder = f"users/{username}"
    os.makedirs(user_folder, exist_ok=True)
    shutil.copy(TEMPLATE_FILE, f"{user_folder}/index.html")
    return user_folder

# Сохранение данных в файл data.txt
def save_user_data(user_folder: str, data: dict):
    button1_url = f"showPopup(event, 'Пересылаю1...', '{data.get('button1_url', '')}');"
    button2_url = f"showPopup(event, 'Пересылаю2...', '{data.get('button2_url', '')}');"
    
    with open(f"{user_folder}/data.txt", "w", encoding="utf-8") as f:
        f.write(f"{data.get('title', '')}\n")
        f.write(f"{data.get('description', '')}\n")
        f.write(f"{data.get('button1_text', '')}\n")
        f.write(f"{data.get('button1_url', '')}\n")
        f.write(f"{data.get('button2_text', '')}\n")
        f.write(f"{data.get('button2_url', '')}\n")

# Загрузка данных из файла data.txt
def load_user_data(user_folder: str):
    with open(f"{user_folder}/data.txt", "r", encoding="utf-8") as f:
        lines = f.readlines()
    return {
        "title": lines[0].strip(),
        "description": lines[1].strip(),
        "button1_text": lines[2].strip(),
        "button1_url": lines[3].strip(),
        "button2_text": lines[4].strip(),
        "button2_url": lines[5].strip(),
    }

# Команда /start
async def start(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    db = load_database()

    # Инициализация пользователя в базе данных
    if str(user_id) not in db:
        db[str(user_id)] = {"access": False, "site_created": False, "username": None}
        save_database(db)

    # Проверка доступа
    if not db[str(user_id)]["access"]:
        await update.message.reply_text("У вас нет доступа. Обратитесь к администратору для покупки доступа.")
        return

    # Проверка, создан ли уже сайт
    if db[str(user_id)]["site_created"]:
        await update.message.reply_text("Вы уже создали сайт. Используйте /edit для редактирования.")
    else:
        await update.message.reply_text(
            "Введите ваш никнейм для сайта (например, v3n). "
            "Он будет использоваться в URL: bio.69.mu/ваш_никнейм"
        )
        context.user_data["step"] = "username"

# Обработка текстовых сообщений
async def handle_message(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    text = update.message.text
    step = context.user_data.get("step")

    if step == "username":
        # Проверка никнейма на допустимые символы
        if not text.isalnum():
            await update.message.reply_text("Никнейм должен содержать только буквы и цифры. Попробуйте снова.")
            return
        context.user_data["username"] = text
        await update.message.reply_text("Теперь введите название сайта (до 12 символов):")
        context.user_data["step"] = "title"

    elif step == "title":
        if len(text) > 12:
            await update.message.reply_text("Название должно быть до 12 символов. Попробуйте снова.")
            return
        context.user_data["title"] = text
        await update.message.reply_text("Теперь введите описание сайта (до 48 символов):")
        context.user_data["step"] = "description"

    elif step == "description":
        if len(text) > 48:
            await update.message.reply_text("Описание должно быть до 48 символов. Попробуйте снова.")
            return
        context.user_data["description"] = text
        await update.message.reply_text("Введите текст для первой кнопки:")
        context.user_data["step"] = "button1_text"

    elif step == "button1_text":
        context.user_data["button1_text"] = text
        await update.message.reply_text("Введите ссылку для первой кнопки:")
        context.user_data["step"] = "button1_url"

    elif step == "button1_url":
        context.user_data["button1_url"] = text
        await update.message.reply_text("Введите текст для второй кнопки:")
        context.user_data["step"] = "button2_text"

    elif step == "button2_text":
        context.user_data["button2_text"] = text
        await update.message.reply_text("Введите ссылку для второй кнопки:")
        context.user_data["step"] = "button2_url"

    elif step == "button2_url":
        context.user_data["button2_url"] = text
        await update.message.reply_text("Теперь отправьте фотографию для аватарки:")
        context.user_data["step"] = "avatar"

    # Шаги редактирования
    elif step == "edit_title":
        if len(text) > 12:
            await update.message.reply_text("Название должно быть до 12 символов. Попробуйте снова.")
            return
        username = context.user_data["username"]
        user_folder = f"users/{username}"
        user_data = load_user_data(user_folder)
        user_data["title"] = text
        save_user_data(user_folder, user_data)
        await update.message.reply_text("Название успешно обновлено!")
        context.user_data["step"] = None

    elif step == "edit_description":
        if len(text) > 48:
            await update.message.reply_text("Описание должно быть до 48 символов. Попробуйте снова.")
            return
        username = context.user_data["username"]
        user_folder = f"users/{username}"
        user_data = load_user_data(user_folder)
        user_data["description"] = text
        save_user_data(user_folder, user_data)
        await update.message.reply_text("Описание успешно обновлено!")
        context.user_data["step"] = None

    elif step == "edit_button1_text":
        username = context.user_data["username"]
        user_folder = f"users/{username}"
        user_data = load_user_data(user_folder)
        user_data["button1_text"] = text
        save_user_data(user_folder, user_data)
        await update.message.reply_text("Текст первой кнопки успешно обновлен!")
        context.user_data["step"] = None

    elif step == "edit_button1_url":
        username = context.user_data["username"]
        user_folder = f"users/{username}"
        user_data = load_user_data(user_folder)
        user_data["button1_url"] = text
        save_user_data(user_folder, user_data)
        await update.message.reply_text("Ссылка первой кнопки успешно обновлена!")
        context.user_data["step"] = None

    elif step == "edit_button2_text":
        username = context.user_data["username"]
        user_folder = f"users/{username}"
        user_data = load_user_data(user_folder)
        user_data["button2_text"] = text
        save_user_data(user_folder, user_data)
        await update.message.reply_text("Текст второй кнопки успешно обновлен!")
        context.user_data["step"] = None

    elif step == "edit_button2_url":
        username = context.user_data["username"]
        user_folder = f"users/{username}"
        user_data = load_user_data(user_folder)
        user_data["button2_url"] = text
        save_user_data(user_folder, user_data)
        await update.message.reply_text("Ссылка второй кнопки успешно обновлена!")
        context.user_data["step"] = None

# Обработка фотографий
async def handle_photo(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    step = context.user_data.get("step")

    if step == "avatar":
        photo = await update.message.photo[-1].get_file()
        username = context.user_data["username"]
        user_folder = setup_user_folder(username)
        await photo.download_to_drive(f"{user_folder}/photo.jpg")
        await update.message.reply_text("Аватарка сохранена. Теперь отправьте фотографию для фона:")
        context.user_data["step"] = "background"

    elif step == "background":
        photo = await update.message.photo[-1].get_file()
        username = context.user_data["username"]
        user_folder = f"users/{username}"
        await photo.download_to_drive(f"{user_folder}/background.jpg")
        await update.message.reply_text("Фон сохранен. Сайт создается...")

        # Сохраняем данные в файл data.txt
        save_user_data(user_folder, context.user_data)

        # Обновляем базу данных
        db = load_database()
        db[str(user_id)]["site_created"] = True
        db[str(user_id)]["username"] = username
        save_database(db)

        await update.message.reply_text(
            f"Ваш сайт успешно создан и доступен по ссылке: {BASE_URL}/{username}"
        )

    # Шаги редактирования
    elif step == "edit_avatar":
        photo = await update.message.photo[-1].get_file()
        username = context.user_data["username"]
        user_folder = f"users/{username}"
        await photo.download_to_drive(f"{user_folder}/photo.jpg")
        await update.message.reply_text("Аватарка успешно обновлена!")
        context.user_data["step"] = None

    elif step == "edit_background":
        photo = await update.message.photo[-1].get_file()
        username = context.user_data["username"]
        user_folder = f"users/{username}"
        await photo.download_to_drive(f"{user_folder}/background.jpg")
        await update.message.reply_text("Фон успешно обновлен!")
        context.user_data["step"] = None

# Команда /edit
async def edit_site(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    db = load_database()

    if str(user_id) not in db or not db[str(user_id)]["site_created"]:
        await update.message.reply_text("У вас ещё нет сайта. Используйте /start, чтобы создать его.")
        return

    # Сохраняем username в context.user_data
    context.user_data["username"] = db[str(user_id)]["username"]

    # Предлагаем выбрать, что редактировать
    await update.message.reply_text(
        "Что вы хотите изменить?",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("Название", callback_data="edit_title")],
            [InlineKeyboardButton("Описание", callback_data="edit_description")],
            [InlineKeyboardButton("Кнопка 1", callback_data="edit_button1")],
            [InlineKeyboardButton("Кнопка 2", callback_data="edit_button2")],
            [InlineKeyboardButton("Аватарка", callback_data="edit_avatar")],
            [InlineKeyboardButton("Фон", callback_data="edit_background")]
        ])
    )

# Обработка callback-запросов
async def handle_callback(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()  # Обязательно отвечаем на callback

    data = query.data

    if data == "edit_title":
        await query.message.reply_text("Введите новое название (до 12 символов):")
        context.user_data["step"] = "edit_title"
    elif data == "edit_description":
        await query.message.reply_text("Введите новое описание (до 48 символов):")
        context.user_data["step"] = "edit_description"
    elif data == "edit_button1":
        await query.message.reply_text("Что вы хотите изменить для первой кнопки?",
                                      reply_markup=InlineKeyboardMarkup([
                                          [InlineKeyboardButton("Текст", callback_data="edit_button1_text")],
                                          [InlineKeyboardButton("Ссылку", callback_data="edit_button1_url")]
                                      ]))
    elif data == "edit_button2":
        await query.message.reply_text("Что вы хотите изменить для второй кнопки?",
                                      reply_markup=InlineKeyboardMarkup([
                                          [InlineKeyboardButton("Текст", callback_data="edit_button2_text")],
                                          [InlineKeyboardButton("Ссылку", callback_data="edit_button2_url")]
                                      ]))
    elif data == "edit_button1_text":
        await query.message.reply_text("Введите новый текст для первой кнопки:")
        context.user_data["step"] = "edit_button1_text"
    elif data == "edit_button1_url":
        await query.message.reply_text("Введите новую ссылку для первой кнопки:")
        context.user_data["step"] = "edit_button1_url"
    elif data == "edit_button2_text":
        await query.message.reply_text("Введите новый текст для второй кнопки:")
        context.user_data["step"] = "edit_button2_text"
    elif data == "edit_button2_url":
        await query.message.reply_text("Введите новую ссылку для второй кнопки:")
        context.user_data["step"] = "edit_button2_url"
    elif data == "edit_avatar":
        await query.message.reply_text("Отправьте новую фотографию для аватарки:")
        context.user_data["step"] = "edit_avatar"
    elif data == "edit_background":
        await query.message.reply_text("Отправьте новую фотографию для фона:")
        context.user_data["step"] = "edit_background"

# Запуск бота
async def main():
    application = Application.builder().token("7913843319:AAG4RmLARW5tnW8ArPdWpq-sz8c7UIVdTI8").build()  # Замените на ваш токен

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("edit", edit_site))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    application.add_handler(CallbackQueryHandler(handle_callback))

    await application.run_polling()

# Запуск бота с использованием существующего цикла событий
if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    try:
        loop.run_until_complete(main())
    except KeyboardInterrupt:
        pass
    finally:
        loop.close()