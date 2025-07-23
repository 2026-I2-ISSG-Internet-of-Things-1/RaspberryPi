import serial
import time
from sense_hat import SenseHat
from database_bridge import db_bridge

# Configuration du Sense HAT
sense = SenseHat()

# Configuration des deux ports série
capteurs = serial.Serial("/dev/ttyACM0", 9600, timeout=1)  # Arduino capteurs
actionneurs = serial.Serial("/dev/ttyACM1", 9600, timeout=1)  # Arduino actionneurs


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
                db_bridge.store_sensor_data("joystick", "Sense HAT Joystick", 1.0, "direction", f"Direction: {direction}")
                print(f"✅ Joystick {direction} stocké en base")
            except Exception as e:
                print(f"❌ Erreur stockage joystick: {e}")
            
            return True
    return False


def check_web_commands():
    """Vérifie s'il y a des commandes depuis le site web"""
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

        # Afficher la température sur le LCD (vérifier que temp contient bien des données)
        if temp and "TEMP:" in temp:
            lcd_message = temp.replace("TEMP:", "Temp:") + "C"
            print(f"Affichage LCD : {lcd_message}")
            lcd_response = send_command(actionneurs, "LCD " + lcd_message)
            print(f"LCD response: {lcd_response}")
        else:
            print(f"Erreur: température invalide reçue: {temp}")

        print("========================\n")

        loop_counter += 1

        # Synchroniser avec le cloud toutes les 10 boucles
        if loop_counter % 10 == 0:
            print("🔄 Synchronisation avec le cloud...")
            db_bridge.sync_to_cloud()

        time.sleep(0.5)

except KeyboardInterrupt:
    print("Arrêt du programme.")
    capteurs.close()
    actionneurs.close()
