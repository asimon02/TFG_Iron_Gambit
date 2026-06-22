"""
utils.py -- Funciones auxiliares compartidas entre renderers
"""

import sys
import os
import pygame

def resource_path(relative_path: str) -> str:
    """
    Obtiene la ruta absoluta a un recurso, compatible con la ejecucion
    de desarrollo y con el empaquetado de PyInstaller.
    """
    try:
        # PyInstaller crea una carpeta temporal y guarda la ruta en _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_path, relative_path)

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