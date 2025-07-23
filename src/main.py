import serial
import time
from sense_hat import SenseHat
from database_bridge import db_bridge

# Configuration du Sense HAT
sense = SenseHat()

# Configuration des deux ports série
capteurs = serial.Serial("/dev/ttyACM0", 9600, timeout=1)  # Arduino capteurs
actionneurs = serial.Serial("/dev/ttyACM1", 9600, timeout=1)  # Arduino actionneurs

# Variable globale pour stocker le dernier message LCD du web
last_web_message = ""


def send_command(ser, command):
    ser.write((command + "\n").encode())
    response = ser.readline().decode().strip()
    return response


def check_joystick():
    """Vérifie si le joystick a été actionné dans une direction et stocke l'événement"""
    events = sense.stick.get_events()
    for event in events:
        if event.action == "pressed":
            direction = event.direction
            print(f"joystick : {direction} PRESSED")

            # Stocker l'événement joystick en base locale
            try:
                db_bridge.store_sensor_data(
                    "joystick",
                    "Sense HAT Joystick",
                    1.0,
                    "direction",
                    f"Direction: {direction}",
                )
                print(f"✅ Joystick {direction} stocké en base")

                # Synchronisation immédiate pour les événements joystick
                print("🔄 Synchronisation immédiate du joystick...")
                db_bridge.sync_to_cloud()

            except Exception as e:
                print(f"❌ Erreur stockage joystick: {e}")

            return True
    return False


def update_lcd_display(temp_string, web_message=""):
    """Met à jour l'affichage LCD avec température en haut et message web en bas"""
    global last_web_message
    
    if not temp_string or "TEMP:" not in temp_string:
        return
    
    # Ligne 1: Température (limitée à 16 caractères)
    temp_display = temp_string.replace("TEMP:", "Temp:") + "C"
    temp_display = temp_display[:16]  # Limite à 16 caractères pour ligne 1
    
    # Ligne 2: Message web ou vide (limitée à 16 caractères)
    message_display = (web_message or last_web_message)[:16]
    
    # Construire la commande LCD avec les deux lignes
    # Format: "LCD_DUAL ligne1|ligne2"
    if message_display:
        lcd_command = f"LCD_DUAL {temp_display}|{message_display}"
        print(f"Affichage LCD (2 lignes): '{temp_display}' + '{message_display}'")
    else:
        # Si pas de message web, afficher seulement la température
        lcd_command = f"LCD {temp_display}"
        print(f"Affichage LCD (1 ligne): '{temp_display}'")
    
    lcd_response = send_command(actionneurs, lcd_command)
    print(f"LCD response: {lcd_response}")


def check_web_commands():
    """Vérifie s'il y a des commandes depuis le site web"""
    global last_web_message
    
    try:
        # Récupérer les dernières commandes non traitées
        local_data = db_bridge.get_local_data(10)
        for data in local_data:
            command = data["MyAssetComment"]

            # Commandes buzzer
            if data["MyAssetType"] == "command" and "BUZZER" in command:
                print(f"🌐 Commande buzzer reçue du site: {command}")

                if command == "BUZZER_ON":
                    print("🔊 Activation du buzzer depuis le site!")
                    buzz_response = send_command(actionneurs, "CMD BUZZ")
                    print(f"Buzzer response: {buzz_response}")

                elif command == "BUZZER_OFF":
                    print("🔇 Désactivation du buzzer")
                    # Le buzzer s'arrête automatiquement après le délai

            # Commandes couleur LED RGB
            elif data["MyAssetType"] == "command" and "SET_COLOR:" in command:
                print(f"🌈 Commande couleur reçue du site: {command}")
                color_response = send_command(actionneurs, command)
                print(f"LED RGB response: {color_response}")

            # Commandes LCD
            elif data["MyAssetType"] == "command" and command.startswith("LCD "):
                print(f"📱 Commande LCD reçue du site: {command}")
                # Extraire le message (enlever "LCD ")
                message = command[4:]  # Enlever "LCD "
                # Stocker le message pour l'affichage avec la température
                last_web_message = message
                print(f"Message LCD stocké: {last_web_message}")

    except Exception as e:
        print(f"❌ Erreur check_web_commands: {e}")

    except Exception as e:
        print(f"❌ Erreur check_web_commands: {e}")


try:
    loop_counter = 0

    while True:
        # === Vérification du joystick Sense HAT ===
        check_joystick()

        # === Vérification des commandes web ===
        check_web_commands()

        # === Lecture des capteurs sur ttyACM0 ===
        temp = send_command(capteurs, "GET TEMP")
        lum = send_command(capteurs, "GET LUM")
        button = send_command(capteurs, "GET BUTTON")

        print("=== Données capteurs ===")
        print(temp)
        print(lum)
        print(button)

        # === Stockage en base locale ===
        # Stocker température
        if temp and "TEMP:" in temp:
            temp_value = float(temp.replace("TEMP:", ""))
            db_bridge.store_sensor_data("temperature", "Arduino Temp", temp_value, "°C")

        # Stocker luminosité
        if lum and "LUM:" in lum:
            lum_value = float(lum.replace("LUM:", ""))
            db_bridge.store_sensor_data("light", "Arduino Light", lum_value, "%")

        # Stocker état bouton
        if button:
            button_value = 1.0 if "PRESSED" in button else 0.0
            db_bridge.store_sensor_data(
                "button", "Arduino Button", button_value, "bool"
            )

        # === Commandes actionneurs sur ttyACM1 ===
        # Exemple : faire buzzer si bouton pressé
        if "PRESSED" in button:
            print("Bouton pressé : on déclenche le buzzer !")
            buzz_response = send_command(actionneurs, "CMD BUZZ")
            print(f"Buzzer response: {buzz_response}")
            time.sleep(0.1)  # Petit délai après le buzzer

        # Mettre à jour l'affichage LCD avec température + message web
        if temp and "TEMP:" in temp:
            update_lcd_display(temp)
        else:
            print(f"Erreur: température invalide reçue: {temp}")

        print("========================\n")

        loop_counter += 1

        # Synchroniser avec le cloud toutes les 10 boucles
        if loop_counter % 10 == 0:
            print("🔄 Synchronisation avec le cloud...")
            db_bridge.sync_to_cloud()

            # Debug: afficher les dernières données locales
            if loop_counter % 50 == 0:  # Moins fréquent pour éviter le spam
                try:
                    local_data = db_bridge.get_local_data(5)
                    print(f"📊 Dernières données locales ({len(local_data)} entrées):")
                    for data in local_data:
                        print(
                            f"  - {data['MyAssetType']}: {data['MyAssetComment']} ({data['MyAssetTimeStamp']})"
                        )
                except Exception as e:
                    print(f"❌ Erreur lecture données locales: {e}")

        time.sleep(0.5)

except KeyboardInterrupt:
    print("Arrêt du programme.")
    capteurs.close()
    actionneurs.close()
