import serial
import time

# Configuration du port série (adapter /dev/ttyACM0 ou /dev/ttyUSB0 selon ton cas)
arduino = serial.Serial("/dev/ttyACM0", 9600, timeout=1)


# Fonction pour envoyer une commande et lire la réponse
def send_command(command):
    arduino.write((command + "\n").encode())
    response = arduino.readline().decode().strip()
    return response


try:
    while True:
        # Demande température
        temp = send_command("GET TEMP")

        # Demande luminosité
        lum = send_command("GET LUM")

        # Demande état du bouton
        button = send_command("GET BUTTON")

        # Affiche les données reçues
        print("=== Données capteurs ===")
        print(temp)
        print(lum)
        print(button)
        print("========================\n")

        time.sleep(0.5)

except KeyboardInterrupt:
    print("Arrêt du programme.")
    arduino.close()
