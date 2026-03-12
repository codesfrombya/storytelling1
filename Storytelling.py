from menu import main_menu, post_game_menu, title, narrate
from player import create_player
from loop import create_loop_state
from story import intro
from events import run_loop, DeathInLoop, GameFinished


def ask_player_name():
    print()
    name = input("Digite o nome da personagem: ").strip()
    return name if name else "Larissa"


def show_summary(player, loop_state, ending_name):
    print("\nFIM DE JOGO")
    print(f"Final alcançado: {ending_name}")
    print(f"Loops vividos: {loop_state['loop']}")
    print(f"Mortes totais: {player['mortes']}")
    print(f"Pistas descobertas: {len(player['pistas'])}")
    print(f"Memórias recuperadas: {len(player['memorias'])}")


def play_game():
    while True:
        player = create_player(ask_player_name())
        loop_state = create_loop_state()

        intro(player)

        while True:
            try:
                run_loop(player, loop_state)
            except DeathInLoop:
                continue
            except GameFinished as ending:
                show_summary(player, loop_state, ending.ending_name)
                choice = post_game_menu()

                if choice == "1":
                    break
                if choice == "2":
                    return
                if choice == "3":
                    title("ENCERRANDO")
                    narrate("Até a próxima. Ou até o próximo loop.")
                    raise SystemExit


def main():
    while True:
        choice = main_menu()

        if choice == "exit":
            break

        if choice == "play":
            play_game()


if __name__ == "__main__":
    main()