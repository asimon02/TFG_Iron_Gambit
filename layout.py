"""
layout.py — Geometria dinamica de la ventana

Calcula en tiempo real el tamaño de casilla, posicion del tablero y
dimensiones del panel lateral para que todo entre correctamente en
cualquier resolucion o tamaño de ventana
"""

class Layout:
    """
    Calcula los valores de layout a partir del tamaño real de la ventana

    Atributos publicos
    ------------------
    sq        : int   — pixeles por lado de cada casilla
    board_px  : int   — pixeles totales del tablero (sq * 8)
    bx, by    : int   — esquina superior-izquierda del tablero
    px, py    : int   — esquina superior-izquierda del panel lateral
    pw, ph    : int   — ancho y alto disponibles del panel
    bax, bay  : int   — esquina superior-izquierda de la barra de ventaja
    baw, bah  : int   — ancho y alto de la barra de ventaja
    """

    # Geometria base del layout
    BASE_W = 1020
    BASE_H = 680

    # Limites de tamaño de casilla
    SQ_MIN = 44
    SQ_MAX = 92

    # Ancho minimo del panel para que el texto sea legible
    PANEL_MIN_W = 200

    def __init__(self, w: int, h: int):
        self.update(w, h)

    # Actualiza el layout con un nuevo tamaño de ventana
    def update(self, w: int, h: int):
        self.w = w
        self.h = h

        margin    = max(12, int(h * 0.022))
        coord_gap = 18
        COORD_BOT = 20
        BAR_W     = 10
        BAR_GAP   = 8

        # Casilla: el cuadrado mas grande que deja espacio al panel
        sq = min(
            (h - margin * 2 - COORD_BOT) // 8,
            (w - self.PANEL_MIN_W - margin * 3 - coord_gap - BAR_W - BAR_GAP * 2) // 8,
        )
        sq = max(self.SQ_MIN, min(sq, self.SQ_MAX))

        self.sq       = sq
        self.board_px = sq * 8

        # Tablero centrado verticalmente, con hueco para coordenadas a la izquierda
        self.bx = margin + coord_gap
        self.by = (h - self.board_px - COORD_BOT) // 2

        # Barra de ventaja: entre el tablero y el panel
        self.bax = self.bx + self.board_px + BAR_GAP
        self.bay = self.by
        self.baw = BAR_W
        self.bah = self.board_px

        # Panel: justo a la derecha del tablero
        self.px  = self.bax + BAR_W + BAR_GAP * 2
        self.pw  = w - self.px - margin
        self.py  = self.by
        self.ph  = self.board_px