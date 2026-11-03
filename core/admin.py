from django.contrib import admin
from .models import Registro


@admin.register(Registro)
class RegistroAdmin(admin.ModelAdmin):
    """
    Configuración del modelo Registro en el panel de administración de Django.
    Permite visualizar columnas clave, filtrar por expansión y estado de eliminación,
    buscar por nombre de carta y proteger el campo de fecha de eliminación.
    """
    list_display = ("nombre_carta", "expansion", "cantidad_solicitada", "resultado", "fecha", "eliminado")
    list_filter = ("expansion", "eliminado")
    search_fields = ("nombre_carta",)
    readonly_fields = ("fecha_eliminacion",)
