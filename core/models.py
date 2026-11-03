from django.db import models
from django.utils import timezone


class Registro(models.Model):
    """
    Modelo para el almacenamiento de registros del verificador de cartas.
    Implementa borrado lógico con los campos 'eliminado' y 'fecha_eliminacion'.
    """
    nombre_carta = models.CharField(max_length=150, verbose_name="Nombre de la carta")
    expansion = models.CharField(max_length=150, verbose_name="Expansión")
    cantidad_solicitada = models.IntegerField(verbose_name="Cantidad solicitada")
    resultado = models.CharField(max_length=255, verbose_name="Resultado")
    fecha = models.DateTimeField(default=timezone.now, verbose_name="Fecha")

    # Borrado lógico: no se borra físicamente de la base de datos, sólo se oculta
    eliminado = models.BooleanField(default=False, verbose_name="Eliminado")
    fecha_eliminacion = models.DateTimeField(null=True, blank=True, verbose_name="Fecha de eliminación")

    class Meta:
        ordering = ["-fecha"]
        verbose_name = "Registro"
        verbose_name_plural = "Registros"

    def __str__(self):
        return f"{self.nombre_carta} - {self.resultado}"

    def soft_delete(self):
        """Marca el registro como eliminado y guarda la fecha actual sin destruirlo."""
        self.eliminado = True
        self.fecha_eliminacion = timezone.now()
        self.save()

    # Aliases de compatibilidad
    @property
    def nombre(self):
        return self.nombre_carta

    @nombre.setter
    def nombre(self, value):
        self.nombre_carta = value

    @property
    def estado(self):
        return self.expansion

    @estado.setter
    def estado(self, value):
        self.expansion = value

    @property
    def cantidad(self):
        return self.cantidad_solicitada

    @cantidad.setter
    def cantidad(self, value):
        self.cantidad_solicitada = value

    @property
    def imagen_url(self) -> str:
        """URL de la imagen oficial de la carta para previsualización."""
        from .utils import obtener_imagen_carta
        return obtener_imagen_carta(self.nombre_carta)

    @property
    def precio_tcgplayer(self) -> str:
        """Precio de mercado oficial en TCGplayer en dólares estadounidenses (USD)."""
        from .utils import obtener_precio_tcgplayer
        return obtener_precio_tcgplayer(self.nombre_carta)

    @property
    def tcgplayer_url(self) -> str:
        """Enlace a la publicación oficial del producto en TCGplayer."""
        from .utils import obtener_url_tcgplayer
        return obtener_url_tcgplayer(self.nombre_carta)
