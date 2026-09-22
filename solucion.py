import json

def evaluar_disponibilidad(nombre_carta, expansion, cantidad_solicitada):
    try:
        with open('stock.json', 'r', encoding='utf-8') as archivo:
            inventario = json.load(archivo)
    except FileNotFoundError:
        return " Error: No se encontró el archivo stock.json."

    # 1. Verificar si la carta existe en alguna expansión
    cartas_encontradas = [item for item in inventario if item["carta"].lower() == nombre_carta.lower()]
    if not cartas_encontradas:
        return " La carta no existe en el inventario."

    # 2. Verificar si existe en la expansión pedida
    carta_exacta = next((item for item in cartas_encontradas if item["expansion"].lower() == expansion.lower()), None)
    if not carta_exacta:
        return " Esa carta no pertenece a esa expansión."

    # 3 y 4. Verificar cantidad de stock
    if carta_exacta["stock"] < cantidad_solicitada:
        return f" Stock insuficiente. Disponible: {carta_exacta['stock']}."
    else:
        return f" Se puede vender. Stock disponible: {carta_exacta['stock']}."