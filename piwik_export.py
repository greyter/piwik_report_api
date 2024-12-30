import os
import requests
from datetime import datetime
import json

# Créer un fichier json avec cette structure dans lun dossier nommé config
# {
#     "client_id": "xxx_client_id",
#     "client_secret": "xxx_client_secret",
#     "piwik_hostname": "lifelong-learning", # xxx.piwik.pro
#     "date_from": "2024-05-01", # Optionnel. Si absent, reprend le 01/01 de l'année précédente
#     "date_to": "2024-12-08", # Optionnel. Si absent, reprend le 31/12 de l'année précédente
#     "website_id": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
#     "columns": [
#         {
#             "column_id": "timestamp",
#             "transformation_id": "to_start_of_month"
#         },
#         {
#             "custom_channel_grouping_id": "cbacbb7e-a585-41b1-a334-c6ffce5880eb",
#             "column_id": "custom_channel_grouping"
#         },
#         {
#             "column_id": "sessions"
#         },
#         {
#             "column_id": "goal_conversions",
#             "goal_uuid": "4c800ddd-c932-46f2-9da8-a379430e95d4",
#             "requires_events": false
#         }
#     ],
#     "order_by": null,
#     "filters" : null,
#     "metric_filters" : null,
#     "_comment" : [{
#       "order_by" : [[1, "asc"]]
#     }]
# }

# Dossier contenant les fichiers de configuration
config_folder = "config"

# Parcourir chaque fichier JSON dans le dossier de configuration
for config_file in os.listdir(config_folder):
    if config_file.endswith(".json"):  # Filtrer uniquement les fichiers JSON
        config_path = os.path.join(config_folder, config_file)

        # Charger la configuration depuis le fichier JSON
        with open(config_path, "r") as file:
            config = json.load(file)

        # Vérifier si date_from et date_to sont définis dans la configuration
        if not config.get("date_from") or not config.get("date_to"):
            # Calculer les dates pour l'année précédente
            current_year = datetime.now().year
            date_from = f"{current_year - 1}-01-01"
            date_to = f"{current_year - 1}-12-31"
        else:
            date_from = config["date_from"]
            date_to = config["date_to"]

        # Récupérer les autres variables depuis la configuration
        client_id = config["client_id"]
        client_secret = config["client_secret"]
        piwik_hostname = config["piwik_hostname"]
        website_id = config["website_id"]
        columns = config["columns"]
        order_by = config["order_by"]
        filters = config["filters"]
        metric_filters = config["metric_filters"]
        

        # URL de l'endpoint d'authentification
        AUTH_URL = f"https://{piwik_hostname}.piwik.pro/auth/token"

        # Corps de la requête pour l'authentification
        payload = {
            "grant_type": "client_credentials",
            "client_id": client_id,
            "client_secret": client_secret
        }

        # Effectuer la requête POST pour obtenir le token
        response = requests.post(AUTH_URL, data=payload)

        if response.status_code == 200:
            token = response.json().get("access_token")  # Extraire le token d'accès
            print(f"[{config_file}] Token d'authentification obtenu :", token)
        else:
            print(f"[{config_file}] Erreur lors de l'obtention du token :", response.status_code, response.text)
            continue

        #-----------------

        # URL et headers pour l'API de Piwik
        PIWIK_URL = f"https://{piwik_hostname}.piwik.pro/api/analytics/v1/query/"
        HEADERS = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/vnd.api+json"
        }

        # Corps de la requête pour extraire les données
        PAYLOAD = {
            "date_from": date_from,
            "date_to": date_to,
            "website_id": website_id,
            "offset": 0,
            "limit": 10000,
            "format": "csv",
            "columns": columns,
            "order_by": order_by if order_by is not None else [[0, "desc"]],
            "filters": filters,
            "metric_filters": metric_filters
        }

        # Effectuer la requête POST pour récupérer les données
        response = requests.post(PIWIK_URL, headers=HEADERS, json=PAYLOAD)

        if response.status_code == 200:
            # Traiter la réponse CSV
            data = response.text
            print(f"[{config_file}] Données extraites avec succès.")
            
            # Générer le nom du fichier avec la date et l'heure
            current_datetime = datetime.now().strftime("%Y%m%d-%H%M%S")
            #filename = os.path.join("export", f"{piwik_hostname}_{date_from}_{date_to}_{current_datetime}.csv")
            config_basename = os.path.splitext(config_file)[0]  # Remove the extension from the filename
            filename = os.path.join("export", f"{config_basename}_{date_from}_{date_to}.csv")

            # Sauvegarder dans un fichier CSV
            with open(filename, "w", encoding='utf-8', newline='') as file:
                file.write(data)
            print(f"[{config_file}] Données sauvegardées dans '{filename}'")
        else:
            print(f"[{config_file}] Erreur :", response.status_code, response.text)
