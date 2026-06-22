"""
panel_renderer.py -- Dibuja el panel lateral de informacion

Secciones:
  - Titulo "IRON GAMBIT" y subtitulo
  - Relojes de ambos jugadores
  - Piezas capturadas
  - Historial de movimientos con scrollbar
  - Controles de teclado
"""

import pygame
import chess

from theme        import Theme
from layout       import Layout
from font_manager import FontManager
from game_state   import GameState

class PanelRenderer:
    """
    Dibuja el panel lateral derecho con reloj, capturas e historial.
    """

    def __init__(self, surface: pygame.Surface,
                 fonts: FontManager, layout: Layout):
        self.surface        = surface
        self.fonts          = fonts
        self.layout         = layout
        self._scroll_offset = 0
        self.move_rects     = []

    def update_layout(self, layout: Layout, fonts: FontManager):
        self.layout = layout
        self.fonts  = fonts

    def handle_scroll(self, delta: int):
        self._scroll_offset = max(0, self._scroll_offset + delta)

    def draw(self, gs: GameState, clock_times: dict, active_color: chess.Color,
             white_clock: str, black_clock: str):
        L  = self.layout
        px = L.px
        pw = L.pw

        pygame.draw.rect(
            self.surface,
            Theme.BG_PANEL,
            (px - 6, L.py - 4, pw + 10, L.ph + 8),
            border_radius=6,
        )

        y = L.py + 14
        y = self._draw_title(px, y)
        y = self._divider(px, y, pw) + 12

        y = self._draw_clocks(px, y, pw, active_color, white_clock, black_clock) + 10
        y = self._divider(px, y, pw) + 10

        y = self._draw_captured(px, y, pw, gs)
        y = self._divider(px, y, pw) + 10

        controls_h  = self._controls_height()
        hist_bottom = L.py + L.ph - controls_h - 14
        self._draw_history(px, y, pw, hist_bottom, gs)

        self._divider(px, hist_bottom, pw)
        self._draw_controls(px, hist_bottom + 10)

    def _draw_title(self, x: int, y: int) -> int:
        f = self.fonts
        t1 = f.title.render("IRON", True, Theme.GOLD_LT)
        t2 = f.title.render("GAMBIT", True, Theme.TEXT)
        self.surface.blit(t1, (x, y))
        self.surface.blit(t2, (x + t1.get_width() + 6, y))
        y += max(t1.get_height(), t2.get_height()) + 4

        sub = f.small.render("Otra forma de aprender ajedrez", True, Theme.TEXT_SOFT)
        self.surface.blit(sub, (x, y))
        return y + sub.get_height() + 4

    def _draw_clocks(self, x: int, y: int, w: int, active_color: chess.Color,
                     white_clock: str, black_clock: str) -> int:
        self._section_header(x, y, "RELOJ")
        y += self.fonts.heading.get_height() + 8

        card_h = max(44, self.fonts.title.get_height() + 18)
        gap = 10
        card_w = (w - gap) // 2

        white_rect = pygame.Rect(x, y, card_w, card_h)
        black_rect = pygame.Rect(x + card_w + gap, y, card_w, card_h)

        self._draw_clock_card(
            white_rect,
            "BLANCAS",
            white_clock,
            Theme.PIECE_WHITE,
            Theme.PIECE_BLACK,
            active_color == chess.WHITE,
        )
        self._draw_clock_card(
            black_rect,
            "NEGRAS",
            black_clock,
            Theme.PIECE_BLACK,
            Theme.PIECE_WHITE,
            active_color == chess.BLACK,
        )

        return y + card_h

    def _draw_clock_card(self, rect: pygame.Rect, label: str, value: str,
                         bg: tuple, fg: tuple, active: bool):
        pygame.draw.rect(self.surface, bg, rect, border_radius=5)
        pygame.draw.rect(self.surface, Theme.GOLD_LT if active else Theme.BG_SOFT, rect, 2 if active else 1, border_radius=5)

        label_surf = self.fonts.small.render(label, True, fg)
        value_surf = self.fonts.title.render(value, True, fg)
        self.surface.blit(label_surf, (rect.x + 10, rect.y + 6))
        self.surface.blit(
            value_surf,
            (
                rect.x + (rect.width - value_surf.get_width()) // 2,
                rect.y + rect.height - value_surf.get_height() - 5,
            ),
        )

    def _draw_captured(self, x: int, y: int, w: int, gs: GameState) -> int:
        f = self.fonts
        cap_w, cap_b = gs.captured_pieces()
        self._section_header(x, y, "CAPTURADAS")
        y += f.heading.get_height() + 8

        icon_sz = max(14, min(22, w // 10))
        piece_font = pygame.font.SysFont("Segoe UI Symbol", icon_sz)
        block_w = w - 4

        for label, caps, piece_col, shadow_col, block_bg in [
            ("Blancas:", cap_b, Theme.PIECE_WHITE, Theme.SHADOW_WHITE, Theme.BG_CARD),
            ("Negras:",  cap_w, Theme.PIECE_BLACK, Theme.SHADOW_BLACK, Theme.BG_CAPTURED_BLACK),
        ]:
            lbl = f.small.render(label, True, Theme.TEXT_SOFT)
            self.surface.blit(lbl, (x, y))
            y += lbl.get_height() + 3

            if not caps:
                dash_h = f.small.get_height() + 12
                dash_rect = pygame.Rect(x, y, block_w, dash_h)
                pygame.draw.rect(self.surface, block_bg, dash_rect, border_radius=4)
                dash = f.small.render("--", True, Theme.TEXT_DIM)
                self.surface.blit(dash, (dash_rect.x + 10, dash_rect.y + (dash_rect.height - dash.get_height()) // 2))
                y += dash_rect.height + 6
                continue

            pieces_per_row = max(1, block_w // max(18, icon_sz))
            rows = max(1, (len(caps) + pieces_per_row - 1) // pieces_per_row)
            row_h = icon_sz + 2
            block_h = rows * row_h + 12
            block_rect = pygame.Rect(x, y, block_w, block_h)
            pygame.draw.rect(self.surface, block_bg, block_rect, border_radius=4)

            cx = block_rect.x + 10
            cy = block_rect.y + 6
            max_x = block_rect.right - 10
            for sym in caps:
                glyph = Theme.PIECES.get(sym, sym)
                sh_surf = piece_font.render(glyph, True, shadow_col)
                self.surface.blit(sh_surf, (cx + 1, cy + 1))
                pc_surf = piece_font.render(glyph, True, piece_col)
                self.surface.blit(pc_surf, (cx, cy))
                cx += pc_surf.get_width() + 2
                if cx + icon_sz > max_x:
                    cx = block_rect.x + 10
                    cy += row_h
            y += block_rect.height + 6

        return y

    def _san_to_icon(self, san: str) -> tuple[str, str]:
        piece_icons = {
            "N": "\u265e", "B": "\u265d", "R": "\u265c", "Q": "\u265b", "K": "\u265a",
        }
        if san and san[0] in piece_icons:
            return piece_icons[san[0]], san[1:]
        return "", san

    def _draw_move_cell(self, san: str, is_white: bool,
                        cx: int, cy: int, row_h: int,
                        highlight: bool):
        if not san:
            return

        f = self.fonts
        icon, rest = self._san_to_icon(san)

        if highlight:
            text_col = Theme.GOLD_LT
            icon_col = Theme.GOLD_LT
        else:
            text_col = Theme.TEXT
            icon_col = Theme.PIECE_WHITE if is_white else Theme.TEXT_SOFT

        draw_x = cx + 5
        draw_y = cy + (row_h - f.hist_move.get_height()) // 2

        if icon:
            icon_surf = f.hist_icon.render(icon, True, icon_col)
            icon_y = cy + (row_h - icon_surf.get_height()) // 2
            self.surface.blit(icon_surf, (draw_x, icon_y))
            draw_x += icon_surf.get_width() + 2

        move_surf = f.hist_move.render(rest, True, text_col)
        self.surface.blit(move_surf, (draw_x, draw_y))

    def _draw_history(self, x: int, y: int, w: int,
                      bottom: int, gs: GameState) -> int:
        f = self.fonts
        sans = gs.san_history

        self._section_header(x, y, "HISTORIAL")
        y += f.heading.get_height() + 8

        sb_w = 5
        sb_gap = 4
        tbl_w = w - sb_w - sb_gap
        num_w = max(22, f.hist_move.size("99.")[0] + 6)
        col_w = (tbl_w - num_w - 4) // 2
        row_h = f.hist_move.get_height() + 8
        area_h = bottom - y
        max_vis = max(1, area_h // row_h)

        total_pairs = (len(sans) + 1) // 2
        max_scroll = max(0, total_pairs - max_vis)
        scroll = max(0, min(self._scroll_offset, max_scroll))
        self._scroll_offset = scroll

        first_pair = max(0, total_pairs - max_vis - scroll)
        rows_drawn = min(max_vis, total_pairs - first_pair)

        div_x1 = x + num_w + 2
        div_x2 = div_x1 + col_w + 2
        table_h = rows_drawn * row_h
        highlighted_idx = gs.view_move_idx if gs.view_move_idx is not None else (len(sans) - 1)
        self.move_rects = []

        for pair_offset in range(rows_drawn):
            pair_num = first_pair + pair_offset
            idx_w = pair_num * 2
            idx_b = idx_w + 1
            ry = y + pair_offset * row_h

            row_bg = Theme.BG_CARD if pair_num % 2 == 0 else Theme.BG_CARD_ALT
            pygame.draw.rect(self.surface, row_bg, (x, ry, tbl_w, row_h), border_radius=3)

            if highlighted_idx in (idx_w, idx_b):
                pygame.draw.rect(
                    self.surface,
                    Theme.CRIMSON_LT,
                    (x, ry, 2, row_h),
                    border_top_left_radius=3,
                    border_bottom_left_radius=3,
                )

            num_str = f"{pair_num + 1}."
            num_surf = f.hist_move.render(num_str, True, Theme.TEXT_DIM)
            self.surface.blit(
                num_surf,
                (x + num_w - num_surf.get_width() - 3,
                 ry + (row_h - num_surf.get_height()) // 2),
            )

            if idx_w < len(sans):
                w_rect = pygame.Rect(div_x1, ry, col_w, row_h)
                self.move_rects.append((w_rect, idx_w))
                self._draw_move_cell(sans[idx_w], True, div_x1 + 2, ry, row_h, idx_w == highlighted_idx)
            if idx_b < len(sans):
                b_rect = pygame.Rect(div_x2, ry, col_w, row_h)
                self.move_rects.append((b_rect, idx_b))
                self._draw_move_cell(sans[idx_b], False, div_x2 + 2, ry, row_h, idx_b == highlighted_idx)


        sb_x = x + tbl_w + sb_gap
        sb_y = y
        sb_h = area_h
        pygame.draw.rect(self.surface, Theme.BG_SOFT, (sb_x, sb_y, sb_w, sb_h), border_radius=3)

        if total_pairs > max_vis:
            thumb_h = max(14, int(sb_h * max_vis / total_pairs))
            scroll_ratio = scroll / max_scroll if max_scroll > 0 else 0
            thumb_y = sb_y + int((sb_h - thumb_h) * (1.0 - scroll_ratio))
            pygame.draw.rect(self.surface, Theme.TEXT_SOFT, (sb_x, thumb_y, sb_w, thumb_h), border_radius=3)

        return y + table_h

    def _draw_controls(self, x: int, y: int):
        f = self.fonts
        pw = self.layout.pw
        keys = [
            ("N",   "Nueva partida"),
            ("Z",   "Deshacer"),
            ("R",   "Rotar tablero"),
            ("A",   "Ajustes"),
            ("P",   "Personalizar"),
            ("F11", "Pantalla completa"),
        ]
        
        col2_offset = max(140, pw // 2)
        kh = f.key.get_height() + 4
        
        for i in range(3):
            ry = y + i * (kh + 7)
            
            # Columna 1
            k1, d1 = keys[i]
            ks1 = f.key.render(" " + k1 + " ", True, Theme.TEXT)
            kw1 = ks1.get_width() + 6
            pygame.draw.rect(self.surface, Theme.BG_CARD, (x, ry, kw1, kh), border_radius=4)
            self.surface.blit(ks1, (x + 3, ry + 2))
            ds1 = f.small.render(d1, True, Theme.TEXT_SOFT)
            self.surface.blit(ds1, (x + kw1 + 8, ry + (kh - ds1.get_height()) // 2))
            
            # Columna 2
            k2, d2 = keys[i + 3]
            ks2 = f.key.render(" " + k2 + " ", True, Theme.TEXT)
            kw2 = ks2.get_width() + 6
            cx = x + col2_offset
            pygame.draw.rect(self.surface, Theme.BG_CARD, (cx, ry, kw2, kh), border_radius=4)
            self.surface.blit(ks2, (cx + 3, ry + 2))
            ds2 = f.small.render(d2, True, Theme.TEXT_SOFT)
            self.surface.blit(ds2, (cx + kw2 + 8, ry + (kh - ds2.get_height()) // 2))

    def _controls_height(self) -> int:
        kh = self.fonts.key.get_height() + 4
        return (kh + 7) * 3 + 4

    def _section_header(self, x: int, y: int, text: str):
        s = self.fonts.heading.render(text, True, Theme.TEXT)
        self.surface.blit(s, (x, y))

    def _divider(self, x: int, y: int, w: int) -> int:
        pygame.draw.line(self.surface, Theme.BG_SOFT, (x, y), (x + w, y), 1)
        return y
