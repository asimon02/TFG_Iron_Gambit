"""
side_selector.py -- Modal para elegir bando al iniciar una nueva partida

Muestra un dialogo con tres opciones:
  - Jugar con Blancas
  - Jugar con Negras
  - Dos jugadores (sin motor)

Devuelve la eleccion a App para que configure el motor correctamente
"""

import pygame

from theme        import Theme
from layout       import Layout
from font_manager import FontManager

# Constantes de eleccion
SIDE_WHITE  = "white"
SIDE_BLACK  = "black"
SIDE_HUMAN  = "human"

class SideSelector:
    """
    Modal de seleccion de bando

    Uso:
        selector = SideSelector(screen, fonts, layout)
        # En el bucle de eventos:
        choice = selector.handle_click(pos)
        # En render:
        if selector.active:
            selector.draw(mouse_pos)
    """

    # Inicializacion
    def __init__(self, surface: pygame.Surface,
                 fonts: FontManager, layout: Layout):
        self.surface = surface
        self.fonts   = fonts
        self.layout  = layout
        self.active  = False
        self._rects  = []

    # Permite actualizar layout y fonts si cambian
    def update_layout(self, layout: Layout, fonts: FontManager):
        self.layout = layout
        self.fonts  = fonts

    # Mostrar el modal
    def show(self):
        self.active = True
        self._rects = []

    # Ocultar el modal
    def hide(self):
        self.active = False

    # Manejar click: devuelve la eleccion o None si no se ha hecho ninguna
    def handle_click(self, pos: tuple):
        if not self.active:
            return None
        for rect, choice in self._rects:
            if rect.collidepoint(pos):
                self.hide()
                return choice
        return None

    # Renderizar el modal (mouse_pos para resaltar las opciones al pasar el raton)
    def draw(self, mouse_pos: tuple = None):
        if not self.active:
            return

        W, H = self.surface.get_size()
        f    = self.fonts

        # Overlay semitransparente
        ov = pygame.Surface((W, H), pygame.SRCALPHA)
        ov.fill((0, 0, 0, 200))
        self.surface.blit(ov, (0, 0))

        # Dimensiones del modal
        card_w  = min(420, W - 60)
        btn_h   = 52
        gap     = 12
        pad     = 24
        title_h = f.title.get_height() + 8
        sub_h   = f.small.get_height() + 6
        modal_h = pad + title_h + sub_h + (btn_h + gap) * 3 + pad
        mx      = (W - card_w) // 2
        my      = (H - modal_h) // 2

        # Fondo del modal
        pygame.draw.rect(self.surface, Theme.BG_PANEL,
                         (mx, my, card_w, modal_h), border_radius=6)
        pygame.draw.rect(self.surface, Theme.GOLD,
                         (mx, my, card_w, modal_h), 2, border_radius=6)
        pygame.draw.rect(self.surface, Theme.CRIMSON,
                         (mx + 2, my + 2, card_w - 4, modal_h - 4), 1, border_radius=6)

        # Titulo
        t = f.title.render("NUEVA PARTIDA", True, Theme.GOLD_LT)
        self.surface.blit(t, (mx + (card_w - t.get_width()) // 2, my + pad))

        # Subtitulo
        sub = f.small.render("Elige con que bando quieres jugar", True, Theme.TEXT)
        self.surface.blit(sub, (mx + (card_w - sub.get_width()) // 2,
                                my + pad + title_h))

        # Botones
        options = [
            (SIDE_WHITE, "Jugar con Blancas",  Theme.PIECE_WHITE,  Theme.PIECE_BLACK),
            (SIDE_BLACK, "Jugar con Negras",   Theme.PIECE_BLACK,  Theme.PIECE_WHITE),
            (SIDE_HUMAN, "Dos Jugadores",      Theme.BG_CARD,      Theme.GOLD_LT),
        ]

        self._rects = []
        by = my + pad + title_h + sub_h + gap

        for choice, label, bg, fg in options:
            rect    = pygame.Rect(mx + pad, by, card_w - pad * 2, btn_h)
            hovered = mouse_pos is not None and rect.collidepoint(mouse_pos)

            bg_col  = Theme.GOLD        if hovered else bg
            brd_col = Theme.GOLD_LT     if hovered else Theme.STEEL
            txt_col = Theme.PIECE_BLACK if hovered else fg

            pygame.draw.rect(self.surface, bg_col,  rect, border_radius=5)
            pygame.draw.rect(self.surface, brd_col, rect, 1, border_radius=5)

            s = f.body.render(label, True, txt_col)
            self.surface.blit(s, (rect.x + rect.w // 2 - s.get_width() // 2,
                                  rect.y + rect.h // 2 - s.get_height() // 2))

            self._rects.append((rect, choice))
            by += btn_h + gap