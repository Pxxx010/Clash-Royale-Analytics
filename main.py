from pymongo import MongoClient
from datetime import datetime
from config import MONGO_URI, DB_NAME
import sys
import os

def limpar_console():
    os.system('cls' if os.name == 'nt' else 'clear')

# Conexão com o MongoDB
client = MongoClient(MONGO_URI)
db = client[DB_NAME]
battles = db["battles"]

def menu():
    print("\n=== MENU DE ANÁLISES - CLASH ROYALE ===")
    print("1. Análise de Vitórias/Derrotas com uma Carta Específica")
    print("2. Análise de Decks com Alta Taxa de Vitória")
    print("3. Análise de Derrotas com Combos de Cartas")
    print("4. Análise de Vitórias com Carta Específica")
    print("5. Análise de Combos de Cartas com Alta Taxa de Vitória")
    print("6. Análise de Clãs Enfrentados")
    print("7. Análise de Performance por Horário")
    print("8. Análise de Evolução de Troféus")
    print("0. Sair")
    return input("\nEscolha uma opção (0-8): ")

def executar_analise(opcao):
    # Definir período padrão para todas as análises
    inicio = datetime(2025, 3, 1)
    fim = datetime(2025, 4, 30)
    
    if opcao == "1":
        # Consulta 1 - % de Vitórias/Derrotas com uma Carta Específica
        print("exemplo: Arrows")
        carta = input("Digite o nome da carta:")
        pipeline1 = [
            {
                "$match": {
                    "utcTime": {"$gte": inicio, "$lte": fim},
                    "$or": [
                        {"team.cards.name": carta},
                        {"opponent.cards.name": carta}
                    ]
                }
            },
            {
                "$group": {
                    "_id": "$is_winner",
                    "total": {"$sum": 1}
                }
            }
        ]
        result1 = list(battles.aggregate(pipeline1))
        vitorias = sum(doc["total"] for doc in result1 if doc["_id"] == True)
        derrotas = sum(doc["total"] for doc in result1 if doc["_id"] == False)
        total = vitorias + derrotas
        
        print(f"\nCarta: {carta}")
        print(f"Período: {inicio.date()} até {fim.date()}")
        if total == 0:
            print("Nenhuma batalha encontrada com essa carta no intervalo fornecido.")
        else:
            print(f"Total de batalhas: {total}")
            print(f"Vitórias: {vitorias} ({(vitorias/total)*100:.2f}%)")
            print(f"Derrotas: {derrotas} ({(derrotas/total)*100:.2f}%)")
    
    elif opcao == "2":
        # Consulta 2 - Decks com mais de X% de vitórias
        min_porcentagem = float(input("Digite a porcentagem mínima de vitórias (ex: 60): "))
        pipeline2 = [
            {
                "$match": {
                    "utcTime": {"$gte": inicio, "$lte": fim}
                }
            },
            {
                "$project": {
                    "deck": {
                        "$sortArray": {
                            "input": {
                                "$map": {
                                    "input": {
                                        "$ifNull": [
                                            { "$getField": {
                                                "field": "cards",
                                                "input": { "$arrayElemAt": ["$team", 0] }
                                            }},
                                            []
                                        ]
                                    },
                                    "as": "card",
                                    "in": "$$card.name"
                                }
                            },
                            "sortBy": 1
                        }
                    },
                    "is_winner": 1
                }
            },
            {
                "$group": {
                    "_id": "$deck",
                    "total": {"$sum": 1},
                    "vitorias": {
                        "$sum": {
                            "$cond": [{"$eq": ["$is_winner", True]}, 1, 0]
                        }
                    }
                }
            },
            {
                "$project": {
                    "_id": 0,
                    "deck": "$_id",
                    "total": 1,
                    "vitorias": 1,
                    "porcentagem": {
                        "$multiply": [
                            {"$divide": ["$vitorias", "$total"]},
                            100
                        ]
                    }
                }
            },
            {
                "$match": {
                    "porcentagem": {"$gt": min_porcentagem}
                }
            },
            {
                "$sort": {"porcentagem": -1}
            }
        ]
        result2 = list(battles.aggregate(pipeline2))
        print(f"\nDecks com mais de {min_porcentagem}% de vitórias entre {inicio.date()} e {fim.date()}")
        for deck in result2:
            print(f"\nDeck: {deck['deck']}")
            print(f"Vitórias: {deck['vitorias']} / {deck['total']} ({deck['porcentagem']:.2f}%)")
    
    elif opcao == "3":
        # Consulta 3 - Derrotas com combo de cartas
        print("exemplo: Arrows, Bowler")
        combo = input("Digite as cartas do combo separadas por vírgula: ").split(",")
        combo = [carta.strip() for carta in combo]
        pipeline3 = [
            {
                "$match": {
                    "utcTime": {"$gte": inicio, "$lte": fim},
                    "is_winner": False
                }
            },
            {
                "$project": {
                    "cartas": {
                        "$map": {
                            "input": {
                                "$ifNull": [
                                    { "$getField": {
                                        "field": "cards",
                                        "input": { "$arrayElemAt": ["$team", 0] }
                                    }},
                                    []
                                ]
                            },
                            "as": "card",
                            "in": "$$card.name"
                        }
                    }
                }
            },
            {
                "$match": {
                    "cartas": {
                        "$all": combo
                    }
                }
            },
            {
                "$count": "total_derrotas"
            }
        ]
        result3 = list(battles.aggregate(pipeline3))
        print(f"\nCombo: {combo}")
        print(f"Período: {inicio.date()} até {fim.date()}")
        if result3:
            print(f"Total de derrotas com esse combo: {result3[0]['total_derrotas']}")
        else:
            print("Nenhuma derrota encontrada com esse combo no intervalo.")
    
    elif opcao == "4":
        # Consulta 4 - Vitórias com carta específica e menos troféus
        carta = input("Digite o nome da carta: ")
        pipeline4 = [
            {
                "$match": {
                    "utcTime": {"$gte": inicio, "$lte": fim},
                    "is_winner": True
                }
            },
            {
                "$project": {
                    "teamTrophies": { "$arrayElemAt": ["$team.startingTrophies", 0] },
                    "opponentTrophies": { "$arrayElemAt": ["$opponent.startingTrophies", 0] },
                    "opponentCrowns": { "$arrayElemAt": ["$opponent.crowns", 0] },
                    "tem_carta": {
                        "$in": [carta, {
                            "$map": {
                                "input": {
                                    "$ifNull": [{ "$arrayElemAt": ["$team.cards", 0] }, []]
                                },
                                "as": "card",
                                "in": "$$card.name"
                            }
                        }]
                    }
                }
            },
            {
                "$match": {
                    "$expr": {
                        "$and": [
                            { "$lt": ["$teamTrophies", "$opponentTrophies"] },
                            { "$gte": ["$opponentCrowns", 0] },
                            { "$eq": ["$tem_carta", True] }
                        ]
                    }
                }
            },
            {
                "$count": "total"
            }
        ]
        result4 = list(battles.aggregate(pipeline4))
        print(f"\nCarta: {carta}")
        print(f"Período: {inicio.date()} até {fim.date()}")
        if result4:
            print(f"Total de vitórias com esses critérios: {result4[0]['total']}")
        else:
            print("Nenhuma vitória encontrada com esses critérios.")
    
    elif opcao == "5":
        # Consulta 5 - Combos de N cartas com alta taxa de vitória
        combo_size = int(input("Digite o tamanho do combo (ex: 3): "))
        min_porcentagem = float(input("Digite a porcentagem mínima de vitórias (ex: 50): "))
        
        from itertools import combinations
        from collections import defaultdict
        
        matches = list(battles.find({
            "utcTime": {"$gte": inicio, "$lte": fim}
        }))
        
        combo_stats = defaultdict(lambda: {"total": 0, "vitorias": 0})
        
        for match in matches:
            team = match.get("team", [])
            if not team or "cards" not in team[0]:
                continue
            
            cards = sorted(card["name"] for card in team[0]["cards"])
            if len(cards) != 8:
                continue
            
            is_winner = match.get("is_winner", False)
            
            for combo in combinations(cards, combo_size):
                combo_stats[combo]["total"] += 1
                if is_winner:
                    combo_stats[combo]["vitorias"] += 1
        
        result5 = []
        for combo, stats in combo_stats.items():
            total = stats["total"]
            vitorias = stats["vitorias"]
            porcentagem = (vitorias / total) * 100
            if porcentagem > min_porcentagem:
                result5.append({
                    "combo": combo,
                    "vitorias": vitorias,
                    "total": total,
                    "porcentagem": porcentagem
                })
        
        result5.sort(key=lambda x: x["porcentagem"], reverse=True)
        
        print(f"\nCombos de {combo_size} cartas com mais de {min_porcentagem}% de vitórias entre {inicio.date()} e {fim.date()}")
        for combo in result5:
            print(f"\nCombo: {combo['combo']}")
            print(f"Vitórias: {combo['vitorias']} / {combo['total']} ({combo['porcentagem']:.2f}%)")
    
    elif opcao == "6":
        # Análise de Clãs Enfrentados
        pipeline_clans = [
            {
                "$match": {
                    "utcTime": {"$gte": inicio, "$lte": fim}
                }
            },
            {
                "$project": {
                    "clan_opponent": { "$arrayElemAt": ["$opponent.clan", 0] },
                    "is_winner": 1,
                    "opponentTrophies": { "$arrayElemAt": ["$opponent.startingTrophies", 0] }
                }
            },
            {
                "$group": {
                    "_id": "$clan_opponent",
                    "total_battles": { "$sum": 1 },
                    "vitorias": { "$sum": { "$cond": ["$is_winner", 1, 0] } },
                    "avg_opponent_trophies": { "$avg": "$opponentTrophies" }
                }
            },
            {
                "$project": {
                    "clan": "$_id",
                    "total_battles": 1,
                    "vitorias": 1,
                    "taxa_vitoria": {
                        "$multiply": [
                            { "$divide": ["$vitorias", "$total_battles"] },
                            100
                        ]
                    },
                    "avg_opponent_trophies": 1
                }
            },
            { "$sort": { "total_battles": -1 } }
        ]
        
        result_clans = list(battles.aggregate(pipeline_clans))
        
        print(f"\nAnálise de Clãs Enfrentados entre {inicio.date()} e {fim.date()}")
        print(f"Total de clãs diferentes enfrentados: {len(result_clans)}")
        print("\nDetalhes por clã:")
        for clan in result_clans:
            print(f"\nClã: {clan['clan']}")
            print(f"Total de batalhas: {clan['total_battles']}")
            print(f"Vitórias: {clan['vitorias']} ({clan['taxa_vitoria']:.2f}%)")
            print(f"Média de troféus dos oponentes: {clan['avg_opponent_trophies']:.0f}")
    
    elif opcao == "7":
        # Análise de Performance por Horário
        pipeline_horario = [
            {
                "$match": {
                    "utcTime": {"$gte": inicio, "$lte": fim}
                }
            },
            {
                "$project": {
                    "hora": { "$hour": "$utcTime" },
                    "is_winner": 1,
                    "teamTrophies": { "$arrayElemAt": ["$team.startingTrophies", 0] },
                    "opponentTrophies": { "$arrayElemAt": ["$opponent.startingTrophies", 0] },
                    "teamCrowns": { "$arrayElemAt": ["$team.crowns", 0] },
                    "opponentCrowns": { "$arrayElemAt": ["$opponent.crowns", 0] }
                }
            },
            {
                "$group": {
                    "_id": "$hora",
                    "total_battles": { "$sum": 1 },
                    "vitorias": { "$sum": { "$cond": ["$is_winner", 1, 0] } },
                    "avg_team_trophies": { "$avg": "$teamTrophies" },
                    "avg_opponent_trophies": { "$avg": "$opponentTrophies" },
                    "total_crowns": { "$sum": "$teamCrowns" },
                    "total_crowns_opponent": { "$sum": "$opponentCrowns" }
                }
            },
            {
                "$project": {
                    "hora": "$_id",
                    "total_battles": 1,
                    "vitorias": 1,
                    "taxa_vitoria": {
                        "$multiply": [
                            { "$divide": ["$vitorias", "$total_battles"] },
                            100
                        ]
                    },
                    "avg_team_trophies": 1,
                    "avg_opponent_trophies": 1,
                    "total_crowns": 1,
                    "total_crowns_opponent": 1,
                    "diferenca_trofeus": {
                        "$subtract": ["$avg_team_trophies", "$avg_opponent_trophies"]
                    },
                    "diferenca_crowns": {
                        "$subtract": ["$total_crowns", "$total_crowns_opponent"]
                    }
                }
            },
            { "$sort": { "hora": 1 } }
        ]
        
        result_horario = list(battles.aggregate(pipeline_horario))
        
        print(f"\nAnálise de Performance por Horário entre {inicio.date()} e {fim.date()}")
        print("\nDetalhes por horário:")
        for hora in result_horario:
            print(f"\nHora: {hora['hora']}:00")
            print(f"Total de batalhas: {hora['total_battles']}")
            print(f"Vitórias: {hora['vitorias']} ({hora['taxa_vitoria']:.2f}%)")
            print(f"Média de troféus (time): {hora['avg_team_trophies']:.0f}")
            print(f"Média de troféus (oponente): {hora['avg_opponent_trophies']:.0f}")
            print(f"Diferença média de troféus: {hora['diferenca_trofeus']:.0f}")
            print(f"Coroas (time): {hora['total_crowns']}")
            print(f"Coroas (oponente): {hora['total_crowns_opponent']}")
            print(f"Diferença de coroas: {hora['diferenca_crowns']}")
        
        melhor_horario = max(result_horario, key=lambda x: x['taxa_vitoria'])
        pior_horario = min(result_horario, key=lambda x: x['taxa_vitoria'])
        
        print("\nResumo:")
        print(f"Melhor horário: {melhor_horario['hora']}:00 ({melhor_horario['taxa_vitoria']:.2f}% de vitórias)")
        print(f"Pior horário: {pior_horario['hora']}:00 ({pior_horario['taxa_vitoria']:.2f}% de vitórias)")
    
    elif opcao == "8":
        # Análise de Evolução de Troféus
        pipeline_evolucao = [
            {
                "$match": {
                    "utcTime": {"$gte": inicio, "$lte": fim}
                }
            },
            {
                "$project": {
                    "data": { "$dateToString": { "format": "%Y-%m-%d", "date": "$utcTime" } },
                    "is_winner": 1,
                    "teamTrophies": { "$arrayElemAt": ["$team.startingTrophies", 0] },
                    "opponentTrophies": { "$arrayElemAt": ["$opponent.startingTrophies", 0] },
                    "teamCrowns": { "$arrayElemAt": ["$team.crowns", 0] },
                    "opponentCrowns": { "$arrayElemAt": ["$opponent.crowns", 0] }
                }
            },
            {
                "$group": {
                    "_id": "$data",
                    "total_battles": { "$sum": 1 },
                    "vitorias": { "$sum": { "$cond": ["$is_winner", 1, 0] } },
                    "min_trofeus": { "$min": "$teamTrophies" },
                    "max_trofeus": { "$max": "$teamTrophies" },
                    "avg_trofeus": { "$avg": "$teamTrophies" },
                    "total_crowns": { "$sum": "$teamCrowns" },
                    "total_crowns_opponent": { "$sum": "$opponentCrowns" }
                }
            },
            {
                "$project": {
                    "data": "$_id",
                    "total_battles": 1,
                    "vitorias": 1,
                    "taxa_vitoria": {
                        "$multiply": [
                            { "$divide": ["$vitorias", "$total_battles"] },
                            100
                        ]
                    },
                    "min_trofeus": 1,
                    "max_trofeus": 1,
                    "avg_trofeus": 1,
                    "total_crowns": 1,
                    "total_crowns_opponent": 1,
                    "diferenca_crowns": {
                        "$subtract": ["$total_crowns", "$total_crowns_opponent"]
                    },
                    "variacao_trofeus": {
                        "$subtract": ["$max_trofeus", "$min_trofeus"]
                    }
                }
            },
            { "$sort": { "data": 1 } }
        ]
        
        result_evolucao = list(battles.aggregate(pipeline_evolucao))
        
        print(f"\nAnálise de Evolução de Troféus entre {inicio.date()} e {fim.date()}")
        print("\nDetalhes por dia:")
        for dia in result_evolucao:
            print(f"\nData: {dia['data']}")
            print(f"Total de batalhas: {dia['total_battles']}")
            print(f"Vitórias: {dia['vitorias']} ({dia['taxa_vitoria']:.2f}%)")
            print(f"Troféus (mín): {dia['min_trofeus']:.0f}")
            print(f"Troféus (máx): {dia['max_trofeus']:.0f}")
            print(f"Troféus (média): {dia['avg_trofeus']:.0f}")
            print(f"Variação de troféus: {dia['variacao_trofeus']:.0f}")
            print(f"Coroas (time): {dia['total_crowns']}")
            print(f"Coroas (oponente): {dia['total_crowns_opponent']}")
            print(f"Diferença de coroas: {dia['diferenca_crowns']}")
        
        if result_evolucao:
            total_battles = sum(dia['total_battles'] for dia in result_evolucao)
            total_vitorias = sum(dia['vitorias'] for dia in result_evolucao)
            taxa_vitoria_geral = (total_vitorias / total_battles) * 100
            variacao_total = result_evolucao[-1]['max_trofeus'] - result_evolucao[0]['min_trofeus']
            
            print("\nResumo Geral:")
            print(f"Total de batalhas no período: {total_battles}")
            print(f"Taxa de vitória geral: {taxa_vitoria_geral:.2f}%")
            print(f"Variação total de troféus: {variacao_total:.0f}")
            print(f"Trofeus inicial: {result_evolucao[0]['min_trofeus']:.0f}")
            print(f"Trofeus final: {result_evolucao[-1]['max_trofeus']:.0f}")

def main():
    while True:
        limpar_console()
        opcao = menu()
        if opcao == "0":
            print("\nObrigado por usar o sistema de análise do Clash Royale!")
            break
        elif opcao in ["1", "2", "3", "4", "5", "6", "7", "8"]:
            executar_analise(opcao)
            input("\nPressione Enter para continuar...")
            limpar_console()
        else:
            print("\nOpção inválida! Por favor, escolha uma opção entre 0 e 8.")
            input("\nPressione Enter para continuar...")
            limpar_console()

if __name__ == "__main__":
    main()