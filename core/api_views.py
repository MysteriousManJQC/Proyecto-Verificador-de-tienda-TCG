from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Registro
from .serializers import RegistroSerializer
from .permissions import PermisoPorRol
from solucion import evaluar_disponibilidad


class RegistroViewSet(viewsets.ModelViewSet):
    """
    ViewSet RESTful para gestionar registros de verificación de cartas (Criterios 3.1.1, 3.1.2, 3.1.3, 3.1.4).
    Provee automáticamente las rutas:
      - GET    /api/registros/      -> Listar registros (paginado)
      - POST   /api/registros/      -> Crear registro con evaluación de stock
      - GET    /api/registros/{id}/  -> Detalle de un registro
      - PUT    /api/registros/{id}/  -> Reemplazo completo y recálculo de stock
      - PATCH  /api/registros/{id}/  -> Modificación parcial y recálculo de stock
      - DELETE /api/registros/{id}/  -> Borrado lógico (soft delete)
    """
    queryset = Registro.objects.filter(eliminado=False).order_by("-fecha")
    serializer_class = RegistroSerializer
    permission_classes = [PermisoPorRol]

    def perform_create(self, serializer):
        """
        Lógica de negocio: El estado/resultado no lo envía el cliente.
        Se calcula en el servidor mediante la función evaluar_disponibilidad.
        """
        nombre = serializer.validated_data["nombre_carta"]
        expansion = serializer.validated_data["expansion"]
        cantidad = serializer.validated_data["cantidad_solicitada"]
        resultado = evaluar_disponibilidad(nombre, expansion, cantidad)
        serializer.save(resultado=resultado)

    def perform_update(self, serializer):
        """
        Al actualizar (PUT o PATCH), recalcula la disponibilidad con los nuevos datos.
        """
        instance = serializer.save()
        nuevo_resultado = evaluar_disponibilidad(
            instance.nombre_carta,
            instance.expansion,
            instance.cantidad_solicitada
        )
        instance.resultado = nuevo_resultado
        instance.save(update_fields=["resultado"])

    def perform_destroy(self, instance):
        """
        Borrado lógico (soft delete): oculta el registro marcando eliminado=True
        y registrando la fecha_eliminacion sin borrar la fila en SQLite.
        """
        instance.soft_delete()

    @action(detail=False, methods=["get"])
    def disponibles(self, request):
        """
        Endpoint personalizado adicional: GET /api/registros/disponibles/
        Retorna únicamente los registros cuyo stock fue suficiente ('Se puede vender').
        Demuestra el uso de @action y respuesta explícita HTTP 200 OK (Criterio 3.1.3).
        """
        qs = self.get_queryset().filter(resultado__icontains="Se puede vender")
        page = self.paginate_queryset(qs)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(qs, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
