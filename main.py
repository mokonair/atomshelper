import time

import requests.exceptions
import telebot
from telebot import types
import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.environ.get("BOT_TOKEN")
bot = telebot.TeleBot(BOT_TOKEN, parse_mode='MARKDOWN')

text = str
file = bytes
emptyfile = bytes


def whitelist_check(user_id):
    in_whitelist = False
    whitelist = open('whitelist.txt', 'r')
    for line in whitelist.readlines():
        line = line.replace('\n', '')
        try:
            int_line = int(line)
            if int_line == user_id:
                in_whitelist = True
        except Exception as e:
            print(e)
    whitelist.close()
    return in_whitelist


@bot.message_handler(commands=['start'])
def command_start(message):
    if whitelist_check(message.from_user.id):
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton('📝 Создать пост', callback_data='input_text'))
        outline_message = f'✋ Добро пожаловать. Для подсказки введите /help'
        bot.send_message(message.chat.id, outline_message, parse_mode='markdown', reply_markup=markup)
    else:
        bot.send_message(message.chat.id, f'<b>Не выполнена аутентификация через whitelist, обратитесь к администратору\nВаш id: </b>{message.from_user.id}',
                         parse_mode='html', reply_markup=None)


@bot.message_handler(commands=['help'])
def command_help(message):
    bot.send_message(message.chat.id, 'Форматирование производится следующим путём:\n'
                                      '<b>*Жирный текст*</b>\n'
                                      '<i>_Курсив_</i>\n'
                                      '[Название сайта](ссылка)', parse_mode='html')


@bot.message_handler(commands=['addtowhitelist'])
def command_addtowhitelist(message):
    if whitelist_check(message.from_user.id):
        msg = bot.send_message(message.chat.id, 'Введите id пользователя: ', parse_mode='markdown', reply_markup=None)
        bot.register_next_step_handler(msg, add_to_whitelist)
    else:
        bot.send_message(message.chat.id, f'<b>Не выполнена аутентификация через whitelist, обратитесь к администратору\nВаш id: </b>{message.from_user.id}',
                         parse_mode='html', reply_markup=None)


@bot.message_handler(commands=['deletefromwhitelist'])
def command_deletefromwhitelist(message):
    if whitelist_check(message.from_user.id):
        msg = bot.send_message(message.chat.id, 'Введите id пользователя: ', parse_mode='markdown', reply_markup=None)
        bot.register_next_step_handler(msg, delete_from_whitelist)
    else:
        bot.send_message(message.chat.id, f'<b>Не выполнена аутентификация через whitelist, обратитесь к администратору\nВаш id: </b>{message.from_user.id}',
                         parse_mode='html', reply_markup=None)


# Когда бот входит в новый чат
@bot.message_handler(content_types=['new_chat_members'])
def welcome_new_member(message):
    if message.json['new_chat_participant']['id'] == bot.get_me().id:
        file_chat_id = open('chats.txt', 'a')
        file_chat_id.write(str(message.chat.id) + '\n')
        file_chat_id.close()


# Нажатие на кнопку
@bot.callback_query_handler(func=lambda call: True)
def callback_inline(call):
    if whitelist_check(call.from_user.id):
        if call.message:
            if call.data == 'input_text':
                bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
                                      text=f'✋ Добро пожаловать. Для подсказки введите /help*',
                                      reply_markup=None, parse_mode='html')
                msg = bot.send_message(chat_id=call.message.chat.id, text='<b>Введите текст: </b>', reply_markup=None,
                                       parse_mode='html')
                bot.register_next_step_handler(msg, input_text)
            elif call.data == 'download_image':
                msg = bot.send_message(call.message.chat.id, '<b>Загрузите картинку: </b>', reply_markup=None,
                                       parse_mode='html')
                bot.register_next_step_handler(msg, download_image)
            elif call.data == 'send_post':
                global text
                global file
                file_chat_id = open('chats.txt', 'r')
                for line in file_chat_id.readlines():
                    if not isinstance(file, bytes):
                        try:
                            bot.send_message(line, text, reply_markup=None, parse_mode='markdown')
                        except requests.exceptions.ReadTimeout:
                            time.sleep(15)
                            bot.send_message(line, text, reply_markup=None, parse_mode='markdown')
                    else:
                        try:
                            bot.send_photo(line, file, reply_markup=None, caption=text, parse_mode='markdown')
                        except requests.exceptions.ReadTimeout:
                            time.sleep(15)
                            bot.send_photo(line, file, reply_markup=None, caption=text, parse_mode='markdown')
                markup = types.InlineKeyboardMarkup()
                markup.add(types.InlineKeyboardButton('📝 Создать пост', callback_data='input_text'))
                if not isinstance(file, bytes):
                    bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
                                          text=f'*Пост отправлен!\nТекст поста: \n*{text}', reply_markup=markup,
                                          parse_mode='markdown')
                else:
                    bot.edit_message_caption(chat_id=call.message.chat.id, message_id=call.message.message_id,
                                             caption=f'*Пост отправлен!\nТекст поста: \n*{text}',
                                             parse_mode='markdown')
                file_chat_id.close()
                text = None
                file = None
    else:
        bot.send_message(call.message.chat.id, f'<b>Не выполнена аутентификация через whitelist, '
                                               f'обратитесь к администратору\nВаш id: </b>{call.from_user.id}',
                         parse_mode='html', reply_markup=None)


def input_text(message):
    if whitelist_check(message.from_user.id):
        global text
        text = message.text
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton('📝 Изменить текст', callback_data='input_text'))
        markup.add(types.InlineKeyboardButton('🖼 Добавить картинку', callback_data='download_image'))
        markup.add(types.InlineKeyboardButton('🗣 Отправить пост', callback_data='send_post'))
        bot.send_message(message.chat.id, f'*Ваш текст:*\n{text}', parse_mode='markdown',
                         reply_markup=markup)
    else:
        bot.send_message(message.chat.id, f'<b>Не выполнена аутентификация через whitelist, обратитесь к администратору'
                                          f'\nВаш id: </b>{message.from_user.id}',
                         parse_mode='html', reply_markup=None)


def download_image(message):
    if whitelist_check(message.from_user.id):
        global text
        global file
        file_info = bot.get_file(message.photo[len(message.photo) - 1].file_id)
        file = bot.download_file(file_info.file_path)
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton('📝 Изменить текст', callback_data='input_text'))
        markup.add(types.InlineKeyboardButton('🖼 Изменить картинку', callback_data='download_image'))
        markup.add(types.InlineKeyboardButton('🗣 Отправить пост', callback_data='send_post'))
        bot.send_photo(message.chat.id, file, reply_markup=markup, caption=f'*Ваш текст:*\n{text}',
                       parse_mode='markdown')
    else:
        bot.send_message(message.chat.id, f'<b>Не выполнена аутентификация через whitelist, обратитесь к администратору'
                                          f'\nВаш id: </b>{message.from_user.id}',
                         parse_mode='html', reply_markup=None)


def add_to_whitelist(message):
    if message.text.isdigit():
        file_whitelist = open('whitelist.txt', 'a')
        file_whitelist.write('\n' + str(message.text))
        file_whitelist.close()
        bot.send_message(message.chat.id, 'ID добавлен в whitelist.', parse_mode='html')
    else:
        bot.send_message(message.chat.id, 'ID не является числом, введите команду снова.', parse_mode='html')


def delete_from_whitelist(message):
    file_whitelist = open('whitelist.txt', 'r')
    str_out = ''
    arr_out = []
    print(type(arr_out))
    for line in file_whitelist.readlines():
        if not line.isspace():
            line = line.replace('\n', '')
            print(line, message.text)
            if line != message.text:
                arr_out.append(line)
                str_out = str_out + '\n' + line
            else:
                bot.send_message(message.chat.id, 'ID удален из whitelist.', parse_mode='html')
    file_whitelist.close()
    file_whitelist = open('whitelist.txt', 'w')
    for arr_line in arr_out:
        file_whitelist.writelines('\n' + arr_line)
    file_whitelist.close()


while True:
    try:
        bot.infinity_polling(timeout=123)
    except Exception as e:
        time.sleep(15)
