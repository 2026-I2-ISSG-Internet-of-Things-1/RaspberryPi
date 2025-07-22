import serial
import time

# Configuration des deux ports série
capteurs = serial.Serial("/dev/ttyACM0", 9600, timeout=1)  # Arduino capteurs
actionneurs = serial.Serial("/dev/ttyACM1", 9600, timeout=1)  # Arduino actionneurs


def send_command(ser, command):
    ser.write((command + "\n").encode())
    response = ser.readline().decode().strip()
    return response


try:
    while True:
        # === Lecture des capteurs sur ttyACM0 ===
        temp = send_command(capteurs, "GET TEMP")
        lum = send_command(capteurs, "GET LUM")
        button = send_command(capteurs, "GET BUTTON")

        print("=== Données capteurs ===")
        print(temp)
        print(lum)
        print(button)

        # === Commandes actionneurs sur ttyACM1 ===
        # Exemple : faire buzzer si bouton pressé
        if "PRESSED" in button:
            print("Bouton pressé : on déclenche le buzzer !")
            print(send_command(actionneurs, "CMD BUZZ"))

        # Exemple : changer la LED RGB toutes les 5 boucles
        if int(time.time() * 2) % 5 == 0:
            print("Changement couleur RGB")
            print(send_command(actionneurs, "CMD RGB NEXT"))

        # Exemple : afficher la température sur le LCD
        lcd_message = temp.replace("TEMP:", "Temp:") + "C"
        print("Affichage LCD : " + lcd_message)
        print(send_command(actionneurs, "LCD " + lcd_message))

        print("========================\n")

        time.sleep(0.5)

except KeyboardInterrupt:
    print("Arrêt du programme.")
    capteurs.close()
    actionneurs.close()
