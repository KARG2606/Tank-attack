class PrologBridge:

    def __init__(self, prolog_manager):
        self.prolog = prolog_manager

    def get_path(self, start, goal):
        return self.prolog.find_path(
            start[0], start[1],
            goal[0], goal[1]
        )