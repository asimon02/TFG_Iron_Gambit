"""
top_bar.py -- Barra superior con desplegables de motor y nivel de dificultad

Dibuja una barra fija en la parte superior de la ventana con:
  - Desplegable de motor (Stockfish por defecto)
  - Desplegable de nivel de dificultad
  - Indicador de estado del motor (verde/rojo)

Los desplegables se abren al hacer clic y se cierran al seleccionar
una opcion o al hacer clic fuera de ellos
"""

import pygame
from theme      import Theme
from engine     import LEVEL_NAMES

# Motores disponibles
ENGINE_NAMES = ["Stockfish"]

# Altura fija de la barra superior
BAR_H = 36

class TopBar:
    """
    Barra superior con desplegables de motor y dificultad

    Comunicacion con App
    --------------------
    Tras cada frame, App debe consultar:
        top_bar.engine_changed  -> bool, True si cambio el motor
        top_bar.level_changed   -> bool, True si cambio el nivel
        top_bar.selected_engine -> str, motor activo
        top_bar.selected_level  -> str, nivel activo
    y luego llamar a top_bar.clear_flags() para resetear los flags
    """

    def __init__(self, surface: pygame.Surface, engine_name: str, level_name: str):
        self.surface = surface

        # Estado seleccionado
        self.selected_engine = engine_name
        self.selected_level  = level_name

        # Flags de nueva seleccion
        self.engine_changed  = False
        self.level_changed   = False

        # Estado de los desplegables
        self._open_engine = False
        self._open_level  = False

        # Rectangulos calculados en draw()
        self._rect_engine      = pygame.Rect(0, 0, 0, 0)
        self._rect_level       = pygame.Rect(0, 0, 0, 0)
        self._rects_eng_items  = []
        self._rects_lvl_items  = []

        # Fuentes inicializadas en draw()
        self._font_bar  = None
        self._font_drop = None

    # -- API publica ----------------------------------------------------------

    # Permite actualizar layout y fonts si cambian
    def clear_flags(self):
        self.engine_changed = False
        self.level_changed  = False

    # Manejar clics: devuelve True si el clic fue consumido por la barra
    def handle_click(self, pos: tuple) -> bool:
        mx, my = pos

        # Clic en la barra superior
        W = self.surface.get_width()
        if my < BAR_H:
            # Desplegable motor
            if self._rect_engine.collidepoint(mx, my):
                self._open_engine = not self._open_engine
                self._open_level  = False
                return True
            # Desplegable nivel
            if self._rect_level.collidepoint(mx, my):
                self._open_level  = not self._open_level
                self._open_engine = False
                return True
            return True

        # Clic en items desplegados -- motor
        if self._open_engine:
            for rect, name in self._rects_eng_items:
                if rect.collidepoint(mx, my):
                    self.selected_engine = name
                    self.engine_changed  = True
                    self._open_engine    = False
                    return True
            self._open_engine = False
            return False

        # Clic en items desplegados -- nivel
        if self._open_level:
            for rect, name in self._rects_lvl_items:
                if rect.collidepoint(mx, my):
                    self.selected_level = name
                    self.level_changed  = True
                    self._open_level    = False
                    return True
            self._open_level = False
            return False

        return False

    # Manejar teclas: devuelve True si la tecla fue consumida por la barra
    def handle_key(self, key: int):
        if key == pygame.K_ESCAPE:
            self._open_engine = False
            self._open_level  = False

    # -- Renderizado ----------------------------------------------------------

    # Dibuja la barra fija (fondo + controles)
    def draw(self, engine_ready: bool):
        W = self.surface.get_width()
        self._engine_ready = engine_ready

        # Inicializar fuentes la primera vez
        if self._font_bar is None:
            self._font_bar  = pygame.font.SysFont("Tahoma", 13, bold=True)
            self._font_drop = pygame.font.SysFont("Tahoma", 12)

        # Fondo de la barra
        pygame.draw.rect(self.surface, Theme.BG_PANEL, (0, 0, W, BAR_H))
        pygame.draw.line(self.surface, Theme.GOLD, (0, BAR_H - 1), (W, BAR_H - 1), 1)

        # Indicador de estado del motor (circulo verde/rojo)
        dot_color = (60, 200, 80) if engine_ready else (200, 50, 50)
        pygame.draw.circle(self.surface, dot_color, (14, BAR_H // 2), 5)

        # Etiqueta "MOTOR:"
        lbl = self._font_bar.render("MOTOR:", True, Theme.TEXT)
        self.surface.blit(lbl, (26, BAR_H // 2 - lbl.get_height() // 2))
        cx = 26 + lbl.get_width() + 6

        # Desplegable motor
        self._rect_engine = self._draw_dropdown(
            cx, 4, self.selected_engine, self._open_engine, active=True)
        cx = self._rect_engine.right + 16

        # Etiqueta "NIVEL:"
        lbl2 = self._font_bar.render("NIVEL:", True, Theme.TEXT)
        self.surface.blit(lbl2, (cx, BAR_H // 2 - lbl2.get_height() // 2))
        cx += lbl2.get_width() + 6

        # Desplegable nivel
        self._rect_level = self._draw_dropdown(
            cx, 4, self.selected_level, self._open_level, active=engine_ready)

    # Dibuja los overlays de los desplegables abiertos y calcula rects de items
    def draw_overlays(self):
        self._rects_eng_items = []
        self._rects_lvl_items = []

        # Solo dibujar overlays si el motor esta listo
        if self._open_engine:
            self._rects_eng_items = self._draw_dropdown_list(
                self._rect_engine, ENGINE_NAMES, self.selected_engine)

        # Solo dibujar overlay de nivel si el motor esta listo
        if self._open_level:
            self._rects_lvl_items = self._draw_dropdown_list(
                self._rect_level, LEVEL_NAMES, self.selected_level)

    # Dibuja un control desplegable (sin overlay) y devuelve su rect
    def _draw_dropdown(self, x: int, y: int, text: str, is_open: bool, active: bool = True) -> pygame.Rect:
        f       = self._font_bar
        pad_x   = 8
        arrow_w = 14
        text_w  = f.size(text)[0]
        w       = text_w + pad_x * 2 + arrow_w
        h       = BAR_H - y * 2

        # Colores segun estado: fondo, borde y texto
        col_bg  = Theme.BG_CARD
        col_brd = Theme.GOLD if is_open else Theme.STEEL
        col_txt = Theme.TEXT if active else Theme.STEEL

        # Fondo del control
        rect = pygame.Rect(x, y, w, h)
        pygame.draw.rect(self.surface, col_bg,  rect, border_radius=3)
        pygame.draw.rect(self.surface, col_brd, rect, 1, border_radius=3)

        # Texto del item seleccionado
        s = f.render(text, True, col_txt)
        self.surface.blit(s, (x + pad_x, y + h // 2 - s.get_height() // 2))

        # Flechas
        arrow = "\u25b2" if is_open else "\u25bc"
        af = pygame.font.SysFont("Tahoma", 9)
        ar = af.render(arrow, True, col_txt)
        self.surface.blit(ar, (x + w - arrow_w, y + h // 2 - ar.get_height() // 2))

        return rect

    # Dibuja el overlay de la lista desplegada y devuelve rects de cada item
    def _draw_dropdown_list(self, anchor: pygame.Rect,
                             items: list, selected: str) -> list:
        f        = self._font_drop
        pad_x    = 8
        item_h   = 22
        w        = max(anchor.width, max(f.size(n)[0] for n in items) + pad_x * 2)
        list_h   = item_h * len(items)
        lx       = anchor.x
        ly       = anchor.bottom + 2

        # Fondo de la lista
        bg_rect = pygame.Rect(lx, ly, w, list_h)
        pygame.draw.rect(self.surface, Theme.BG_CARD,  bg_rect, border_radius=4)
        pygame.draw.rect(self.surface, Theme.GOLD,     bg_rect, 1, border_radius=4)

        rects = []
        
        # Dibujar cada item y calcular su rect para deteccion de clics
        for i, name in enumerate(items):
            iy      = ly + i * item_h
            item_r  = pygame.Rect(lx, iy, w, item_h)
            is_sel  = (name == selected)

            if is_sel:
                pygame.draw.rect(self.surface, (40, 30, 10), item_r)

            col = Theme.GOLD_LT if is_sel else Theme.TEXT
            s   = f.render(name, True, col)
            self.surface.blit(s, (lx + pad_x, iy + item_h // 2 - s.get_height() // 2))

            # Separador entre items
            if i < len(items) - 1:
                pygame.draw.line(self.surface, Theme.STEEL,
                                 (lx + 4, iy + item_h - 1),
                                 (lx + w - 4, iy + item_h - 1), 1)

            rects.append((item_r, name))

        return rects