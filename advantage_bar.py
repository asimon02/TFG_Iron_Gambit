"""
advantage_bar.py — Barra lateral de ventaja de material

Dibuja una barra vertical a la izquierda del tablero:
  - Mitad superior: color de las negras
  - Mitad inferior: color de las blancas
  - La proporcion cambia segun la ventaja de material calculada por GameState

La barra tiene animacion suave: el valor real se interpola hacia el
valor objetivo en cada frame para que el cambio no sea brusco

Valores de material estandar: P=1 N=3 B=3 R=5 Q=9 → maximo = 39
"""

import pygame
from theme      import Theme
from layout     import Layout
from game_state import GameState

MAX_MATERIAL = 39

class AdvantageBar:
    """
    Barra vertical de ventaja de material

    Se coloca entre el margen izquierdo y las coordenadas del tablero
    La mitad inferior es blanca (blancas) y la superior negra (negras)
    Cuando las blancas tienen ventaja, la zona blanca crece hacia arriba
    """

    # Velocidad de interpolacion
    LERP_SPEED = 0.08

    def __init__(self, surface: pygame.Surface, layout: Layout):
        self.surface       = surface
        self.layout        = layout
        self._display_frac = 0.5

    def update_layout(self, layout: Layout):
        self.layout = layout

    # Actualiza el valor mostrado por la barra, interpolando hacia el valor objetivo
    def update(self, gs: GameState):
        adv    = gs.material_advantage()
        target = 0.5 + adv / (MAX_MATERIAL * 2)
        target = max(0.05, min(0.95, target))

        self._display_frac += (target - self._display_frac) * self.LERP_SPEED

    # Dibuja la barra de ventaja en su posicion designada
    def draw(self, gs: GameState):
        self.update(gs)

        L = self.layout
        x = L.bax
        w = L.baw
        y = L.bay
        h = L.bah

        # Zona negra (parte superior)
        black_h = int(h * (1.0 - self._display_frac))
        
        # Zona blanca (parte inferior)
        white_h = h - black_h

        # Dibujar las dos zonas con sus respectivos colores
        pygame.draw.rect(self.surface, Theme.PIECE_BLACK, (x, y,            w, black_h))
        pygame.draw.rect(self.surface, Theme.PIECE_WHITE, (x, y + black_h,  w, white_h))

        # Linea divisoria
        div_y = y + black_h
        pygame.draw.line(self.surface, Theme.GOLD, (x, div_y), (x + w, div_y), 1)

        # Borde exterior
        pygame.draw.rect(self.surface, Theme.STEEL, (x, y, w, h), 1)

        # Etiquetas de ventaja en puntos si hay diferencia notable
        adv = gs.material_advantage()
        if abs(adv) >= 1:
            self._draw_label(adv, x, y, w, h, black_h, white_h)

    # Dibuja el numero de puntos de ventaja sobre la zona ganadora
    def _draw_label(self, adv: float, x: int, y: int, w: int, h: int, black_h: int, white_h: int):
        try:
            font = pygame.font.SysFont("Tahoma", max(8, w - 2), bold=True)
        except Exception:
            return

        txt   = str(abs(int(adv)))
        color = Theme.PIECE_BLACK if adv > 0 else Theme.PIECE_WHITE
        bg    = Theme.PIECE_WHITE if adv > 0 else Theme.PIECE_BLACK

        label = font.render(txt, True, color)
        lw, lh = label.get_size()

        # Posicion: dentro de la zona del bando ganador, cerca de la linea
        if adv > 0:
            ly = y + black_h + 3
        else:
            ly = y + black_h - lh - 3

        lx = x + (w - lw) // 2

        # Fondo pequeño para legibilidad
        pygame.draw.rect(self.surface, bg, (lx - 1, ly - 1, lw + 2, lh + 2))
        self.surface.blit(label, (lx, ly))