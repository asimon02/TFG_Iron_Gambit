"""
adaptation_engine.py -- Motor de adaptacion basado en biofeedback

Procesa la Frecuencia Cardiaca (HR) en tiempo real para inferir
estados fisiologicos simples (estres, relajacion) a partir de una
media movil del propio usuario.
"""

from collections import deque

class AdaptationEngine:
    def __init__(self):
        # Mantenemos las ultimas lecturas para hacer una media movil
        self.MAX_HISTORY = 10
        self._hr_history = deque(maxlen=self.MAX_HISTORY)

    # Anade una nueva lectura de BPM al historial
    def add_reading(self, bpm: int):
        if bpm > 0:
            self._hr_history.append(bpm)

    # Devuelve la media movil actual, o None si no hay datos suficientes
    def get_average_bpm(self) -> float | None:
        if not self._hr_history:
            return None
        return sum(self._hr_history) / len(self._hr_history)

    # Clasifica el estado fisiologico actual respecto a la media movil
    def get_hr_state(self, current_bpm: int | None) -> str:
        avg_bpm = self.get_average_bpm()
        if current_bpm is None or avg_bpm is None:
            return "normal"

        if current_bpm >= avg_bpm + 5:
            return "high"
        if current_bpm <= avg_bpm - 5:
            return "low"
        return "normal"