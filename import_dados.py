import time
import requests
import pymongo
from datetime import datetime, timedelta
from config import API_TOKEN, PLAYER_TAGS, DB_NAME, MONGO_URI

client = pymongo.MongoClient(MONGO_URI)
db = client[DB_NAME]
battles_collection = db["battles"]
players_collection = db["players"]

headers = {
    "Authorization": API_TOKEN
}

MAX_BATTLES_PER_PLAYER = 1000
DAYS_TO_KEEP = 60
REQUEST_DELAY = 1

def clean_old_battles():
    cutoff_date = datetime.now() - timedelta(days=DAYS_TO_KEEP)
    battles_collection.delete_many({"utcTime": {"$lt": cutoff_date}})
    print(f"Batalhas anteriores a {cutoff_date.strftime('%Y-%m-%d')} removidas.")

def get_battle_count(tag):
    return battles_collection.count_documents({"team.tag": tag})

def import_battles():
    clean_old_battles()
    
    for tag in PLAYER_TAGS:
        if get_battle_count(tag) >= MAX_BATTLES_PER_PLAYER:
            print(f"Limite de {MAX_BATTLES_PER_PLAYER} batalhas atingido para {tag}")
            continue

        encoded_tag = tag.replace("#", "%23")
        url = f"https://api.clashroyale.com/v1/players/{encoded_tag}/battlelog"

        try:
            response = requests.get(url, headers=headers)
            
            if response.status_code == 200:
                battlelog = response.json()
                
                if not battlelog:
                    print(f"Nenhuma batalha encontrada para {tag}")
                    continue

                for battle in battlelog:
                    if get_battle_count(tag) >= MAX_BATTLES_PER_PLAYER:
                        print(f"Limite de {MAX_BATTLES_PER_PLAYER} batalhas atingido para {tag}")
                        break

                    player = battle.get("team", [{}])[0]
                    player_info = {
                        "name": player.get("name"),
                        "tag": tag,
                        "trophies": player.get("startingTrophies"),
                        "expLevel": player.get("expLevel"),
                        "lastUpdate": datetime.now()
                    }
                    players_collection.update_one({"tag": tag}, {"$set": player_info}, upsert=True)

                    battle_time_str = battle.get("battleTime")
                    battle_time_dt = datetime.strptime(battle_time_str, "%Y%m%dT%H%M%S.%fZ")

                    existing_battle = battles_collection.find_one({
                        "utcTime": battle_time_dt,
                        "team.name": player_info["name"]
                    })
                    
                    if existing_battle:
                        print(f"Batalha já existe: {battle_time_dt}")
                        continue

                    team = battle.get("team", [{}])
                    opponent = battle.get("opponent", [{}])

                    team_starting_trophies = team[0].get("startingTrophies")
                    if team_starting_trophies is None:
                        team_starting_trophies = player.get("startingTrophies", 0)

                    opponent_starting_trophies = opponent[0].get("startingTrophies", 0)

                    if team:
                        team[0]["startingTrophies"] = team_starting_trophies
                        team[0]["crowns"] = team[0].get("crowns", 0)

                    if opponent:
                        opponent[0]["startingTrophies"] = opponent_starting_trophies
                        opponent[0]["crowns"] = opponent[0].get("crowns", 0)

                        battle_data = {
                            "utcTime": battle_time_dt,
                            "type": battle.get("type"),
                            "team": team,
                            "opponent": opponent,
                            "is_winner": team[0].get("crowns", 0) > opponent[0].get("crowns", 0),
                            "importedAt": datetime.now()
                        }

                        battles_collection.insert_one(battle_data)
                    
                    time.sleep(REQUEST_DELAY)

                print(f"Batalhas de {tag} importadas com sucesso.")
            else:
                print(f"Erro ao buscar batalhas para {tag}: {response.status_code}")
                print(response.text)

        except requests.exceptions.RequestException as e:
            print(f"Erro na requisição para {tag}: {str(e)}")
        except Exception as e:
            print(f"Erro inesperado para {tag}: {str(e)}")

if __name__ == "__main__":
    import_battles()