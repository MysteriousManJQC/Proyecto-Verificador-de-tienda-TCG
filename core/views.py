import requests
from functools import wraps
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from solucion import evaluar_disponibilidad
from .models import Registro
from .utils import obtener_imagen_carta, obtener_precio_tcgplayer, obtener_url_tcgplayer


# ── Roles y decoradores (Fase 4 · Criterio 2.1.4) ──

def tiene_rol(user, *roles):
    """Verifica si el usuario pertenece a alguno de los grupos indicados o es superusuario."""
    return user.groups.filter(name__in=roles).exists() or user.is_superuser


def requiere_rol(*roles):
    """
    Decorador que protege vistas en el servidor según roles.
    Si el usuario no tiene el rol correspondiente, muestra un mensaje de error
    y lo redirige a la lista.
    """
    def decorador(view_func):
        @wraps(view_func)
        @login_required(login_url="login")
        def wrapper(request, *args, **kwargs):
            if tiene_rol(request.user, *roles):
                return view_func(request, *args, **kwargs)
            messages.error(request, "No tienes permiso para esta accion.")
            return redirect("lista")
        return wrapper
    return decorador


# ── Autenticación: Login y Logout (Fase 4 · Criterio 2.1.4) ──

def vista_login(request):
    """Vista de inicio de sesión."""
    if request.user.is_authenticated:
        return redirect("lista")
    if request.method == "POST":
        user = authenticate(
            request,
            username=request.POST.get("username", "").strip(),
            password=request.POST.get("password", "")
        )
        if user:
            login(request, user)
            messages.success(request, f"¡Bienvenido/a, {user.username}!")
            return redirect("lista")
        messages.error(request, "Usuario o contrasena incorrectos.")
    return render(request, "login.html")


def vista_logout(request):
    """Cierra la sesión y redirige al login."""
    logout(request)
    messages.info(request, "Has cerrado sesión correctamente.")
    return redirect("login")


# ── Operaciones CRUD (Fase 3 · Criterio 2.1.3) ──

@login_required(login_url="login")
def lista(request):
    """READ: Lista todos los registros activos (eliminado=False). Accesible para todos los autenticados."""
    registros = Registro.objects.filter(eliminado=False)
    return render(request, "lista.html", {"registros": registros})


@requiere_rol("admin", "normal")
def crear(request):
    """CREATE: Formulario de creación de registro. Accesible para admin y normal."""
    error = None
    if request.method == "POST":
        nombre = request.POST.get("nombre", "").strip() or request.POST.get("nombre_carta", "").strip()
        try:
            cantidad = int(request.POST.get("cantidad", "") or request.POST.get("cantidad_solicitada", ""))
            if cantidad < 1 or cantidad > 10000:
                error = "La cantidad debe estar entre 1 y 10000."
        except (ValueError, OverflowError):
            error = "La cantidad debe ser un numero entero entre 1 y 10000."

        if not error:
            estado = request.POST.get("estado", "").strip() or request.POST.get("expansion", "").strip()
            resultado = evaluar_disponibilidad(nombre, estado, cantidad)
            Registro.objects.create(
                nombre_carta=nombre,
                cantidad_solicitada=cantidad,
                expansion=estado,
                resultado=resultado
            )
            messages.success(request, f"Registro de '{nombre}' creado con éxito.")
            return redirect("lista")
    return render(request, "form.html", {"accion": "Crear", "error": error})


@requiere_rol("admin")
def editar(request, pk):
    """UPDATE: Formulario de edición con recálculo de la regla. Solo accesible para admin."""
    reg = get_object_or_404(Registro, pk=pk, eliminado=False)
    error = None
    if request.method == "POST":
        nombre = request.POST.get("nombre", "").strip() or request.POST.get("nombre_carta", "").strip()
        try:
            cantidad = int(request.POST.get("cantidad", "") or request.POST.get("cantidad_solicitada", ""))
            if cantidad < 1 or cantidad > 10000:
                error = "La cantidad debe estar entre 1 y 10000."
        except (ValueError, OverflowError):
            error = "La cantidad debe ser un numero entero entre 1 y 10000."

        if not error:
            estado = request.POST.get("estado", "").strip() or request.POST.get("expansion", "").strip()
            reg.nombre_carta = nombre
            reg.cantidad_solicitada = cantidad
            reg.expansion = estado
            reg.resultado = evaluar_disponibilidad(reg.nombre_carta, reg.expansion, reg.cantidad_solicitada)  # Recalcular
            reg.save()
            messages.success(request, f"Registro de '{reg.nombre_carta}' actualizado con éxito.")
            return redirect("lista")
        return render(request, "form.html", {"accion": "Editar", "registro": reg, "error": error})
    return render(request, "form.html", {"accion": "Editar", "registro": reg, "error": error})


@requiere_rol("admin")
def eliminar(request, pk):
    """DELETE lógico: Oculta el registro sin borrarlo de la base de datos. Solo accesible para admin."""
    reg = get_object_or_404(Registro, pk=pk, eliminado=False)
    if request.method == "POST":
        reg.soft_delete()
        messages.success(request, f"Registro de '{reg.nombre_carta}' eliminado con éxito.")
        return redirect("lista")
    return render(request, "confirmar.html", {"registro": reg})


# ── Vista adicional original de consulta con API externa ──

@login_required(login_url="login")
def verificar_carta(request):
    """Consulta de cartas en APIs externas con previsualización de imágenes."""
    resultado = None
    imagen_url = None
    
    precio_tcgplayer = None
    tcgplayer_url = None
    
    if request.method == 'POST':
        juego = request.POST.get('juego')
        nombre = request.POST.get('nombre_carta', '').strip()
        expansion = request.POST.get('expansion', '').strip()
        try:
            cantidad = int(request.POST.get('cantidad_solicitada', 0))
            if cantidad < 1 or cantidad > 10000:
                cantidad = 0
        except (ValueError, OverflowError):
            cantidad = 0
        
        resultado = evaluar_disponibilidad(nombre, expansion, cantidad)
        precio_tcgplayer = obtener_precio_tcgplayer(nombre)
        tcgplayer_url = obtener_url_tcgplayer(nombre)

        try:
            cabeceras = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            }
            if juego == 'pokemon':
                url = f'https://api.pokemontcg.io/v2/cards?q=name:"{nombre}"&pageSize=1'
                respuesta = requests.get(url, headers=cabeceras, timeout=5)
                if respuesta.status_code == 200:
                    datos = respuesta.json()
                    if datos.get('data'):
                        imagen_url = datos['data'][0]['images']['small']
            elif juego == 'yugioh':
                url = f'https://db.ygoprodeck.com/api/v7/cardinfo.php?fname={nombre}'
                respuesta = requests.get(url, headers=cabeceras, timeout=5)
                if respuesta.status_code == 200:
                    datos = respuesta.json()
                    if datos.get('data'):
                        imagen_url = datos['data'][0]['card_images'][0]['image_url_small']
            elif juego == 'magic':
                url = f'https://api.scryfall.com/cards/named?fuzzy={nombre}'
                respuesta = requests.get(url, headers=cabeceras, timeout=5)
                if respuesta.status_code == 200:
                    datos = respuesta.json()
                    if 'image_uris' in datos:
                        imagen_url = datos['image_uris']['normal']
        except Exception as e:
            print(f"--> Error al conectar con la API: {e}")

        if not imagen_url:
            imagen_url = obtener_imagen_carta(nombre)

    return render(request, 'resumen.html', {
        'resultado': resultado,
        'imagen_url': imagen_url,
        'precio_tcgplayer': precio_tcgplayer,
        'tcgplayer_url': tcgplayer_url
    })