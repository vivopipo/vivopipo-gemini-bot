import os
import time
import logging
import telebot
from telebot import apihelper
from google import genai
from google.genai.errors import APIError

# 1. Отключаем спам-логгер telebot для защиты от бана консоли
telebot.logger.setLevel(logging.CRITICAL)

# 2. Фиксируем API URL для стабильности через прокси PythonAnywhere
apihelper.API_URL = "https://api.telegram.org/bot{0}/{1}"

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

ADMIN_ID = 823050506 

bot = telebot.TeleBot(TELEGRAM_BOT_TOKEN)
client = genai.Client(api_key=GEMINI_API_KEY)

SYSTEM_INSTRUCTION = """
Ты — рофляный и ироничный участник дружеского чата. 
Общайся непринужденно, подкалывай друзей, используй юмор и сленг, отвечай кратко и по делу.
"""

chats_history = {}

def get_or_create_chat(chat_id):
    if chat_id not in chats_history:
        chats_history[chat_id] = client.chats.create(
            model='gemini-3.6-flash',
            config={'system_instruction': SYSTEM_INSTRUCTION}
        )
    return chats_history[chat_id]

# --- КОМАНДЫ ДЛЯ ПОЛЬЗОВАТЕЛЕЙ ---

@bot.message_handler(commands=['start', 'help'])
def send_help(message):
    text = (
        "Здорово! Я бот на базе Gemini.\n\n"
        "Команды:\n"
        "/reset — Сбросить память диалога в этом чате\n"
        "/help — Показать эту справку"
    )
    bot.reply_to(message, text)

@bot.message_handler(commands=['reset'])
def reset_chat(message):
    chat_id = message.chat.id
    if chat_id in chats_history:
        del chats_history[chat_id]
    bot.reply_to(message, "Память очищена, начинаем с чистого листа!")

# --- КОМАНДА ДЛЯ АДМИНА ---

@bot.message_handler(commands=['say'])
def say_as_bot(message):
    if message.from_user.id != ADMIN_ID:
        return

    text_to_send = message.text.replace('/say', '', 1).strip()
    
    if text_to_send:
        try:
            bot.delete_message(message.chat.id, message.message_id)
        except Exception:
            pass
            
        bot.send_message(message.chat.id, text_to_send)

# --- ОСНОВНАЯ ЛОГИКА ---

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    if message.text and message.text.startswith('/'):
        return

    try:
        chat_type = message.chat.type
        bot_info = bot.get_me()
        bot_username = bot_info.username
        bot_id = bot_info.id
        
        is_mentioned = bot_username and message.text and f"@{bot_username}" in message.text
        is_reply_to_bot = message.reply_to_message and message.reply_to_message.from_user.id == bot_id
        is_private = chat_type == 'private'

        if is_private or is_mentioned or is_reply_to_bot:
            clean_text = message.text
            if is_mentioned and bot_username:
                clean_text = clean_text.replace(f"@{bot_username}", "").strip()

            if not clean_text:
                return

            chat_session = get_or_create_chat(message.chat.id)

            # Безопасный запрос к Gemini
            try:
                response = chat_session.send_message(clean_text)
                bot.reply_to(message, response.text)
            except APIError as e:
                if e.code == 429:
                    # Удаляем сессию без немедленного пересоздания
                    if message.chat.id in chats_history:
                        del chats_history[message.chat.id]
                    
                    bot.reply_to(message, "Гугл временно заблокировал запросы (429). Подожди 1 минуту и напиши снова!")
                    time.sleep(5)
                elif e.code == 503:
                    bot.reply_to(message, "Сервера Гугла лагают (503). Попробуй через пару секунд.")
                else:
                    print(f"Ошибка API: {e}")
            
    except Exception as e:
        print(f"Системная ошибка: {e}")

# --- БЕЗОПАСНЫЙ ЗАПУСК ---

if __name__ == "__main__":
    print("Бот запущен...")
    while True:
        try:
            bot.polling(none_stop=True, interval=2, timeout=30)
        except Exception as e:
            print(f"Сбой сети/прокси: {e}. Переподключение через 10 секунд...")
            time.sleep(10)
