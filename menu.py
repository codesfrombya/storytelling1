import os
import sys
import time
from arts import *


def clear_screen():
    os.system("cls" if os.name == "nt" else "clear")


def typewriter(text="", delay=0.018):
    for char in text:
        print(char, end="", flush=True)
        time.sleep(delay)
    print()


def narrate(*lines, delay=0.018):
    for line in lines:
        typewriter(line, delay=delay)


def pause():
    input("\nPressione ENTER para continuar...")


def title(text):
    clear_screen()
    print("=" * 68)
    print(text.center(68))
    print("=" * 68)


def show_logo():
    art_logo()
    time.sleep(1.5)


def choose(valid_options):
    while True:
        choice = input("\nEscolha: ").strip()
        if choice in valid_options:
            return choice
        print("Opção inválida.")


def show_instructions():
    title("INSTRUÇÕES")
    narrate("PARADOX é um RPG de texto com terror psicológico.")
    narrate("Você vai explorar a floresta, encontrar pistas e morrer algumas vezes.")
    narrate("E sim morrer faz parte do progresso.")
    narrate("É um jogo de múltipa escolha, porém algumas escolhas erradas levam à morte imediata.")
    narrate("As pistas, itens e memórias encontradas ajudam a quebrar o ciclo.")
    pause()


def main_menu():
    while True:
        show_logo()
        print("1. Jogar")
        print("2. Instruções")
        print("3. Sair")

        choice = choose(["1", "2", "3"])

        if choice == "1":
            return "play"
        if choice == "2":
            show_instructions()
        if choice == "3":
            title("ENCERRANDO")
            narrate("Até a próxima. Ou até o próximo loop.")
            return "exit"


def post_game_menu():
    print("\n1. Jogar novamente")
    print("2. Voltar ao menu inicial")
    print("3. Sair")
    return choose(["1", "2", "3"])