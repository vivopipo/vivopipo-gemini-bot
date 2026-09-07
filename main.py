import os
import telebot
from google import genai

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Твой цифровой Telegram ID
ADMIN_ID = 823050506 

bot = telebot.TeleBot(TELEGRAM_BOT_TOKEN)
client = genai.Client(api_key=GEMINI_API_KEY)

SYSTEM_INSTRUCTION = """
Ты — рофляный и ироничный участник дружеского чата. 
Общайся непринужденно, подкалывай друзей, используй юмор и сленг, отвечай кратко и по делу.
"""

# Хранилище сессий чата для контекста
chats_history = {}

def get_or_create_chat(chat_id):
    if chat_id not in chats_history:
        chats_history[chat_id] = client.chats.create(
            model='gemini-3.6-flash',
            config={'system_instruction': SYSTEM_INSTRUCTION}
        )
    return chats_history[chat_id]

# Команда для отправки сообщений от лица бота
@bot.message_handler(commands=['say'])
def say_as_bot(message):
    # Проверяем, что команду пишет админ
    if message.from_user.id != ADMIN_ID:
        return

    # Отрезаем "/say " от текста
    text_to_send = message.text.replace('/say', '', 1).strip()
    
    if text_to_send:
        # Удаляем твоё исходное сообщение с командой, чтобы было незаметно
        try:
            bot.delete_message(message.chat.id, message.message_id)
        except Exception:
            pass # Если у бота нет прав на удаление сообщений в группе
            
        # Отправляем сообщение от имени бота
        bot.send_message(message.chat.id, text_to_send)

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    # Игнорируем команды, начинающиеся с /
    if message.text and message.text.startswith('/'):
        return

    try:
        chat_type = message.chat.type
        bot_username = bot.get_me().username
        
        is_mentioned = bot_username and message.text and f"@{bot_username}" in message.text
        is_reply_to_bot = message.reply_to_message and message.reply_to_message.from_user.id == bot.get_user_id()
        is_private = chat_type == 'private'

        # В группах реагируем только на теги/реплаи, в ЛС — на всё
        if is_private or is_mentioned or is_reply_to_bot:
            clean_text = message.text
            if is_mentioned and bot_username:
                clean_text = clean_text.replace(f"@{bot_username}", "").strip()

            if not clean_text:
                return

            chat_session = get_or_create_chat(message.chat.id)
            response = chat_session.send_message(clean_text)
            
            bot.reply_to(message, response.text)
            
    except Exception as e:
        print(f"Ошибка: {e}")

if __name__ == "__main__":
    print("Бот запущен...")
    bot.infinity_polling()
