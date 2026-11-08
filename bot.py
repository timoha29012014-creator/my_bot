import telebot
import random
import threading
from flask import Flask
import os
from supabase import create_client, Client
from telebot.types import BotCommand

# ==========================================
# НАСТРОЙКИ (ВСТАВЬ СВОИ ДАННЫЕ!)
# ==========================================
TOKEN = '8223102732:AAEpffK57NMYYpKlaZelkD_d6v3bsqlEUio' # <--- НЕ ЗАБУДЬ ВСТАВИТЬ СВОЙ ТОКЕН ОТ BOTFATHER!

# Данные от Supabase
SUPABASE_URL = "https://aalglenmfezruefjksqq.supabase.co"
SUPABASE_KEY = "sb_publishable_5MU3pqwNq8NqN4fAfRu1UA_dnQhLzFv"

# ==========================================
# ИНИЦИАЛИЗАЦИЯ
# ==========================================
bot = telebot.TeleBot(TOKEN)

# Подключаемся к базе данных Supabase
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Временное хранилище для анкет
user_states = {}

# ==========================================
# НАСТРОЙКА МЕНЮ КОМАНД
# ==========================================
def set_bot_commands():
    commands = [
        BotCommand('start', 'Запустить бота'),
        BotCommand('create_profile', 'Заполнить портфолио'),
        BotCommand('my_profile', 'Моя анкета'),
        BotCommand('lfg', 'Искать тиммейтов'),
        BotCommand('coin', 'Подкинуть монетку')
    ]
    try:
        bot.set_my_commands(commands)
        print("Меню команд успешно обновлено!")
    except Exception as e:
        print(f"Ошибка при установке меню: {e}")

# ==========================================
# БАЗОВЫЕ КОМАНДЫ
# ==========================================
@bot.message_handler(commands=['start'])
def start_message(message):
    bot.reply_to(message, "Привет! Я бот для поиска тиммейтов в Brawl Stars.\n\n"
                          "Заполни анкету (/create_profile), и я помогу тебе найти напарников!")

@bot.message_handler(commands=['coin'])
def coin_flip(message):
    result = random.choice(["Орел 🦅", "Решка 🪙"])
    bot.reply_to(message, f"Выпало: {result}")

# ==========================================
# ЛОГИКА ПОРТФОЛИО (FSM)
# ==========================================
@bot.message_handler(commands=['create_profile'])
def start_profile(message):
    user_states[message.chat.id] = {'step': 1}
    bot.reply_to(message, "Шаг 1/7. Напиши свой тег в Brawl Stars (например, #2PP0L):")

@bot.message_handler(commands=['my_profile'])
def show_profile(message):
    try:
        response = supabase.table('profiles').select('*').eq('user_id', message.chat.id).execute()
        
        if response.data:
            profile = response.data[0]
            text = (f"📋 **Твое портфолио:**\n\n"
                    f"🏷 Твой тег: `{profile['brawl_tag']}`\n"
                    f"🎮 Любимые режимы: {profile['modes']}\n"
                    f"🏆 Твои кубки: {profile['trophies']}\n"
                    f"🥇 Твой ранг: {profile['rank']}\n\n"
                    f"🔎 **Кого ищешь:**\n"
                    f"📈 Кубки тиммейта: {profile['req_trophies']}\n"
                    f"🏅 Ранг тиммейта: {profile['req_rank']}\n"
                    f"🎯 Цель поиска: {profile['goal']}")
            bot.reply_to(message, text, parse_mode='Markdown')
        else:
            bot.reply_to(message, "У тебя пока нет портфолио. Напиши /create_profile, чтобы создать.")
    except Exception as e:
        bot.reply_to(message, f"Ошибка базы данных: {e}")

@bot.message_handler(func=lambda message: message.chat.id in user_states)
def handle_profile_steps(message):
    state = user_states[message.chat.id]
    step = state['step']
    
    if step == 1:
        state['brawl_tag'] = message.text
        state['step'] = 2
        bot.reply_to(message, "Шаг 2/7. Какие режимы тебе нравятся больше всего? (Например: Бравлбол, Захват кристаллов, Ограбление)")
    elif step == 2:
        state['modes'] = message.text
        state['step'] = 3
        bot.reply_to(message, "Шаг 3/7. Сколько у тебя кубков? (Например: 25000)")
    elif step == 3:
        state['trophies'] = message.text
        state['step'] = 4
        bot.reply_to(message, "Шаг 4/7. Какой у тебя текущий ранг в Ранкеде? (Например: Мифик 1, или Бронза 3)")
    elif step == 4:
        state['rank'] = message.text
        state['step'] = 5
        bot.reply_to(message, "Шаг 5/7. От скольки и до скольки кубков должен быть твой тиммейт? (Например: от 20000 до 30000)")
    elif step == 5:
        state['req_trophies'] = message.text
        state['step'] = 6
        bot.reply_to(message, "Шаг 6/7. Какой ранг должен быть у тиммейта? (Например: от Легенда 1 до Легенда 3, или без разницы)")
    elif step == 6:
        state['req_rank'] = message.text
        state['step'] = 7
        bot.reply_to(message, "Шаг 7/7. Для чего именно ищешь тиммейта? (Например: Пуш кубков, Пуш ранкеда, просто поиграть)")
    elif step == 7:
        state['goal'] = message.text
        state['step'] = 8
        
        username = message.from_user.username or "Скрытый_ник"
        
        try:
            # Сохраняем или обновляем данные в Supabase
            data = {
                "user_id": message.chat.id,
                "username": username,
                "brawl_tag": state['brawl_tag'],
                "modes": state['modes'],
                "trophies": state['trophies'],
                "rank": state['rank'],
                "req_trophies": state['req_trophies'],
                "req_rank": state['req_rank'],
                "goal": state['goal']
            }
            
            # Проверяем, есть ли уже пользователь
            check = supabase.table('profiles').select('*').eq('user_id', message.chat.id).execute()
            
            if check.data:
                # Если есть - обновляем
                supabase.table('profiles').update(data).eq('user_id', message.chat.id).execute()
            else:
                # Если нет - вставляем
                supabase.table('profiles').insert(data).execute()
                
            del user_states[message.chat.id]
            bot.reply_to(message, "✅ Портфолио успешно сохранено в облаке Supabase! Посмотреть: /my_profile\n\nТеперь можешь искать тиммейтов командой /lfg")
        except Exception as e:
            bot.reply_to(message, f"Ошибка при сохранении: {e}")

# ==========================================
# ПОИСК ТИММЕЙТОВ (LFG)
# ==========================================
@bot.message_handler(commands=['lfg'])
def send_lfg(message):
    try:
        my_profile_resp = supabase.table('profiles').select('*').eq('user_id', message.chat.id).execute()
        
        if not my_profile_resp.data:
            bot.reply_to(message, "Сначала заполни портфолио командой /create_profile!")
            return

        my_profile = my_profile_resp.data[0]
        
        # Получаем всех остальных пользователей
        all_users_resp = supabase.table('profiles').select('user_id').neq('user_id', message.chat.id).execute()
        
        sent_count = 0
        for other in all_users_resp.data:
            chat_id = other['user_id']
            try:
                text = (f"🔔 **Поиск тиммейта!**\n\n"
                        f"👤 Игрок: @{my_profile['username']}\n"
                        f"🏷 Тег: `{my_profile['brawl_tag']}`\n"
                        f"🏆 Кубки: {my_profile['trophies']} | 🥇 Ранг: {my_profile['rank']}\n"
                        f"🎮 Режимы: {my_profile['modes']}\n\n"
                        f"🎯 **Ищет для:** {my_profile['goal']}\n"
                        f"📈 **Требования:** Кубки {my_profile['req_trophies']}, Ранг {my_profile['req_rank']}\n\n"
                        f"Напиши ему в личку!")
                bot.send_message(chat_id, text, parse_mode='Markdown')
                sent_count += 1
            except:
                pass
                
        bot.reply_to(message, f"✅ Твоя анкета с требованиями отправлена {sent_count} игрокам!")
    except Exception as e:
        bot.reply_to(message, f"Ошибка при рассылке: {e}")

# ==========================================
# ЗАПУСК БОТА И ВЕБ-СЕРВЕРА (FLASK)
# ==========================================
def run_bot():
    print("Бот запущен!")
    set_bot_commands()
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
