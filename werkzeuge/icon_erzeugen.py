"""Erzeugt das App-Symbol für den Startbildschirm.

    python werkzeuge/icon_erzeugen.py

Legt static/app-icon.png (512 px) und app-icon-180.png an – der Ordner static/
wird von Streamlit unter /app/static/ ausgeliefert.
"""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw

ZIEL = Path(__file__).resolve().parents[1] / "static"
DUNKEL = (14, 43, 71)      # tiefes Blau
HELL = (23, 106, 148)      # Petrol
WASSER = (86, 190, 214)    # Tropfenblau
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


def haus(zeichnung: ImageDraw.ImageDraw, g: int) -> None:
    """Weißes Haus mit einem Wassertropfen in der Mitte."""
    e = g / 100  # eine Einheit = 1 % der Kantenlänge

    # Dach
    zeichnung.polygon([(50 * e, 18 * e), (87 * e, 47 * e), (13 * e, 47 * e)], fill=WEISS)
    # Wände
    zeichnung.rounded_rectangle([(22 * e, 45 * e), (78 * e, 84 * e)],
                                radius=int(5 * e), fill=WEISS)
    # Tropfen: Kreis mit aufgesetzter Spitze
    mitte_x, mitte_y, r = 50 * e, 68 * e, 11.5 * e
    zeichnung.ellipse([(mitte_x - r, mitte_y - r), (mitte_x + r, mitte_y + r)], fill=WASSER)
    zeichnung.polygon([(mitte_x, mitte_y - 22 * e),
                       (mitte_x - r * 0.9, mitte_y + 2 * e),
                       (mitte_x + r * 0.9, mitte_y + 2 * e)], fill=WASSER)


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
