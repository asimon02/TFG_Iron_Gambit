"""
game_state.py -- Logica de ajedrez pura, sin dependencia de pygame

Gestiona el tablero, el historial, la seleccion de piezas, los movimientos
legales, la promocion de peones y la deteccion del fin de partida
"""

import chess

class GameState:
    """
    Encapsula todo el estado logico de la partida

    Esta clase no importa ni usa pygame en absoluto, lo que la hace
    facilmente testeable de forma independiente

    Atributos publicos
    ------------------
    board              : chess.Board  -- posicion actual
    san_history        : list[str]    -- movimientos en notacion SAN
    selected_sq        : chess.Square -- casilla seleccionada (o None)
    legal_moves        : list[Move]   -- movimientos legales desde selected_sq
    flipped            : bool         -- tablero girado (negras abajo)
    promotion_pending  : chess.Move   -- movimiento pendiente de promocion
    game_over          : bool
    game_over_msg      : str
    """

    # Inicializa un nuevo estado de partida con la posicion inicial y sin movimientos
    def __init__(self):
        self.board              = chess.Board()
        self._fen_history       = []
        self.san_history        = []
        self.selected_sq        = None
        self.legal_moves        = []
        self.flipped            = False
        self.promotion_pending  = None
        self.game_over          = False
        self.game_over_msg      = ""
        self.checkmate_winner   = None
        self.view_move_idx      = None

    # -- API publica ----------------------------------------------------------

    def reset(self):
        self.__init__()

    # Maneja un clic en el tablero, seleccionando o moviendo piezas segun el contexto
    def click_square(self, sq: chess.Square):
        if self.game_over or self.promotion_pending:
            return

        piece = self.board.piece_at(sq)

        if self.selected_sq is not None:
            move = self._match(self.selected_sq, sq)
            if move:
                piece_moving = self.board.piece_at(self.selected_sq)
                is_promotion = (
                    piece_moving is not None
                    and piece_moving.piece_type == chess.PAWN
                    and chess.square_rank(sq) in (0, 7)
                )
                if is_promotion:
                    self.promotion_pending = chess.Move(self.selected_sq, sq)
                    return
                self._execute(move)
                return

            if piece and piece.color == self.board.turn:
                self._select(sq)
                return

            self._deselect()
            return

        if piece and piece.color == self.board.turn:
            self._select(sq)

    # Confirma la promocion de un peon, ejecutando el movimiento con la pieza elegida
    def confirm_promotion(self, piece_type: int):
        if not self.promotion_pending:
            return
        move = chess.Move(
            self.promotion_pending.from_square,
            self.promotion_pending.to_square,
            promotion=piece_type,
        )
        self.promotion_pending = None
        self._execute(move)

    # Ejecuta un movimiento del motor directamente (sin seleccion ni validacion de UI)
    def apply_engine_move(self, move):
        if self.game_over or self.promotion_pending:
            return
        if move in self.board.legal_moves:
            self._execute(move)

    # Deshace el ultimo movimiento, restaurando el estado anterior
    def undo(self):
        if not self._fen_history:
            return
        self.board.set_fen(self._fen_history.pop())
        self.san_history.pop()
        self._deselect()
        self.game_over = False
        self._refresh()

    # -- Propiedades de conveniencia ------------------------------------------

    # Ultimo movimiento en formato SAN, o None si no hay movimientos
    @property
    def last_move(self):
        return self.board.peek() if self.board.move_stack else None

    # Lista de piezas capturadas por cada bando, en orden de captura
    def captured_pieces(self):
        by_white, by_black = [], []
        tmp = chess.Board()
        for mv in self.board.move_stack:
            cap = tmp.piece_at(mv.to_square)
            if tmp.is_en_passant(mv):
                ep  = mv.to_square + (-8 if tmp.turn == chess.WHITE else 8)
                cap = tmp.piece_at(ep)
            if cap:
                (by_white if tmp.turn == chess.WHITE else by_black).append(cap.symbol())
            tmp.push(mv)
        return by_white, by_black

    # -- Internos -------------------------------------------------------------

    # Selecciona una casilla y calcula los movimientos legales desde ella
    def _select(self, sq: chess.Square):
        self.selected_sq = sq
        self.legal_moves = [m for m in self.board.legal_moves if m.from_square == sq]
        self._refresh()

    # Deselecciona cualquier casilla seleccionada y borra los movimientos legales
    def _deselect(self):
        self.selected_sq = None
        self.legal_moves = []
        self._refresh()

    # Busca un movimiento legal que coincida con las casillas de origen y destino dadas
    def _match(self, from_sq: chess.Square, to_sq: chess.Square):
        for m in self.legal_moves:
            if m.from_square == from_sq and m.to_square == to_sq:
                return m
        return None

    # Ejecuta un movimiento, actualizando el historial y comprobando el fin de partida
    def _execute(self, move: chess.Move):
        self._fen_history.append(self.board.fen())
        self.san_history.append(self.board.san(move))
        self.board.push(move)
        self._deselect()
        self._check_end()

    def _refresh(self):
        return

    # Comprueba si la partida ha terminado por jaque mate, tablas o cualquier otra condicion
    def _check_end(self):
        b = self.board
        if b.is_checkmate():
            w = "Blancas" if b.turn == chess.BLACK else "Negras"
            self.checkmate_winner = chess.BLACK if b.turn == chess.WHITE else chess.WHITE
            self._end("Jaque Mate! Ganan las " + w)
        elif b.is_stalemate():
            self._end("Tablas - Ahogado")
        elif b.is_insufficient_material():
            self._end("Tablas - Material insuficiente")
        elif b.is_seventyfive_moves():
            self._end("Tablas - Regla de los 75 movimientos")
        elif b.is_fivefold_repetition():
            self._end("Tablas - Quíntuple repetición")
        elif b.can_claim_threefold_repetition():
            self._end("Tablas - Triple repetición")
        elif b.can_claim_fifty_moves():
            self._end("Tablas - Regla de los 50 movimientos")
        elif b.is_game_over(claim_draw=True):
            self._end("Tablas - Partida finalizada")

    # Marca la partida como terminada
    def _end(self, msg: str):
        self.game_over     = True
        self.game_over_msg = msg

    # Calcula la ventaja material actual, sumando el valor de las piezas de cada bando
    def material_advantage(self) -> float:
        VALUES = {
            chess.PAWN:   1,
            chess.KNIGHT: 3,
            chess.BISHOP: 3,
            chess.ROOK:   5,
            chess.QUEEN:  9,
        }
        score = 0
        board = self.display_board
        for piece_type, value in VALUES.items():
            score += len(board.pieces(piece_type, chess.WHITE)) * value
            score -= len(board.pieces(piece_type, chess.BLACK)) * value
        return score

    @property
    def display_board(self) -> chess.Board:
        if self.view_move_idx is None or self.view_move_idx >= len(self.san_history):
            return self.board
        
        board = chess.Board()
        if self.view_move_idx + 1 < len(self._fen_history):
            board.set_fen(self._fen_history[self.view_move_idx + 1])
            return board
        else:
            return self.board

    @property
    def display_last_move(self):
        b = self.display_board
        return b.peek() if b.move_stack else None

