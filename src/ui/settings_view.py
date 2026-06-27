"""
settings_view.py -- Pantalla completa de ajustes

Vista integral que reemplaza la pantalla de juego cuando esta activa.
Muestra las opciones de Motor, Nivel y Tiempo en tarjetas estilizadas
con el tema Kingambit.

No es un popup: ocupa toda la ventana como un cambio de vista
en una aplicacion movil.
"""

import pygame
from typing import Optional

from theme  import Theme
from layout import Layout
from font_manager import FontManager
from engine import LEVEL_NAMES
from top_bar import TIME_OPTIONS, BAR_H


class SettingsView:
    """
    Pantalla de ajustes a pantalla completa.

    Uso desde App:
        settings = SettingsView(screen, fonts, layout, {...})
        # En el bucle de eventos:
        result = settings.handle_click(pos)
        # En render:
        settings.draw(mouse_pos)
    """

    # Constantes de layout interno
    _CARD_PAD     = 20
    _CARD_GAP     = 16
    _OPTION_H     = 44
    _OPTION_GAP   = 10
    _BACK_W       = 140
    _BACK_H       = 38
    _HEADER_H     = 60

    def __init__(self, surface: pygame.Surface, fonts: FontManager,
                 layout: Layout, current_settings: dict):
        self.surface = surface
        self.fonts   = fonts
        self.layout  = layout

        # Texto del boton de retorno (contextual: "Jugar" al inicio, "Volver" en juego)
        self.back_label_text = "Volver"

        # Estado actual de los ajustes (copia local)
        self.selected_engine = current_settings.get("engine", "Stockfish")
        self.selected_level  = current_settings.get("level", "Intermedio")
        self.selected_time_label   = current_settings.get("time_label", "5 min")
        self.selected_time_seconds = current_settings.get("time_seconds", 300)
        self.selected_time_mode      = current_settings.get("time_mode", "Normal")
        self.selected_time_increment = current_settings.get("time_increment", 3)

        # Rects para deteccion de clics
        self._back_rect: Optional[pygame.Rect] = None
        self._level_rects: list[tuple[pygame.Rect, str]] = []
        self._time_rects: list[tuple[pygame.Rect, str, int]] = []
        self._lower_hr_rects: list[tuple[pygame.Rect, int]] = []
        self._upper_hr_rects: list[tuple[pygame.Rect, int]] = []
        self._time_mode_rects: list[tuple[pygame.Rect, str]] = []
        self._increment_rects: list[tuple[pygame.Rect, int]] = []
        self._hr_player_rects: list[tuple[pygame.Rect, str]] = []

        self.LOWER_HR_OPTIONS = [60, 70, 80, 90]
        self.UPPER_HR_OPTIONS = [90, 100, 110, 120]

        self.selected_lower_hr = current_settings.get("lower_hr", 70)
        self.selected_upper_hr = current_settings.get("upper_hr", 100)
        self._low_penalty_rects: list[tuple[pygame.Rect, int]] = []
        self.LOW_PENALTY_OPTIONS = [2, 3, 5, 10]
        self.selected_low_penalty = current_settings.get("low_penalty", 10)
        self.selected_hr_player = current_settings.get("hr_player", "white")
        self.selected_design = current_settings.get("design", "Kingambit")

        self.active_tab = "ajustes"
        self._tab1_rect = None
        self._tab2_rect = None
        self._design_rects: list[tuple[pygame.Rect, str]] = []

        # Fonts internas (se crean en el primer draw)
        self._font_header  = None
        self._font_tab     = None
        self._font_section = None
        self._font_option  = None
        self._font_back    = None
        self._font_info    = None

        # Scroll
        self._scroll_y = 0
        self._content_h = 0

    def update_layout(self, layout: Layout, fonts: FontManager):
        self.layout = layout
        self.fonts  = fonts
        # Forzar recreacion de fonts internas
        self._font_header = None

    def sync_settings(self, current_settings: dict):
        """Sincroniza los valores visibles con los ajustes actuales de la app."""
        self.selected_engine       = current_settings.get("engine", self.selected_engine)
        self.selected_level        = current_settings.get("level", self.selected_level)
        self.selected_time_label   = current_settings.get("time_label", self.selected_time_label)
        self.selected_time_seconds = current_settings.get("time_seconds", self.selected_time_seconds)
        self.selected_lower_hr     = current_settings.get("lower_hr", self.selected_lower_hr)
        self.selected_upper_hr       = current_settings.get("upper_hr", self.selected_upper_hr)
        self.selected_time_mode      = current_settings.get("time_mode", self.selected_time_mode)
        self.selected_time_increment = current_settings.get("time_increment", self.selected_time_increment)
        self.selected_low_penalty    = current_settings.get("low_penalty", self.selected_low_penalty)
        self.selected_hr_player      = current_settings.get("hr_player", self.selected_hr_player)
        self.selected_design         = current_settings.get("design", self.selected_design)

    def handle_click(self, pos: tuple) -> Optional[dict]:
        """
        Procesa un clic y devuelve un dict con el cambio, o None.
        """
        mx, my = pos

        # Clic en pestaña Ajustes
        if self._tab1_rect and self._tab1_rect.collidepoint(mx, my):
            if self.active_tab != "ajustes":
                self.active_tab = "ajustes"
                self._scroll_y = 0
            return None

        # Clic en pestaña Personalización
        if self._tab2_rect and self._tab2_rect.collidepoint(mx, my):
            if self.active_tab != "personalizacion":
                self.active_tab = "personalizacion"
                self._scroll_y = 0
            return None

        # Boton volver / jugar
        if self._back_rect and self._back_rect.collidepoint(mx, my):
            return {"action": "back"}

        if self.active_tab == "ajustes":
            # Opciones de nivel
            for rect, name in self._level_rects:
                if rect.collidepoint(mx, my):
                    if name != self.selected_level:
                        self.selected_level = name
                        return {"level": name}
                    return None

            # Opciones de tiempo
            for rect, label, seconds in self._time_rects:
                if rect.collidepoint(mx, my):
                    if label != self.selected_time_label:
                        self.selected_time_label   = label
                        self.selected_time_seconds = seconds
                        return {"time_label": label, "time_seconds": seconds}
                    return None

            # Opciones de pulsacion inferior
            for rect, val in self._lower_hr_rects:
                if rect.collidepoint(mx, my):
                    if val != self.selected_lower_hr:
                        self.selected_lower_hr = val
                        return {"lower_hr": val}
                    return None

            # Opciones de pulsacion superior
            for rect, val in self._upper_hr_rects:
                if rect.collidepoint(mx, my):
                    if val != self.selected_upper_hr:
                        self.selected_upper_hr = val
                        return {"upper_hr": val}
                    return None

            # Opciones de modo de juego/tiempo
            for rect, mode in self._time_mode_rects:
                if rect.collidepoint(mx, my):
                    if mode != self.selected_time_mode:
                        self.selected_time_mode = mode
                        return {"time_mode": mode}
                    return None

            # Opciones de incremento de tiempo
            for rect, val in self._increment_rects:
                if rect.collidepoint(mx, my):
                    if val != self.selected_time_increment:
                        self.selected_time_increment = val
                        return {"time_increment": val}
                    return None

            # Opciones de penalización por pulsación baja
            for rect, val in self._low_penalty_rects:
                if rect.collidepoint(mx, my):
                    if val != self.selected_low_penalty:
                        self.selected_low_penalty = val
                        return {"low_penalty": val}
                    return None

            # Opciones de Portador del Pulsómetro
            for rect, val in self._hr_player_rects:
                if rect.collidepoint(mx, my):
                    if val != self.selected_hr_player:
                        self.selected_hr_player = val
                        return {"hr_player": val}
                    return None

        elif self.active_tab == "personalizacion":
            # Opciones de diseño
            for rect, name in self._design_rects:
                if rect.collidepoint(mx, my):
                    if name != self.selected_design:
                        self.selected_design = name
                        return {"design": name}
                    return None

        return None

    def handle_key(self, key: int) -> bool:
        """Devuelve True si consume el evento (Escape = volver)."""
        if key == pygame.K_ESCAPE:
            return True  # App interpretara esto como "back"
        return False

    def handle_scroll(self, y: int):
        """Gestiona el scroll del raton."""
        self._scroll_y = max(0, self._scroll_y - y * 30)
        # Clampar al contenido disponible
        W, H = self.surface.get_size()
        max_scroll = max(0, self._content_h - (H - BAR_H - self._HEADER_H - 20))
        self._scroll_y = min(self._scroll_y, max_scroll)

    def draw(self, mouse_pos: tuple, engine_ready: bool = True):
        """Dibuja la pantalla completa de ajustes."""
        W, H = self.surface.get_size()
        mx, my = mouse_pos if mouse_pos else (0, 0)

        self._ensure_fonts()
        self._level_rects = []
        self._time_rects  = []
        self._lower_hr_rects = []
        self._upper_hr_rects = []
        self._time_mode_rects = []
        self._increment_rects = []
        self._low_penalty_rects = []
        self._hr_player_rects = []
        self._design_rects = []

        # --- Fondo completo ---
        self.surface.fill(Theme.BG)

        # Calcular ancho de las tarjetas
        card_max_w = min(600, W - 60)
        card_x = (W - card_max_w) // 2

        # --- Area de contenido ---
        content_top = BAR_H + self._HEADER_H + 16

        if self.active_tab == "ajustes":
            cy = content_top - self._scroll_y

            # ===================================================================
            # PRIMERA PASADA: calcular posiciones y dibujar tarjetas de fondo
            # ===================================================================

            # --- TARJETA: Motor ---
            motor_section_y = cy
            cy = self._advance_section_header(cy)
            motor_card_top = cy
            cy += self._CARD_PAD
            cy += 34  # info del motor
            motor_card_h = cy - motor_card_top + self._CARD_PAD
            cy = motor_card_top + motor_card_h
            self._draw_card_bg(card_x, motor_card_top, card_max_w, motor_card_h)

            # --- TARJETA: Nivel ---
            cy += self._CARD_GAP
            level_section_y = cy
            cy = self._advance_section_header(cy)
            level_card_top = cy
            cy += self._CARD_PAD
            level_items_y = cy
            for _ in LEVEL_NAMES:
                cy += self._OPTION_H + self._OPTION_GAP
            cy -= self._OPTION_GAP
            cy += self._CARD_PAD // 2
            level_card_h = cy - level_card_top + self._CARD_PAD
            cy = level_card_top + level_card_h
            self._draw_card_bg(card_x, level_card_top, card_max_w, level_card_h)

            # --- TARJETA: Tiempo ---
            cy += self._CARD_GAP
            time_section_y = cy
            cy = self._advance_section_header(cy)
            time_card_top = cy
            cy += self._CARD_PAD
            time_items_y = cy
            for _ in TIME_OPTIONS:
                cy += self._OPTION_H + self._OPTION_GAP
            cy -= self._OPTION_GAP
            cy += self._CARD_PAD // 2
            time_card_h = cy - time_card_top + self._CARD_PAD
            cy = time_card_top + time_card_h
            self._draw_card_bg(card_x, time_card_top, card_max_w, time_card_h)

            # --- TARJETA: Modo de juego (Normal / Incremento y segundos de incremento) ---
            cy += self._CARD_GAP
            mode_section_y = cy
            cy = self._advance_section_header(cy)
            mode_card_top = cy
            cy += self._CARD_PAD

            # Subsección: Modo
            mode_y = cy
            cy += 20 + self._OPTION_H

            # Subsección: Incremento
            cy += 16
            increment_y = cy
            cy += 20 + self._OPTION_H

            cy += self._CARD_PAD // 2
            mode_card_h = cy - mode_card_top + self._CARD_PAD
            cy = mode_card_top + mode_card_h
            self._draw_card_bg(card_x, mode_card_top, card_max_w, mode_card_h)

            # --- TARJETA: Umbrales de FC ---
            cy += self._CARD_GAP
            hr_section_y = cy
            cy = self._advance_section_header(cy)
            hr_card_top = cy
            cy += self._CARD_PAD
            
            # Subsección: Pulsación Inferior
            lower_hr_y = cy
            cy += 20 + self._OPTION_H
            
            # Subsección: Pulsación Superior
            cy += 16
            upper_hr_y = cy
            cy += 20 + self._OPTION_H

            # Subsección: Penalización por Pulsación Baja
            cy += 16
            low_penalty_y = cy
            cy += 20 + self._OPTION_H
            
            # Subsección: Portador del Pulsómetro
            cy += 16
            hr_player_y = cy
            cy += 20 + self._OPTION_H
            
            cy += self._CARD_PAD // 2
            hr_card_h = cy - hr_card_top + self._CARD_PAD
            cy = hr_card_top + hr_card_h
            self._draw_card_bg(card_x, hr_card_top, card_max_w, hr_card_h)

            # Guardar altura total del contenido para scroll
            self._content_h = cy - content_top + self._scroll_y + 16

            # ===================================================================
            # SEGUNDA PASADA: dibujar contenido sobre las tarjetas
            # ===================================================================

            # --- Header de seccion: Motor ---
            self._draw_section_header(motor_section_y, card_x, card_max_w, "MOTOR DE AJEDREZ")

            # Contenido Motor
            info_y = motor_card_top + self._CARD_PAD
            status_color = Theme.GOLD_LT if engine_ready else Theme.CRIMSON_LT
            status_text  = "Conectado" if engine_ready else "No disponible"
            dot_y_pos = info_y + 11
            pygame.draw.circle(self.surface, status_color, (card_x + self._CARD_PAD + 6, dot_y_pos), 5)
            engine_label = self._font_option.render(
                f"  {self.selected_engine}  \u2014  {status_text}", True, Theme.TEXT)
            self.surface.blit(engine_label, (card_x + self._CARD_PAD + 16, info_y + 4))

            # --- Header de seccion: Nivel ---
            self._draw_section_header(level_section_y, card_x, card_max_w, "NIVEL DE DIFICULTAD")

            # Opciones de Nivel
            oy = level_items_y
            for name in LEVEL_NAMES:
                opt_rect = pygame.Rect(
                    card_x + self._CARD_PAD, oy,
                    card_max_w - self._CARD_PAD * 2, self._OPTION_H)
                is_selected = (name == self.selected_level)
                hovered = opt_rect.collidepoint(mx, my)
                self._draw_option(opt_rect, name, is_selected, hovered)
                self._level_rects.append((opt_rect, name))
                oy += self._OPTION_H + self._OPTION_GAP

            # --- Header de seccion: Tiempo ---
            self._draw_section_header(time_section_y, card_x, card_max_w, "TIEMPO DE RELOJ")

            # Opciones de Tiempo
            oy = time_items_y
            for label, seconds in TIME_OPTIONS:
                opt_rect = pygame.Rect(
                    card_x + self._CARD_PAD, oy,
                    card_max_w - self._CARD_PAD * 2, self._OPTION_H)
                is_selected = (label == self.selected_time_label)
                hovered = opt_rect.collidepoint(mx, my)
                self._draw_option(opt_rect, label, is_selected, hovered)
                self._time_rects.append((opt_rect, label, seconds))
                oy += self._OPTION_H + self._OPTION_GAP

            # --- Header de seccion: Modo de juego ---
            self._draw_section_header(mode_section_y, card_x, card_max_w, "MODO DE JUEGO")

            # Opciones de Modo
            self._draw_horizontal_options_generic(
                "Modo de Tiempo:",
                ["Normal", "Incremento"],
                self.selected_time_mode,
                mode_y,
                card_x,
                card_max_w,
                mx,
                my,
                self._time_mode_rects,
                lambda v: v
            )

            # Opciones de Incremento de Tiempo (solo activas si el modo es "Incremento")
            increment_enabled = (self.selected_time_mode == "Incremento")
            self._draw_horizontal_options_generic(
                "Incremento por Jugada:",
                [1, 2, 3, 5, 10],
                self.selected_time_increment,
                increment_y,
                card_x,
                card_max_w,
                mx,
                my,
                self._increment_rects,
                lambda v: f"{v} s",
                enabled=increment_enabled
            )

            # --- Header de seccion: Frecuencia Cardíaca ---
            self._draw_section_header(hr_section_y, card_x, card_max_w, "UMBRALES DE FRECUENCIA CARDÍACA")

            # Opciones de Pulsación Inferior
            self._draw_horizontal_options(
                "Pulsación Inferior:",
                self.LOWER_HR_OPTIONS,
                self.selected_lower_hr,
                lower_hr_y,
                card_x,
                card_max_w,
                mx,
                my,
                self._lower_hr_rects
            )

            # Opciones de Pulsación Superior
            self._draw_horizontal_options(
                "Pulsación Superior:",
                self.UPPER_HR_OPTIONS,
                self.selected_upper_hr,
                upper_hr_y,
                card_x,
                card_max_w,
                mx,
                my,
                self._upper_hr_rects
            )

            # Opciones de Penalización por Pulsación Baja
            self._draw_horizontal_options_generic(
                "Penalización por Pulsación Baja:",
                self.LOW_PENALTY_OPTIONS,
                self.selected_low_penalty,
                low_penalty_y,
                card_x,
                card_max_w,
                mx,
                my,
                self._low_penalty_rects,
                lambda v: f"-{v} s"
            )

            # Opciones de Portador del Pulsómetro
            self._draw_horizontal_options_generic(
                "Portador del Pulsómetro:",
                ["white", "black"],
                self.selected_hr_player,
                hr_player_y,
                card_x,
                card_max_w,
                mx,
                my,
                self._hr_player_rects,
                lambda v: "Blancas" if v == "white" else "Negras"
            )

        elif self.active_tab == "personalizacion":
            cy = content_top - self._scroll_y

            # ===================================================================
            # PRIMERA PASADA: calcular posiciones y dibujar tarjetas de fondo
            # ===================================================================

            design_section_y = cy
            cy = self._advance_section_header(cy)
            design_card_top = cy
            cy += self._CARD_PAD
            design_items_y = cy

            designs = ["Kingambit", "Verano", "Otoño", "Invierno", "Primavera"]
            opt_h = 58
            opt_gap = 12

            for _ in designs:
                cy += opt_h + opt_gap
            cy -= opt_gap
            cy += self._CARD_PAD // 2
            design_card_h = cy - design_card_top + self._CARD_PAD
            cy = design_card_top + design_card_h
            self._draw_card_bg(card_x, design_card_top, card_max_w, design_card_h)

            # Guardar altura total del contenido para scroll
            self._content_h = cy - content_top + self._scroll_y + 16

            # ===================================================================
            # SEGUNDA PASADA: dibujar contenido sobre las tarjetas
            # ===================================================================
            self._draw_section_header(design_section_y, card_x, card_max_w, "DISEÑOS DE TABLERO Y PIEZAS")

            oy = design_items_y
            for name in designs:
                opt_rect = pygame.Rect(
                    card_x + self._CARD_PAD, oy,
                    card_max_w - self._CARD_PAD * 2, opt_h)
                is_selected = (name == self.selected_design)
                hovered = opt_rect.collidepoint(mx, my)

                colors = Theme.THEMES.get(name, Theme.THEMES["Kingambit"])
                self._draw_design_option(opt_rect, f"Diseño {name}", colors, is_selected, hovered)

                self._design_rects.append((opt_rect, name))
                oy += opt_h + opt_gap

        # ===================================================================
        # CABECERA (se dibuja al final para quedar por encima del scroll)
        # ===================================================================
        header_rect = pygame.Rect(0, 0, W, BAR_H + self._HEADER_H)
        pygame.draw.rect(self.surface, Theme.BG_PANEL, header_rect)
        # Linea decorativa inferior
        pygame.draw.line(self.surface, Theme.GOLD,
                         (0, header_rect.bottom - 1),
                         (W, header_rect.bottom - 1), 2)
        pygame.draw.line(self.surface, Theme.CRIMSON_DIM,
                         (0, header_rect.bottom + 1),
                         (W, header_rect.bottom + 1), 1)

        # Boton "Volver" / "Jugar" (contextual)
        back_x = 20
        back_y = BAR_H + (self._HEADER_H - self._BACK_H) // 2
        self._back_rect = pygame.Rect(back_x, back_y, self._BACK_W, self._BACK_H)
        back_hovered = self._back_rect.collidepoint(mx, my)

        back_bg  = Theme.GOLD if back_hovered else Theme.BG_CARD
        back_brd = Theme.GOLD_LT if back_hovered else Theme.STEEL
        back_txt = Theme.PIECE_BLACK if back_hovered else Theme.GOLD_LT
        pygame.draw.rect(self.surface, back_bg, self._back_rect, border_radius=5)
        pygame.draw.rect(self.surface, back_brd, self._back_rect, 1, border_radius=5)
        back_label = self._font_back.render(self.back_label_text, True, back_txt)
        self.surface.blit(back_label, (
            self._back_rect.x + (self._back_rect.w - back_label.get_width()) // 2,
            self._back_rect.y + (self._back_rect.h - back_label.get_height()) // 2,
        ))

        # Pestañas en el centro
        tab1_surf = self._font_tab.render("AJUSTES", True, Theme.GOLD_LT if self.active_tab == "ajustes" else Theme.TEXT_SOFT)
        tab2_surf = self._font_tab.render("PERSONALIZACIÓN", True, Theme.GOLD_LT if self.active_tab == "personalizacion" else Theme.TEXT_SOFT)
        
        tab_gap = 40
        total_tab_w = tab1_surf.get_width() + tab_gap + tab2_surf.get_width()
        tab_start_x = (W - total_tab_w) // 2
        tab_y = BAR_H + (self._HEADER_H - tab1_surf.get_height()) // 2
        
        self._tab1_rect = pygame.Rect(tab_start_x - 12, BAR_H + 6, tab1_surf.get_width() + 24, self._HEADER_H - 12)
        self._tab2_rect = pygame.Rect(tab_start_x + tab1_surf.get_width() + tab_gap - 12, BAR_H + 6, tab2_surf.get_width() + 24, self._HEADER_H - 12)
        
        # Hover effect
        tab1_hover = self._tab1_rect.collidepoint(mx, my)
        tab2_hover = self._tab2_rect.collidepoint(mx, my)
        
        if tab1_hover and self.active_tab != "ajustes":
            tab1_surf = self._font_tab.render("AJUSTES", True, Theme.TEXT)
        if tab2_hover and self.active_tab != "personalizacion":
            tab2_surf = self._font_tab.render("PERSONALIZACIÓN", True, Theme.TEXT)
            
        self.surface.blit(tab1_surf, (tab_start_x, tab_y))
        self.surface.blit(tab2_surf, (tab_start_x + tab1_surf.get_width() + tab_gap, tab_y))
        
        # Underline bar
        if self.active_tab == "ajustes":
            underline_rect = pygame.Rect(tab_start_x, BAR_H + self._HEADER_H - 4, tab1_surf.get_width(), 4)
        else:
            underline_rect = pygame.Rect(tab_start_x + tab1_surf.get_width() + tab_gap, BAR_H + self._HEADER_H - 4, tab2_surf.get_width(), 4)
        pygame.draw.rect(self.surface, Theme.GOLD, underline_rect, border_radius=2)

    def _draw_horizontal_options(self, title: str, options: list, selected_val: int, y: int, card_x: int, card_max_w: int, mx: int, my: int, rects_list: list):
        """Dibuja una subsección con opciones horizontales en pastillas y añade los rects de clic."""
        self._draw_horizontal_options_generic(
            title, options, selected_val, y, card_x, card_max_w, mx, my, rects_list,
            lambda v: f"{v} BPM", enabled=True
        )

    def _draw_option_pill(self, rect: pygame.Rect, text: str, is_selected: bool, hovered: bool):
        """Dibuja una opción en formato pastilla centrada (sin círculo de radio)."""
        self._draw_option_pill_generic(rect, text, is_selected, hovered, enabled=True)

    def _draw_horizontal_options_generic(self, title: str, options: list, selected_val, y: int, card_x: int, card_max_w: int, mx: int, my: int, rects_list: list, label_fn, enabled: bool = True):
        """Dibuja una subsección con opciones horizontales en pastillas y añade los rects de clic."""
        title_color = Theme.TEXT_SOFT if enabled else Theme.TEXT_DIM
        lbl = self.fonts.small.render(title, True, title_color)
        self.surface.blit(lbl, (card_x + self._CARD_PAD, y))
        y += lbl.get_height() + 8

        opt_h = self._OPTION_H
        gap = 8
        avail_w = card_max_w - self._CARD_PAD * 2
        num_opts = len(options)
        opt_w = (avail_w - (num_opts - 1) * gap) // num_opts

        ox = card_x + self._CARD_PAD
        for val in options:
            opt_rect = pygame.Rect(ox, y, opt_w, opt_h)
            is_selected = (val == selected_val)
            hovered = opt_rect.collidepoint(mx, my) if enabled else False
            self._draw_option_pill_generic(opt_rect, label_fn(val), is_selected, hovered, enabled)
            if enabled:
                rects_list.append((opt_rect, val))
            ox += opt_w + gap

    def _draw_option_pill_generic(self, rect: pygame.Rect, text: str, is_selected: bool, hovered: bool, enabled: bool = True):
        """Dibuja una opción en formato pastilla centrada (sin círculo de radio)."""
        if not enabled:
            bg  = Theme.BG_PANEL
            brd = Theme.BG_SOFT
            txt = Theme.TEXT_DIM
        elif is_selected:
            bg  = Theme.BG_CARD_ALT
            brd = Theme.GOLD
            txt = Theme.GOLD_LT
        elif hovered:
            bg  = Theme.BG_CARD
            brd = Theme.STEEL_LT
            txt = Theme.TEXT
        else:
            bg  = Theme.BG_PANEL
            brd = Theme.BG_SOFT
            txt = Theme.TEXT_SOFT

        pygame.draw.rect(self.surface, bg, rect, border_radius=4)
        pygame.draw.rect(self.surface, brd, rect, 1, border_radius=4)

        if is_selected and enabled:
            bar_rect = pygame.Rect(rect.x + 8, rect.bottom - 3, rect.w - 16, 2)
            pygame.draw.rect(self.surface, Theme.GOLD, bar_rect, border_radius=1)

        label = self._font_option.render(text, True, txt)
        self.surface.blit(label, (
            rect.x + (rect.w - label.get_width()) // 2,
            rect.y + (rect.h - label.get_height()) // 2,
        ))

    # -- Helpers internos de dibujo -------------------------------------------

    def _ensure_fonts(self):
        """Crea las fuentes internas si aun no existen."""
        if self._font_header is not None:
            return
        self._font_header  = pygame.font.SysFont("Segoe UI", 24, bold=True)
        self._font_tab     = pygame.font.SysFont("Segoe UI", 16, bold=True)
        self._font_section = pygame.font.SysFont("Tahoma",   13, bold=True)
        self._font_option  = pygame.font.SysFont("Tahoma",   13)
        self._font_back    = pygame.font.SysFont("Tahoma",   13, bold=True)
        self._font_info    = pygame.font.SysFont("Tahoma",   11)

    def _advance_section_header(self, y: int) -> int:
        """Avanza la y lo que ocupa un header de seccion (sin dibujar)."""
        h = self._font_section.get_height()
        return y + h + 6

    def _draw_section_header(self, y: int, x: int, w: int, title: str):
        """Dibuja el titulo de una seccion."""
        label = self._font_section.render(title, True, Theme.GOLD)
        self.surface.blit(label, (x + 4, y))

    def _draw_card_bg(self, x: int, y: int, w: int, h: int):
        """Dibuja el fondo de una tarjeta."""
        card_rect = pygame.Rect(x, y, w, h)
        pygame.draw.rect(self.surface, Theme.BG_PANEL, card_rect, border_radius=6)
        pygame.draw.rect(self.surface, Theme.BG_SOFT, card_rect, 1, border_radius=6)

    def _draw_option(self, rect: pygame.Rect, text: str,
                     is_selected: bool, hovered: bool):
        """Dibuja una opcion seleccionable con hover/seleccion."""
        if is_selected:
            bg  = Theme.BG_CARD_ALT
            brd = Theme.GOLD
            txt = Theme.GOLD_LT
        elif hovered:
            bg  = Theme.BG_CARD
            brd = Theme.STEEL_LT
            txt = Theme.TEXT
        else:
            bg  = Theme.BG_PANEL
            brd = Theme.BG_SOFT
            txt = Theme.TEXT_SOFT

        pygame.draw.rect(self.surface, bg, rect, border_radius=4)
        pygame.draw.rect(self.surface, brd, rect, 1, border_radius=4)

        # Barra lateral dorada de seleccion
        if is_selected:
            bar_rect = pygame.Rect(rect.x, rect.y + 4, 3, rect.h - 8)
            pygame.draw.rect(self.surface, Theme.GOLD, bar_rect, border_radius=2)

        # Indicador de seleccion (circulo tipo radio button)
        indicator_x = rect.x + 18
        indicator_y = rect.y + rect.h // 2
        if is_selected:
            pygame.draw.circle(self.surface, Theme.GOLD, (indicator_x, indicator_y), 7)
            pygame.draw.circle(self.surface, Theme.BG_PANEL, (indicator_x, indicator_y), 3)
        else:
            pygame.draw.circle(self.surface, brd, (indicator_x, indicator_y), 7, 1)

        label = self._font_option.render(text, True, txt)
        self.surface.blit(label, (
            rect.x + 36,
            rect.y + (rect.h - label.get_height()) // 2,
        ))

    def _draw_design_option(self, rect: pygame.Rect, name: str, colors: dict,
                            is_selected: bool, hovered: bool):
        if is_selected:
            bg  = Theme.BG_CARD_ALT
            brd = Theme.GOLD
            txt = Theme.GOLD_LT
        elif hovered:
            bg  = Theme.BG_CARD
            brd = Theme.STEEL_LT
            txt = Theme.TEXT
        else:
            bg  = Theme.BG_PANEL
            brd = Theme.BG_SOFT
            txt = Theme.TEXT_SOFT

        pygame.draw.rect(self.surface, bg, rect, border_radius=6)
        pygame.draw.rect(self.surface, brd, rect, 1, border_radius=6)

        if is_selected:
            bar_rect = pygame.Rect(rect.x, rect.y + 4, 3, rect.h - 8)
            pygame.draw.rect(self.surface, Theme.GOLD, bar_rect, border_radius=2)

        # Radio indicator
        indicator_x = rect.x + 20
        indicator_y = rect.y + rect.h // 2
        if is_selected:
            pygame.draw.circle(self.surface, Theme.GOLD, (indicator_x, indicator_y), 7)
            pygame.draw.circle(self.surface, Theme.BG_PANEL, (indicator_x, indicator_y), 3)
        else:
            pygame.draw.circle(self.surface, brd, (indicator_x, indicator_y), 7, 1)

        # Text label
        label = self._font_option.render(name, True, txt)
        self.surface.blit(label, (rect.x + 38, rect.y + (rect.h - label.get_height()) // 2))

        # Color preview circle row
        circle_r = 10
        circle_gap = 6
        colors_to_show = [
            colors["SQ_LIGHT"],
            colors["SQ_DARK"],
            colors["PIECE_WHITE"],
            colors["PIECE_BLACK"]
        ]
        
        # Pill background
        pill_w = len(colors_to_show) * (circle_r * 2) + (len(colors_to_show) - 1) * circle_gap + 16
        pill_h = circle_r * 2 + 10
        pill_x = rect.right - pill_w - 16
        pill_y = rect.y + (rect.h - pill_h) // 2
        pygame.draw.rect(self.surface, Theme.BG_PANEL if not hovered and not is_selected else Theme.BG_CARD_ALT, (pill_x, pill_y, pill_w, pill_h), border_radius=12)
        
        cx = pill_x + 8 + circle_r
        cy = pill_y + pill_h // 2
        for col in colors_to_show:
            pygame.draw.circle(self.surface, col, (cx, cy), circle_r)
            # Add subtle border to circles if too bright
            if sum(col) / 3 > 200:
                pygame.draw.circle(self.surface, Theme.BG_SOFT, (cx, cy), circle_r, 1)
            cx += circle_r * 2 + circle_gap
