"""
board_renderer.py -- Dibuja el tablero: casillas, highlights, piezas y coordenadas
"""

import pygame
import chess

from theme        import Theme
from layout       import Layout
from font_manager import FontManager
from game_state   import GameState
from utils        import resource_path

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

    # Constructor que recibe la superficie de dibujo, el gestor de fuentes y el layout
    def __init__(self, surface: pygame.Surface,
                 fonts: FontManager, layout: Layout):
        self.surface = surface
        self.fonts   = fonts
        self.layout  = layout
        self._hl     = self._make_hl_surface()
        self._crown_win  = None
        self._crown_lose = None

        # Drag & drop
        self._drag_piece  = None
        self._drag_color  = None
        self._drag_sq     = None
        self._drag_pos    = (0, 0)

        # Animacion de movimiento de pieza
        self._anim_piece  = None
        self._anim_color  = None
        self._anim_from   = None
        self._anim_to     = None
        self._anim_start  = 0
        self._anim_dur    = 250
        self._anim_sq_hide = None

    # -- Actualizacion de layout ----------------------------------------------

    # Actualiza el layout y regenera las superficies de highlights
    def update_layout(self, layout: Layout):
        self.layout = layout
        self._hl    = self._make_hl_surface()

    # Crea una superficie transparente para dibujar highlights con alpha
    def _make_hl_surface(self) -> pygame.Surface:
        sq = self.layout.sq
        return pygame.Surface((sq, sq), pygame.SRCALPHA)

    # -- Conversion de coordenadas --------------------------------------------

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

    # -- Dibujo principal -----------------------------------------------------

    # Dibuja el tablero completo: casillas, piezas, highlights y coordenadas
    def draw(self, gs: GameState, show_stop: bool = False):
        self._draw_squares(gs)
        self._draw_pieces(gs)
        self._draw_anim()
        self._draw_coords(gs.flipped)
        # La pieza arrastrada se dibuja encima de todo
        self._draw_drag()
        # Mostrar coronas si hubo jaque mate, incluso tras cerrar el modal
        if getattr(gs, 'checkmate_winner', None) is not None:
            self._draw_checkmate_crowns(gs)

        # Mostrar overlay de STOP si la frecuencia cardíaca es demasiado alta
        if show_stop:
            L = self.layout
            # Overlay sobre el tablero
            overlay = pygame.Surface((L.board_px, L.board_px), pygame.SRCALPHA)
            overlay.fill((20, 20, 20, 180))  # Gris muy oscuro y traslúcido
            self.surface.blit(overlay, (L.bx, L.by))
            
            # Caja de alerta en el centro
            card_w = min(280, L.board_px - 40)
            card_h = min(150, L.board_px - 60)
            cx = L.bx + (L.board_px - card_w) // 2
            cy = L.by + (L.board_px - card_h) // 2
            
            # Dibujar la caja de la alerta
            pygame.draw.rect(self.surface, (15, 15, 18), (cx, cy, card_w, card_h), border_radius=8)
            pygame.draw.rect(self.surface, (210, 60, 60), (cx, cy, card_w, card_h), 2, border_radius=8)  # Borde rojo carmesí
            
            # Texto principal "STOP"
            font_stop = pygame.font.SysFont("Impact", max(36, card_h // 3), bold=True)
            stop_surf = font_stop.render("STOP", True, (230, 50, 50))
            
            # Texto secundario
            font_sub = pygame.font.SysFont("Tahoma", max(11, card_h // 12), bold=True)
            sub_surf1 = font_sub.render("Pulsaciones Elevadas", True, (240, 240, 245))
            sub_surf2 = font_sub.render("Relájate para continuar", True, (160, 160, 170))
            
            # Dibujar elementos centrados
            stop_x = cx + (card_w - stop_surf.get_width()) // 2
            stop_y = cy + 18
            self.surface.blit(stop_surf, (stop_x, stop_y))
            
            sub1_x = cx + (card_w - sub_surf1.get_width()) // 2
            sub1_y = stop_y + stop_surf.get_height() + 8
            self.surface.blit(sub_surf1, (sub1_x, sub1_y))
            
            sub2_x = cx + (card_w - sub_surf2.get_width()) // 2
            sub2_y = sub1_y + sub_surf1.get_height() + 4
            self.surface.blit(sub_surf2, (sub2_x, sub2_y))

    # -- Drag & drop ----------------------------------------------------------

    # Inicia el arrastre de la pieza en la casilla sq
    def start_drag(self, gs: GameState, sq: chess.Square, mouse_pos: tuple):
        piece = gs.display_board.piece_at(sq)
        if piece is None:
            return
        self._drag_piece = Theme.PIECES[piece.symbol()]
        self._drag_color = Theme.PIECE_WHITE if piece.color == chess.WHITE else Theme.PIECE_BLACK
        self._drag_sq    = sq
        self._drag_pos   = mouse_pos

    # Actualiza la posicion del arrastre
    def update_drag(self, mouse_pos: tuple):
        self._drag_pos = mouse_pos

    # Termina el arrastre y devuelve la casilla origen, o None
    def end_drag(self):
        sq = self._drag_sq
        self._drag_piece = None
        self._drag_sq    = None
        return sq

    def is_dragging(self) -> bool:
        return self._drag_sq is not None

    # Dibuja la pieza siendo arrastrada centrada en el cursor
    def _draw_drag(self):
        if not self.is_dragging():
            return
        L  = self.layout
        f  = self.fonts.piece
        mx, my = self._drag_pos

        # Sombra
        shadow = f.render(self._drag_piece, True, (30, 30, 35))
        sx = mx - shadow.get_width()  // 2
        sy = my - shadow.get_height() // 2
        offset = max(1, L.sq // 42)
        self.surface.blit(shadow, (sx + offset, sy + offset))
        
        # Pieza
        psurf = f.render(self._drag_piece, True, self._drag_color)
        self.surface.blit(psurf, (mx - psurf.get_width() // 2,
                                   my - psurf.get_height() // 2))

    # Comprueba si hay una animacion en curso
    def is_animating(self) -> bool:
        if self._anim_piece is None:
            return False
        return pygame.time.get_ticks() < self._anim_start + self._anim_dur

    # Limpia la animacion
    def clear_anim(self):
        self._anim_piece   = None
        self._anim_sq_hide = None
        self._anim_from    = None
        self._anim_to      = None

    # Inicia la animacion de movimiento para el move dado
    def start_anim(self, gs: GameState, move: chess.Move):
        piece = gs.display_board.piece_at(move.from_square)
        if piece is None:
            return
        self._anim_piece   = Theme.PIECES[piece.symbol()]
        self._anim_color   = Theme.PIECE_WHITE if piece.color == chess.WHITE else Theme.PIECE_BLACK
        self._anim_from    = self.sq_to_px(move.from_square, gs.flipped)
        self._anim_to      = self.sq_to_px(move.to_square,   gs.flipped)
        self._anim_start   = pygame.time.get_ticks()
        self._anim_sq_hide = move.from_square

    # -- Casillas y highlights ------------------------------------------------

    # Dibuja las casillas del tablero con sus colores base y highlights de seleccion
    def _draw_squares(self, gs: GameState):
        L        = self.layout
        board    = gs.display_board
        last     = gs.display_last_move
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

    # -- Piezas ---------------------------------------------------------------

    # Dibuja las piezas en sus casillas usando caracteres unicode con sombra
    def _draw_pieces(self, gs: GameState):
        L = self.layout
        f = self.fonts.piece

        for sq in chess.SQUARES:
            # Ocultar la pieza que esta siendo animada o arrastrada
            if sq == self._anim_sq_hide and self.is_animating():
                continue
            if sq == self._drag_sq and self.is_dragging():
                continue
            piece = gs.display_board.piece_at(sq)
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

    # Dibuja la pieza animada interpolando su posicion entre origen y destino
    def _draw_anim(self):
        if self._anim_piece is None:
            return
        now     = pygame.time.get_ticks()
        elapsed = now - self._anim_start
        if elapsed >= self._anim_dur:
            return

        # Interpolacion lineal suave (ease-out cuadratico)
        t  = elapsed / self._anim_dur
        t  = 1 - (1 - t) ** 2
        fx, fy = self._anim_from
        tx, ty = self._anim_to
        cx = int(fx + (tx - fx) * t)
        cy = int(fy + (ty - fy) * t)

        L  = self.layout
        f  = self.fonts.piece
        # Sombra
        shadow = f.render(self._anim_piece, True, (30, 30, 35))
        sx = cx + L.sq // 2 - shadow.get_width()  // 2
        sy = cy + L.sq // 2 - shadow.get_height() // 2
        offset = max(1, L.sq // 42)
        self.surface.blit(shadow, (sx + offset, sy + offset))
        # Pieza
        psurf = f.render(self._anim_piece, True, self._anim_color)
        self.surface.blit(psurf, (sx, sy))

    # -- Marco del tablero ----------------------------------------------------

    # Dibuja un marco dorado y carmesi alrededor del tablero
    def _draw_border(self):
        L = self.layout
        pygame.draw.rect(self.surface, Theme.GOLD,
                         (L.bx - 3, L.by - 3, L.board_px + 6, L.board_px + 6), 2)
        pygame.draw.rect(self.surface, Theme.CRIMSON,
                         (L.bx - 6, L.by - 6, L.board_px + 12, L.board_px + 12), 1)

    # -- Jaque mate -----------------------------------------------------------

    # Carga las imagenes de corona si aun no estan cargadas
    def _load_crowns(self):
        if self._crown_win is not None:
            return
        
        candidates = [
            resource_path("images/crown_win.png"),
        ]
        for path in candidates:
            try:
                self._crown_win  = pygame.image.load(path).convert_alpha()
                lose_path = path.replace("crown_win", "crown_lose")
                self._crown_lose = pygame.image.load(lose_path).convert_alpha()
                print(f"[crown] Cargadas desde: {path}")
                return
            except Exception as e:
                print(f"[crown] Fallo cargar {path}: {e}")
                continue
        
        self._crown_win  = False
        self._crown_lose = False

    # Dibuja iconos de corona sobre el rey ganador y el rey perdedor
    def _draw_checkmate_crowns(self, gs: GameState):
        self._load_crowns()
        L = self.layout

        winner_color = gs.checkmate_winner
        loser_color  = not winner_color

        icon_sz = max(16, L.sq // 3)

        for color, is_winner in [(winner_color, True), (loser_color, False)]:
            king_sq = gs.display_board.king(color)
            if king_sq is None:
                continue
            kx, ky = self.sq_to_px(king_sq, gs.flipped)

            img = self._crown_win if is_winner else self._crown_lose
            if img is not False and img is not None:
                scaled = pygame.transform.smoothscale(img, (icon_sz, icon_sz))
                self.surface.blit(scaled, (kx + 2, ky + 2))
            else:
                # Fallback visible: cuadrado de color con letra
                bg = (210, 170, 20) if is_winner else (180, 30, 30)
                pygame.draw.rect(self.surface, bg,
                                 (kx + 2, ky + 2, icon_sz, icon_sz), border_radius=3)
                ff = pygame.font.SysFont("Segoe UI Symbol", max(10, icon_sz - 4))
                cs = ff.render("\u265a", True, (200, 200, 205))
                self.surface.blit(cs, (kx + 2 + (icon_sz - cs.get_width()) // 2,
                                       ky + 2 + (icon_sz - cs.get_height()) // 2))

    # -- Coordenadas ----------------------------------------------------------

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