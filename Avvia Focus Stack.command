#!/bin/zsh
# Doppio clic dal Finder per avviare Focus Stack.
cd "$(dirname "$0")"
if [ ! -x .venv/bin/python ]; then
  echo "Prima installazione: creo l'ambiente Python…"
  python3 -m venv .venv || { echo "Serve Python 3 (brew install python)"; read; exit 1; }
  .venv/bin/pip install -q -r requirements.txt
fi
echo "Focus Stack in esecuzione su http://localhost:8765  —  chiudi questa finestra per terminare."
exec .venv/bin/python run.py
