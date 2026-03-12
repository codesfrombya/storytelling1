import os
import time
import threading

try:
    import msvcrt
except ImportError:
    msvcrt = None

from menu import title, narrate, pause
from player import add_item, add_memory, add_clue
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
        remaining = timeout - int(time.time() - start_time)

        if remaining != last_second:
            print(f"\rTempo para se esconder: {remaining:2d} segundos | Escolha: ", end="", flush=True)
            last_second = remaining

        if remaining <= 0:
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
            return result[0]
        print(f"\rTempo para se esconder: {remaining:2d} segundos ", end="", flush=True)
        time.sleep(1)

    print("\rTempo esgotado!                           ")
    return None


def timed_choice(valid_options, timeout=15):
    if os.name == "nt" and msvcrt is not None:
        return timed_input_windows(valid_options, timeout)
    return timed_input_fallback("\nEscolha rapidamente: ", timeout)


def die(player, loop_state, reason, clue_after_death=None):
    title("VOCÊ MORREU")
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


def creature_hide_event(player, loop_state):
    title("A CRIATURA SE APROXIMA")
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
            "hesitar_diante_da_criatura_e_morte"
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
            "a_cabana_nao_e_bom_esconderijo_em_panico"
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
            "o_mato_so_funciona_depois_de_aprender_o_padrao"
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
            "ficar_parada_sem_entender_a_entidade_falha"
        )

    die(
        player,
        loop_state,
        "Na pressa, você escolhe mal e perde segundos preciosos.",
        "o_panico_tambem_mata"
    )


def start_loop_scene(player, loop_state):
    title(f"PARADOX - LOOP {loop_state['loop']}")
    narrate(f"{player['nome']}, você desperta no mesmo chão frio de sempre.")
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

    choice = choose(["1", "2", "3", "4"])

    if choice == "1":
        examine_body_scene(player, loop_state)
    elif choice == "2":
        scream_scene(player, loop_state)
    elif choice == "3":
        lake_scene(player, loop_state)
    else:
        cemetery_scene(player, loop_state)


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

    choice = choose(["1", "2"])
    if choice == "1":
        lake_scene(player, loop_state)
    else:
        cemetery_scene(player, loop_state)


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
        narrate("Você chega a um lago imóvel, liso como vidro.")
        narrate("Perto da margem há uma mochila rasgada.")

        print("\n1. Abrir a mochila")
        print("2. Olhar seu reflexo")
        print("3. Beber a água")
        print("4. Voltar")

        choice = choose(["1", "2", "3", "4"])

        if choice == "1":
            if "cracha_quebrado" not in player["itens"]:
                narrate("Dentro da mochila há um crachá quebrado com parte de um nome:")
                narrate("'...issa A.' e as letras 'N.T.E. - Núcleo Temporal Experimental'")
                add_item(player, "cracha_quebrado")
                add_clue(player, "laboratorio_temporal")
            else:
                narrate("A mochila já está vazia.")
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
                "nao_beber_agua"
            )
        else:
            return start_loop_scene(player, loop_state)


def cemetery_scene(player, loop_state):
    while True:
        title("CEMITÉRIO")
        narrate("Você encontra lápides sem nomes. Só números.")
        narrate("Algumas parecem recentes. Outras, quebradas.")

        print("\n1. Investigar as lápides")
        print("2. Cavar perto de uma cruz caída")
        print("3. Fugir ao ouvir passos")
        print("4. Ler os números com atenção")

        choice = choose(["1", "2", "3", "4"])

        if choice == "1":
            narrate("Atrás de uma lápide há uma placa metálica enterrada.")
            narrate("Nela está escrito: 'Pacientes Reabilitáveis - Série 08'")
            add_clue(player, "voce_era_cobaia")
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

        else:
            narrate("Um dos números chama sua atenção: 08-17-LA.")
            narrate("Esse código faz sua cabeça doer.")
            add_memory(player, "Você assinou algum documento com esse código.")
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
        narrate("Uma cabana apodrecida surge entre as árvores.")
        narrate("Na madeira da parede, alguém riscou palavras com as unhas.")

        print("\n1. Forçar a porta")
        if "chave_enferrujada" in player["itens"]:
            print("2. Usar a chave enferrujada")
        print("3. Entrar pela janela")
        print("4. Observar a parede antes de entrar")

        valid = ["1", "3", "4"]
        if "chave_enferrujada" in player["itens"]:
            valid.append("2")

        choice = choose(valid)

        if choice == "1":
            die(
                player,
                loop_state,
                "Você faz barulho demais. A entidade te alcança antes que a porta ceda.",
                "a_porta_nao_deve_ser_forcada"
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

        else:
            narrate("Na parede está escrito:")
            narrate("'NÃO CORRA DELA. ELA É VOCÊ.'")
            add_clue(player, "mensagem_da_parede")
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

        choice = choose(["1", "2", "3", "4"])

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
            pause()

        elif choice == "3":
            laboratory_scene(player, loop_state)
            return

        else:
            narrate("Na fotografia, você aparece sentada na calçada.")
            narrate("Duas pessoas de roupa social estão de pé à sua frente.")
            narrate("No verso, escrito à mão: 'Uma oportunidade de mudar de vida.'")
            add_memory(player, "Você aceitou uma proposta estranha quando estava no fundo do poço.")
            pause()


def laboratory_scene(player, loop_state):
    while True:
        title("LABORATÓRIO SUBTERRÂNEO")
        narrate("O alçapão leva a um corredor frio iluminado por lâmpadas falhas.")
        narrate("Você encontrou o centro do experimento.")

        print("\n1. Acessar o computador")
        print("2. Abrir uma cela trancada")
        print("3. Assistir a uma gravação")
        print("4. Destruir os equipamentos")

        choice = choose(["1", "2", "3", "4"])

        if choice == "1":
            narrate("Nos arquivos do sistema você lê:")
            narrate("'Projeto Érebo - Reabilitação por Recorrência Temporal.'")
            narrate("'Financiamento autorizado por órgão estatal confidencial.'")
            add_clue(player, "governo_e_cientistas")
            pause()

        elif choice == "2":
            die(
                player,
                loop_state,
                "Dentro da cela havia alguém. Ou algo. Quando a porta abre, a criatura salta em você.",
                "nem_toda_porta_deve_ser_aberta"
            )

        elif choice == "3":
            narrate("A gravação mostra você assinando um termo.")
            narrate("Seus olhos estão vazios.")
            narrate("Você diz: 'Não tenho mais nada a perder.'")
            add_memory(player, "Você entrou no experimento por desespero.")
            pause()
            revelation_scene(player, loop_state)
            return

        else:
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
                "destruir_sem_entender_e_erro"
            )


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

    choice = choose(["1", "2", "3", "4"])

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
            "fugir_da_verdade_reinicia"
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

    die(
        player,
        loop_state,
        "Você a ataca. Ela não revida. Só segura seu braço e sussurra: 'ainda não.'",
        "violencia_sem_compreensao_falha"
    )


def final_decision_scene(player, loop_state):
    title("DECISÃO FINAL")
    narrate("O núcleo temporal pulsa no centro do laboratório.")
    narrate("Você entende que pode encerrar tudo agora.")
    narrate("Mas cada escolha cobra alguma coisa.")

    print("\n1. Desligar o experimento e escapar")
    print("2. Manter o loop para continuar 'se corrigindo'")
    print("3. Sacrificar sua versão futura para quebrar o paradoxo")
    print("4. Fundir-se com sua outra versão")

    choice = choose(["1", "2", "3", "4"])

    if choice == "1":
        ending_liberation()
    elif choice == "2":
        ending_reincidence()
    elif choice == "3":
        ending_sacrifice()
    else:
        ending_fusion()


def ending_liberation():
    title("FINAL: LIBERTAÇÃO")
    narrate("Você desliga o núcleo.")
    narrate("As luzes morrem.")
    narrate("A floresta treme como se estivesse sendo desfeita.")
    narrate("Quando você abre os olhos, está do lado de fora do laboratório, ao amanhecer.")
    narrate("Você não lembra de tudo.")
    narrate("Mas lembra o bastante para nunca mais aceitar ser apagada.")
    raise GameFinished("Libertação")


def ending_reincidence():
    title("FINAL: REINCIDÊNCIA")
    narrate("Você escolhe continuar.")
    narrate("Diz a si mesma que ainda merece punição, ainda merece repetir, ainda merece pagar.")
    narrate("A entidade sorri.")
    narrate("Então você entende: ela sorriu porque agora é você quem vai correr atrás da próxima versão.")
    raise GameFinished("Reincidência")


def ending_sacrifice():
    title("FINAL: SACRIFÍCIO")
    narrate("Você abraça sua versão futura enquanto o núcleo colapsa.")
    narrate("Ela sussurra: 'obrigada por finalmente entender.'")
    narrate("A fenda se fecha.")
    narrate("As outras cobaias presas nos registros do sistema são libertadas do ciclo.")
    narrate("Seu nome desaparece junto com o experimento.")
    raise GameFinished("Sacrifício")


def ending_fusion():
    title("FINAL: FUSÃO")
    narrate("Você toca a mão da entidade.")
    narrate("As memórias se juntam.")
    narrate("As mortes, os medos, as versões, os erros.")
    narrate("Pela primeira vez, você se torna inteira.")
    narrate("O loop quebra não porque foi destruído, mas porque não há mais duas de você para sustentá-lo.")
    raise GameFinished("Fusão")


def run_loop(player, loop_state):
    start_loop_scene(player, loop_state)