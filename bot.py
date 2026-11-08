import telebot
import random

# ВСТАВЬ СЮДА СВОЙ НОВЫЙ ТОКЕН В КАВЫЧКАХ!
TOKEN = '8223102732:AAEpffK57NMYYpKlaZelkD_d6v3bsqlEUio' 
bot = telebot.TeleBot(TOKEN)

@bot.message_handler(commands=['start'])
def start_message(message):
    bot.reply_to(message, "О, здарова. Я бот. Напиши /coin чтобы подкинуть монетку, или просто поболтай со мной.")

@bot.message_handler(commands=['coin'])
def coin_flip(message):
    result = random.choice(["Орел 🦅", "Решка 🪙"])
    bot.reply_to(message, f"Подбрасываю... Выпало: {result}")

@bot.message_handler(func=lambda message: True)
def echo_all(message):
    bot.reply_to(message, f"Ты написал: '{message.text}'. Серьезно? Больше нечего сказать?")

print("Бот запущен! Иди в телегу и пиши ему.")
bot.polling(none_stop=True)
