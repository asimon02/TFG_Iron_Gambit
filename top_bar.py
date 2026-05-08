"""
top_bar.py -- Barra superior con desplegables de motor, nivel y tiempo
"""

import pygame
from typing import Optional

from theme  import Theme
from engine import LEVEL_NAMES


ENGINE_NAMES = ["Stockfish"]
TIME_OPTIONS = [
    ("1 min", 60),
    ("5 min", 5 * 60),
    ("10 min", 10 * 60),
]

BAR_H = 36
HR_UP_COLOR = (210, 60, 60)
HR_DOWN_COLOR = (70, 185, 90)


class TopBar:
    """
    Barra superior con desplegables de motor, dificultad y tiempo de reloj.
    """

    def __init__(self, surface: pygame.Surface, engine_name: str, level_name: str,
                 initial_time_seconds: int):
        self.surface = surface

        self.selected_engine = engine_name
        self.selected_level = level_name
        self.selected_time_seconds = initial_time_seconds
        self.selected_time_label = self._label_for_seconds(initial_time_seconds)

        self.engine_changed = False
        self.level_changed = False
        self.time_changed = False

        self._open_engine = False
        self._open_level = False
        self._open_time = False

        self._rect_engine = pygame.Rect(0, 0, 0, 0)
        self._rect_level = pygame.Rect(0, 0, 0, 0)
        self._rect_time = pygame.Rect(0, 0, 0, 0)
        self._rects_eng_items = []
        self._rects_lvl_items = []
        self._rects_time_items = []

        self._font_bar = None
        self._font_drop = None

    def clear_flags(self):
        self.engine_changed = False
        self.level_changed = False
        self.time_changed = False

    def handle_click(self, pos: tuple) -> bool:
        mx, my = pos

        if my < BAR_H:
            if self._rect_engine.collidepoint(mx, my):
                self._open_engine = not self._open_engine
                self._open_level = False
                self._open_time = False
                return True
            if self._rect_level.collidepoint(mx, my):
                self._open_level = not self._open_level
                self._open_engine = False
                self._open_time = False
                return True
            if self._rect_time.collidepoint(mx, my):
                self._open_time = not self._open_time
                self._open_engine = False
                self._open_level = False
                return True
            return True

        if self._open_engine:
            for rect, name in self._rects_eng_items:
                if rect.collidepoint(mx, my):
                    self.selected_engine = name
                    self.engine_changed = True
                    self._open_engine = False
                    return True
            self._open_engine = False
            return False

        if self._open_level:
            for rect, name in self._rects_lvl_items:
                if rect.collidepoint(mx, my):
                    self.selected_level = name
                    self.level_changed = True
                    self._open_level = False
                    return True
            self._open_level = False
            return False

        if self._open_time:
            for rect, item in self._rects_time_items:
                if rect.collidepoint(mx, my):
                    label, seconds = item
                    self.selected_time_label = label
                    self.selected_time_seconds = seconds
                    self.time_changed = True
                    self._open_time = False
                    return True
            self._open_time = False
            return False

        return False

    def handle_key(self, key: int):
        if key == pygame.K_ESCAPE:
            self._open_engine = False
            self._open_level = False
            self._open_time = False

    def draw(self, engine_ready: bool, current_hr: Optional[int] = None,
             average_hr: Optional[float] = None, hr_state: str = "normal",
             show_stop: bool = False):
        w = self.surface.get_width()
        self._engine_ready = engine_ready

        if self._font_bar is None:
            self._font_bar = pygame.font.SysFont("Tahoma", 13, bold=True)
            self._font_drop = pygame.font.SysFont("Tahoma", 12)

        pygame.draw.rect(self.surface, Theme.BG_PANEL, (0, 0, w, BAR_H))

        dot_color = Theme.GOLD_LT if engine_ready else Theme.CRIMSON_LT
        pygame.draw.circle(self.surface, dot_color, (14, BAR_H // 2), 5)

        lbl = self._font_bar.render("MOTOR:", True, Theme.TEXT_SOFT)
        self.surface.blit(lbl, (26, BAR_H // 2 - lbl.get_height() // 2))
        cx = 26 + lbl.get_width() + 6

        self._rect_engine = self._draw_dropdown(cx, 4, self.selected_engine, self._open_engine, active=True)
        cx = self._rect_engine.right + 16

        lbl2 = self._font_bar.render("NIVEL:", True, Theme.TEXT_SOFT)
        self.surface.blit(lbl2, (cx, BAR_H // 2 - lbl2.get_height() // 2))
        cx += lbl2.get_width() + 6

        self._rect_level = self._draw_dropdown(cx, 4, self.selected_level, self._open_level, active=engine_ready)
        cx = self._rect_level.right + 16

        lbl3 = self._font_bar.render("TIEMPO:", True, Theme.TEXT_SOFT)
        self.surface.blit(lbl3, (cx, BAR_H // 2 - lbl3.get_height() // 2))
        cx += lbl3.get_width() + 6

        self._rect_time = self._draw_dropdown(cx, 4, self.selected_time_label, self._open_time, active=True)

        hr_text = str(current_hr) if current_hr is not None else "--"
        avg_text = str(int(round(average_hr))) if average_hr is not None else "--"
        avg_label = self._font_bar.render(f"MEDIA: {avg_text}", True, Theme.TEXT_SOFT)
        bpm_label = self._font_bar.render(f"BPM: {hr_text}", True, Theme.TEXT)
        right_x = w - bpm_label.get_width() - 16
        avg_x = right_x - avg_label.get_width() - 16
        self.surface.blit(avg_label, (avg_x, BAR_H // 2 - avg_label.get_height() // 2))
        self.surface.blit(bpm_label, (right_x, BAR_H // 2 - bpm_label.get_height() // 2))

        indicator_x = avg_x - 8
        if show_stop:
            stop_surf = self._font_bar.render("STOP", True, HR_UP_COLOR)
            indicator_x -= stop_surf.get_width()
            self.surface.blit(
                stop_surf,
                (
                    indicator_x,
                    BAR_H // 2 - stop_surf.get_height() // 2,
                ),
            )
            indicator_x -= 10

        if hr_state != "normal":
            arrow = "\u2191" if hr_state == "high" else "\u2193"
            color = HR_UP_COLOR if hr_state == "high" else HR_DOWN_COLOR
            arrow_surf = self._font_bar.render(arrow, True, color)
            arrow_x = indicator_x - arrow_surf.get_width()
            arrow_y = BAR_H // 2 - arrow_surf.get_height() // 2
            self.surface.blit(arrow_surf, (arrow_x, arrow_y))
            self.surface.blit(arrow_surf, (arrow_x + 1, arrow_y))

    def draw_overlays(self):
        self._rects_eng_items = []
        self._rects_lvl_items = []
        self._rects_time_items = []

        if self._open_engine:
            self._rects_eng_items = self._draw_dropdown_list(self._rect_engine, ENGINE_NAMES, self.selected_engine)

        if self._open_level:
            self._rects_lvl_items = self._draw_dropdown_list(self._rect_level, LEVEL_NAMES, self.selected_level)

        if self._open_time:
            self._rects_time_items = self._draw_dropdown_list(self._rect_time, TIME_OPTIONS, self.selected_time_label)

    def _draw_dropdown(self, x: int, y: int, text: str, is_open: bool, active: bool = True) -> pygame.Rect:
        f = self._font_bar
        pad_x = 8
        arrow_w = 14
        text_w = f.size(text)[0]
        w = text_w + pad_x * 2 + arrow_w
        h = BAR_H - y * 2

        col_bg = Theme.BG_CARD
        col_brd = Theme.BG_SOFT
        col_txt = Theme.TEXT if active else Theme.TEXT_DIM

        rect = pygame.Rect(x, y, w, h)
        pygame.draw.rect(self.surface, col_bg, rect, border_radius=3)
        pygame.draw.rect(self.surface, col_brd, rect, 1, border_radius=3)

        s = f.render(text, True, col_txt)
        self.surface.blit(s, (x + pad_x, y + h // 2 - s.get_height() // 2))

        arrow = "\u25b2" if is_open else "\u25bc"
        af = pygame.font.SysFont("Tahoma", 9)
        ar = af.render(arrow, True, col_txt)
        self.surface.blit(ar, (x + w - arrow_w, y + h // 2 - ar.get_height() // 2))
        return rect

    def _draw_dropdown_list(self, anchor: pygame.Rect, items: list, selected) -> list:
        f = self._font_drop
        pad_x = 8
        item_h = 22
        labels = [item[0] if isinstance(item, tuple) else item for item in items]
        w = max(anchor.width, max(f.size(label)[0] for label in labels) + pad_x * 2)
        list_h = item_h * len(items)
        lx = anchor.x
        ly = anchor.bottom + 2

        bg_rect = pygame.Rect(lx, ly, w, list_h)
        pygame.draw.rect(self.surface, Theme.BG_CARD, bg_rect, border_radius=4)
        pygame.draw.rect(self.surface, Theme.BG_SOFT, bg_rect, 1, border_radius=4)

        rects = []
        for i, item in enumerate(items):
            label = item[0] if isinstance(item, tuple) else item
            iy = ly + i * item_h
            item_r = pygame.Rect(lx, iy, w, item_h)
            is_sel = label == selected

            if is_sel:
                pygame.draw.rect(self.surface, Theme.BG_CARD_ALT, item_r)

            col = Theme.GOLD_LT if is_sel else Theme.TEXT
            s = f.render(label, True, col)
            self.surface.blit(s, (lx + pad_x, iy + item_h // 2 - s.get_height() // 2))

            if i < len(items) - 1:
                pygame.draw.line(self.surface, Theme.BG_SOFT, (lx + 4, iy + item_h - 1), (lx + w - 4, iy + item_h - 1), 1)

            rects.append((item_r, item))

        return rects

    def _label_for_seconds(self, seconds: int) -> str:
        for label, value in TIME_OPTIONS:
            if value == seconds:
                return label
        return f"{seconds // 60} min"
