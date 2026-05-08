"""
theme.py -- Paleta de colores y constantes visuales (estetica Kingambit)

Todos los colores de la aplicacion estan centralizados aqui para facilitar
futuros cambios de tema sin tocar el resto del codigo
"""

class Theme:
    """
    Paleta de colores inspirada en Pokemon Kingambit:
      - Negro profundo  -> fondos
      - Rojo carmesi    -> acentos, bordes y alertas
      - Dorado          -> destacados, marcos y seleccion
      - Gris acero      -> elementos secundarios
      - Blanco / Negro  -> piezas (maximo contraste sobre tablero gris)
    """

    # -- Fondos ---------------------------------------------------------------
    BG           = ( 10,  10,  12)
    BG_PANEL     = ( 22,  24,  28)
    BG_CARD      = ( 30,  32,  38)
    BG_CARD_ALT  = ( 38,  40,  46)
    BG_SOFT      = ( 48,  50,  58)

    # -- Rojo carmesi (cuerpo de Kingambit) -----------------------------------
    CRIMSON      = (192,  39,  45)
    CRIMSON_LT   = (228,  68,  74)
    CRIMSON_DIM  = ( 98,  18,  22)

    # -- Dorado (filos de Kingambit) ------------------------------------------
    GOLD         = (210, 158,  18)
    GOLD_LT      = (242, 196,  56)

    # -- Gris acero (armadura de Kingambit) -----------------------------------
    STEEL        = (108, 116, 128)
    STEEL_LT     = (155, 162, 172)

    # -- Texto ----------------------------------------------------------------
    TEXT         = (245, 245, 245)
    TEXT_SOFT    = (184, 188, 194)
    TEXT_DIM     = (142, 146, 154)

    # -- Piezas ---------------------------------------------------------------
    PIECE_WHITE  = (235, 235, 235)
    PIECE_BLACK  = ( 18,  18,  20)
    SHADOW_WHITE = ( 50,  50,  50)
    SHADOW_BLACK = (155, 155, 155)

    # -- Tablero -- grises neutros --------------------------------------------
    SQ_LIGHT     = (178, 180, 184)
    SQ_DARK      = ( 80,  84,  92)

    # -- Highlights con canal alfa (RGBA) -------------------------------------
    HL_SELECT    = (210, 158,  18, 168)
    HL_LAST      = (192,  39,  45,  52)
    HL_CHECK     = (230,  40,  46, 210)
    HL_MOVE      = (242, 196,  56, 192)

    # -- Simbolos unicode de piezas -------------------------------------------
    PIECES = {
        "P": "\u265f", "N": "\u265e", "B": "\u265d",
        "R": "\u265c", "Q": "\u265b", "K": "\u265a",
        "p": "\u265f", "n": "\u265e", "b": "\u265d",
        "r": "\u265c", "q": "\u265b", "k": "\u265a",
    }
