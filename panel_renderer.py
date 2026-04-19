"""
panel_renderer.py — Dibuja el panel lateral de informacion

Secciones:
  - Titulo "IRON GAMBIT" y subtitulo
  - Estado de la partida y mensaje de turno
  - Indicador de color de turno
  - Piezas capturadas
  - Historial de movimientos
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
        self.surface = surface
        self.fonts   = fonts
        self.layout  = layout

    #  Actualiza el layout y las fuentes
    def update_layout(self, layout: Layout, fonts: FontManager):
        self.layout = layout
        self.fonts  = fonts

    # ── Dibujo principal ──────────────────────────────────────────────────────

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
        controls_h = self._controls_height()
        hist_bottom = L.py + L.ph - controls_h - 10
        self._draw_history(px, y, pw, hist_bottom, gs)

        self._divider(px, hist_bottom, pw)
        self._draw_controls(px, hist_bottom + 7, pw)

    # ── Secciones ─────────────────────────────────────────────────────────────

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

        # Tamaño de cada miniatura: proporcional al panel pero pequeño
        icon_sz = max(14, min(22, w // 10))
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
            cx  = x
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

    # Dibuja el historial de movimientos en formato SAN
    def _draw_history(self, x: int, y: int, w: int,
                      bottom: int, gs: GameState) -> int:
        f = self.fonts
        self._section_header(x, y, "HISTORIAL")
        y += f.heading.get_height() + 5

        row_h   = f.mono.get_height() + 3
        space   = bottom - y
        max_vis = max(2, (space // row_h // 2) * 2)

        sans    = gs.san_history
        start   = max(0, len(sans) - max_vis)
        visible = sans[start:]

        for i in range(0, len(visible), 2):
            num   = (start + i) // 2 + 1
            w_san = visible[i]
            b_san = visible[i + 1] if i + 1 < len(visible) else ""
            row   = "{:>3}. {:<8} {}".format(num, w_san, b_san)
            col   = Theme.GOLD_LT if (i + start >= len(sans) - 2) else Theme.TEXT
            self.surface.blit(f.mono.render(row, True, col), (x, y))
            y += row_h
        return y

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

    # ── Helpers ───────────────────────────────────────────────────────────────

    # Calcula la altura total que ocupan los controles para reservar espacio en el historial
    def _controls_height(self) -> int:
        kh = self.fonts.key.get_height() + 4
        return (kh + 5) * 5 + 4

    # Dibuja un encabezado de seccion con una linea debajo para separarlo visualmente
    def _section_header(self, x: int, y: int, text: str):
        s = self.fonts.heading.render(text, True, Theme.CRIMSON_LT)
        self.surface.blit(s, (x, y))
        uy = y + s.get_height() + 1
        pygame.draw.line(self.surface, Theme.GOLD, (x, uy), (x + s.get_width(), uy), 2)

    def _divider(self, x: int, y: int, w: int) -> int:
        pygame.draw.line(self.surface, Theme.CRIMSON_DIM, (x, y), (x + w, y), 1)
        return y