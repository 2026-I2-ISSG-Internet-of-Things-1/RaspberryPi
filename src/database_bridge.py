#!/usr/bin/env python3
"""
Passerelle MariaDB locale pour Raspberry Pi
Reçoit les données du site web et les stocke en local, puis les synchronise avec le cloud
"""

import mysql.connector
import requests
import json
import time
from datetime import datetime
import os
from dotenv import load_dotenv

# Charger les variables d'environnement
load_dotenv()


class DatabaseBridge:
    def __init__(self):
        # Configuration base locale (MariaDB sur RPi)
        self.local_db_config = {
            "host": "localhost",
            "user": "iot_user",
            "password": "iot_password",
            "database": "iot_local",
        }

        # Configuration base cloud (AWS)
        self.cloud_db_config = {
            "host": os.getenv("DB_HOST"),
            "user": os.getenv("DB_USER"),
            "password": os.getenv("DB_PASSWORD"),
            "database": os.getenv("DB_NAME"),
        }

        self.init_local_database()

    def get_local_connection(self):
        """Connexion à la base locale"""
        try:
            return mysql.connector.connect(**self.local_db_config)
        except mysql.connector.Error as e:
            print(f"Erreur connexion locale: {e}")
            return None

    def get_cloud_connection(self):
        """Connexion à la base cloud"""
        try:
            return mysql.connector.connect(**self.cloud_db_config)
        except mysql.connector.Error as e:
            print(f"Erreur connexion cloud: {e}")
            return None

    def init_local_database(self):
        """Initialise la base de données locale"""
        conn = self.get_local_connection()
        if not conn:
            print("❌ Impossible de créer la base locale")
            return False

        try:
            cursor = conn.cursor()

            # Créer la table locale identique au cloud
            create_table_query = """
            CREATE TABLE IF NOT EXISTS MyAsset (
                MyAssetNumber INT(11) AUTO_INCREMENT PRIMARY KEY,
                MyAssetType CHAR(12) NOT NULL,
                MyAssetName CHAR(20) NOT NULL,
                MyAssetValue FLOAT NOT NULL,
                MyAssetUnit CHAR(12) NOT NULL,
                MyAssetComment TEXT,
                MyAssetTimeStamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                synchronized BOOLEAN DEFAULT FALSE
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
            """

            cursor.execute(create_table_query)
            conn.commit()
            print("✅ Base locale initialisée")
            return True

        except Exception as e:
            print(f"❌ Erreur init base locale: {e}")
            return False
        finally:
            cursor.close()
            conn.close()

    def store_sensor_data(self, asset_type, asset_name, value, unit, comment=""):
        """Stocke les données capteurs en local"""
        conn = self.get_local_connection()
        if not conn:
            return False

        try:
            cursor = conn.cursor()
            query = """
            INSERT INTO MyAsset (MyAssetType, MyAssetName, MyAssetValue, MyAssetUnit, MyAssetComment)
            VALUES (%s, %s, %s, %s, %s)
            """
            cursor.execute(query, (asset_type, asset_name, value, unit, comment))
            conn.commit()
            print(f"✅ Données stockées localement: {asset_type} = {value}")
            return True

        except Exception as e:
            print(f"❌ Erreur stockage local: {e}")
            return False
        finally:
            cursor.close()
            conn.close()

    def sync_to_cloud(self):
        """Synchronise les données non synchronisées vers le cloud"""
        local_conn = self.get_local_connection()
        cloud_conn = self.get_cloud_connection()

        if not local_conn or not cloud_conn:
            print("❌ Impossible de se connecter pour synchronisation")
            return False

        try:
            local_cursor = local_conn.cursor(dictionary=True)
            cloud_cursor = cloud_conn.cursor()

            # Récupérer les données non synchronisées
            local_cursor.execute("""
                SELECT * FROM MyAsset WHERE synchronized = FALSE
                ORDER BY MyAssetTimeStamp ASC
            """)
            unsync_data = local_cursor.fetchall()

            sync_count = 0
            for data in unsync_data:
                try:
                    # Insérer dans le cloud
                    cloud_cursor.execute(
                        """
                        INSERT INTO MyAsset (MyAssetType, MyAssetName, MyAssetValue, MyAssetUnit, MyAssetComment, MyAssetTimeStamp)
                        VALUES (%s, %s, %s, %s, %s, %s)
                    """,
                        (
                            data["MyAssetType"],
                            data["MyAssetName"],
                            data["MyAssetValue"],
                            data["MyAssetUnit"],
                            data["MyAssetComment"],
                            data["MyAssetTimeStamp"],
                        ),
                    )

                    # Marquer comme synchronisé
                    local_cursor.execute(
                        """
                        UPDATE MyAsset SET synchronized = TRUE WHERE MyAssetNumber = %s
                    """,
                        (data["MyAssetNumber"],),
                    )

                    sync_count += 1

                except Exception as e:
                    print(f"❌ Erreur sync item {data['MyAssetNumber']}: {e}")
                    continue

            cloud_conn.commit()
            local_conn.commit()

            if sync_count > 0:
                print(f"✅ {sync_count} éléments synchronisés vers le cloud")

            return True

        except Exception as e:
            print(f"❌ Erreur synchronisation: {e}")
            return False
        finally:
            local_cursor.close()
            cloud_cursor.close()
            local_conn.close()
            cloud_conn.close()

    def get_local_data(self, limit=20):
        """Récupère les dernières données locales"""
        conn = self.get_local_connection()
        if not conn:
            return []

        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute(
                """
                SELECT * FROM MyAsset 
                ORDER BY MyAssetTimeStamp DESC 
                LIMIT %s
            """,
                (limit,),
            )
            return cursor.fetchall()

        except Exception as e:
            print(f"❌ Erreur lecture locale: {e}")
            return []
        finally:
            cursor.close()
            conn.close()


# Instance globale
db_bridge = DatabaseBridge()


def main():
    """Fonction principale pour test"""
    print("🚀 Test de la passerelle base de données")

    # Test stockage local
    db_bridge.store_sensor_data(
        "temperature", "RPi Sensor", 25.3, "°C", "Test from RPi"
    )

    # Test lecture locale
    data = db_bridge.get_local_data(5)
    print(f"📊 {len(data)} éléments en local")

    # Test synchronisation
    db_bridge.sync_to_cloud()


if __name__ == "__main__":
    main()
