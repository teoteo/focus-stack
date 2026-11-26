# Esempio di calibrazione (matita, 2026-11-26)

Pila `Pencil_20261126-100229` (68 scatti) e set `flat_20261126-101412`, `dark_20261126-101753`,
`flat-dark_20261126-101609` nella cartella Prove focuser. Sony A6400, 70-350 mm a 350 mm, Raynox +8 diottrie,
f/20, ISO 400, 1/20 s.

- `flat-normalizzato.png`: F = (media flat − media dark dei flat) ÷ sua media, contrasto accentuato.
- `originale.jpg`: Pencil_0035, luce lineare decodificata con LibRaw, resa sRGB.
- `corretto.jpg`: (I − D) ÷ F con la stessa resa dell'originale.
- `calibrazione-esempio.jpg`: la figura della guida (tre pannelli, macchia a x 2177, y 880); genera_guida.py la copia in img/<lingua>/.

Tutto a metà risoluzione (3012 × 2012). Servono anche per la guida di Focus Fusion. I tre file a piena
risoluzione non sono nel repository (.gitignore): si rifanno dai RAW con gli script.
Per rifarle: `script/rawdump.cpp` (compilato con gli oggetti di build/rawstat/obj, tranne rawstat.o),
poi `masters.py` e `figure.py` (Python 3.11 con numpy e Pillow).
