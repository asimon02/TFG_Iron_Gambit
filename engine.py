"""
engine.py -- Wrapper sobre motores de ajedrez UCI (Stockfish)

Gestiona la comunicacion con el ejecutable del motor, el nivel de dificultad
y el calculo del mejor movimiento para una posicion dada

Cada nivel combina tres parametros de Stockfish para una dificultad real:
  - Skill Level (0-20): controla la calidad de la busqueda
  - Depth:              limita la profundidad de analisis
  - Time:               tiempo maximo de calculo en segundos
"""

import chess
import chess.engine

# Niveles de dificultad: nombre -> (Skill Level, depth, tiempo segundos)
LEVELS = {
    "Principiante": (0,  1, 0.05),
    "Facil":        (3,  2, 0.1 ),
    "Normal":       (8,  5, 0.3 ),
    "Dificil":      (14, 8, 0.8 ),
    "Experto":      (18, 12, 1.5),
    "Maestro":      (20, 20, 3.0),
}
LEVEL_NAMES = list(LEVELS.keys())

class Engine:
    """
    Interfaz con un motor UCI (por defecto Stockfish)

    Atributos publicos
    ------------------
    name    : str   -- nombre del motor activo
    level   : str   -- clave del nivel activo (de LEVEL_NAMES)
    ready   : bool  -- True si el motor esta disponible
    """

    # Inicializa el motor con el ejecutable dado
    def __init__(self, path: str = "stockfish/stockfish-windows-x86-64-avx2.exe"):
        self.name  = "Stockfish"
        self.level = LEVEL_NAMES[2]
        self._path = path
        self._eng  = None
        self.ready = False
        self._start()

    # -- Ciclo de vida --------------------------------------------------------

    # Arranca el proceso del motor
    def _start(self):
        try:
            self._eng  = chess.engine.SimpleEngine.popen_uci(self._path)
            self.ready = True
            self._apply_level()
        except Exception:
            self._eng  = None
            self.ready = False

    # Cierra el proceso del motor limpiamente
    def close(self):
        if self._eng:
            try:
                self._eng.quit()
            except Exception:
                pass
            self._eng  = None
            self.ready = False

    # -- Configuracion --------------------------------------------------------

    # Cambia el nivel de dificultad del motor, aplicando los parametros correspondientes
    def set_level(self, level_name: str):
        if level_name in LEVELS:
            self.level = level_name
            if self.ready:
                self._apply_level()

    # Aplica los parametros del nivel actual al motor, si esta listo
    def _apply_level(self):
        skill, depth, _ = LEVELS[self.level]
        try:
            self._eng.configure({"Skill Level": skill})
        except Exception:
            pass

    # -- Calculo de movimiento ------------------------------------------------

    # Devuelve el mejor movimiento para la posicion dada
    def best_move(self, board: chess.Board):
        if not self.ready or board.is_game_over():
            return None
        skill, depth, time_limit = LEVELS[self.level]
        try:
            result = self._eng.play(
                board,
                chess.engine.Limit(depth=depth, time=time_limit),
            )
            return result.move
        except Exception:
            return None