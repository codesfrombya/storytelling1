def create_player():
    return {
        "nome": None,
        "idade": 25,
        "historico": (
            "Ex-viciada em drogas e álcool, marcada por problemas familiares e pela falta de "
            "perspectiva, até aceitar uma misteriosa 'oportunidade de mudar de vida'."
        ),
        "sanidade": 5,
        "mortes": 0,
        "memorias": [],
        "pistas": [],
        "itens": [],
        "verdade_revelada": False,
    }


def add_item(player, item):
    if item not in player["itens"]:
        player["itens"].append(item)
        print(f"\n[Item adquirido] {item}")


def add_memory(player, memory):
    if memory not in player["memorias"]:
        player["memorias"].append(memory)
        print(f"\n[Memória recuperada] {memory}")


def add_clue(player, clue):
    if clue not in player["pistas"]:
        player["pistas"].append(clue)
        print(f"\n[Pista adquirida] {clue}")



def get_player_name(player):
    return player["nome"] if player.get("nome") else "Você"
