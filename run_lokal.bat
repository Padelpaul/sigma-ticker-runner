@echo off
REM Distressed-Ticker Feed-Runner, lokale Variante fuer Windows.
REM Legt die Ergebnisse direkt in den Insolvenzen-Ordner, den Cowork lesen kann.
REM Einrichtung: Aufgabenplanung -> Neue Aufgabe -> taeglich 09:40 -> dieses Skript.

set ZIEL=%USERPROFILE%\Desktop\claude code\Insolvenzen\runner
if not exist "%ZIEL%" mkdir "%ZIEL%"

python "%~dp0lib\sammeln.py" --tage 2 --out "%ZIEL%\rohtreffer.json" --digest "%ZIEL%\digest"
python "%~dp0lib\sammeln.py" --feedcheck > "%ZIEL%\digest\feedcheck.txt"

echo Fertig. Ergebnisse in %ZIEL%
