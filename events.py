import os
import time
import threading
from arts import *

try:
    import msvcrt
except ImportError:
    msvcrt = None

from menu import title, narrate, pause
from player import add_item, add_memory, add_clue, get_player_name
from loop import register_death


class DeathInLoop(Exception):
    pass


class GameFinished(Exception):
    def __init__(self, ending_name):
        super().__init__(ending_name)
        self.ending_name = ending_name


def show_status(player, loop_state):
    print(f"\nLoop atual: {loop_state['loop']}")
    print(f"Sanidade: {player['sanidade']}")
    print(f"Mortes: {player['mortes']}")
    print(f"Itens: {', '.join(player['itens']) if player['itens'] else 'Nenhum'}")
    print(f"Pistas descobertas: {len(player['pistas'])}")
    print(f"Memórias recuperadas: {len(player['memorias'])}")


def choose(valid_options):
    while True:
        choice = input("\nEscolha: ").strip()
        if choice in valid_options:
            return choice
        print("Opção inválida.")


def timed_input_windows(valid_options, timeout=15):
    start_time = time.time()
    last_second = None

    while True:
        elapsed = time.time() - start_time
        remaining = max(0, timeout - int(elapsed))

        if remaining != last_second:
            print(
                f"\rTempo para se esconder: {remaining:2d} segundos | Escolha: ",
                end="",
                flush=True,
            )
            last_second = remaining

        if elapsed >= timeout:
            print("\rTempo esgotado!                                         ")
            return None

        if msvcrt and msvcrt.kbhit():
            key = msvcrt.getwch()
            if key in valid_options:
                print(key)
                return key

        time.sleep(0.05)


def timed_input_fallback(prompt, timeout=15):
    result = [None]

    def read_input():
        try:
            result[0] = input(prompt).strip()
        except Exception:
            result[0] = None

    thread = threading.Thread(target=read_input, daemon=True)
    thread.start()

    for remaining in range(timeout, 0, -1):
        if result[0] is not None:
            print()
            return result[0]
        print(f"\rTempo para se esconder: {remaining:2d} segundos ", end="", flush=True)
        time.sleep(1)

    print("\rTempo esgotado!                           ")
    return None


def timed_choice(valid_options, timeout=15):
    if os.name == "nt" and msvcrt is not None:
        return timed_input_windows(valid_options, timeout)

    choice = timed_input_fallback("\nEscolha rapidamente: ", timeout)
    if choice in valid_options:
        return choice
    return choice


def die(player, loop_state, reason, clue_after_death=None):
    title("VOCÊ MORREU")
    art_morte()
    narrate(reason)

    if clue_after_death:
        add_clue(player, clue_after_death)

    print(f"\nTotal de mortes até agora: {player['mortes'] + 1}")
    narrate("\nTudo escurece.")
    time.sleep(0.8)
    narrate("Você ouve passos.")
    time.sleep(0.8)
    narrate("Uma voz sussurra: 'de novo...'")
    pause()

    register_death(player, loop_state)
    raise DeathInLoop()


def creature_hide_event(player, loop_state, intro_lines=None):
    title("A CRIATURA SE APROXIMA")
    art_entidade()
    if intro_lines:
        for line in intro_lines:
            narrate(line)
    narrate("Você ouve passos rápidos entre as árvores.")
    narrate("Algo corre na sua direção.")
    narrate("A criatura está perto.")
    narrate("\nVocê tem 15 segundos para se esconder.\n")

    print("1. Atrás de uma árvore grossa")
    print("2. Dentro da cabana abandonada")
    print("3. No mato alto")
    print("4. Ficar parada e prender a respiração")

    choice = timed_choice(["1", "2", "3", "4"], 15)

    if choice is None:
        die(
            player,
            loop_state,
            "Você hesita por tempo demais. A criatura te encontra antes que consiga reagir.",
            "hesitar_diante_da_criatura_e_morte",
        )

    if choice == "1":
        narrate("\nVocê se esconde atrás da árvore e tenta não respirar alto.")
        narrate("Os passos passam por você... por enquanto.")
        pause()
        return True

    if choice == "2":
        die(
            player,
            loop_state,
            "A porta da cabana range alto demais. A criatura ouve o som e te alcança.",
            "a_cabana_nao_e_bom_esconderijo_em_panico",
        )

    if choice == "3":
        if loop_state["loop"] >= 2:
            narrate("\nVocê se joga no mato alto.")
            narrate("Desta vez, lembrando do padrão da criatura, consegue sobreviver.")
            pause()
            return True
        die(
            player,
            loop_state,
            "Você tenta se esconder no mato, mas a criatura parece já saber onde procurar.",
            "o_mato_so_funciona_depois_de_aprender_o_padrao",
        )

    if choice == "4":
        if "a_entidade_e_voce" in player["pistas"]:
            narrate("\nVocê fica imóvel.")
            narrate("A criatura para diante de você... e recua.")
            narrate("Como se tivesse reconhecido algo.")
            pause()
            return True
        die(
            player,
            loop_state,
            "Ficar parada parecia uma boa ideia. Não era.",
            "ficar_parada_sem_entender_a_entidade_falha",
        )

    die(
        player,
        loop_state,
        "Na pressa, você escolhe mal e perde segundos preciosos.",
        "o_panico_tambem_mata",
    )


def surprise_creature_event(player, loop_state, event_id, intro_lines, on_survive=None):
    if event_id in player["pistas"]:
        if on_survive:
            on_survive()
        return

    add_clue(player, event_id)
    survived = creature_hide_event(player, loop_state, intro_lines=intro_lines)
    if survived and on_survive:
        on_survive()


def has_secret_route(player):
    required_clues = {
        "fenda_aberta",
        "a_entidade_e_voce",
        "governo_e_cientistas",
        "morrer_revela",
    }
    return required_clues.issubset(set(player["pistas"])) and len(player["memorias"]) >= 3


def reveal_name_if_needed(player):
    if player.get("nome"):
        return False

    title("MEMÓRIA RECUPERADA")
    narrate("Você vira a fotografia com as mãos trêmulas.")
    narrate("No verso, escrito com tinta quase apagada, há uma identificação.")
    narrate("'Lívia Moreira - participante 08-17-LA'")
    narrate("Algo dentro de você se encaixa.")
    narrate("Como uma peça esquecida voltando ao lugar.")
    narrate("Lívia Moreira. Esse é o seu nome.")

    player["nome"] = "Lívia Moreira"
    add_memory(player, "Seu nome é Lívia Moreira.")
    pause()
    return True


def start_loop_scene(player, loop_state):
    title(f"PARADOX - LOOP {loop_state['loop']}")
    art_floresta()
    narrate(f"{get_player_name(player)} desperta no mesmo chão frio de sempre.")
    narrate("Há árvores tortas, lama e uma sensação insuportável de déjà vu.")

    if loop_state["loop"] > 1:
        narrate("\nVocê sente que já esteve aqui antes.")
        if "nota_inicial" in player["pistas"]:
            narrate("Uma frase ecoa na sua mente: 'NÃO CONFIE NO QUE CORRE ATRÁS DE VOCÊ.'")

    show_status(player, loop_state)

    print("\n1. Examinar seu corpo")
    print("2. Gritar por ajuda")
    print("3. Seguir pela trilha da esquerda")
    print("4. Seguir pela trilha da direita")
    if loop_state["loop"] >= 2:
        print("5. Seguir o zumbido metálico ao longe")

    valid_choices = ["1", "2", "3", "4"]
    if loop_state["loop"] >= 2:
        valid_choices.append("5")

    choice = choose(valid_choices)

    if choice == "1":
        examine_body_scene(player, loop_state)
    elif choice == "2":
        scream_scene(player, loop_state)
    elif choice == "3":
        lake_scene(player, loop_state)
    elif choice == "4":
        cemetery_scene(player, loop_state)
    else:
        direct_lab_hint_scene(player, loop_state)


def direct_lab_hint_scene(player, loop_state):
    title("ZUMBIDO METÁLICO")
    narrate("Você segue um ruído baixo, quase industrial, vindo de trás das árvores.")
    narrate("Não parece natural. Parece escondido.")
    add_clue(player, "zumbido_do_laboratorio")
    surprise_creature_event(
        player,
        loop_state,
        "surpresa_zumbido",
        [
            "O som para de repente.",
            "No silêncio que sobra, alguma coisa dispara na sua direção.",
        ],
        on_survive=lambda: cabin_scene(player, loop_state),
    )


def examine_body_scene(player, loop_state):
    title("EXAMINAR O CORPO")
    narrate("Você toca a parte de trás da cabeça e sente um inchaço forte.")
    narrate("No bolso do casaco há um papel amassado.")

    if "nota_inicial" not in player["pistas"]:
        narrate("\nO papel diz: 'Se você acordou, ainda não terminou. Não beba a água.'")
        add_clue(player, "nota_inicial")
    else:
        narrate("\nDesta vez, o papel está em branco. Como se a mensagem já tivesse sido entregue.")

    print("\n1. Ir para a trilha da esquerda")
    print("2. Ir para a trilha da direita")
    print("3. Examinar o sangue seco na roupa")

    choice = choose(["1", "2", "3"])
    if choice == "1":
        lake_scene(player, loop_state)
    elif choice == "2":
        cemetery_scene(player, loop_state)
    else:
        narrate("Você encontra respingos escuros na manga do casaco.")
        narrate("Não parecem recentes. Parecem repetidos.")
        add_memory(player, "Em outros loops, você também acordou ferida do mesmo jeito.")
        surprise_creature_event(
            player,
            loop_state,
            "surpresa_corpo",
            [
                "Ao perceber isso, seu peito aperta.",
                "Um galho quebra logo atrás de você.",
            ],
        )


def scream_scene(player, loop_state):
    title("GRITO NA FLORESTA")
    narrate("Você grita.")
    narrate("O som some rápido demais, como se a floresta engolisse sua voz.")
    narrate("Então, algo responde.")
    narrate("\nUm vulto se move entre as árvores. Rápido. Familiar. Errado.")

    survived = creature_hide_event(player, loop_state)
    if survived:
        narrate("\nDepois de escapar por pouco, você corre sem olhar para trás.")
        pause()
        cabin_scene(player, loop_state)


def lake_scene(player, loop_state):
    while True:
        title("LAGO ESCURO")
        art_lago()
        narrate("Você chega a um lago imóvel, liso como vidro.")
        narrate("Perto da margem há uma mochila rasgada.")

        print("\n1. Abrir a mochila")
        print("2. Olhar seu reflexo")
        print("3. Beber a água")
        print("4. Examinar as pegadas na margem")
        print("5. Voltar")

        choice = choose(["1", "2", "3", "4", "5"])

        if choice == "1":
            if "cracha_quebrado" not in player["itens"]:
                narrate("Dentro da mochila há um crachá quebrado com parte de um nome:")
                narrate("'...ívia M.' e as letras 'N.T.E. - Núcleo Temporal Experimental'")
                add_item(player, "cracha_quebrado")
                add_clue(player, "laboratorio_temporal")
            else:
                narrate("A mochila já está vazia.")

            surprise_creature_event(
                player,
                loop_state,
                "surpresa_lago_mochila",
                [
                    "Quando você fecha a mochila, o silêncio do lago muda.",
                    "Um estalo seco ecoa atrás de você.",
                    "A sensação de estar sendo observada volta de uma vez.",
                ],
            )
            pause()

        elif choice == "2":
            narrate("Seu reflexo demora meio segundo para imitar você.")
            player["sanidade"] -= 1
            add_clue(player, "reflexo_atrasado")

            if player["sanidade"] <= 0:
                die(player, loop_state, "Seu reflexo sorri, mas você não. Sua mente se parte ali mesmo.")
            pause()

        elif choice == "3":
            die(
                player,
                loop_state,
                "A água desce queimando pela sua garganta. Seu corpo trava em segundos.",
                "nao_beber_agua",
            )
        elif choice == "4":
            narrate("Há marcas de pés descalços e arrastados perto da água.")
            narrate("As pegadas começam na margem... e terminam no nada.")
            add_clue(player, "pegadas_interrompidas")
            surprise_creature_event(
                player,
                loop_state,
                "surpresa_lago_pegadas",
                [
                    "Você se abaixa para olhar melhor.",
                    "No reflexo da água, algo se move antes de você ouvir os passos.",
                ],
            )
            pause()
        else:
            return start_loop_scene(player, loop_state)


def cemetery_scene(player, loop_state):
    while True:
        title("CEMITÉRIO")
        art_cemiterio()
        narrate("Você encontra lápides sem nomes. Só números.")
        narrate("Algumas parecem recentes. Outras, quebradas.")

        print("\n1. Investigar as lápides")
        print("2. Cavar perto de uma cruz caída")
        print("3. Fugir ao ouvir passos")
        print("4. Ler os números com atenção")
        print("5. Tocar a lápide mais recente")

        choice = choose(["1", "2", "3", "4", "5"])

        if choice == "1":
            narrate("Atrás de uma lápide há uma placa metálica enterrada.")
            narrate("Nela está escrito: 'Pacientes Reabilitáveis - Série 08'")
            add_clue(player, "voce_era_cobaia")
            surprise_creature_event(
                player,
                loop_state,
                "surpresa_cemiterio_lapides",
                [
                    "O vento para de repente.",
                    "As árvores ao redor parecem se inclinar na sua direção.",
                    "Logo depois, alguma coisa corre entre as lápides.",
                ],
            )
            pause()

        elif choice == "2":
            if "chave_enferrujada" not in player["itens"]:
                narrate("Você encontra uma pequena chave enferrujada envolta em pano.")
                add_item(player, "chave_enferrujada")
            else:
                narrate("Você já pegou o que havia ali.")
            pause()

        elif choice == "3":
            chase_scene(player, loop_state)
            return

        elif choice == "4":
            narrate("Um dos números chama sua atenção: 08-17-LA.")
            narrate("Esse código faz sua cabeça doer.")
            add_memory(player, "Você assinou algum documento com esse código.")
            surprise_creature_event(
                player,
                loop_state,
                "surpresa_cemiterio_codigo",
                [
                    "Sua visão falha por um instante.",
                    "Quando você ergue a cabeça, sente passos se aproximando em alta velocidade.",
                ],
            )
            pause()
        else:
            narrate("A pedra está gelada demais.")
            narrate("Sob seus dedos, alguém riscou uma única palavra: LÍVIA.")
            narrate("O nome ecoa dentro da sua cabeça, familiar e distante ao mesmo tempo.")
            add_memory(player, "Em algum loop, alguém marcou o nome Lívia em uma lápide.")
            surprise_creature_event(
                player,
                loop_state,
                "surpresa_cemiterio_nome",
                [
                    "No mesmo instante, algo atravessa o cemitério correndo.",
                    "Desta vez, parece saber exatamente onde você está.",
                ],
            )
            pause()


def chase_scene(player, loop_state):
    title("PERSEGUIÇÃO")
    narrate("Passos atrás de você.")
    narrate("Respiração falha.")
    narrate("Galhos quebrando.")
    narrate("A entidade está perto.")

    survived = creature_hide_event(player, loop_state)
    if survived:
        narrate("\nVocê aproveita a distração da criatura e corre para a cabana.")
        pause()
        cabin_scene(player, loop_state)


def cabin_scene(player, loop_state):
    while True:
        title("CABANA ABANDONADA")
        art_cabana()
        narrate("Uma cabana apodrecida surge entre as árvores.")
        narrate("Na madeira da parede, alguém riscou palavras com as unhas.")

        print("\n1. Forçar a porta")
        if "chave_enferrujada" in player["itens"]:
            print("2. Usar a chave enferrujada")
        print("3. Entrar pela janela")
        print("4. Observar a parede antes de entrar")
        print("5. Chamar por alguém dentro da cabana")

        valid = ["1", "3", "4", "5"]
        if "chave_enferrujada" in player["itens"]:
            valid.append("2")

        choice = choose(valid)

        if choice == "1":
            die(
                player,
                loop_state,
                "Você faz barulho demais. A entidade te alcança antes que a porta ceda.",
                "a_porta_nao_deve_ser_forcada",
            )

        elif choice == "2":
            narrate("A chave gira com dificuldade. A porta se abre.")
            pause()
            inside_cabin_scene(player, loop_state)
            return

        elif choice == "3":
            narrate("Você corta o braço ao entrar, mas consegue passar.")
            player["sanidade"] -= 1

            if player["sanidade"] <= 0:
                die(player, loop_state, "A dor e o medo esmagam o resto da sua lucidez.")
            pause()
            inside_cabin_scene(player, loop_state)
            return

        elif choice == "4":
            narrate("Na parede está escrito:")
            narrate("'NÃO CORRA DELA. ELA É VOCÊ.'")
            add_clue(player, "mensagem_da_parede")
            surprise_creature_event(
                player,
                loop_state,
                "surpresa_cabana_parede",
                [
                    "Antes que você consiga se afastar da parede, a madeira estala atrás de você.",
                    "Alguma coisa acabou de chegar à cabana.",
                ],
            )
            pause()
        else:
            narrate("Você chama, mas ninguém responde.")
            narrate("Depois de alguns segundos, uma voz igual à sua sussurra do outro lado da porta:")
            narrate("'Tarde demais.'")
            surprise_creature_event(
                player,
                loop_state,
                "surpresa_cabana_voz",
                [
                    "A resposta vem acompanhada de passos violentos do lado de fora.",
                ],
            )
            pause()


def inside_cabin_scene(player, loop_state):
    while True:
        title("INTERIOR DA CABANA")
        narrate("Há uma mesa velha, um rádio, objetos espalhados e um alçapão no chão.")
        narrate("Sobre a mesa, uma fotografia rasgada.")

        print("\n1. Ler as anotações da parede")
        print("2. Ligar o rádio")
        print("3. Abrir o alçapão")
        print("4. Procurar objetos pessoais")
        print("5. Examinar a fotografia com cuidado")

        choice = choose(["1", "2", "3", "4", "5"])

        if choice == "1":
            narrate("As frases se repetem por toda a madeira:")
            narrate("'MORRER TAMBÉM É APRENDER'")
            narrate("'NÃO CONFIE NA PRIMEIRA MEMÓRIA'")
            narrate("'VOCÊ ACEITOU A OFERTA'")
            add_clue(player, "morrer_revela")
            pause()

        elif choice == "2":
            narrate("O rádio chia e uma gravação toca:")
            narrate("'Paciente 08-17-LA apresentou resistência ao ciclo de reabilitação.'")
            narrate("'Persistência identitária acima do esperado.'")
            add_clue(player, "paciente_08_17_la")
            surprise_creature_event(
                player,
                loop_state,
                "surpresa_radio",
                [
                    "No meio do chiado, um ruído de passos invade a cabana.",
                    "A presença do lado de fora já está perto demais.",
                ],
            )
            pause()

        elif choice == "3":
            laboratory_scene(player, loop_state)
            return

        elif choice == "4":
            narrate("Na fotografia, você aparece sentada na calçada.")
            narrate("Duas pessoas de roupa social estão de pé à sua frente.")
            narrate("No verso, escrito à mão: 'Uma oportunidade de mudar de vida.'")
            add_memory(player, "Você aceitou uma proposta estranha quando estava no fundo do poço.")

            if player.get("nome") is None:
                reveal_name_if_needed(player)
            else:
                pause()
        else:
            narrate("Ao aproximar a fotografia da luz, você percebe outra figura ao fundo.")
            narrate("A silhueta tem o seu corpo... mas está mais velha, torta, quebrada.")
            add_memory(player, "A entidade já aparecia ao fundo antes mesmo do experimento começar.")
            surprise_creature_event(
                player,
                loop_state,
                "surpresa_fotografia",
                [
                    "A janela da cabana vibra.",
                    "Do lado de fora, passos circulam a casa.",
                ],
            )
            pause()


def laboratory_scene(player, loop_state):
    while True:
        title("LABORATÓRIO SUBTERRÂNEO")
        art_laboratorio()
        narrate("O alçapão leva a um corredor frio iluminado por lâmpadas falhas.")
        narrate("Você encontrou o centro do experimento.")

        print("\n1. Acessar o computador")
        print("2. Abrir uma cela trancada")
        print("3. Assistir a uma gravação")
        print("4. Destruir os equipamentos")
        print("5. Vasculhar os armários médicos")

        choice = choose(["1", "2", "3", "4", "5"])

        if choice == "1":
            narrate("Nos arquivos do sistema você lê:")
            narrate("'Projeto Érebo - Reabilitação por Recorrência Temporal.'")
            narrate("'Financiamento autorizado por órgão estatal confidencial.'")
            add_clue(player, "governo_e_cientistas")
            surprise_creature_event(
                player,
                loop_state,
                "surpresa_laboratorio_computador",
                [
                    "A tela pisca duas vezes.",
                    "As luzes do corredor falham e um som de passos ecoa no metal.",
                ],
            )
            pause()

        elif choice == "2":
            die(
                player,
                loop_state,
                "Dentro da cela havia alguém. Ou algo. Quando a porta abre, a criatura salta em você.",
                "nem_toda_porta_deve_ser_aberta",
            )

        elif choice == "3":
            narrate("A gravação mostra você assinando um termo.")
            narrate("Seus olhos estão vazios.")
            narrate("Você diz: 'Não tenho mais nada a perder.'")
            add_memory(player, "Você entrou no experimento por desespero.")
            pause()
            revelation_scene(player, loop_state)
            return

        elif choice == "4":
            if len(player["pistas"]) >= 6:
                narrate("Os equipamentos entram em colapso.")
                narrate("Alarmes soam. Uma fenda se abre no corredor.")
                add_clue(player, "fenda_aberta")
                pause()
                revelation_scene(player, loop_state)
                return

            die(
                player,
                loop_state,
                "Você ativa um protocolo de contenção. Gás invade o laboratório.",
                "destruir_sem_entender_e_erro",
            )
        else:
            narrate("Você encontra seringas quebradas, pulseiras hospitalares e relatórios incompletos.")
            narrate("Em uma delas, seu nome aparece várias vezes, sempre seguido da palavra: reincidência.")
            add_memory(player, "Seu tratamento nunca pretendeu te curar. Pretendia te repetir.")
            surprise_creature_event(
                player,
                loop_state,
                "surpresa_laboratorio_armario",
                [
                    "Uma bandeja metálica cai atrás de você.",
                    "Algo já entrou no corredor.",
                ],
            )
            pause()


def revelation_scene(player, loop_state):
    title("REVELAÇÃO")
    narrate("A entidade aparece diante de você.")
    narrate("Agora dá para ver claramente.")
    narrate("Ela é você.")
    narrate("Ou o que sobrou de você depois de incontáveis loops.")

    print("\n1. Aceitar que a entidade é você")
    print("2. Negar tudo e fugir")
    print("3. Tentar conversar")
    print("4. Atacá-la")
    print("5. Perguntar quem começou o experimento")

    choice = choose(["1", "2", "3", "4", "5"])

    if choice == "1":
        player["verdade_revelada"] = True
        add_clue(player, "a_entidade_e_voce")
        narrate("A entidade abaixa a cabeça. Como se esperasse por isso há anos.")
        pause()
        final_decision_scene(player, loop_state)
        return

    if choice == "2":
        die(
            player,
            loop_state,
            "Você foge pelo corredor, mas corre direto para dentro da própria fenda temporal.",
            "fugir_da_verdade_reinicia",
        )

    if choice == "3":
        narrate("A entidade fala com a sua voz:")
        narrate("'Cada morte solta uma trava. Eu te matei para te empurrar adiante.'")
        narrate("'Mas em alguns loops... eu só enlouqueci.'")
        add_clue(player, "a_morte_quebra_travas")
        add_clue(player, "a_entidade_e_voce")
        player["verdade_revelada"] = True
        pause()
        final_decision_scene(player, loop_state)
        return

    if choice == "4":
        die(
            player,
            loop_state,
            "Você a ataca. Ela não revida. Só segura seu braço e sussurra: 'ainda não.'",
            "violencia_sem_compreensao_falha",
        )

    narrate("'Quem colocou a gente aqui?', você pergunta.")
    narrate("A criatura aponta para o núcleo e para as câmeras quebradas do laboratório.")
    narrate("'Eles começaram', ela sussurra. 'Mas nós mantivemos.'")
    add_clue(player, "culpa_compartilhada")
    add_clue(player, "a_entidade_e_voce")
    player["verdade_revelada"] = True
    pause()
    final_decision_scene(player, loop_state)


def final_decision_scene(player, loop_state):
    title("DECISÃO FINAL")
    narrate("O núcleo temporal pulsa no centro do laboratório.")
    narrate("Você entende que pode encerrar tudo agora.")
    narrate("Mas cada escolha cobra alguma coisa.")

    print("\n1. Libertar as outras cobaias e encerrar o núcleo")
    print("2. Sacrificar sua versão futura e sair sozinha")
    print("3. Levar os arquivos e expor a verdade")
    print("4. Permanecer no loop e aceitar o silêncio")

    valid_choices = ["1", "2", "3", "4"]
    if has_secret_route(player):
        print("5. Entrar na fenda e tocar o coração oculto do experimento")
        valid_choices.append("5")

    choice = choose(valid_choices)

    if choice == "1":
        ending_true_redemption(player)
    elif choice == "2":
        ending_good_fall(player)
    elif choice == "3":
        ending_neutral_truth(player)
    elif choice == "4":
        ending_bad_silence(player)
    else:
        ending_secret_hidden(player)


def ending_true_redemption(player):
    title("FINAL VERDADEIRO (TRUE ENDING) - REDENÇÃO")
    narrate("Você desliga o núcleo, mas não para em si mesma.")
    narrate("Usa o pouco tempo restante para abrir as celas, apagar os protocolos e romper o ciclo de todos.")
    narrate("A entidade segura seu pulso pela última vez. Não para te matar. Para te impedir de desistir.")
    narrate("Quando a estrutura desaba, a floresta começa a desaparecer junto com o experimento.")
    narrate("Ao amanhecer, Lívia Moreira deixa o lugar viva, carregando culpa, memória e uma chance real de recomeço.")
    raise GameFinished("Final Verdadeiro (True Ending) - Redenção")


def ending_good_fall(player):
    title("FINAL BOM (GOOD ENDING) - QUEDA")
    narrate("Você destrói a versão futura de si mesma para quebrar a corrente principal do paradoxo.")
    narrate("O loop entra em colapso e você consegue sair.")
    narrate("Mas sai sozinha.")
    narrate("Lá fora, a verdade é incompleta, e as vozes dos que ficaram ecoam como uma queda que nunca termina.")
    narrate("Você sobrevive. Nem todo mundo consegue o mesmo.")
    raise GameFinished("Final Bom (Good Ending) - Queda")


def ending_bad_silence(player):
    title("FINAL RUIM (BAD ENDING) - SILÊNCIO")
    narrate("Você toca o núcleo e escolhe não lutar mais.")
    narrate("As luzes do laboratório se apagam uma a uma, até restar apenas o som do próprio coração.")
    narrate("Depois, nem isso.")
    narrate("A floresta permanece. O loop continua. E a próxima coisa que desperta no chão frio já não é bem você.")
    raise GameFinished("Final Ruim (Bad Ending) - Silêncio")


def ending_neutral_truth(player):
    title("FINAL NEUTRO (NEUTRAL ENDING) - VERDADE")
    narrate("Você arranca os arquivos do sistema e força uma saída antes do colapso total.")
    narrate("O mundo enfim vê o Projeto Érebo pelo que ele era.")
    narrate("A verdade vem à tona, mas o loop não some por completo.")
    narrate("Parte de você continua presa entre as versões, repetindo fragmentos da floresta em algum lugar fora do tempo.")
    raise GameFinished("Final Neutro (Neutral Ending) - Verdade")


def ending_secret_hidden(player):
    title("FINAL SECRETO (SECRET ENDING) - OCULTO")
    narrate("Você atravessa a fenda sem recuar.")
    narrate("Do outro lado do núcleo, o tempo não corre. Ele observa.")
    narrate("Você percebe que o experimento nunca tentou só corrigir pessoas. Tentou cultivar algo dentro delas.")
    narrate("Ao tocar o coração oculto da máquina, Lívia deixa de ser paciente, vítima ou perseguidora.")
    narrate("Você se torna a falha que nenhum protocolo consegue conter.")
    raise GameFinished("Final Secreto (Secret Ending) - Oculto")


def run_loop(player, loop_state):
    start_loop_scene(player, loop_state)
