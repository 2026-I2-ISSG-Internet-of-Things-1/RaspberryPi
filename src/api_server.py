#!/usr/bin/env python3
"""
API simple sur Raspberry Pi pour recevoir les données du site web
"""

from flask import Flask, request, jsonify
from database_bridge import db_bridge
import threading
import time

app = Flask(__name__)


@app.route("/api/data", methods=["POST"])
def receive_data():
    """Reçoit les données du site web et les stocke localement"""
    try:
        data = request.get_json()

        if not data:
            return jsonify({"error": "No data provided"}), 400

        # Extraire les informations
        asset_type = data.get("type", "unknown")
        asset_name = data.get("name", "Web Data")
        value = data.get("value", 0.0)
        unit = data.get("unit", "")
        comment = data.get("comment", "From website")

        # Stocker en base locale
        success = db_bridge.store_sensor_data(
            asset_type, asset_name, value, unit, comment
        )

        if success:
            print(f"✅ Données reçues du site: {asset_type} = {value}")
            return jsonify({"status": "success", "message": "Data stored locally"}), 200
        else:
            return jsonify({"error": "Failed to store data"}), 500

    except Exception as e:
        print(f"❌ Erreur API: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/status", methods=["GET"])
def status():
    """Statut de la passerelle"""
    try:
        # Compter les données locales
        local_data = db_bridge.get_local_data(1)
        return jsonify(
            {
                "status": "running",
                "local_entries": len(local_data),
                "last_sync": "active",
            }
        ), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


def sync_worker():
    """Worker pour synchronisation périodique"""
    while True:
        try:
            print("🔄 Synchronisation automatique...")
            db_bridge.sync_to_cloud()
            time.sleep(60)  # Sync toutes les minutes
        except Exception as e:
            print(f"❌ Erreur sync worker: {e}")
            time.sleep(30)


if __name__ == "__main__":
    # Démarrer le worker de synchronisation
    sync_thread = threading.Thread(target=sync_worker, daemon=True)
    sync_thread.start()

    print("🚀 API Raspberry Pi démarrée sur port 5001")
    app.run(host="0.0.0.0", port=5001, debug=False)
