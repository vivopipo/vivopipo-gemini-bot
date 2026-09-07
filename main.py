import os
import telebot
from google import genai

# Берем ключи из переменных окружения
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

bot = telebot.TeleBot(TELEGRAM_BOT_TOKEN)
client = genai.Client(api_key=GEMINI_API_KEY)

SYSTEM_INSTRUCTION = """
Ты — рофляный и ироничный участник дружеского чата. 
Общайся непринужденно, подкалывай друзей, используй юмор и сленг, отвечай кратко и по делу.
"""

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    try:
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=message.text,
            config={'system_instruction': SYSTEM_INSTRUCTION}
        )
        bot.reply_to(message, response.text)
    except Exception as e:
        print(f"Ошибка: {e}")

if __name__ == "__main__":
    print("Бот запущен...")
    bot.infinity_polling()
