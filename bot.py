import nest_asyncio
nest_asyncio.apply()
import os
import json
import asyncio
from github import Github
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext, CallbackQueryHandler

# Конфигурация
CHANNEL_ID = "@bio69mu"  # Замените на username или ID вашего канала
TEMPLATE_FILE = "template.html"  # Файл шаблона сайта
BASE_URL = "bio.69.mu"  # Базовый URL для сайтов
GITHUB_TOKEN = os.getenv("GIT_TOKEN")  # Токен GitHub из переменных окружения
REPO_NAME = "ваш_username/ваш_репозиторий"  # Например, "username/repo"

# Подключение к GitHub
g = Github(GITHUB_TOKEN)
repo = g.get_repo(REPO_NAME)

# Загрузка базы данных через GitHub API
def load_database():
    try:
        file = repo.get_contents("database.json")
        data = json.loads(file.decoded_content.decode("utf-8"))
        return data
    except Exception as e:
        print(f"Ошибка загрузки базы данных: {e}")
        return {}

# Сохранение базы данных через GitHub API
def save_database(data):
    try:
        content = json.dumps(data, indent=4)
        try:
            file = repo.get_contents("database.json")
            repo.update_file(file.path, "Обновление базы данных", content, file.sha)
        except:
            repo.create_file("database.json", "Создание базы данных", content)
        return True
    except Exception as e:
        print(f"Ошибка сохранения базы данных: {e}")
        return False

# Создание папки пользователя и копирование шаблона через GitHub API
def setup_user_folder(username: str):
    try:
        # Создаем папку пользователя
        repo.create_file(f"users/{username}/index.html", "Создание шаблона", repo.get_contents(TEMPLATE_FILE).decoded_content.decode("utf-8"))
        return True
    except Exception as e:
        print(f"Ошибка создания папки пользователя: {e}")
        return False

# Сохранение данных в файл data.txt через GitHub API
def save_user_data(username: str, data: dict):
    try:
        content = "\n".join([
            data.get("title", ""),
            data.get("description", ""),
            data.get("button1_text", ""),
            data.get("button1_url", ""),
            data.get("button2_text", ""),
            data.get("button2_url", ""),
        ])
        path = f"users/{username}/data.txt"

        # Проверяем, существует ли файл
        try:
            file = repo.get_contents(path)
            repo.update_file(path, "Обновление данных", content, file.sha)
        except:
            repo.create_file(path, "Создание файла данных", content)

        return True
    except Exception as e:
        print(f"Ошибка сохранения данных: {e}")
        return False

# Загрузка данных из файла data.txt через GitHub API
def load_user_data(username: str):
    try:
        file = repo.get_contents(f"users/{username}/data.txt")
        data = file.decoded_content.decode("utf-8").split("\n")
        return {
            "title": data[0].strip(),
            "description": data[1].strip(),
            "button1_text": data[2].strip(),
            "button1_url": data[3].strip(),
            "button2_text": data[4].strip(),
            "button2_url": data[5].strip(),
        }
    except Exception as e:
        print(f"Ошибка загрузки данных: {e}")
        return None

# Удаление папки пользователя через GitHub API
def delete_user_folder(username: str):
    try:
        contents = repo.get_contents(f"users/{username}")
        for content in contents:
            repo.delete_file(content.path, "Удаление файла", content.sha)
        return True
    except Exception as e:
        print(f"Ошибка удаления папки: {e}")
        return False

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

        # Сохраняем данные через GitHub API
        username = context.user_data["username"]
        if save_user_data(username, context.user_data):
            await update.message.reply_text("Данные успешно сохранены!")
        else:
            await update.message.reply_text("Ошибка при сохранении данных.")

# Команда /delete
async def delete_site(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    username = context.user_data.get("username")

    if not username:
        await update.message.reply_text("У вас ещё нет сайта. Используйте /start, чтобы создать его.")
        return

    # Удаляем папку через GitHub API
    if delete_user_folder(username):
        await update.message.reply_text("Сайт успешно удален. Используйте /start, чтобы создать новый.")
    else:
        await update.message.reply_text("Ошибка при удалении сайта.")

# Запуск бота
async def main():
    application = Application.builder().token("7913843319:AAG4RmLARW5tnW8ArPdWpq-sz8c7UIVdTI8").build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("edit", edit_site))
    application.add_handler(CommandHandler("delete", delete_site))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    application.add_handler(CallbackQueryHandler(handle_callback))

    await application.run_polling()

if __name__ == "__main__":
    asyncio.run(main())
