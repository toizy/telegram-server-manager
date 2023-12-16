#!/bin/bash

# Переменные
readonly SERVICE_NAME="lcn_tg_bot"
readonly SERVICE_DIR="$HOME/.config/systemd/user"
readonly SERVICE_FILE="$SERVICE_DIR/${SERVICE_NAME}.service"

# Остановка и отключение службы
systemctl --user stop "${SERVICE_NAME}.service"
if [[ ! $? ]]; then
    echo "Ошибка остановки службы."
fi

systemctl --user disable "${SERVICE_NAME}.service"
if [[ ! $? ]]; then
    echo "Ошибка отключения службы."
fi

# Удаление файла службы
rm -f "$SERVICE_FILE"
if [[ ! $? ]]; then
    echo "Ошибка удаления файла службы."
fi

# Перезапуск systemd
systemctl --user daemon-reload
if [[ ! $? ]]; then
    echo "Ошибка перезапуска systemd."
fi

echo "Служба успешно деинсталлирована."
