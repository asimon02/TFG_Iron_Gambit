@echo off
echo ===================================================
echo   Compilando Iron Gambit a Ejecutable (.exe)
echo ===================================================
echo.
echo 1. Compilando con PyInstaller...
pyinstaller --paths=src --paths=src/core --paths=src/ui --paths=src/hardware --paths=src/common --noconsole --onefile --icon=images/Icon.png --name="Iron_Gambit" --distpath=. --add-data "images;images" --add-data "stockfish/stockfish-windows-x86-64-avx2.exe;stockfish" main.py
echo.
echo 2. Limpiando cache de compilacion...
if exist build (
    rd /s /q build
)
echo.
echo ===================================================
echo   Compilacion completada!
echo   El ejecutable se encuentra en la raiz del proyecto:
echo   .\Iron_Gambit.exe
echo ===================================================
pause
