import telebot
import random
import threading
from flask import Flask
import os
from supabase import create_client, Client
from telebot.types import BotCommand, InlineKeyboardMarkup, InlineKeyboardButton

# ==========================================
# НАСТРОЙКИ (ВСТАВЬ СВОИ ДАННЫЕ!)
# ==========================================
TOKEN = '8223102732:AAEpffK57NMYYpKlaZelkD_d6v3bsqlEUio' 

# Данные от Supabase
SUPABASE_URL = "https://aalglenmfezruefjksqq.supabase.co"
SUPABASE_KEY = "sb_publishable_5MU3pqwNq8NqN4fAfRu1UA_dnQhLzFv"

# ==========================================
# ИНИЦИАЛИЗАЦИЯ
# ==========================================
bot = telebot.TeleBot(TOKEN)
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
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
        BotCommand('find_club', 'Поиск клуба')
    ]
    try:
        bot.set_my_commands(commands)
        print("Меню команд обновлено!")
    except Exception as e:
        print(f"Ошибка меню: {e}")

# ==========================================
# КЛАВИАТУРЫ
# ==========================================
def get_main_menu():
    markup = InlineKeyboardMarkup()
    markup.row(InlineKeyboardButton("🏆 Ранговый бой", callback_data="menu_ranked"),
               InlineKeyboardButton("🏆 Кубки", callback_data="menu_trophies"))
    markup.row(InlineKeyboardButton("🏆 Киберспорт", callback_data="menu_esports"),
               InlineKeyboardButton("⚠️ Другое", callback_data="menu_other"))
    markup.row(InlineKeyboardButton("🤖 Создать анкету", callback_data="create_profile"))
    return markup

def get_back_menu():
    markup = InlineKeyboardMarkup()
    markup.row(InlineKeyboardButton("⬅️ Назад", callback_data="back_to_main"))
    return markup

def get_club_menu():
    markup = InlineKeyboardMarkup()
    markup.row(InlineKeyboardButton("🔍 Найти клуб по тегу", callback_data="find_club_tag"))
    markup.row(InlineKeyboardButton("⬅️ Назад", callback_data="back_to_main"))
    return markup

# ==========================================
# БАЗОВЫЕ КОМАНДЫ
# ==========================================
@bot.message_handler(commands=['start'])
def start_message(message):
    # Картинка для приветствия (замени ссылку на свою, если хочешь)
    photo_url = "https://i.imgur.com/your_image.jpg" 
    text = ("👋 Привет! Я бот для поиска тиммейтов в Brawl Stars.\n\n"
            "Выберите раздел для поиска или создайте анкету.")
    
    # Отправляем картинку с кнопками (если картинка не загрузится, отправит текст)
    try:
        bot.send_photo(message.chat.id, photo_url, caption=text, reply_markup=get_main_menu())
    except:
        bot.send_message(message.chat.id, text, reply_markup=get_main_menu())

# ==========================================
# ОБРАБОТКА КНОПОК (CALLBACK)
# ==========================================
@bot.callback_query_handler(func=lambda call: True)
def callback_inline(call):
    try:
        if call.data == "back_to_main":
            bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, 
                                  text="Выберите раздел:", reply_markup=get_main_menu())
        
        elif call.data == "create_profile":
            bot.answer_callback_query(call.id, "Заполняем анкету...")
            bot.delete_message(call.message.chat.id, call.message.message_id)
            start_profile(call.message)
            
        elif call.data.startswith("menu_"):
            section = call.data.split("_")[1]
            if section == "ranked":
                text = "🏆 **Ранговый бой**\nЗдесь можно искать тиммейтов для пуша ранга.\n\nНапиши `/create_profile`, чтобы указать свой ранг и требования."
            elif section == "trophies":
                text = "🏆 **Кубки**\nПоиск тиммейтов для набивания кубков.\n\nНапиши `/create_profile`, чтобы указать свои кубки и требования."
            elif section == "esports":
                text = "🏆 **Киберспорт**\nПоиск для турниров и скримов.\n\nНапиши `/create_profile`."
            else:
                text = "⚠️ **Другое**\nЛюбые другие цели.\n\nНапиши `/create_profile`."
                
            bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, 
                                  text=text, reply_markup=get_back_menu(), parse_mode='Markdown')

        elif call.data == "find_club_tag":
            bot.answer_callback_query(call.id, "Введи тег клуба:")
            msg = bot.send_message(call.message.chat.id, "Введите тег клуба (например, #ABC123):")
            bot.register_next_step_handler(msg, process_club_search)
            
    except Exception as e:
        print(f"Ошибка кнопки: {e}")

# ==========================================
# ПОИСК КЛУБА
# ==========================================
@bot.message_handler(commands=['find_club'])
def find_club_command(message):
    bot.reply_to(message, "Нажми на кнопку ниже или введи тег клуба:", reply_markup=get_club_menu())

def process_club_search(message):
    # Тут мы просто имитируем поиск, так как у нас нет API Brawl Stars
    tag = message.text
    if not tag.startswith("#"):
        bot.reply_to(message, "Тег должен начинаться с #. Попробуй еще раз.")
        return
    
    bot.reply_to(message, f"🔍 Ищем клуб с тегом `{tag}`...\n\n⚠️ (Функция поиска клубов находится в разработке. Мы пока не подключили API Brawl Stars, но скоро это сделаем!)", parse_mode='Markdown')

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
            text = (f"✨ **Твоя анкета готова!** ✨\n"
                    f"━━━━━━━━━━━━━━━━━━\n"
                    f"👤 **Игрок:** @{profile['username']}\n"
                    f"🏷 **Тег:** `{profile['brawl_tag']}`\n"
                    f"🏆 **Кубки:** {profile['trophies']}\n"
                    f"🥇 **Ранг:** {profile['rank']}\n"
                    f"🎮 **Режимы:** {profile['modes']}\n"
                    f"━━━━━━━━━━━━━━━━━━\n"
                    f"🔎 **Кого ищем:**\n"
                    f"📈 Кубки: {profile['req_trophies']}\n"
                    f"🏅 Ранг: {profile['req_rank']}\n"
                    f"🎯 Цель: {profile['goal']}\n"
                    f"━━━━━━━━━━━━━━━━━━\n"
                    f"💡 *Чтобы отправить анкету другим, напиши /lfg*")
            bot.reply_to(message, text, parse_mode='Markdown')
        else:
            bot.reply_to(message, "😕 У тебя пока нет анкеты. Напиши /create_profile, чтобы создать её.")
    except Exception as e:
        bot.reply_to(message, f"❌ Ошибка базы данных: {e}")

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
        bot.reply_to(message, "Шаг 4/7. Какой у тебя текущий ранг в Ранкеде? (Например: Мифик 1)")
    elif step == 4:
        state['rank'] = message.text
        state['step'] = 5
        bot.reply_to(message, "Шаг 5/7. От скольки и до скольки кубков должен быть твой тиммейт? (Например: от 20000 до 30000)")
    elif step == 5:
        state['req_trophies'] = message.text
        state['step'] = 6
        bot.reply_to(message, "Шаг 6/7. Какой ранг должен быть у тиммейта? (Например: от Легенда 1 до Легенда 3)")
    elif step == 6:
        state['req_rank'] = message.text
        state['step'] = 7
        bot.reply_to(message, "Шаг 7/7. Для чего именно ищешь тиммейта? (Например: Пуш кубков, Пуш ранкеда)")
    elif step == 7:
        state['goal'] = message.text
        state['step'] = 8
        
        username = message.from_user.username or "Скрытый_ник"
        
        try:
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
            
            check = supabase.table('profiles').select('*').eq('user_id', message.chat.id).execute()
            
            if check.data:
                supabase.table('profiles').update(data).eq('user_id', message.chat.id).execute()
            else:
                supabase.table('profiles').insert(data).execute()
                
            del user_states[message.chat.id]
            bot.reply_to(message, "✅ Портфолио сохранено! Посмотреть: /my_profile\n\nИскать тиммейтов: /lfg")
        except Exception as e:
            bot.reply_to(message, f"❌ Ошибка сохранения: {e}")

# ==========================================
# ПОИСК ТИММЕЙТОВ (LFG)
# ==========================================
@bot.message_handler(commands=['lfg'])
def send_lfg(message):
    try:
        my_profile_resp = supabase.table('profiles').select('*').eq('user_id', message.chat.id).execute()
        
        if not my_profile_resp.data:
            bot.reply_to(message, "⚠️ Сначала заполни портфолио командой /create_profile!")
            return

        my_profile = my_profile_resp.data[0]
        all_users_resp = supabase.table('profiles').select('user_id').neq('user_id', message.chat.id).execute()
        
        sent_count = 0
        for other in all_users_resp.data:
            chat_id = other['user_id']
            try:
                text = (f"🔥 **Внимание! Поиск тиммейта!** 🔥\n"
                        f"━━━━━━━━━━━━━━━━━━\n"
                        f"👤 **Игрок:** @{my_profile['username']}\n"
                        f"🏷 **Тег:** `{my_profile['brawl_tag']}`\n"
                        f"🏆 **Кубки:** {my_profile['trophies']}\n"
                        f"🥇 **Ранг:** {my_profile['rank']}\n"
                        f"🎮 **Режимы:** {my_profile['modes']}\n"
                        f"━━━━━━━━━━━━━━━━━━\n"
                        f"🎯 **Ищет для:** {my_profile['goal']}\n"
                        f"📈 **Требования:**\n"
                        f"┣ Кубки: {my_profile['req_trophies']}\n"
                        f"┗ Ранг: {my_profile['req_rank']}\n"
                        f"━━━━━━━━━━━━━━━━━━\n"
                        f"✉️ *Напиши ему в личку, чтобы договориться!*")
                bot.send_message(chat_id, text, parse_mode='Markdown')
                sent_count += 1
            except:
                pass
                
        bot.reply_to(message, f"✅ Твоя анкета отправлена {sent_count} игрокам!")
    except Exception as e:
        bot.reply_to(message, f"❌ Ошибка рассылки: {e}")

# ==========================================
# ЗАПУСК (FLASK)
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
