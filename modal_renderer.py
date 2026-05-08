"""
modal_renderer.py -- Dialogos flotantes sobre la pantalla

Modales disponibles:
  - draw_promotion : selector de pieza de promocion
  - draw_game_over : pantalla de fin de partida
  - draw_exit_confirmation : confirmacion de salida
"""

import pygame
import chess

from theme        import Theme
from layout       import Layout
from font_manager import FontManager

class ModalRenderer:
    """
    Dibuja los modales flotantes que aparecen sobre el tablero y el panel.
    """

    def __init__(self, surface: pygame.Surface,
                 fonts: FontManager, layout: Layout):
        self.surface = surface
        self.fonts   = fonts
        self.layout  = layout

    def update_layout(self, layout: Layout, fonts: FontManager):
        self.layout = layout
        self.fonts  = fonts

    def draw_promotion(self, turn_color, mouse_pos: tuple = None) -> list:
        W, H       = self.surface.get_size()
        f          = self.fonts
        cell       = max(50, min(self.layout.sq, 70))
        grow       = max(10, cell // 5)
        pad        = 14 + grow
        bw         = cell * 4 + pad * 2 + 12 + grow * 4
        bh         = cell + grow + pad * 2 + f.heading.get_height() + 8
        bx, by, _, _ = self._centered_box(bw, bh, overlay_alpha=195)

        ttl = f.heading.render("PROMOCION -- Elige pieza", True, Theme.GOLD_LT)
        self.surface.blit(ttl, (bx + (bw - ttl.get_width()) // 2, by + 8))

        pieces  = [chess.QUEEN, chess.ROOK, chess.BISHOP, chess.KNIGHT]
        symbols = ["Q", "R", "B", "N"] if turn_color == chess.WHITE else ["q", "r", "b", "n"]
        pc      = Theme.PIECE_WHITE if turn_color == chess.WHITE else Theme.PIECE_BLACK
        rects   = []

        base_y  = by + f.heading.get_height() + pad + 4
        gap     = cell + grow + 3
        start_x = bx + pad

        for i, (pt, sym) in enumerate(zip(pieces, symbols)):
            rx       = start_x + i * gap
            ry       = base_y
            hit_rect = pygame.Rect(rx, ry, cell + grow, cell + grow)
            hovered  = mouse_pos is not None and hit_rect.collidepoint(mouse_pos)

            if hovered:
                draw_x   = rx - grow // 2
                draw_y   = ry - grow // 2
                draw_c   = cell + grow
                bg_col   = (45, 35, 12)
                border_c = Theme.GOLD_LT
                border_w = 2
                big_font = pygame.font.SysFont("Segoe UI Symbol", max(18, int(draw_c * 0.72)))
                psurf    = big_font.render(Theme.PIECES[sym], True, pc)
            else:
                draw_x   = rx
                draw_y   = ry
                draw_c   = cell
                bg_col   = Theme.BG_CARD
                border_c = Theme.CRIMSON_DIM
                border_w = 1
                psurf    = self.fonts.piece.render(Theme.PIECES[sym], True, pc)

            pygame.draw.rect(self.surface, bg_col, (draw_x, draw_y, draw_c, draw_c), border_radius=4)
            pygame.draw.rect(self.surface, border_c, (draw_x, draw_y, draw_c, draw_c), border_w, border_radius=4)
            self.surface.blit(
                psurf,
                (
                    draw_x + draw_c // 2 - psurf.get_width() // 2,
                    draw_y + draw_c // 2 - psurf.get_height() // 2,
                ),
            )
            rects.append((hit_rect, pt))

        return rects

    def draw_game_over(self, msg: str) -> pygame.Rect:
        f = self.fonts
        bw = min(430, self.surface.get_width() - 40)
        bh = f.title.get_height() + f.body.get_height() + f.small.get_height() + 52
        bx, by, bw, bh = self._centered_box(bw, bh, overlay_alpha=185)

        close_sz = 20
        close_r  = pygame.Rect(bx + bw - close_sz - 6, by + 6, close_sz, close_sz)
        mx, my   = pygame.mouse.get_pos()
        hovered  = close_r.collidepoint(mx, my)
        pygame.draw.rect(
            self.surface,
            Theme.CRIMSON_LT if hovered else Theme.CRIMSON_DIM,
            close_r,
            border_radius=4,
        )
        xf = pygame.font.SysFont("Tahoma", 13, bold=True)
        xs = xf.render("X", True, Theme.TEXT)
        self.surface.blit(xs, (close_r.x + (close_sz - xs.get_width()) // 2,
                               close_r.y + (close_sz - xs.get_height()) // 2))

        t1 = f.title.render("FIN DE PARTIDA", True, Theme.GOLD_LT)
        self.surface.blit(t1, (bx + (bw - t1.get_width()) // 2, by + 14))

        t2 = f.body.render(msg, True, Theme.TEXT)
        self.surface.blit(t2, (bx + (bw - t2.get_width()) // 2, by + 18 + t1.get_height()))

        t3 = f.small.render("Pulsa N para nueva partida", True, Theme.STEEL_LT)
        self.surface.blit(t3, (bx + (bw - t3.get_width()) // 2, by + bh - t3.get_height() - 14))

        return close_r

    def draw_exit_confirmation(self) -> tuple[pygame.Rect, pygame.Rect]:
        f = self.fonts
        mx, my = pygame.mouse.get_pos()

        card_w  = min(420, self.surface.get_width() - 60)
        btn_w   = 132
        btn_h   = 52
        gap     = 12
        pad     = 24
        title_h = f.title.get_height() + 8
        modal_h = pad + title_h + gap + btn_h + pad

        bx, by, bw, bh = self._centered_box(card_w, modal_h, overlay_alpha=185)

        title = f.title.render("SALIR DE LA APLICACION", True, Theme.GOLD_LT)
        title_gap = 8
        title_w = title.get_width()
        title_x = bx + (bw - title_w) // 2
        title_y = by + pad

        self.surface.blit(title, (title_x, title_y))

        total_w = btn_w * 2 + gap
        start_x = bx + (bw - total_w) // 2
        btn_y = by + pad + title_h + gap

        yes_r = pygame.Rect(start_x, btn_y, btn_w, btn_h)
        no_r  = pygame.Rect(start_x + btn_w + gap, btn_y, btn_w, btn_h)

        self._draw_modal_button(yes_r, "Si", yes_r.collidepoint(mx, my), primary=True)
        self._draw_modal_button(no_r, "No", no_r.collidepoint(mx, my), primary=False)
        return yes_r, no_r

    def _overlay(self, w: int, h: int, alpha: int):
        ov = pygame.Surface((w, h), pygame.SRCALPHA)
        ov.fill((0, 0, 0, alpha))
        self.surface.blit(ov, (0, 0))

    def _draw_box(self, x: int, y: int, w: int, h: int):
        pygame.draw.rect(self.surface, Theme.BG_PANEL, (x, y, w, h))
        pygame.draw.rect(self.surface, Theme.GOLD,     (x, y, w, h), 2)
        pygame.draw.rect(self.surface, Theme.CRIMSON,  (x + 2, y + 2, w - 4, h - 4), 1)

    def _centered_box(self, bw: int, bh: int, overlay_alpha: int = 185) -> tuple[int, int, int, int]:
        w, h = self.surface.get_size()
        bx = (w - bw) // 2
        by = (h - bh) // 2
        self._overlay(w, h, overlay_alpha)
        self._draw_box(bx, by, bw, bh)
        return bx, by, bw, bh

    def _draw_modal_button(self, rect: pygame.Rect, text: str, hovered: bool, primary: bool):
        bg = Theme.GOLD if hovered else (Theme.BG_CARD if not primary else Theme.BG_CARD)
        border = Theme.GOLD_LT if hovered else Theme.STEEL
        text_color = Theme.PIECE_BLACK if hovered else (Theme.GOLD_LT if primary else Theme.TEXT)

        pygame.draw.rect(self.surface, bg, rect, border_radius=5)
        pygame.draw.rect(self.surface, border, rect, 1, border_radius=5)

        label = self.fonts.body.render(text, True, text_color)
        self.surface.blit(
            label,
            (
                rect.x + (rect.width - label.get_width()) // 2,
                rect.y + (rect.height - label.get_height()) // 2,
            ),
        )
