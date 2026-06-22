"""
main.py — Punto de entrada de Iron Gambit
"""

import sys
import os

# Configurar rutas para encontrar los archivos en sus nuevas subcarpetas
base_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.join(base_dir, "src")

# Añadir src y todas las subcarpetas a sys.path
sys.path.insert(0, src_dir)
sys.path.insert(0, os.path.join(src_dir, "core"))
sys.path.insert(0, os.path.join(src_dir, "ui"))
sys.path.insert(0, os.path.join(src_dir, "hardware"))
sys.path.insert(0, os.path.join(src_dir, "common"))

from app import App

if __name__ == "__main__":
    App().run()