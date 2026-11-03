from rest_framework import permissions


class PermisoPorRol(permissions.BasePermission):
    """
    Control de acceso diferenciado por rol para la API RESTful (Criterio 3.1.2 · Nivel 4).
    - No autenticados: Sin acceso (401 Unauthorized vía TokenAuthentication).
    - Rol 'viewer': Solo métodos seguros de lectura (GET, HEAD, OPTIONS).
    - Rol 'normal': Lectura y creación de nuevos registros (GET, POST).
    - Rol 'admin' o staff/superuser: Acceso total CRUD (GET, POST, PUT, PATCH, DELETE).
    """

    def has_permission(self, request, view):
        # 1. El usuario debe estar autenticado con token
        if not request.user or not request.user.is_authenticated:
            return False

        # 2. Superusuarios y staff tienen acceso completo
        if request.user.is_superuser or request.user.is_staff:
            return True

        # 3. Métodos de solo lectura (SAFE_METHODS: GET, HEAD, OPTIONS) para cualquier autenticado
        if request.method in permissions.SAFE_METHODS:
            return True

        # 4. Obtener roles asociados al usuario
        user_groups = set(request.user.groups.values_list("name", flat=True))

        # Admin tiene acceso total
        if "admin" in user_groups:
            return True

        # Normal sólo puede crear (POST), pero no actualizar ni eliminar
        if "normal" in user_groups:
            return request.method == "POST"

        # Viewer (o usuarios sin rol asignado) no pueden modificar
        return False
