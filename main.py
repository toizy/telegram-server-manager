import os
import re
import signal
import tempfile
import time
from subprocess import check_output
import requests
import telebot
from telebot import types
from config import bot_token, api_url, api_key, dashboard_options
from logger import log
from permissions import check_permission

# Флаг для контроля выхода из цикла
exit_flag = False

# Токен бота
bot = telebot.TeleBot(bot_token)

# Константы для текстов сообщений
OPERATION_CONFIRMATION_TEXT = "Внимание! {operation_description} Продолжить?"
CANCEL_MESSAGE = "Вы отменили операцию."
INVALID_COMMAND_MESSAGE = "Invalid command"

# Команды для управления сервером
COMMAND_STATUS = "status'"
COMMAND_STOP = "stop'"
COMMAND_RESTART = "restart'"
COMMAND_DISCORDBOT_RESTART = "restart_discordbot'"


#
# Создание уникального имени файла средствами системы
#
def generate_unique_filename(file_suffix=""):
    _, temp_filename = tempfile.mkstemp(suffix=file_suffix, dir='/var/tmp/')
    return temp_filename


#
# Проверка доступа пользователя
#
def check_and_send_permission_error(message, command):
    permission_result = check_permission(message, command)
    if permission_result["code"] != "SUCCESS":
        error_message = permission_result["message"]
        bot.send_message(message.chat.id, error_message, parse_mode='HTML')
        log.error(
            f"check_and_send_permission_error: "
            f"chat id: {message.chat.id}, "
            f"username: {message.from_user.username}, "
            f"user id: {message.from_user.id}, "
            f"command: {command}, "
            f"error: {error_message}"
        )
        return False
    log.info(
        f"check_and_send_permission_error: "
        f"chat id: {message.chat.id}, "
        f"username: {message.from_user.username}, "
        f"user id: {message.from_user.id}, "
        f"command: {command}, "
        f"status: SUCCESS"
    )
    return True


#
# Изображение графика
#
def get_grafana_panel_image(file_name, url, key, dashboard_uid, panel_id, timefrom="now", timeto="now-6h",
                            width=1000, height=500):
    url = f"{url}/render/d-solo/{dashboard_uid}"\
          f"?orgId=1"\
          f"&panelId={panel_id}"\
          f"&width={width}"\
          f"&height={height}"\
          f"&tz=Europe/Moscow"\
          f"&from=${timefrom}"\
          f"&to=${timeto}"

    headers = {
        "Authorization": f"Bearer {key}"
    }

    response = requests.get(url, headers=headers, stream=True)

    if response.status_code == 200:
        with open(f"{file_name}", 'wb') as f:
            for chunk in response.iter_content(chunk_size=1024):
                if chunk:
                    f.write(chunk)
    else:
        log.error(f"Ошибка получения изображения. Код состояния: {response.status_code}")


#
# Подтверждение действий пользователя
#
def send_confirmation_message(message, operation_description, command):
    # Создаем клавиатуру с кнопками "Да" и "Нет"
    keyboard = types.ReplyKeyboardMarkup(row_width=2, one_time_keyboard=True)
    button_yes = types.KeyboardButton(text="Да")
    button_no = types.KeyboardButton(text="Нет")
    keyboard.add(button_yes, button_no)

    # Отправляем пользователю подтверждение с клавиатурой
    confirmation_message = OPERATION_CONFIRMATION_TEXT.format(operation_description=operation_description)
    bot.send_message(message.chat.id, confirmation_message, reply_markup=keyboard)

    # Устанавливаем следующий хендлер для обработки ответа пользователя
    bot.register_next_step_handler(message, lambda m: process_confirmation(m, command))


def process_confirmation(message, command):
    if message.text == "Да":
        execute_shell_command(message, command)
    else:
        bot.send_message(message.chat.id, CANCEL_MESSAGE, reply_markup=types.ReplyKeyboardRemove())


#
# Получение имени пользователя для отправки скрипту
#
def get_username_by_id(user_id):
    try:
        user_info = bot.get_chat_member(user_id, user_id)
        username = user_info.user.username
        return f"@{username}"
    except Exception as ex:
        log.error(f"Error getting user information: {ex}")
        return None


#
# Хендлеры команд бота
#
# lcnova
@bot.message_handler(commands=['server_status_lcnova'])
def server_status_lcnova(message):
    if check_and_send_permission_error(message, 'server_status_lcnova'):
        username = get_username_by_id(message.from_user.id)
        command = f"sudo -u lcnova bash -c 'cd ~/ && ./run.sh -u {username} {COMMAND_STATUS}"
        execute_shell_command(message, command)


@bot.message_handler(commands=['server_stop_lcnova'])
def server_stop_lcnova(message):
    if check_and_send_permission_error(message, 'server_stop_lcnova'):
        username = get_username_by_id(message.from_user.id)
        command = f"sudo -u lcnova bash -c 'cd ~/ && ./run.sh -u {username} {COMMAND_STOP}"
        send_confirmation_message(message, "Действие приведёт к остановке сервера.", command)


@bot.message_handler(commands=['server_restart_lcnova'])
def server_restart_lcnova(message):
    if check_and_send_permission_error(message, 'server_restart_lcnova'):
        username = get_username_by_id(message.from_user.id)
        command = f"sudo -u lcnova bash -c 'cd ~/ && ./run.sh -u {username} {COMMAND_RESTART}"
        send_confirmation_message(message, "Действие приведёт к перезапуску сервера.", command)


@bot.message_handler(commands=['server_lcnova_dbot_restart'])
def server_restart_lcnova(message):
    if check_and_send_permission_error(message, 'server_lcnova_dbot_restart'):
        username = get_username_by_id(message.from_user.id)
        command = f"sudo -u lcnova bash -c 'cd ~/ && ./run.sh -u {username} {COMMAND_DISCORDBOT_RESTART}"
        send_confirmation_message(message, "Действие приведёт к перезапуску Discord бота.", command)


# lctest
@bot.message_handler(commands=['server_status_lctest'])
def server_status_lctest(message):
    if check_and_send_permission_error(message, 'server_status_lctest'):
        username = get_username_by_id(message.from_user.id)
        command = f"sudo -u lctest bash -c 'cd ~/ && ./run.sh -u {username} {COMMAND_STATUS}"
        execute_shell_command(message, command)


@bot.message_handler(commands=['server_stop_lctest'])
def server_stop_lctest(message):
    if check_and_send_permission_error(message, 'server_stop_lctest'):
        username = get_username_by_id(message.from_user.id)
        command = f"sudo -u lctest bash -c 'cd ~/ && ./run.sh -u {username} {COMMAND_STOP}"
        send_confirmation_message(message, "Действие приведёт к остановке сервера.", command)


@bot.message_handler(commands=['server_restart_lctest'])
def server_restart_lctest(message):
    if check_and_send_permission_error(message, 'server_restart_lctest'):
        username = get_username_by_id(message.from_user.id)
        command = f"sudo -u lctest bash -c 'cd ~/ && ./run.sh -u {username} {COMMAND_RESTART}"
        send_confirmation_message(message, "Действие приведёт к перезапуску сервера.", command)


#
# Grafana
#
# Добавляем хендлер для команды "grafana"
@bot.message_handler(commands=['grafana'])
def handle_grafana(message):
    if check_and_send_permission_error(message, 'grafana'):
        # Создаем клавиатуру с кнопками
        keyboard = types.InlineKeyboardMarkup()
        button_online = types.InlineKeyboardButton("Online", callback_data='online_value')
        button_online_chart = types.InlineKeyboardButton("Online chart", callback_data='online_chart')
        button_gold = types.InlineKeyboardButton("Gold", callback_data='gold')
        button_gold_rate = types.InlineKeyboardButton("Gold rate", callback_data='gold_rate')

        # Добавляем кнопки на клавиатуру
        keyboard.add(button_online, button_online_chart, button_gold, button_gold_rate)

        # Отправляем сообщение с клавиатурой
        bot.send_message(message.chat.id, "Выберите опцию:", reply_markup=keyboard)


# Добавляем хендлер для обработки нажатий на кнопки
@bot.callback_query_handler(func=lambda call: True)
def handle_button_click(call):
    # Получаем данные из нажатой кнопки
    option = call.data

    if option in dashboard_options:
        option_values = dashboard_options[option]
        # Уникальное имя файла для графика, чтобы избежать конфликтов имён
        file_name = generate_unique_filename() + ".png"
        # Обрабатываем выбранную опцию
        get_grafana_panel_image(
            file_name,
            api_url,
            api_key,
            option_values['dashboard_uid'],
            option_values['panel_id'],
            option_values['time_from'],
            option_values['time_to'],
            option_values['width'],
            option_values['height']
        )

        log.info(
            f"GRAFANA: "
            f"chat id: {call.message.chat.id}, "
            f"username: {call.message.from_user.username}, "
            f"user id: {call.message.from_user.id}, "
            f"option: {option}"
        )

        # Отправляем изображение пользователю
        with open(file_name, 'rb') as photo:
            bot.send_photo(call.message.chat.id, photo)
        # Удаляем файл
        os.remove(file_name)


# Whatever
@bot.message_handler(content_types=["text"])
def main(message):
    bot.send_message(message.chat.id, INVALID_COMMAND_MESSAGE)


#
# Выполняем shell команды на сервере.
#
def execute_shell_command(message, shell_command):
    try:
        log.info(f"Executing command: \"{shell_command}\" by {message.from_user.id} [{message.from_user.username}]")

        output = check_output(shell_command, shell=True)

        # Очистка вывода Bash скриптов от кодов цвета консоли
        def remove_color_codes(text):
            color_pattern = re.compile(rb'\033\[[;0-9]*[a-zA-Z]')
            cleaned_text = color_pattern.sub(b'', text).decode('utf-8')
            return cleaned_text

        cleaned_output = remove_color_codes(output)

        # Обрамление в тег <code> текста: [число] текст.
        pattern = re.compile(r'\[(\d+)] ([\w\s]+)\.')

        def replace_tags(match):
            index = match.group(1)
            text = match.group(2)
            return f"<code>[{index}] {text}.</code>"

        cleaned_output = re.sub(pattern, replace_tags, cleaned_output)

        # Форматирование онлайна
        pattern = re.compile(r'Online: (\d+)$')

        def replace_online(match):
            number = match.group(1)
            return f"<b>Online: {number}</b>"

        cleaned_output = re.sub(pattern, replace_online, cleaned_output)

        bot.send_message(message.chat.id, cleaned_output, reply_markup=types.ReplyKeyboardRemove(), parse_mode='HTML')
        return cleaned_output
    except Exception as ex:
        error_message = f"Error executing command: {ex}"
        bot.send_message(message.chat.id, error_message)
        return "Error!"


#
# Хендлер выхода из бота по CTRL+C, завершения работы
#
def handle_exit():
    log.info("Received signal to exit. Stopping the bot.")
    global exit_flag
    exit_flag = True
    bot.stop_polling()
    raise KeyboardInterrupt


#
# __main__
#
if __name__ == '__main__':
    signal.signal(signal.SIGINT, handle_exit)
    signal.signal(signal.SIGTERM, handle_exit)

    try:
        log.timestamp()
        log.info(f"Bot started. Bot token: {bot_token}")
        # Retry mechanism:
        while not exit_flag:
            try:
                bot.polling(none_stop=True, timeout=25)
            except requests.exceptions.ReadTimeout:
                log.error("Timeout error. Retrying...")
                time.sleep(5)
                continue
            except Exception as e:
                log.exception(f"Error in main loop: {e}. Trying to restart.")
                time.sleep(5)
                continue
    except KeyboardInterrupt:
        log.info("Bot stopped.")
