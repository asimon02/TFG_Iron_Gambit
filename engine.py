"""
engine.py -- Wrapper sobre motores de ajedrez UCI (Stockfish)

Gestiona la comunicacion con el ejecutable del motor, el nivel de dificultad
y el calculo del mejor movimiento para una posicion dada

Cada nivel combina parametros de Stockfish para una dificultad real:
  - UCI_LimitStrength y UCI_Elo: para emular errores humanos (versiones modernas)
  - Skill Level (0-20): controla la calidad de la busqueda (versiones antiguas o nivel Max)
  - Depth:              limita la profundidad de analisis
  - Time:               tiempo maximo de calculo en segundos
"""

import chess
import chess.engine

# Diccionario con la configuración completa por nivel:
# Nombre -> {"uci_limit": bool, "uci_elo": int, "skill": int, "depth": int, "time": float}
LEVELS = {
    "Principiante": {
        "uci_limit": True,
        "uci_elo": 800,
        "skill": 0,
        "depth": 2,
        "time": 0.05
    },
    "Intermedio": {
        "uci_limit": True,
        "uci_elo": 1400,
        "skill": 5,
        "depth": 4,
        "time": 0.2
    },
    "Avanzado": {
        "uci_limit": True,
        "uci_elo": 1800,
        "skill": 10,
        "depth": 8,
        "time": 0.5
    },
    "Gran Maestro": {
        "uci_limit": False,
        "uci_elo": 2500,
        "skill": 20,
        "depth": 10,
        "time": 1.5
    }
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
        self.level = LEVEL_NAMES[1]
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
        config = LEVELS[self.level]
        try:
            options = {
                "UCI_LimitStrength": config["uci_limit"],
                "Skill Level": config["skill"]
            }
            if config["uci_limit"]:
                options["UCI_Elo"] = config["uci_elo"]
                
            self._eng.configure(options)
        except Exception as e:
            print(f"Error al configurar motor: {e}")

    # -- Calculo de movimiento ------------------------------------------------

    # Devuelve el mejor movimiento para la posicion dada
    def best_move(self, board: chess.Board):
        if not self.ready or board.is_game_over():
            return None
            
        config = LEVELS[self.level]
        try:
            result = self._eng.play(
                board,
                chess.engine.Limit(depth=config["depth"], time=config["time"]),
            )
            return result.move
        except Exception:
            return None