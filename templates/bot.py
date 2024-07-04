import telebot
import requests
from telebot import types

# Подключение у боту по токену
bot = telebot.TeleBot('7219344051:AAFYRCr-m5OPpwfA5lkYOCc4UoePROu0XAQ')

# Переменные используемые ботом
region_id = None
name = None
salary_to = 2147483647
salary_from = 0
time_day = None
data = None
k = 1

# Функция меню бота
@bot.message_handler(commands=['start', 'menu'])
def start(message):
    global k
    k = 1
    markup = types.ReplyKeyboardMarkup()
    btn = types.KeyboardButton("Найти вакансию")
    markup.add(btn)
    bot.send_message(message.chat.id, "Привтствую, это бот для поиска вакансий, хотите найти вакансию?",
                     reply_markup=markup)
    bot.register_next_step_handler(message, open_search)

# Функция выбора региона
def open_search(message):
    if message.text == "Найти вакансию":
        bot.send_message(message.chat.id, "Введите регион, в котором ищете вакансии",
                         reply_markup=types.ReplyKeyboardRemove())
        bot.register_next_step_handler(message, get_id_region)
    else:
        bot.send_message(message.chat.id, "Команда не распознана",
                         reply_markup=types.ReplyKeyboardRemove())

# Функция выбора вакансии
def get_id_region(message):
    url = f"http://0.0.0.0:8000/region/{message.text}"
    data = requests.get(url).json()
    global region_id
    if data.get('id') is not None:
        region_id = data["id"]
        bot.send_message(message.chat.id, "Введите название профессии")
        bot.register_next_step_handler(message, get_name)
    else:
        bot.send_message(message.chat.id, "ошибка, региона не существует, попробуйте ещё раз")
        bot.register_next_step_handler(message, get_id_region)

# Функция фильтра вакансий по нижний границы зарплаты
def get_name(message):
    global name
    name = message.text.replace(" ", "+")
    markup = types.ReplyKeyboardMarkup()
    btn = types.KeyboardButton("Пропустить")
    markup.add(btn)
    bot.send_message(message.chat.id, "Введите нижнюю граниу ЗП",
                     reply_markup=markup)
    bot.register_next_step_handler(message, get_salary_from)

# Функция фильтра вакансий по верхний границы зарплаты
def get_salary_from(message):
    global salary_from
    if message.text != "Пропустить":
        salary_from = message.text
    markup = types.ReplyKeyboardMarkup()
    btn = types.KeyboardButton("Пропустить")
    markup.add(btn)
    bot.send_message(message.chat.id, "Введите верхнюю граниу ЗП",
                     reply_markup=markup)
    bot.register_next_step_handler(message, get_salary_to)


# Функция фильтра вакансий по занятости
def get_salary_to(message):
    global salary_to
    if message.text != "Пропустить":
        salary_to = message.text
    markup = types.ReplyKeyboardMarkup()
    td1 = types.KeyboardButton("Полная занятость")
    td2 = types.KeyboardButton("Частичная занятость")
    markup.row(td1, td2)
    btn = types.KeyboardButton("Пропустить")
    markup.row(btn)
    bot.send_message(message.chat.id, "Выберете график",
                     reply_markup=markup)
    bot.register_next_step_handler(message, get_time_day)


# Функция запроса первой вакансии
def get_time_day(message):
    global time_day
    if message.text != "Пропустить":
        time_day = message.text
    url = f"http://0.0.0.0:8000/vacancy?vacancy={name}&salaryFrom={salary_from}&salaryTo={salary_to}&" \
          f"timeDay={time_day}&area={region_id}"
    global data
    data = requests.get(url).json()
    if not data:
        bot.send_message(message.chat.id, "Вакансий по запросу не найдено", reply_markup=types.ReplyKeyboardRemove())
    else:
        vac = data[0]
        str = f"{vac['vacancy']}\n" \
              f"Компания: {vac['employer']}" \
              f"от{vac['salaryFrom']} до{vac['salaryTo']}\n" \
              f"Адреc: {vac['address']} \n" \
              f"Описание: {vac['requirement']}\n"\
              f"{vac['timeDay']}" \
              f"Ссылка: {vac['alternate_url']}"
        markup = types.ReplyKeyboardMarkup()
        btn1 = types.KeyboardButton("Следующая")
        btn2 = types.KeyboardButton("Меню")
        markup.row(btn1,btn2)
        bot.send_message(message.chat.id, str, reply_markup=markup)
        bot.register_next_step_handler(message, next_vacancy)

# Функция кнопок пролистывания списка вакансий и возврата в меню
def next_vacancy(message):
    if message.text == 'Следующая':
        global k
        vac = data[k]
        str = f"{vac['vacancy']}\n" \
              f"Компания: {vac['employer']}" \
              f"от{vac['salaryFrom']} до{vac['salaryTo']}\n" \
              f"Адреc: {vac['address']} \n" \
              f"Описание: {vac['requirement']}\n" \
              f"{vac['timeDay']}\n" \
              f"Ссылка: {vac['alternate_url']}"
        markup = types.ReplyKeyboardMarkup()
        btn1 = types.KeyboardButton("Следующая")
        btn2 = types.KeyboardButton("Меню")
        markup.row(btn1, btn2)
        bot.send_message(message.chat.id, str, reply_markup=markup)
        k += 1
        bot.register_next_step_handler(message, next_vacancy)
    elif message.text == 'Меню':
        bot.send_message(message.chat.id, "Напишите /menu", reply_markup=types.ReplyKeyboardRemove())
    else:
        bot.send_message(message.chat.id, "Команда не распознана",
                         reply_markup=types.ReplyKeyboardRemove())
        bot.register_next_step_handler(message, next_vacancy)


bot.polling(none_stop=True)
