"""Erzeugt das App-Symbol für den Startbildschirm.

    python werkzeuge/icon_erzeugen.py

Legt static/app-icon.png (512 px) und app-icon-180.png an – der Ordner static/
wird von nebenkosten/design.py in die Seite eingebettet.
"""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw

ZIEL = Path(__file__).resolve().parents[1] / "static"
DUNKEL = (14, 43, 71)      # tiefes Blau
HELL = (23, 106, 148)      # Petrol
WASSER = (86, 190, 214)    # Tropfenblau
FLAMME = (245, 176, 65)    # Warmes Gelb für die Gasflamme
WEISS = (255, 255, 255)


def verlauf(groesse: int) -> Image.Image:
    """Diagonaler Farbverlauf als Hintergrund."""
    bild = Image.new("RGB", (groesse, groesse), DUNKEL)
    zeichnung = ImageDraw.Draw(bild)
    for i in range(groesse):
        anteil = i / max(groesse - 1, 1)
        farbe = tuple(round(d + (h - d) * anteil) for d, h in zip(DUNKEL, HELL))
        zeichnung.line([(0, i), (groesse, i)], fill=farbe)
    return bild


def abgerundet(bild: Image.Image, radius_anteil: float = 0.22) -> Image.Image:
    """Ecken abrunden, wie bei einem App-Symbol üblich."""
    maske = Image.new("L", bild.size, 0)
    ImageDraw.Draw(maske).rounded_rectangle(
        [(0, 0), (bild.size[0] - 1, bild.size[1] - 1)],
        radius=int(bild.size[0] * radius_anteil), fill=255)
    ergebnis = Image.new("RGBA", bild.size, (0, 0, 0, 0))
    ergebnis.paste(bild, (0, 0), maske)
    return ergebnis


def tropfenform(zeichnung: ImageDraw.ImageDraw, x: float, y: float,
                radius: float, farbe: tuple) -> None:
    """Ein Tropfen: Kreis mit aufgesetzter Spitze. Dient auch als Flamme."""
    zeichnung.ellipse([(x - radius, y - radius), (x + radius, y + radius)], fill=farbe)
    zeichnung.polygon([(x, y - radius * 2.1),
                       (x - radius * 0.9, y + radius * 0.12),
                       (x + radius * 0.9, y + radius * 0.12)], fill=farbe)


def haus(zeichnung: ImageDraw.ImageDraw, g: int) -> None:
    """Weißes Haus, darin ein Wassertropfen und eine Gasflamme.

    Die beiden Zeichen stehen für das, was die App verteilt: Wasser und Gas.
    """
    e = g / 100  # eine Einheit = 1 % der Kantenlänge

    # Dach
    zeichnung.polygon([(50 * e, 14 * e), (88 * e, 44 * e), (12 * e, 44 * e)], fill=WEISS)
    # Wände
    zeichnung.rounded_rectangle([(20 * e, 42 * e), (80 * e, 87 * e)],
                                radius=int(6 * e), fill=WEISS)
    tropfenform(zeichnung, 37 * e, 68 * e, 8.5 * e, WASSER)
    tropfenform(zeichnung, 63 * e, 68 * e, 8.5 * e, FLAMME)


def erzeuge(groesse: int) -> Image.Image:
    # Vierfach zeichnen und verkleinern – das glättet die Kanten.
    gross = groesse * 4
    bild = verlauf(gross)
    haus(ImageDraw.Draw(bild), gross)
    return abgerundet(bild).resize((groesse, groesse), Image.LANCZOS)


if __name__ == "__main__":
    ZIEL.mkdir(parents=True, exist_ok=True)
    for groesse, name in ((512, "app-icon.png"), (180, "app-icon-180.png")):
        erzeuge(groesse).save(ZIEL / name)
        print("geschrieben:", ZIEL / name)
