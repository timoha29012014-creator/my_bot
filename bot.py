import telebot
import random
import threading
from flask import Flask
import os

# ВСТАВЬ СЮДА СВОЙ ТОКЕН В КАВЫЧКАХ!
TOKEN = '8223102732:AAEpffK57NMYYpKlaZelkD_d6v3bsqlEUio' 
bot = telebot.TeleBot(TOKEN)

@bot.message_handler(commands=['start'])
def start_message(message):
    bot.reply_to(message, "О, здарова. Я бот. Напиши /coin чтобы подкинуть монетку.")

@bot.message_handler(commands=['coin'])
def coin_flip(message):
    result = random.choice(["Орел 🦅", "Решка 🪙"])
    bot.reply_to(message, f"Подбрасываю... Выпало: {result}")

@bot.message_handler(func=lambda message: True)
def echo_all(message):
    bot.reply_to(message, f"Ты написал: '{message.text}'. Серьезно?")

def run_bot():
    print("Бот запущен!")
    bot.polling(none_stop=True)

app = Flask(__name__)

@app.route('/')
def home():
    return "Бот работает 24/7!"

if __name__ == "__main__":
    t = threading.Thread(target=run_bot)
    t.start()
    
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
