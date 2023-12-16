#!/bin/bash

readonly SCRIPT_PATH=$(readlink -f "${BASH_SOURCE[0]}")
readonly SCRIPT_DIR=$(dirname "$SCRIPT_PATH")
readonly BOT_PATH="$SCRIPT_DIR/../main.py"
readonly SERVICE_NAME="lcn_tg_bot"
readonly PYTHON_PATH=$(which python3.12)
readonly CURRENT_USER=$(logname)
readonly SERVICE_DIR="$HOME/.config/systemd/user"
readonly SERVICE_FILE="$SERVICE_DIR/${SERVICE_NAME}.service"

if [ ! -d "$SERVICE_DIR" ]; then
    mkdir -p "$SERVICE_DIR"
fi

# Создание файла службы
cat > "$SERVICE_FILE" <<EOL
[Unit]
Description=LCN Telegram Bot Service
After=network.target

[Service]
ExecStart=$PYTHON_PATH $BOT_PATH
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=default.target
EOL

# Проверка результатов выполнения команд
if [[ ! $? ]]; then
    echo "Ошибка создания файла службы."
    exit 1
fi

# Перезапуск systemd
systemctl --user daemon-reload
if [[ ! $? ]]; then
    echo "Ошибка перезапуска systemd."
    exit 1
fi

# Включение и запуск службы
systemctl --user enable "${SERVICE_NAME}"
if [[ ! $? ]]; then
    echo "Ошибка включения службы."
    exit 1
fi
echo ${SERVICE_FILE}
systemctl --user start "${SERVICE_NAME}"
if [[ ! $? ]]; then
    echo "Ошибка запуска службы."
    exit 1
fi

echo "Служба успешно настроена и запущена."