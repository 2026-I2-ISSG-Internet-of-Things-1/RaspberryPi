#!/bin/bash
# Script d'installation de la passerelle MariaDB sur Raspberry Pi

echo "🚀 Installation de la passerelle MariaDB locale..."

# 1. Installer MariaDB
echo "📦 Installation de MariaDB..."
sudo apt update
sudo apt install -y mariadb-server mariadb-client python3-pip

# 2. Configurer MariaDB
echo "🔧 Configuration de MariaDB..."
sudo mysql -e "CREATE DATABASE IF NOT EXISTS iot_local;"
sudo mysql -e "CREATE USER IF NOT EXISTS 'iot_user'@'localhost' IDENTIFIED BY 'iot_password';"
sudo mysql -e "GRANT ALL PRIVILEGES ON iot_local.* TO 'iot_user'@'localhost';"
sudo mysql -e "FLUSH PRIVILEGES;"

# 3. Installer les dépendances Python
echo "🐍 Installation des dépendances Python..."
pip3 install mysql-connector-python python-dotenv

# 4. Créer le service systemd pour auto-démarrage
echo "⚙️ Configuration du service auto-démarrage..."
sudo tee /etc/systemd/system/iot-bridge.service > /dev/null <<EOF
[Unit]
Description=IoT Database Bridge Service
After=network.target mariadb.service

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/RaspberryPi/src
ExecStart=/usr/bin/python3 /home/pi/RaspberryPi/src/main.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# 5. Activer le service
sudo systemctl daemon-reload
sudo systemctl enable iot-bridge.service

echo "✅ Installation terminée!"
echo "📋 Commandes utiles:"
echo "   sudo systemctl start iot-bridge    # Démarrer le service"
echo "   sudo systemctl stop iot-bridge     # Arrêter le service"
echo "   sudo systemctl status iot-bridge   # Voir le statut"
echo "   sudo journalctl -u iot-bridge -f   # Voir les logs en temps réel"
