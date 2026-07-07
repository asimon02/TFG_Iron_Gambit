"""
top_bar.py -- Barra superior con indicadores de FC y acceso a ajustes

Muestra unicamente:
  - Indicador de estado del motor (dot)
  - Icono de ajustes (engranaje)
  - Datos de Frecuencia Cardiaca (BPM, media, flechas, STOP)
"""

import pygame
from typing import Optional

from theme  import Theme


# Opciones de tiempo (exportadas para settings_view)
TIME_OPTIONS = [
    ("1 min", 60),
    ("3 min", 3 * 60),
    ("5 min", 5 * 60),
    ("10 min", 10 * 60),
    ("15 min", 15 * 60),
    ("90 min", 90 * 60),
]

BAR_H = 36
HR_UP_COLOR = (210, 60, 60)
HR_DOWN_COLOR = (70, 185, 90)


class TopBar:
    """
    Barra superior con estado del motor, FC y acceso a ajustes.
    """

    def __init__(self, surface: pygame.Surface):
        self.surface = surface
        self.settings_clicked = False
        self._rect_settings = pygame.Rect(0, 0, 0, 0)
        self._font_bar = None

    def clear_flags(self):
        self.settings_clicked = False

    def handle_click(self, pos: tuple) -> bool:
        mx, my = pos
        if my < BAR_H:
            if self._rect_settings.collidepoint(mx, my):
                self.settings_clicked = True
                return True
            return True
        return False

    def handle_key(self, key: int):
        pass  # No hay desplegables que cerrar

    def draw(self, engine_ready: bool, current_hr: Optional[int] = None,
             average_hr: Optional[float] = None, hr_state: str = "normal",
             show_stop: bool = False):
        w = self.surface.get_width()

        if self._font_bar is None:
            self._font_bar = pygame.font.SysFont("Tahoma", 13, bold=True)

        pygame.draw.rect(self.surface, Theme.BG_PANEL, (0, 0, w, BAR_H))

        # --- Icono de ajustes (engranaje) en la esquina izquierda ---
        gear_size = BAR_H - 8
        gear_x = 6
        gear_y = 4
        self._rect_settings = pygame.Rect(gear_x, gear_y, gear_size, gear_size)
        mx_now, my_now = pygame.mouse.get_pos()
        gear_hovered = self._rect_settings.collidepoint(mx_now, my_now)
        gear_bg  = Theme.BG_CARD_ALT if gear_hovered else Theme.BG_CARD
        gear_brd = Theme.GOLD_LT if gear_hovered else Theme.BG_SOFT
        gear_txt = Theme.GOLD_LT if gear_hovered else Theme.STEEL_LT
        pygame.draw.rect(self.surface, gear_bg, self._rect_settings, border_radius=4)
        pygame.draw.rect(self.surface, gear_brd, self._rect_settings, 1, border_radius=4)
        gear_font = pygame.font.SysFont("Segoe UI Symbol", max(14, gear_size - 10))
        gear_surf = gear_font.render("\u2699", True, gear_txt)
        self.surface.blit(gear_surf, (
            gear_x + (gear_size - gear_surf.get_width()) // 2,
            gear_y + (gear_size - gear_surf.get_height()) // 2,
        ))

        # --- Datos de FC (extremo derecho) ---
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
            indicator_x = arrow_x - 4

    def draw_overlays(self):
        """No hay desplegables, metodo mantenido por compatibilidad."""
        pass
