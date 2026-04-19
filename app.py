"""
app.py — Bucle principal, ventana pygame y orquestacion de componentes

La clase App es el punto de entrada de la aplicacion. Gestiona:
  - Creacion y configuracion de la ventana
  - Bucle de eventos y renderizado
  - Redimensionado dinamico y recalculo de layout
  - Modo pantalla completa / ventana
  - Propagacion de cambios de layout a todos los renderers
"""

import sys
import pygame

from advantage_bar  import AdvantageBar
from layout         import Layout
from font_manager   import FontManager
from game_state     import GameState
from board_renderer import BoardRenderer
from panel_renderer import PanelRenderer
from modal_renderer import ModalRenderer
from theme          import Theme

class App:
    """
    Orquesta todos los componentes de la aplicacion y ejecuta el bucle principal

    Controles
    ---------
    Clic izquierdo  — seleccionar / mover pieza
    N               — nueva partida
    Z               — deshacer movimiento
    F               — rotar tablero
    F11             — pantalla completa / ventana
    Esc             — salir (o volver de pantalla completa)
    """

    TITLE = "Iron Gambit"
    FPS   = 60

    # Inicializa pygame, crea la ventana y los componentes principales
    def __init__(self):
        pygame.init()

        icon = pygame.image.load("images/icon.png")
        pygame.display.set_icon(icon)

        self._fullscreen = False
        self._screen     = pygame.display.set_mode(
            (Layout.BASE_W, Layout.BASE_H), pygame.RESIZABLE)
        pygame.display.set_caption(self.TITLE)
        self._clock = pygame.time.Clock()

        # Componentes principales
        self._layout = Layout(Layout.BASE_W, Layout.BASE_H)
        self._fonts  = FontManager(self._layout)
        self._gs     = GameState()

        # Renderers
        self._board  = BoardRenderer(self._screen, self._fonts, self._layout)
        self._panel  = PanelRenderer(self._screen, self._fonts, self._layout)
        self._modal  = ModalRenderer(self._screen, self._fonts, self._layout)

        # Barra de ventaja
        self._adv_bar = AdvantageBar(self._screen, self._layout)

        # Lista de rectangulos de promocion activos
        self._promo_rects = []

    # ── Bucle principal ───────────────────────────────────────────────────────

    def run(self):
        while True:
            for event in pygame.event.get():
                self._handle_event(event)
            self._render()
            pygame.display.flip()
            self._clock.tick(self.FPS)

    # ── Gestion de eventos ────────────────────────────────────────────────────

    # Maneja eventos de ventana, teclado y raton
    def _handle_event(self, event: pygame.event.Event):
        if event.type == pygame.QUIT:
            self._quit()
        elif event.type == pygame.VIDEORESIZE:
            self._resize(event.w, event.h)
        elif event.type == pygame.KEYDOWN:
            self._handle_key(event.key)
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            self._handle_click(event.pos)

    # Maneja eventos de teclado para controles globales
    def _handle_key(self, key: int):
        if key == pygame.K_ESCAPE:
            if self._fullscreen:
                self._toggle_fullscreen()
            else:
                self._quit()
        elif key == pygame.K_F11:
            self._toggle_fullscreen()
        elif key == pygame.K_n:
            self._gs.reset()
            self._promo_rects = []
        elif key in (pygame.K_z, pygame.K_BACKSPACE):
            self._gs.undo()
            self._promo_rects = []
        elif key == pygame.K_f:
            self._gs.flipped = not self._gs.flipped

    # Maneja eventos de clic para seleccionar / mover piezas
    def _handle_click(self, pos: tuple):
        mx, my = pos

        # Clic sobre el modal de promocion activo
        if self._gs.promotion_pending:
            for rect, pt in self._promo_rects:
                if rect.collidepoint(mx, my):
                    self._gs.confirm_promotion(pt)
                    self._promo_rects = []
                    break
            return

        # Ignorar clics cuando la partida ha terminado
        if self._gs.game_over:
            return

        # Clic sobre el tablero
        sq = self._board.px_to_sq(mx, my, self._gs.flipped)
        if sq is not None:
            self._gs.click_square(sq)

    # ── Renderizado ───────────────────────────────────────────────────────────

    # Renderiza todos los componentes en el orden correcto y maneja el modal de promocion
    def _render(self):
        self._screen.fill(Theme.BG)
        self._adv_bar.draw(self._gs)
        self._board.draw(self._gs)
        self._panel.draw(self._gs)

        if self._gs.promotion_pending:
            self._promo_rects = self._modal.draw_promotion(self._gs.board.turn, pygame.mouse.get_pos())
        elif self._gs.game_over:
            self._modal.draw_game_over(self._gs.game_over_msg)

    # ── Gestion de ventana ────────────────────────────────────────────────────

    # Redimensiona la ventana y recalcula el layout
    def _resize(self, w: int, h: int):
        self._layout = Layout(w, h)
        self._fonts.reload(self._layout)
        self._board.update_layout(self._layout)
        self._panel.update_layout(self._layout, self._fonts)
        self._modal.update_layout(self._layout, self._fonts)
        self._adv_bar.update_layout(self._layout)

    # Alterna entre modo pantalla completa y ventana
    def _toggle_fullscreen(self):
        self._fullscreen = not self._fullscreen

        if self._fullscreen:
            info = pygame.display.Info()
            self._screen = pygame.display.set_mode(
                (info.current_w, info.current_h), pygame.FULLSCREEN)
            self._resize(info.current_w, info.current_h)
        else:
            self._screen = pygame.display.set_mode(
                (Layout.BASE_W, Layout.BASE_H), pygame.RESIZABLE)
            self._resize(Layout.BASE_W, Layout.BASE_H)

        for renderer in (self._board, self._panel, self._modal, self._adv_bar):
            renderer.surface = self._screen

    # Cierra pygame y sale del programa
    @staticmethod
    def _quit():
        pygame.quit()
        sys.exit()