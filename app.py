"""
app.py -- Bucle principal, ventana pygame y orquestacion de componentes

La clase App es el punto de entrada de la aplicacion. Gestiona:
  - Creacion y configuracion de la ventana
  - Bucle de eventos y renderizado
  - Redimensionado dinamico y recalculo de layout
  - Modo pantalla completa / ventana
  - Motor de ajedrez (Stockfish) y eleccion de bando
  - Propagacion de cambios de layout a todos los renderers
"""

import random
import threading
import pygame
import queue
from typing import Optional
import chess

from hr_monitor     import HeartRateMonitor
from adaptation_engine import AdaptationEngine
from advantage_bar  import AdvantageBar
from layout         import Layout
from font_manager   import FontManager
from game_state     import GameState
from board_renderer import BoardRenderer
from panel_renderer import PanelRenderer
from modal_renderer import ModalRenderer
from top_bar        import TopBar
from side_selector  import SideSelector, SIDE_WHITE, SIDE_BLACK, SIDE_HUMAN
from engine         import Engine
from theme          import Theme

class App:
    """
    Orquesta todos los componentes de la aplicacion y ejecuta el bucle principal

    Controles
    ---------
    Clic izquierdo  -- seleccionar / mover pieza
    N               -- nueva partida (abre selector de bando)
    Z               -- deshacer movimiento
    R               -- rotar tablero
    F11             -- pantalla completa / ventana
    Esc             -- cerrar desplegable / salir de pantalla completa / salir
    """

    TITLE = "Iron Gambit"
    FPS   = 120
    INITIAL_TIME_SECONDS = 5 * 60

    def __init__(self):
        pygame.init()

        try:
            icon = pygame.image.load("images/icon.png")
            pygame.display.set_icon(icon)
        except Exception:
            pass

        self._fullscreen = False
        self._screen     = pygame.display.set_mode(
            (Layout.BASE_W, Layout.BASE_H), pygame.RESIZABLE)
        pygame.display.set_caption(self.TITLE)
        self._clock = pygame.time.Clock()
        self._running = True
        self._cleanup_done = False

        # Motor UCI
        self._engine      = Engine("stockfish/stockfish-windows-x86-64-avx2.exe")
        self._human_side  = SIDE_WHITE
        self._engine_thinking = False

        # Componentes principales
        self._layout = Layout(Layout.BASE_W, Layout.BASE_H)
        self._fonts  = FontManager(self._layout)
        self._gs     = GameState()

        # Renderers
        self._board    = BoardRenderer(self._screen, self._fonts, self._layout)
        self._panel    = PanelRenderer(self._screen, self._fonts, self._layout)
        self._modal    = ModalRenderer(self._screen, self._fonts, self._layout)
        self._adv_bar  = AdvantageBar(self._screen, self._layout)
        self._top_bar  = TopBar(
            self._screen,
            self._engine.name,
            self._engine.level,
            self.INITIAL_TIME_SECONDS,
        )
        self._selector = SideSelector(self._screen, self._fonts, self._layout)

        # Retraso aleatorio del motor (ms)
        self._ENGINE_DELAY_MIN = 1000
        self._ENGINE_DELAY_MAX = 2000
        self._engine_move_ready   = None
        self._engine_move_at      = None
        self._anim_duration_ms    = 250
        self._pending_move        = None
        self._pending_is_engine   = False

        # Drag diferido: se activa solo cuando el raton sale de la casilla origen
        self._drag_candidate_sq   = None
        self._drag_active         = False

        # Monitor de Frecuencia Cardiaca
        self._hr_queue = queue.Queue()
        self._hr_monitor = HeartRateMonitor(data_queue=self._hr_queue)
        self._hr_monitor.start()
        self._current_hr = None
        self._adaptation_engine = AdaptationEngine()
        self._hr_state = "normal"
        self._average_hr = None
        self._show_hr_stop = False
        self._hr_threshold_zone = "normal"

        # Mostrar selector al arrancar
        self._selector.show()

        self._promo_rects  = []
        self._close_rect   = None
        self._confirm_exit_active = False
        self._confirm_yes_rect: Optional[pygame.Rect] = None
        self._confirm_no_rect: Optional[pygame.Rect] = None
        self._clock_times = {
            chess.WHITE: float(self.INITIAL_TIME_SECONDS),
            chess.BLACK: float(self.INITIAL_TIME_SECONDS),
        }
        self._last_frame_ms = pygame.time.get_ticks()

    # -- Bucle principal -------------------------------------------------------

    def run(self):
        try:
            while self._running:
                now_ms = pygame.time.get_ticks()
                dt = max(0.0, (now_ms - self._last_frame_ms) / 1000.0)
                self._last_frame_ms = now_ms

                for event in pygame.event.get():
                    self._handle_event(event)

                if not self._running:
                    break

                # Actualizar FC y aplicar efectos sobre la interfaz / reloj
                try:
                    while True:
                        bpm = self._hr_queue.get_nowait()
                        self._current_hr = bpm
                        self._adaptation_engine.add_reading(bpm)
                        self._average_hr = self._adaptation_engine.get_average_bpm()
                        self._hr_state = self._adaptation_engine.get_hr_state(self._current_hr)
                        self._show_hr_stop = (self._hr_state == "high")
                        self._apply_hr_threshold_effect()
                except queue.Empty:
                    pass

                self._update_chess_clock(dt)

                # Disparar movimiento del motor si corresponde
                self._maybe_engine_move()
                # Ejecutar movimiento pendiente cuando la animacion termine
                self._maybe_apply_pending()

                self._render()
                pygame.display.flip()
                self._clock.tick(self.FPS)
        except KeyboardInterrupt:
            self._confirm_exit()
        finally:
            self._cleanup()

    # -- Motor -----------------------------------------------------------------

    # Ejecuta el movimiento pendiente cuando la animacion ha terminado
    def _maybe_apply_pending(self):
        if self._pending_move is None:
            return
        if self._board.is_animating():
            return

        move = self._pending_move
        self._pending_move = None
        self._board.clear_anim()

        if not self._gs.game_over:
            if self._pending_is_engine:
                self._gs.apply_engine_move(move)
            else:
                self._gs.click_square(move.to_square)
            self._promo_rects = []

    # Comprueba si es el turno del motor
    def _is_engine_turn(self) -> bool:
        if self._human_side == SIDE_HUMAN:
            return False
        if not self._engine.ready:
            return False
        if self._gs.game_over or self._gs.promotion_pending:
            return False
        if self._selector.active:
            return False
        import chess
        turn = self._gs.board.turn
        if self._human_side == SIDE_WHITE:
            return turn == chess.BLACK
        return turn == chess.WHITE

    # Lanza el calculo del motor en un hilo si es su turno
    def _maybe_engine_move(self):
        if self._engine_move_ready is not None:
            if pygame.time.get_ticks() >= self._engine_move_at:
                move = self._engine_move_ready
                self._engine_move_ready = None
                self._engine_move_at    = None
                if not self._gs.game_over and move in self._gs.board.legal_moves:
                    self._board.start_anim(self._gs, move)
                    self._pending_move      = move
                    self._pending_is_engine = True
            return

        if not self._is_engine_turn() or self._engine_thinking:
            return
        self._engine_thinking = True

        def think():
            current_fen = self._gs.board.fen()
            move = self._engine.best_move(self._gs.board)
            if move and not self._gs.game_over and self._running and pygame.get_init():
                try:
                    pygame.event.post(pygame.event.Event(
                        pygame.USEREVENT, {"engine_move": move, "fen": current_fen}))
                except pygame.error:
                    pass
            self._engine_thinking = False

        threading.Thread(target=think, daemon=True).start()

    # -- Gestion de eventos ---------------------------------------------------

    def _handle_event(self, event: pygame.event.Event):
        if event.type == pygame.QUIT:
            self._request_exit_confirmation()
            return

        if self._confirm_exit_active:
            if event.type == pygame.KEYDOWN:
                self._handle_key(event.key)
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                self._handle_click(event.pos)
            return

        if event.type == pygame.USEREVENT:
            move = getattr(event, "engine_move", None)
            fen  = getattr(event, "fen", None)
            if move and not self._gs.game_over and fen == self._gs.board.fen():
                delay = random.randint(self._ENGINE_DELAY_MIN, self._ENGINE_DELAY_MAX)
                self._engine_move_ready = move
                self._engine_move_at    = pygame.time.get_ticks() + delay

        elif event.type == pygame.VIDEORESIZE:
            self._resize(event.w, event.h)

        elif event.type == pygame.KEYDOWN:
            self._top_bar.handle_key(event.key)
            self._handle_key(event.key)

        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            self._handle_click(event.pos)

        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            self._handle_release(event.pos)

        elif event.type == pygame.MOUSEMOTION:
            if self._drag_active:
                self._board.update_drag(event.pos)
            elif self._drag_candidate_sq is not None:
                hover_sq = self._board.px_to_sq(event.pos[0], event.pos[1],
                                                self._gs.flipped)
                if hover_sq != self._drag_candidate_sq:
                    self._drag_active = True
                    self._board.start_drag(self._gs, self._drag_candidate_sq,
                                           event.pos)

        elif event.type == pygame.MOUSEWHEEL:
            self._panel.handle_scroll(event.y)

        # Procesar cambios en la barra superior
        if self._top_bar.level_changed:
            self._engine.set_level(self._top_bar.selected_level)
        if self._top_bar.time_changed:
            self.INITIAL_TIME_SECONDS = self._top_bar.selected_time_seconds
            self._reset_chess_clock()
        self._top_bar.clear_flags()

    def _handle_key(self, key: int):
        if self._confirm_exit_active:
            if key in (pygame.K_ESCAPE, pygame.K_n):
                self._cancel_exit_confirmation()
            elif key in (pygame.K_RETURN, pygame.K_y, pygame.K_s):
                self._confirm_exit()
            return

        if key == pygame.K_ESCAPE:
            if self._fullscreen:
                self._toggle_fullscreen()
            else:
                self._request_exit_confirmation()
        elif key == pygame.K_F11:
            self._toggle_fullscreen()
        elif key == pygame.K_n:
            self._promo_rects = []
            self._engine_thinking = False
            self._selector.show()
        elif key in (pygame.K_z, pygame.K_BACKSPACE):
            if not self._engine_thinking:
                self._gs.undo()
                if self._is_engine_turn():
                    self._gs.undo()
                self._promo_rects = []
                self._engine_move_ready = None
                self._pending_move      = None
                self._board.clear_anim()
        elif key == pygame.K_r:
            self._gs.flipped = not self._gs.flipped

    def _handle_click(self, pos: tuple):
        mx, my = pos

        if self._confirm_exit_active:
            if self._confirm_yes_rect and self._confirm_yes_rect.collidepoint(mx, my):
                self._confirm_exit()
            elif self._confirm_no_rect and self._confirm_no_rect.collidepoint(mx, my):
                self._cancel_exit_confirmation()
            else:
                self._cancel_exit_confirmation()
            return

        # La barra superior consume el clic primero
        if self._top_bar.handle_click(pos):
            return

        # Modal selector de bando
        if self._selector.active:
            choice = self._selector.handle_click(pos)
            if choice is not None:
                self._start_game(choice)
            return

        # Modal de promocion
        if self._gs.promotion_pending:
            for rect, pt in self._promo_rects:
                if rect.collidepoint(mx, my):
                    self._gs.confirm_promotion(pt)
                    self._promo_rects = []
                    break
            return

        if self._gs.game_over:
            if self._close_rect and self._close_rect.collidepoint(mx, my):
                self._gs.game_over = False
                self._close_rect   = None
            return

        # Solo procesar clic si es turno humano y no hay animacion en curso
        if self._is_engine_turn() or self._engine_thinking or self._board.is_animating():
            return

        sq = self._board.px_to_sq(mx, my, self._gs.flipped)
        if sq is not None:
            import chess as _chess
            piece = self._gs.board.piece_at(sq)
            # Si la pieza es del turno actual, registrar candidato a drag
            if piece and piece.color == self._gs.board.turn:
                self._gs.click_square(sq)
                self._drag_candidate_sq = sq
                self._drag_active       = False
                return
            # Si hay seleccion y el destino es valido, animar
            if self._gs.selected_sq is not None:
                legal_targets = [m.to_square for m in self._gs.legal_moves]
                if sq in legal_targets:
                    fake_move = _chess.Move(self._gs.selected_sq, sq)
                    self._board.start_anim(self._gs, fake_move)
                    self._pending_move      = fake_move
                    self._pending_is_engine = False
                    return
            self._gs.click_square(sq)

    # Gestiona la suelta del boton del raton para completar el drag
    def _handle_release(self, pos: tuple):
        mx, my = pos

        # Drag real: soltar la pieza en la casilla destino
        if self._drag_active:
            self._board.end_drag()
            self._drag_active       = False
            self._drag_candidate_sq = None
            to_sq = self._board.px_to_sq(mx, my, self._gs.flipped)
            if to_sq is not None:
                import chess as _chess
                legal_targets = [m.to_square for m in self._gs.legal_moves]
                if to_sq in legal_targets:
                    self._gs.click_square(to_sq)
                    self._promo_rects = []
        else:
            self._drag_candidate_sq = None

    # -- Nueva partida --------------------------------------------------------

    # Inicia una nueva partida con el bando elegido
    def _start_game(self, side: str):
        self._human_side        = side
        self._engine_thinking   = False
        self._engine_move_ready = None
        self._pending_move      = None
        self._board.clear_anim()
        self._gs.reset()
        self._promo_rects = []
        self._reset_chess_clock()

        self._gs.flipped = (side == SIDE_BLACK)

    # -- Renderizado ----------------------------------------------------------

    def _render(self):
        self._screen.fill(Theme.BG)

        # Barra superior (fondo y controles, sin desplegables abiertos)
        self._top_bar.draw(
            self._engine.ready,
            self._current_hr,
            self._average_hr,
            self._hr_state,
            self._show_hr_stop,
        )
        self._adv_bar.draw(self._gs)
        self._board.draw(self._gs)
        self._panel.draw(
            self._gs,
            self._clock_times,
            self._gs.board.turn,
            self._format_clock(self._clock_times[chess.WHITE]),
            self._format_clock(self._clock_times[chess.BLACK]),
        )

        if self._gs.promotion_pending:
            self._promo_rects = self._modal.draw_promotion(
                self._gs.board.turn, pygame.mouse.get_pos())
        elif self._gs.game_over:
            self._close_rect = self._modal.draw_game_over(self._gs.game_over_msg)

        # Modal selector de bando
        if self._selector.active:
            self._selector.draw(pygame.mouse.get_pos())

        # Indicador "pensando..."
        if self._engine_thinking:
            self._draw_thinking()

        # Desplegables de la barra superior AL FINAL para quedar sobre todo
        self._top_bar.draw_overlays()

        if self._confirm_exit_active:
            self._confirm_yes_rect, self._confirm_no_rect = self._modal.draw_exit_confirmation()

    # Muestra un pequeno indicador de que el motor esta pensando
    def _draw_thinking(self):
        f = pygame.font.SysFont("Tahoma", 11)
        s = f.render("Motor pensando...", True, Theme.GOLD)
        L = self._layout
        x = L.px
        y = L.py + L.ph + 4
        self._screen.blit(s, (x, y))

    # -- Gestion de ventana --------------------------------------------------

    def _resize(self, w: int, h: int):
        self._layout = Layout(w, h)
        self._fonts.reload(self._layout)
        self._board.update_layout(self._layout)
        self._panel.update_layout(self._layout, self._fonts)
        self._modal.update_layout(self._layout, self._fonts)
        self._adv_bar.update_layout(self._layout)
        self._selector.update_layout(self._layout, self._fonts)

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

        for r in (self._board, self._panel, self._modal,
                  self._adv_bar, self._top_bar, self._selector):
            r.surface = self._screen

    def _request_exit_confirmation(self):
        self._confirm_exit_active = True
        self._confirm_yes_rect = None
        self._confirm_no_rect = None

    def _cancel_exit_confirmation(self):
        self._confirm_exit_active = False
        self._confirm_yes_rect = None
        self._confirm_no_rect = None

    def _confirm_exit(self):
        self._running = False
        self._confirm_exit_active = False

    def _cleanup(self):
        if self._cleanup_done:
            return

        self._cleanup_done = True
        self._confirm_exit_active = False
        self._engine_move_ready = None
        self._pending_move = None
        self._engine_thinking = False

        if hasattr(self, "_hr_monitor") and self._hr_monitor:
            self._hr_monitor.stop()

        if hasattr(self, "_engine") and self._engine:
            self._engine.close()

        if pygame.get_init():
            pygame.quit()

    def _reset_chess_clock(self):
        self._clock_times[chess.WHITE] = float(self.INITIAL_TIME_SECONDS)
        self._clock_times[chess.BLACK] = float(self.INITIAL_TIME_SECONDS)
        self._last_frame_ms = pygame.time.get_ticks()

    def _apply_hr_threshold_effect(self):
        zone = self._hr_state
        if zone == "normal":
            self._hr_threshold_zone = "normal"
            return

        if zone == self._hr_threshold_zone:
            return

        if zone == "low":
            self._adjust_human_clock(-10.0)
        elif zone == "high":
            self._adjust_human_clock(10.0)

        self._hr_threshold_zone = zone

    def _adjust_human_clock(self, delta_seconds: float):
        target_color = None
        if self._human_side == SIDE_WHITE:
            target_color = chess.WHITE
        elif self._human_side == SIDE_BLACK:
            target_color = chess.BLACK

        if target_color is None:
            return

        self._clock_times[target_color] = max(
            0.0,
            self._clock_times[target_color] + delta_seconds,
        )

    def _update_chess_clock(self, dt: float):
        if dt <= 0.0 or self._gs.game_over or self._selector.active or self._confirm_exit_active:
            return

        active_color = self._gs.board.turn
        self._clock_times[active_color] = max(0.0, self._clock_times[active_color] - dt)

        if self._clock_times[active_color] <= 0.0:
            winner = "Negras" if active_color == chess.WHITE else "Blancas"
            self._gs.game_over = True
            self._gs.game_over_msg = f"Tiempo agotado - Ganan las {winner}"
            self._gs.checkmate_winner = None
            self._engine_move_ready = None
            self._engine_move_at = None
            self._pending_move = None
            self._engine_thinking = False

    def _format_clock(self, remaining_seconds: float) -> str:
        total = max(0, int(remaining_seconds))
        minutes = total // 60
        seconds = total % 60
        return f"{minutes:02d}:{seconds:02d}"
