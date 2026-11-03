from rest_framework import serializers
from .models import Registro


class RegistroSerializer(serializers.ModelSerializer):
    """
    Serializador para el modelo Registro (Criterio 3.1.1 y 3.1.3).
    Traduce entre objetos Registro y JSON bidireccionalmente, integrando
    cotización oficial de mercado e imagen de TCGplayer.
    """
    precio_tcgplayer = serializers.CharField(read_only=True)
    tcgplayer_url = serializers.CharField(read_only=True)
    imagen_url = serializers.CharField(read_only=True)

    class Meta:
        model = Registro
        fields = [
            "id",
            "nombre_carta",
            "expansion",
            "cantidad_solicitada",
            "resultado",
            "fecha",
            "precio_tcgplayer",
            "tcgplayer_url",
            "imagen_url",
        ]
        # Decisión de seguridad: resultado, fecha, id y cotizaciones de TCGplayer son de solo lectura
        read_only_fields = [
            "id",
            "resultado",
            "fecha",
            "precio_tcgplayer",
            "tcgplayer_url",
            "imagen_url",
        ]

    def validate_cantidad_solicitada(self, valor):
        """Valida que la cantidad esté en el rango seguro (1 a 10000) evitando OverflowError."""
        if valor < 1:
            raise serializers.ValidationError("La cantidad solicitada debe ser de al menos 1.")
        if valor > 10000:
            raise serializers.ValidationError("La cantidad solicitada no puede superar 10000.")
        return valor

    def validate_nombre_carta(self, valor):
        """Valida que el nombre de la carta no contenga sólo espacios en blanco."""
        if not valor or not valor.strip():
            raise serializers.ValidationError("El nombre de la carta no puede estar vacío.")
        return valor.strip()

    def validate_expansion(self, valor):
        """Valida que la expansión no contenga sólo espacios en blanco."""
        if not valor or not valor.strip():
            raise serializers.ValidationError("La expansión no puede estar vacía.")
        return valor.strip()
