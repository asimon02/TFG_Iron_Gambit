"""
modal_renderer.py — Dialogos flotantes sobre la pantalla

Modales disponibles:
  - draw_promotion : selector de pieza de promocion
  - draw_game_over : pantalla de fin de partida
"""

import pygame
import chess

from theme        import Theme
from layout       import Layout
from font_manager import FontManager

class ModalRenderer:
    """
    Dibuja los modales flotantes que aparecen sobre el tablero y el panel.

    Cada método devuelve o dibuja sobre la superficie actual con un overlay
    semitransparente para centrar la atención del usuario.
    """

    # Inicializa el renderer con la superficie, fuentes y layout actuales
    def __init__(self, surface: pygame.Surface,
                 fonts: FontManager, layout: Layout):
        self.surface = surface
        self.fonts   = fonts
        self.layout  = layout

    # Actualiza el layout y las fuentes
    def update_layout(self, layout: Layout, fonts: FontManager):
        self.layout = layout
        self.fonts  = fonts

    # ── Seleccion de promocion ────────────────────────────────────────────────

    # Dibuja el modal de promocion y devuelve una lista de tuplas (rect, pieza) para detectar clicks
    def draw_promotion(self, turn_color, mouse_pos: tuple = None) -> list:
        W, H       = self.surface.get_size()
        f          = self.fonts
        cell       = max(50, min(self.layout.sq, 70))
        GROW       = max(10, cell // 5)
        pad        = 14 + GROW
        bw         = cell * 4 + pad * 2 + 12 + GROW * 4
        bh         = cell + GROW + pad * 2 + f.heading.get_height() + 8
        bx         = (W - bw) // 2
        by         = (H - bh) // 2

        self._overlay(W, H, 195)
        self._draw_box(bx, by, bw, bh)

        ttl = f.heading.render("PROMOCION ─ Elige pieza", True, Theme.GOLD_LT)
        self.surface.blit(ttl, (bx + (bw - ttl.get_width()) // 2, by + 8))

        pieces  = [chess.QUEEN, chess.ROOK, chess.BISHOP, chess.KNIGHT]
        symbols = ["Q", "R", "B", "N"] if turn_color == chess.WHITE else ["q", "r", "b", "n"]
        pc      = Theme.PIECE_WHITE if turn_color == chess.WHITE else Theme.PIECE_BLACK
        rects   = []

        base_y  = by + f.heading.get_height() + pad + 4
        gap     = cell + GROW + 3
        start_x = bx + pad

        for i, (pt, sym) in enumerate(zip(pieces, symbols)):
            rx       = start_x + i * gap
            ry       = base_y
            hit_rect = pygame.Rect(rx, ry, cell + GROW, cell + GROW)
            hovered  = mouse_pos is not None and hit_rect.collidepoint(mouse_pos)

            if hovered:
                draw_x   = rx - GROW // 2
                draw_y   = ry - GROW // 2
                draw_c   = cell + GROW
                bg_col   = (45, 35, 12)
                border_c = Theme.GOLD_LT
                border_w = 2
                big_font = pygame.font.SysFont("Segoe UI Symbol",
                                               max(18, int(draw_c * 0.72)))
                psurf    = big_font.render(Theme.PIECES[sym], True, pc)
            else:
                draw_x   = rx
                draw_y   = ry
                draw_c   = cell
                bg_col   = Theme.BG_CARD
                border_c = Theme.CRIMSON_DIM
                border_w = 1
                psurf    = self.fonts.piece.render(Theme.PIECES[sym], True, pc)

            pygame.draw.rect(self.surface, bg_col,
                             (draw_x, draw_y, draw_c, draw_c), border_radius=4)
            pygame.draw.rect(self.surface, border_c,
                             (draw_x, draw_y, draw_c, draw_c), border_w, border_radius=4)
            self.surface.blit(psurf, (
                draw_x + draw_c // 2 - psurf.get_width() // 2,
                draw_y + draw_c // 2 - psurf.get_height() // 2,
            ))
            rects.append((hit_rect, pt))

        return rects

    # ── Fin de partida ────────────────────────────────────────────────────────

    # Dibuja el modal de fin de partida con el mensaje dado
    def draw_game_over(self, msg: str):
        W, H = self.surface.get_size()
        f    = self.fonts

        bw = min(430, W - 40)
        bh = f.title.get_height() + f.body.get_height() + f.small.get_height() + 52
        bx = (W - bw) // 2
        by = (H - bh) // 2

        self._overlay(W, H, 185)
        self._draw_box(bx, by, bw, bh)

        t1 = f.title.render("FIN DE PARTIDA", True, Theme.GOLD_LT)
        self.surface.blit(t1, (bx + (bw - t1.get_width()) // 2, by + 14))

        t2 = f.body.render(msg, True, Theme.TEXT_BRIGHT)
        self.surface.blit(t2, (bx + (bw - t2.get_width()) // 2,
                                by + 18 + t1.get_height()))

        t3 = f.small.render("Pulsa N para nueva partida", True, Theme.TEXT_DIM)
        self.surface.blit(t3, (bx + (bw - t3.get_width()) // 2,
                                by + bh - t3.get_height() - 14))

    # ── Helpers ───────────────────────────────────────────────────────────────

    # Dibuja un overlay semitransparente sobre toda la pantalla
    def _overlay(self, W: int, H: int, alpha: int):
        ov = pygame.Surface((W, H), pygame.SRCALPHA)
        ov.fill((0, 0, 0, alpha))
        self.surface.blit(ov, (0, 0))

    # Dibuja un recuadro con borde decorativo
    def _draw_box(self, x: int, y: int, w: int, h: int):
        pygame.draw.rect(self.surface, Theme.BG_PANEL, (x, y, w, h))
        pygame.draw.rect(self.surface, Theme.GOLD,     (x, y, w, h), 2)
        pygame.draw.rect(self.surface, Theme.CRIMSON,  (x + 2, y + 2, w - 4, h - 4), 1)