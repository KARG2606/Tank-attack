from game.level_loader import LevelLoader
from prolog.prolog_manager import PrologManager

loader = LevelLoader()
loader.load_level("maps/level1.txt")

print("MAPA OK")

prolog = PrologManager()
print("PROLOG OK")

prolog.generate_graph(loader)
print("GRAFO OK")

path = prolog.find_path(1, 1, 10, 10)

print("PATH:", path)