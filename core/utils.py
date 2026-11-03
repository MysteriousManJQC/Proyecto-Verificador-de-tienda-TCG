import json
from pathlib import Path
from .tcgplayer import obtener_datos_tcgplayer


def obtener_imagen_carta(nombre_carta):
    """
    Retorna la imagen oficial de la carta desde la base de datos de TCGplayer / catálogo oficial.
    """
    datos = obtener_datos_tcgplayer(nombre_carta)
    if datos and datos.get("imagen_url"):
        return datos["imagen_url"]

    # Fallback a card_images.json
    try:
        ruta = Path(__file__).resolve().parent / "card_images.json"
        with open(ruta, "r", encoding="utf-8") as f:
            imgs = json.load(f)
            if nombre_carta in imgs:
                return imgs[nombre_carta]
    except Exception:
        pass

    import urllib.parse
    q = urllib.parse.quote_plus(nombre_carta or "")
    return f"https://api.scryfall.com/cards/named?fuzzy={q}&format=image&version=small"


def obtener_precio_tcgplayer(nombre_carta):
    """
    Retorna el precio de mercado oficial de TCGplayer en USD (Market Price).
    """
    datos = obtener_datos_tcgplayer(nombre_carta)
    return datos.get("precio_usd", "2.50")


def obtener_url_tcgplayer(nombre_carta):
    """
    Retorna la URL canónica de TCGplayer para consultar o comprar la carta.
    """
    datos = obtener_datos_tcgplayer(nombre_carta)
    import urllib.parse
    q = urllib.parse.quote_plus(nombre_carta or "")
    return datos.get("tcgplayer_url", f"https://www.tcgplayer.com/search/all/product?q={q}")
