import time
from menu import title, narrate, pause


def intro(player):
    title("PARADOX")
    narrate("Carregando...", delay=0.02)
    time.sleep(1)
    narrate("Acorde.", delay=0.03)
    time.sleep(1)
    narrate("Você acorda de um transe em uma floresta escura.")
    narrate("Sua cabeça dói.")
    narrate("A última coisa de que lembra é de um clarão e barulhos altos.")
    narrate("De repente, você percebe que está completamente sozinha.")
    narrate("Você não sabe seu nome.")
    narrate("Nem sabe por que está naquele lugar.")
    narrate("E alguma coisa, escondida entre as árvores, parece já saber quem você é.")
    pause()
