import json
import os
from datetime import datetime
from logger import log


# Исключения
class TzeUserNotFound(Exception):
    pass


class TzeCommandListEmpty(Exception):
    pass


class TzeCommandNotFound(Exception):
    pass


class TzeCommandExpired(Exception):
    pass


class TzeCheckSuccess(Exception):
    pass


# Хранилище разрешений
permissions_data = {}

# Путь к файлу для сохранения и загрузки разрешений
PERMISSIONS_FILE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), f"permissions.json")

# Последнее изменение файла
last_modification_time = None


# Загрузка разрешений из файла
def load_permissions():
    global last_modification_time
    global permissions_data
    try:
        # Получаем время последнего изменения файла
        current_modification_time = os.path.getmtime(PERMISSIONS_FILE_PATH)

        # Проверяем, изменился ли файл
        if current_modification_time != last_modification_time:
            with open(PERMISSIONS_FILE_PATH, "r") as file:
                permissions_data = json.load(file)
            # Обновляем время последнего изменения
            last_modification_time = current_modification_time
            log.info(f"Permissions loaded: {datetime.now().strftime('%d-%m-%Y %H:%M:%S')}")
    except FileNotFoundError:
        log.error(f"Error: Permissions file '{PERMISSIONS_FILE_PATH}' not found.")
        permissions_data = {}
    except json.JSONDecodeError:
        log.error(f"Error: Unable to parse JSON in permissions file '{PERMISSIONS_FILE_PATH}'.")
        permissions_data = {}
    except Exception as e:
        log.error(f"Error loading permissions: {e}")
        permissions_data = {}


# Сохранение разрешений в файл
def save_permissions(file_path):
    try:
        with open(file_path, 'w') as file:
            json.dump(permissions_data, file, indent=2)
        log.info(f"Permissions saved to {file_path}")
    except Exception as e:
        log.error(f"Error saving permissions to {file_path}: {e}")


# Функция проверки разрешения
def check_permission(message, command):
    try:
        global permissions_data
        load_permissions()
        user_permissions = permissions_data.get("users", {}).get(str(message.from_user.id), {})
        if not user_permissions:
            raise TzeUserNotFound("")

        command_permissions = user_permissions.get("commands")
        if not command_permissions:
            raise TzeCommandListEmpty("")

        expiration_date_str = command_permissions.get(command)
        if not expiration_date_str:
            raise TzeCommandNotFound("")

        expiration_date = datetime.strptime(expiration_date_str, "%Y-%m-%d %H:%M:%S")
        current_date = datetime.now()
        if current_date > expiration_date:
            raise TzeCommandExpired("")
        else:
            raise TzeCheckSuccess("")

    except TzeCheckSuccess:
        return {"code": "SUCCESS", "message": "Permission granted."}
    except TzeUserNotFound:
        error_message = f"Error: User <code>{message.from_user.id}</code> [@{message.from_user.username}] not found in permissions table."
        return {"code": "USER_NOT_FOUND", "message": error_message}
    except TzeCommandListEmpty:
        error_message = f"Error: User <code>{message.from_user.id}</code> [@{message.from_user.username}] has no commands in permissions table."
        return {"code": "COMMAND_LIST_EMPTY", "message": error_message}
    except TzeCommandNotFound:
        error_message = f"Error: Command <code>{command}</code> not found in permissions for user <code>{message.from_user.id}</code> [@{message.from_user.username}]."
        return {"code": "COMMAND_NOT_FOUND", "message": error_message}
    except TzeCommandExpired:
        error_message = f"Error: Permission for command <code>{command}</code> expired for user <code>{message.from_user.id}</code> [@{message.from_user.username}]."
        return {"code": "EXPIRED_PERMISSION", "message": error_message}
    except KeyError:
        error_message = f"Error: Command <code>{command}</code> not found in permissions for user <code>{message.from_user.id}</code> [@{message.from_user.username}]."
        return {"code": "COMMAND_NOT_FOUND", "message": error_message}
    except Exception as e:
        error_message = f"Error checking permission: {e}"
        return {"code": "GENERAL_ERROR", "message": error_message}
