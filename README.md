# telegram-server-manager

Telegram bot in Python for game server management

## Installing requirements (AlmaLinux 8)

### Python 3.12.1

```text
sudo dnf update -y
sudo dnf install gcc openssl-devel bzip2-devel libffi-devel zlib-devel wget make tar -y
sudo dnf groupinstall "Development Tools"

sudo wget https://www.python.org/ftp/python/3.12.1/Python-3.12.1.tgz
sudo tar -xf Python-3.12.1.tgz
cd Python-3.12.1
sudo ./configure --enable-optimizations
sudo make altinstall

python3.12 --version
pip3.12 --version
```

### telebot 

https://github.com/KyleJamesWalker/telebot
