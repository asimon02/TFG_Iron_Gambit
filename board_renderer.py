"""
board_renderer.py — Dibuja el tablero: casillas, highlights, piezas y coordenadas
"""

import pygame
import chess

from theme        import Theme
from layout       import Layout
from font_manager import FontManager
from game_state   import GameState

class BoardRenderer:
    """
    Responsable exclusivo de renderizar el tablero de ajedrez

    Incluye:
      - Casillas grises (claras y oscuras)
      - Highlights de seleccion, ultimo movimiento, jaque y destinos legales
      - Piezas unicode con sombra
      - Marco dorado/carmesi exterior
      - Coordenadas (letras de columna y numeros de fila)
    """

    # Constructor que recibe la superficie de dibujo, el gestor de fuentes y el layout para calcular posiciones y tamaños
    def __init__(self, surface: pygame.Surface,
                 fonts: FontManager, layout: Layout):
        self.surface = surface
        self.fonts   = fonts
        self.layout  = layout
        self._hl     = self._make_hl_surface()

    # ── Actualizacion de layout ───────────────────────────────────────────────

    # Actualiza el layout y regenera las superficies de highlights
    def update_layout(self, layout: Layout):
        self.layout = layout
        self._hl    = self._make_hl_surface()

    # Crea una superficie transparente para dibujar highlights con alpha
    def _make_hl_surface(self) -> pygame.Surface:
        sq = self.layout.sq
        return pygame.Surface((sq, sq), pygame.SRCALPHA)

    # ── Conversion de coordenadas ─────────────────────────────────────────────

    # Convierte una casilla de ajedrez (0-63) a coordenadas de pixel (x, y)
    def sq_to_px(self, sq: chess.Square, flipped: bool) -> tuple:
        c, r = chess.square_file(sq), chess.square_rank(sq)
        L    = self.layout
        if flipped:
            return L.bx + (7 - c) * L.sq, L.by + r * L.sq
        return L.bx + c * L.sq, L.by + (7 - r) * L.sq

    # Convierte coordenadas de pixel (mx, my) a una casilla de ajedrez (0-63)
    def px_to_sq(self, mx: int, my: int, flipped: bool):
        L  = self.layout
        cx = (mx - L.bx) // L.sq
        cy = (my - L.by) // L.sq
        if not (0 <= cx < 8 and 0 <= cy < 8):
            return None
        return chess.square(cx, 7 - cy) if not flipped else chess.square(7 - cx, cy)

    # ── Dibujo principal ──────────────────────────────────────────────────────

    # Dibuja el tablero completo: casillas, piezas, highlights y coordenadas
    def draw(self, gs: GameState):
        self._draw_squares(gs)
        self._draw_pieces(gs)
        self._draw_coords(gs.flipped)

    # ── Casillas y highlights ─────────────────────────────────────────────────

    # Dibuja las casillas del tablero con sus colores base y highlights de seleccion
    def _draw_squares(self, gs: GameState):
        L        = self.layout
        board    = gs.board
        last     = gs.last_move
        check_sq = board.king(board.turn) if board.is_check() else None
        hl       = self._hl

        for sq in chess.SQUARES:
            x, y = self.sq_to_px(sq, gs.flipped)
            c, r  = chess.square_file(sq), chess.square_rank(sq)

            # Color base de la casilla
            base = Theme.SQ_LIGHT if (c + r) % 2 == 1 else Theme.SQ_DARK
            pygame.draw.rect(self.surface, base, (x, y, L.sq, L.sq))

            # Highlight: ultimo movimiento
            hl.fill((0, 0, 0, 0))
            if last and sq in (last.from_square, last.to_square):
                hl.fill(Theme.HL_LAST)
                self.surface.blit(hl, (x, y))
                hl.fill((0, 0, 0, 0))

            # Highlight: rey en jaque
            if check_sq is not None and sq == check_sq:
                hl.fill(Theme.HL_CHECK)
                self.surface.blit(hl, (x, y))
                hl.fill((0, 0, 0, 0))

            # Highlight: casilla seleccionada
            if gs.selected_sq == sq:
                hl.fill(Theme.HL_SELECT)
                self.surface.blit(hl, (x, y))
                pygame.draw.rect(self.surface, Theme.GOLD, (x, y, L.sq, L.sq), 2)
                hl.fill((0, 0, 0, 0))

            # Indicadores de destinos legales
            if any(m.to_square == sq for m in gs.legal_moves):
                if board.piece_at(sq):
                    # Anillo dorado para capturas
                    pygame.draw.rect(self.surface, Theme.GOLD_LT,
                                     (x, y, L.sq, L.sq), 3)
                else:
                    # Punto dorado para movimientos a casilla vacia
                    dot = pygame.Surface((L.sq, L.sq), pygame.SRCALPHA)
                    rad = max(4, L.sq // 7)
                    pygame.draw.circle(dot, Theme.HL_MOVE, (L.sq // 2, L.sq // 2), rad)
                    self.surface.blit(dot, (x, y))

    # ── Piezas ────────────────────────────────────────────────────────────────

    # Dibuja las piezas en sus casillas usando caracteres unicode con sombra para profundidad
    def _draw_pieces(self, gs: GameState):
        L = self.layout
        f = self.fonts.piece

        for sq in chess.SQUARES:
            piece = gs.board.piece_at(sq)
            if not piece:
                continue

            x, y = self.sq_to_px(sq, gs.flipped)
            sym  = Theme.PIECES[piece.symbol()]

            if piece.color == chess.WHITE:
                piece_color, shadow_color = Theme.PIECE_WHITE, Theme.SHADOW_WHITE
            else:
                piece_color, shadow_color = Theme.PIECE_BLACK, Theme.SHADOW_BLACK

            # Sombra desplazada
            offset = max(1, L.sq // 42)
            shadow = f.render(sym, True, shadow_color)
            cx = x + L.sq // 2 - shadow.get_width() // 2
            cy = y + L.sq // 2 - shadow.get_height() // 2
            self.surface.blit(shadow, (cx + offset, cy + offset))

            # Pieza
            psurf = f.render(sym, True, piece_color)
            self.surface.blit(psurf, (cx, cy))

    # ── Marco del tablero ─────────────────────────────────────────────────────

    # Dibuja un marco dorado y carmesi alrededor del tablero para enmarcarlo visualmente
    def _draw_border(self):
        L = self.layout
        pygame.draw.rect(self.surface, Theme.GOLD,
                         (L.bx - 3, L.by - 3, L.board_px + 6, L.board_px + 6), 2)
        pygame.draw.rect(self.surface, Theme.CRIMSON,
                         (L.bx - 6, L.by - 6, L.board_px + 12, L.board_px + 12), 1)

    # ── Coordenadas ───────────────────────────────────────────────────────────

    # Dibuja las coordenadas de archivos (a-h) y filas (1-8) alrededor del tablero
    def _draw_coords(self, flipped: bool):
        L      = self.layout
        f      = self.fonts.coord
        files  = "hgfedcba" if flipped else "abcdefgh"
        ranks  = "12345678" if flipped else "87654321"
        GAP    = 20

        for i, ch in enumerate(files):
            s = f.render(ch, True, Theme.GOLD)
            x = L.bx + i * L.sq + L.sq // 2 - s.get_width() // 2
            self.surface.blit(s, (x, L.by + L.board_px + 3))

        for i, ch in enumerate(ranks):
            s = f.render(ch, True, Theme.GOLD)
            y = L.by + i * L.sq + L.sq // 2 - s.get_height() // 2
            self.surface.blit(s, (L.bx - s.get_width() - GAP // 2, y))