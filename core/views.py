import requests
from django.shortcuts import render
from solucion import evaluar_disponibilidad

def verificar_carta(request):
    resultado = None
    imagen_url = None
    
    if request.method == 'POST':
        # 1. Capturar datos y limpiar espacios
        juego = request.POST.get('juego')
        nombre = request.POST.get('nombre_carta', '').strip()
        expansion = request.POST.get('expansion', '').strip()
        cantidad = int(request.POST.get('cantidad_solicitada', 0))
        
        # 2. Evaluar regla de negocio local
        resultado = evaluar_disponibilidad(nombre, expansion, cantidad)

        # 3. Consumir la API de imágenes según el juego
        try:
            cabeceras = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            }
            
            if juego == 'pokemon':
                url = f'https://api.pokemontcg.io/v2/cards?q=name:"{nombre}"&pageSize=1'
                respuesta = requests.get(url, headers=cabeceras, timeout=5)
                if respuesta.status_code == 200:
                    datos = respuesta.json()
                    if datos['data']:
                        imagen_url = datos['data'][0]['images']['small']
                        
            elif juego == 'yugioh':
                # API de YGOPRODeck (usa fname para búsquedas difusas/aproximadas)
                url = f'https://db.ygoprodeck.com/api/v7/cardinfo.php?fname={nombre}'
                respuesta = requests.get(url, headers=cabeceras, timeout=5)
                if respuesta.status_code == 200:
                    datos = respuesta.json()
                    if datos['data']:
                        imagen_url = datos['data'][0]['card_images'][0]['image_url_small']
                        
            elif juego == 'magic':
                # API de Scryfall (usa fuzzy para búsquedas aproximadas)
                url = f'https://api.scryfall.com/cards/named?fuzzy={nombre}'
                respuesta = requests.get(url, headers=cabeceras, timeout=5)
                if respuesta.status_code == 200:
                    datos = respuesta.json()
                    if 'image_uris' in datos:
                        imagen_url = datos['image_uris']['normal']
                        
        except Exception as e:
            print(f"--> Error al conectar con la API: {e}")

    return render(request, 'resumen.html', {
        'resultado': resultado,
        'imagen_url': imagen_url
    })