"""
panel_renderer.py -- Dibuja el panel lateral de informacion

Secciones:
  - Titulo "IRON GAMBIT" y subtitulo
  - Estado de la partida y mensaje de turno
  - Indicador de color de turno
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
from utils        import wrap_text

class PanelRenderer:
    """
    Dibuja el panel lateral derecho, que muestra toda la informacion
    de la partida en curso de forma clara y compacta

    Calcula dinamicamente el espacio disponible para el historial
    segun lo que ocupan el resto de secciones y los controles
    """

    # Inicializa con la superficie de dibujo, las fuentes y el layout
    def __init__(self, surface: pygame.Surface,
                 fonts: FontManager, layout: Layout):
        self.surface        = surface
        self.fonts          = fonts
        self.layout         = layout
        self._scroll_offset = 0

    # Actualiza el layout y las fuentes
    def update_layout(self, layout: Layout, fonts: FontManager):
        self.layout = layout
        self.fonts  = fonts

    # -- Scroll ---------------------------------------------------------------

    # Desplaza el historial (delta > 0 = subir hacia jugadas antiguas)
    def handle_scroll(self, delta: int):
        self._scroll_offset = max(0, self._scroll_offset + delta)

    # -- Dibujo principal -----------------------------------------------------

    # Dibuja todas las secciones del panel en orden
    def draw(self, gs: GameState):
        L  = self.layout
        px = L.px
        pw = L.pw

        # Fondo del panel con borde sutil
        pygame.draw.rect(self.surface, Theme.BG_PANEL,
                         (px - 8, L.py - 4, pw + 14, L.ph + 8))
        pygame.draw.rect(self.surface, Theme.CRIMSON_DIM,
                         (px - 8, L.py - 4, pw + 14, L.ph + 8), 1)

        # Cursor vertical que avanza seccion a seccion
        y = L.py + 5
        y = self._draw_title(px, y, pw)
        y = self._divider(px, y, pw) + 5

        y = self._draw_status(px, y, pw, gs)
        y = self._draw_turn(px, y, pw, gs) + 4
        y = self._divider(px, y, pw) + 5

        y = self._draw_captured(px, y, pw, gs)
        y = self._divider(px, y, pw) + 5

        # El historial ocupa el espacio restante hasta los controles
        controls_h  = self._controls_height()
        hist_bottom = L.py + L.ph - controls_h - 10
        self._draw_history(px, y, pw, hist_bottom, gs)

        self._divider(px, hist_bottom, pw)
        self._draw_controls(px, hist_bottom + 7, pw)

    # -- Secciones ------------------------------------------------------------

    # Dibuja el titulo del juego con estilo y el subtitulo debajo
    def _draw_title(self, x: int, y: int, w: int) -> int:
        f  = self.fonts
        t1 = f.title.render("IRON",   True, Theme.GOLD_LT)
        t2 = f.title.render("GAMBIT", True, Theme.TEXT)
        self.surface.blit(t1, (x, y))
        self.surface.blit(t2, (x + t1.get_width() + 5, y))
        y  += max(t1.get_height(), t2.get_height()) + 1
        sub = f.small.render("Otra forma de aprender ajedrez", True, Theme.TEXT)
        self.surface.blit(sub, (x, y))
        return y + sub.get_height() + 5

    # Dibuja el estado de la partida, con color especial para jaque y jaque mate
    def _draw_status(self, x: int, y: int, w: int, gs: GameState) -> int:
        f = self.fonts
        self._section_header(x, y, "ESTADO")
        y += f.heading.get_height() + 5

        color = (Theme.GOLD_LT     if gs.game_over
            else Theme.CRIMSON_LT  if gs.board.is_check()
            else Theme.TEXT)

        for line in wrap_text(gs.status, f.body, w - 2):
            s = f.body.render(line, True, color)
            self.surface.blit(s, (x, y))
            y += s.get_height() + 2
        return y + 3

    # Dibuja un circulo con el color del turno actual y un mensaje indicando de quien es el turno
    def _draw_turn(self, x: int, y: int, w: int, gs: GameState) -> int:
        f        = self.fonts
        radius   = f.body.get_height() // 2 - 1
        cx, cy   = x + radius + 2, y + radius
        pc       = Theme.PIECE_WHITE if gs.board.turn == chess.WHITE else Theme.PIECE_BLACK
        pygame.draw.circle(self.surface, pc,         (cx, cy), radius)
        pygame.draw.circle(self.surface, Theme.GOLD, (cx, cy), radius, 2)
        label = "Blancas" if gs.board.turn == chess.WHITE else "Negras"
        s = f.body.render("Turno: " + label, True, Theme.TEXT)
        self.surface.blit(s, (x + radius * 2 + 8, y))
        return y + max(radius * 2, s.get_height()) + 2

    # Dibuja las piezas capturadas por cada bando como miniaturas con sombra, o "--" si no hay capturas
    def _draw_captured(self, x: int, y: int, w: int, gs: GameState) -> int:
        f            = self.fonts
        cap_w, cap_b = gs.captured_pieces()
        self._section_header(x, y, "CAPTURADAS")
        y += f.heading.get_height() + 5

        # Tamaño de cada miniatura: proporcional al panel pero pequeno
        icon_sz    = max(14, min(22, w // 10))
        piece_font = pygame.font.SysFont("Segoe UI Symbol", icon_sz)

        for label, caps, piece_col, shadow_col in [
            ("Blancas:", cap_b, Theme.PIECE_WHITE, Theme.SHADOW_WHITE),
            ("Negras:",  cap_w, Theme.PIECE_BLACK, Theme.SHADOW_BLACK),
        ]:
            lbl = f.small.render(label, True, Theme.TEXT)
            self.surface.blit(lbl, (x, y))
            y += lbl.get_height() + 2

            if not caps:
                dash = f.small.render("--", True, Theme.TEXT)
                self.surface.blit(dash, (x, y))
                y += dash.get_height() + 4
                continue

            # Dibuja cada pieza capturada como miniatura con sombra
            cx    = x
            row_h = icon_sz + 2
            for sym in caps:
                glyph = Theme.PIECES.get(sym, sym)
                # sombra
                sh_surf = piece_font.render(glyph, True, shadow_col)
                self.surface.blit(sh_surf, (cx + 1, y + 1))
                # pieza
                pc_surf = piece_font.render(glyph, True, piece_col)
                self.surface.blit(pc_surf, (cx, y))
                cx += pc_surf.get_width() + 1
                # salto de linea si se acaba el ancho
                if cx + icon_sz > x + w:
                    cx  = x
                    y  += row_h
            y += row_h + 3

        return y

    # -- Iconos en la notacion SAN --------------------------------------------

    # Sustituye la letra de pieza de un movimiento SAN por su icono unicode
    def _san_to_icon(self, san: str, is_white: bool) -> tuple[str, str]:
        """
        Devuelve (icon, rest) donde icon es el simbolo unicode de la pieza
        (o '' para un peon) y rest es el resto del movimiento sin la letra.

        Ejemplos:
          'Nf3'  -> ('♞', 'f3')
          'Bxe5' -> ('♝', 'xe5')
          'e4'   -> ('',  'e4')   peon, sin icono de pieza
          'O-O'  -> ('',  'O-O')  enroque
        """
        PIECE_ICONS = {
            'N': '\u265e', 'B': '\u265d', 'R': '\u265c', 'Q': '\u265b', 'K': '\u265a',
        }
        if san and san[0] in PIECE_ICONS:
            return PIECE_ICONS[san[0]], san[1:]
        return '', san

    # -- Celda de movimiento (icono + texto) ----------------------------------

    # Dibuja una celda individual del historial con icono + texto
    def _draw_move_cell(self, san: str, is_white: bool,
                        cx: int, cy: int, col_w: int, row_h: int,
                        highlight: bool):
        f = self.fonts

        if not san:
            return

        icon, rest = self._san_to_icon(san, is_white)

        # Colores de texto segun bando y estado de resaltado
        if highlight:
            text_col = Theme.GOLD_LT
            icon_col = Theme.GOLD_LT
        else:
            text_col = Theme.TEXT
            icon_col = (Theme.PIECE_WHITE if is_white else (180, 180, 180))

        pad    = 4
        draw_x = cx + pad
        draw_y = cy + (row_h - f.hist_move.get_height()) // 2

        # Icono de pieza (fuente simbolo, ligeramente mas pequeno)
        if icon:
            icon_surf = f.hist_icon.render(icon, True, icon_col)
            icon_y    = cy + (row_h - icon_surf.get_height()) // 2
            self.surface.blit(icon_surf, (draw_x, icon_y))
            draw_x += icon_surf.get_width() + 1

        # Texto del movimiento (coordenadas + capturas + jaques)
        move_surf = f.hist_move.render(rest, True, text_col)
        self.surface.blit(move_surf, (draw_x, draw_y))

    # -- Tabla de historial ---------------------------------------------------

    # Dibuja el historial de movimientos como tabla de tres columnas:
    #   #  |  blancas  |  negras
    # Sin cabecera, filas grises alternas, scrollbar lateral y
    # acento carmesi en el ultimo movimiento jugado.
    def _draw_history(self, x: int, y: int, w: int,
                      bottom: int, gs: GameState) -> int:
        f    = self.fonts
        sans = gs.san_history

        self._section_header(x, y, "HISTORIAL")
        y += f.heading.get_height() + 5

        # -- Dimensiones -------------------------------------------------------
        SB_W   = 5
        SB_GAP = 3
        tbl_w  = w - SB_W - SB_GAP
        NUM_W  = max(22, f.hist_move.size("99.")[0] + 4)
        COL_W  = (tbl_w - NUM_W - 4) // 2
        ROW_H  = f.hist_move.get_height() + 5
        area_h = bottom - y
        max_vis = max(1, area_h // ROW_H)

        total_pairs = (len(sans) + 1) // 2

        # Ajustar scroll al rango valido
        max_scroll = max(0, total_pairs - max_vis)
        scroll = max(0, min(self._scroll_offset, max_scroll))
        self._scroll_offset = scroll

        # Primer par visible en funcion del scroll
        first_pair = max(0, total_pairs - max_vis - scroll)
        rows_drawn = min(max_vis, total_pairs - first_pair)

        # -- Separadores verticales -------------------------------------------
        div_x1  = x + NUM_W + 2
        div_x2  = div_x1 + COL_W + 2
        table_h = rows_drawn * ROW_H

        if rows_drawn > 0:
            pygame.draw.line(self.surface, Theme.CRIMSON_DIM,
                             (div_x1, y), (div_x1, y + table_h), 1)
            pygame.draw.line(self.surface, Theme.CRIMSON_DIM,
                             (div_x2, y), (div_x2, y + table_h), 1)

        # -- Filas ------------------------------------------------------------
        last_idx = len(sans) - 1

        for pair_offset in range(rows_drawn):
            pair_num = first_pair + pair_offset
            idx_w    = pair_num * 2
            idx_b    = idx_w + 1
            ry       = y + pair_offset * ROW_H

            # Fondo alterno en grises neutros
            row_bg = (48, 48, 53) if pair_num % 2 == 0 else (40, 40, 45)
            pygame.draw.rect(self.surface, row_bg, (x, ry, tbl_w, ROW_H))

            # Acento izquierdo en la fila del ultimo movimiento
            if last_idx in (idx_w, idx_b):
                pygame.draw.rect(self.surface, Theme.CRIMSON_LT,
                                 (x, ry, 2, ROW_H))

            # Numero de jugada
            num_str  = f"{pair_num + 1}."
            num_surf = f.hist_move.render(num_str, True, Theme.STEEL_LT)
            self.surface.blit(num_surf,
                              (x + NUM_W - num_surf.get_width() - 2,
                               ry + (ROW_H - num_surf.get_height()) // 2))

            # Celda blancas
            if idx_w < len(sans):
                hl = (idx_w == last_idx)
                self._draw_move_cell(sans[idx_w], True,
                                     div_x1 + 2, ry, COL_W - 4, ROW_H, hl)

            # Celda negras
            if idx_b < len(sans):
                hl = (idx_b == last_idx)
                self._draw_move_cell(sans[idx_b], False,
                                     div_x2 + 2, ry, COL_W - 4, ROW_H, hl)

        # -- Scrollbar --------------------------------------------------------
        sb_x = x + tbl_w + SB_GAP
        sb_y = y
        sb_h = area_h

        # Pista de la scrollbar
        pygame.draw.rect(self.surface, (35, 35, 40),
                         (sb_x, sb_y, SB_W, sb_h), border_radius=3)

        if total_pairs > max_vis:
            # Thumb proporcional al contenido visible
            thumb_h    = max(14, int(sb_h * max_vis / total_pairs))
            # scroll=0 -> thumb abajo; scroll=max -> thumb arriba
            scroll_ratio = scroll / max_scroll if max_scroll > 0 else 0
            thumb_y    = sb_y + int((sb_h - thumb_h) * (1.0 - scroll_ratio))
            pygame.draw.rect(self.surface, Theme.STEEL,
                             (sb_x, thumb_y, SB_W, thumb_h), border_radius=3)

        return y + table_h

    # Dibuja los controles de teclado con su descripcion, en recuadros rojos para destacarlos
    def _draw_controls(self, x: int, y: int, w: int):
        f    = self.fonts
        keys = [
            ("N",   "Nueva partida"),
            ("Z",   "Deshacer"),
            ("F",   "Rotar tablero"),
            ("P",   "Estilo de piezas"),
            ("F11", "Pantalla completa"),
        ]
        for key, desc in keys:
            ks  = f.key.render(" " + key + " ", True, Theme.TEXT)
            kw  = ks.get_width() + 4
            kh  = ks.get_height() + 4
            pygame.draw.rect(self.surface, Theme.CRIMSON_DIM, (x, y, kw, kh))
            pygame.draw.rect(self.surface, Theme.CRIMSON,     (x, y, kw, kh), 1)
            self.surface.blit(ks, (x + 2, y + 2))
            ds = f.small.render(desc, True, Theme.TEXT)
            self.surface.blit(ds, (x + kw + 7, y + (kh - ds.get_height()) // 2))
            y += kh + 5

    # -- Helpers --------------------------------------------------------------

    # Calcula la altura total que ocupan los controles para reservar espacio en el historial
    def _controls_height(self) -> int:
        kh = self.fonts.key.get_height() + 4
        return (kh + 5) * 5 + 4

    # Dibuja un encabezado de seccion con una linea debajo para separarlo visualmente
    def _section_header(self, x: int, y: int, text: str):
        s  = self.fonts.heading.render(text, True, Theme.CRIMSON_LT)
        self.surface.blit(s, (x, y))
        uy = y + s.get_height() + 1
        pygame.draw.line(self.surface, Theme.GOLD, (x, uy), (x + s.get_width(), uy), 2)

    def _divider(self, x: int, y: int, w: int) -> int:
        pygame.draw.line(self.surface, Theme.CRIMSON_DIM, (x, y), (x + w, y), 1)
        return y