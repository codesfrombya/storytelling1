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
    narrate("Algo mais havia acontecido, mas você não se lembra de nada.")
    narrate(f"Quem é você, {player['nome']}? Como veio parar aqui?")
    narrate("E quem bateu na sua cabeça?")
    pause()