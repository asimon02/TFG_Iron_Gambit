"""
utils.py -- Funciones auxiliares compartidas entre renderers
"""

import pygame

def wrap_text(text: str, font: pygame.font.Font, max_width: int) -> list:
    """
    Divide text en lineas que no superen max_width pixeles
    Devuelve una lista de cadenas (nunca vacia)
    """
    words   = text.split()
    lines   = []
    current = ""

    # Construye cada linea añadiendo palabras hasta que se supere max_width
    for word in words:
        candidate = (current + " " + word).strip()
        if font.size(candidate)[0] <= max_width:
            current = candidate
        else:
            if current:
                lines.append(current)
            current = word

    # Añade la ultima linea si no esta vacia
    if current:
        lines.append(current)

    return lines or [text]