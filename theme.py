"""
theme.py — Paleta de colores y constantes visuales (estetica Kingambit)

Todos los colores de la aplicacion estan centralizados aqui para facilitar
futuros cambios de tema sin tocar el resto del codigo
"""

class Theme:
    """
    Paleta de colores inspirada en Pokemon Kingambit:
      - Negro profundo  → fondos
      - Rojo carmesi    → acentos, bordes y alertas
      - Dorado          → destacados, marcos y seleccion
      - Gris acero      → elementos secundarios
      - Blanco / Negro  → piezas (maximo contraste sobre tablero gris)
    """

    # ── Fondos ────────────────────────────────────────────────────────────────
    BG           = ( 10,  10,  12)   # fondo general
    BG_PANEL     = ( 50,  50,  50)   # fondo del panel lateral
    BG_CARD      = ( 30,  30,  36)   # fondo de tarjetas / modales

    # ── Rojo carmesi (cuerpo de Kingambit) ───────────────────────────────────
    CRIMSON      = (192,  39,  45)   # rojo carmesi
    CRIMSON_LT   = (228,  68,  74)   # hover / enfasis
    CRIMSON_DIM  = ( 98,  18,  22)   # divisores, bordes sutiles

    # ── Dorado (filos de Kingambit) ───────────────────────────────────────────
    GOLD         = (210, 158,  18)   # dorado
    GOLD_LT      = (242, 196,  56)   # texto dorado brillante

    # ── Gris acero (armadura de Kingambit) — solo para fondos / bordes ────────
    STEEL        = (108, 116, 128)
    STEEL_LT     = (155, 162, 172)

    # ── Texto ─────────────────────────────────────────────────────────────────
    TEXT         = (255, 255, 255)   # blanco puro

    # ── Piezas ────────────────────────────────────────────────────────────────
    PIECE_WHITE  = (235, 235, 235)   # blanco real
    PIECE_BLACK  = ( 18,  18,  20)   # negro profundo
    SHADOW_WHITE = ( 88,  88,  93)   # sombra de piezas blancas
    SHADOW_BLACK = (  5,   5,   6)   # sombra de piezas negras

    # ── Tablero — grises neutros ──────────────────────────────────────────────
    SQ_LIGHT     = (178, 180, 184)   # casilla clara
    SQ_DARK      = ( 80,  84,  92)   # casilla oscura

    # ── Highlights con canal alfa (RGBA) ──────────────────────────────────────
    HL_SELECT    = (210, 158,  18, 168)   # casilla seleccionada
    HL_LAST      = (192,  39,  45,  52)   # ultimo movimiento
    HL_CHECK     = (230,  40,  46, 210)   # rey en jaque
    HL_MOVE      = (242, 196,  56, 192)   # destino legal

    # ── Simbolos unicode de piezas ────────────────────────────────────────────
    PIECES = {
        "P": "\u2659", "N": "\u2658", "B": "\u2657",
        "R": "\u2656", "Q": "\u2655", "K": "\u2654",
        "p": "\u265f", "n": "\u265e", "b": "\u265d",
        "r": "\u265c", "q": "\u265b", "k": "\u265a",
    }