import time
import signal
import re
import shutil
import os
from subprocess import check_output
import telebot
from telebot import types
import requests
from config import bot_token, api_url, api_key, dashboard_options
from permissions import check_permission
from logger import log

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
# Проверка доступа пользователя
#
def check_and_send_permission_error(message, command):
	permission_result = check_permission(message, command)
	print(permission_result)
	if permission_result["code"] != "SUCCESS":
		error_message = permission_result["message"]
		bot.send_message(message.chat.id, error_message, parse_mode='HTML')
		log.error(f"check_and_send_permission_error: chat id: {message.chat.id}, username: {message.from_user.username}, user id: {message.from_user.id}, command: {command}, error: {error_message}")
		return False
	log.info(f"check_and_send_permission_error: chat id: {message.chat.id}, username: {message.from_user.username}, user id: {message.from_user.id}, command: {command}, status: SUCCESS")
	return True

#
# Изображение графика
#
def get_grafana_panel_image(api_url, api_key, dashboard_uid, panel_id, timefrom="now", timeto="now-6h", width=1000, height=500):
	url = f"{api_url}/render/d-solo/{dashboard_uid}?orgId=1&panelId={panel_id}&width={width}&height={height}&tz=Europe/Moscow&from=${timefrom}&to=${timeto}"

	headers = {
		"Authorization": f"Bearer {api_key}"
	}

	response = requests.get(url, headers=headers, stream=True)

	if response.status_code == 200:
		with open(f"panel_image.png", 'wb') as f:
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
	except Exception as e:
		log.error(f"Error getting user information: {e}")
		return None

#
# Хендлеры команд бота
#
# lcnova
@bot.message_handler(commands=['server_status_lcnova'])
def server_status_lcnova(message):
	if check_and_send_permission_error(message, 'server_status_lcnova'):
		command = f"sudo -u lcnova bash -c 'cd ~/ && ./run.sh -u {get_username_by_id(message.from_user.id)} {COMMAND_STATUS}"
		execute_shell_command(message, command)

@bot.message_handler(commands=['server_stop_lcnova'])
def server_stop_lcnova(message):
	if check_and_send_permission_error(message, 'server_stop_lcnova'):
		command = f"sudo -u lcnova bash -c 'cd ~/ && ./run.sh -u {get_username_by_id(message.from_user.id)} {COMMAND_STOP}"
		send_confirmation_message(message, "Действие приведёт к остановке сервера.", command)

@bot.message_handler(commands=['server_restart_lcnova'])
def server_restart_lcnova(message):
	if check_and_send_permission_error(message, 'server_restart_lcnova'):
		command = f"sudo -u lcnova bash -c 'cd ~/ && ./run.sh -u {get_username_by_id(message.from_user.id)} {COMMAND_RESTART}"
		send_confirmation_message(message, "Действие приведёт к перезапуску сервера.", command)

@bot.message_handler(commands=['server_lcnova_dbot_restart'])
def server_restart_lcnova(message):
	if check_and_send_permission_error(message, 'server_lcnova_dbot_restart'):
		command = f"sudo -u lcnova bash -c 'cd ~/ && ./run.sh -u {get_username_by_id(message.from_user.id)} {COMMAND_DISCORDBOT_RESTART}"
		send_confirmation_message(message, "Действие приведёт к перезапуску Discord бота.", command)

# lctest
@bot.message_handler(commands=['server_status_lctest'])
def server_status_lctest(message):
	if check_and_send_permission_error(message, 'server_status_lctest'):
		command = f"sudo -u lctest bash -c 'cd ~/ && ./run.sh -u {get_username_by_id(message.from_user.id)} {COMMAND_STATUS}"
		execute_shell_command(message, command)

@bot.message_handler(commands=['server_stop_lctest'])
def server_stop_lctest(message):
	if check_and_send_permission_error(message, 'server_stop_lctest'):
		command = f"sudo -u lctest bash -c 'cd ~/ && ./run.sh -u {get_username_by_id(message.from_user.id)} {COMMAND_STOP}"
		send_confirmation_message(message, "Действие приведёт к остановке сервера.", command)

@bot.message_handler(commands=['server_restart_lctest'])
def server_restart_lctest(message):
	if check_and_send_permission_error(message, 'server_restart_lctest'):
		command = f"sudo -u lctest bash -c 'cd ~/ && ./run.sh -u {get_username_by_id(message.from_user.id)} {COMMAND_RESTART}"
		send_confirmation_message(message, "Действие приведёт к перезапуску сервера.", command)

# Grafana

# Добавляем хендлер для команды "grafana"
@bot.message_handler(commands=['grafana'])
def handle_grafana(message):
	if check_and_send_permission_error(message, 'grafana'):
		# Создаем клавиатуру с кнопками
		keyboard = types.InlineKeyboardMarkup()
		button_online = types.InlineKeyboardButton("Online", callback_data='online_value')
		button_online_chart = types.InlineKeyboardButton("Online chart", callback_data='online_chart')
		#button_players = types.InlineKeyboardButton("Players", callback_data='players')
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
		# Обрабатываем выбранную опцию
		get_grafana_panel_image(
			api_url,
			api_key,
			option_values['dashboard_uid'],
			option_values['panel_id'],
			option_values['time_from'],
			option_values['time_to'],
			option_values['width'],
			option_values['height']
		)

		log.info(f"GRAFANA: chat id: {call.message.chat.id}, username: {call.message.from_user.username}, user id: {call.message.from_user.id}, option: {option}")
		# Отправляем изображение пользователю
		with open('panel_image.png', 'rb') as photo:
			bot.send_photo(call.message.chat.id, photo)
		# Удаляем файл
		os.remove('panel_image.png')

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
		pattern = re.compile(r'\[([\d]+)\] ([\w\s]+)\.')
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
	except Exception as e:
		error_message = f"Error executing command: {e}"
		bot.send_message(message.chat.id, error_message)
		return "Error!"

#
# Хендлер выхода из бота по CTRL+C, завершения работы
#
def handle_exit(signum, frame):
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