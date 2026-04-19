"""
font_manager.py — Carga y escalado de fuentes del sistema

Las fuentes se escalan proporcionalmente al ancho del panel y al tamaño
de la casilla del tablero, garantizando legibilidad en cualquier resolucion
"""

import pygame
from layout import Layout

# Fuentes utilizadas por la aplicacion
_FONT_TITLE = "Segoe UI"
_FONT_BODY  = "Tahoma"
_FONT_MONO  = "Segoe UI Mono"
_FONT_PIECE = "Segoe UI Symbol"

class FontManager:
    """
    Gestiona todas las fuentes de la aplicacion

    Fuentes disponibles
    -------------------
    title    — titulo "IRON GAMBIT"
    heading  — encabezados de seccion
    body     — texto normal del panel
    small    — etiquetas secundarias y subtitulos
    mono     — historial de movimientos en notacion SAN
    key      — etiquetas de teclas de control
    coord    — letras y numeros del tablero
    piece    — simbolos unicode de las piezas
    """

    # Inicializa pygame.font y carga las fuentes segun el layout actual
    def __init__(self, layout: Layout):
        pygame.font.init()
        self._load(layout)

    # Permite recargar las fuentes al cambiar el layout
    def reload(self, layout: Layout):
        self._load(layout)

    # Carga y escala las fuentes segun el layout actual
    def _load(self, layout: Layout):
        pw    = max(150, layout.pw)
        scale = max(0.70, min(1.30, pw / 220.0))

        def sz(base: int) -> int:
            return max(9, int(base * scale))

        self.title   = pygame.font.SysFont(_FONT_TITLE, sz(26), bold=True)
        self.heading = pygame.font.SysFont(_FONT_BODY,  sz(13), bold=True)
        self.body    = pygame.font.SysFont(_FONT_BODY,  sz(12))
        self.small   = pygame.font.SysFont(_FONT_BODY,  sz(10))
        self.mono    = pygame.font.SysFont(_FONT_MONO,  sz(11))
        self.key     = pygame.font.SysFont(_FONT_BODY,  sz(10), bold=True)
        self.coord   = pygame.font.SysFont(_FONT_BODY,  max(9, layout.sq // 6), bold=True)
        self.piece   = pygame.font.SysFont(_FONT_PIECE, max(18, int(layout.sq * 0.70)))