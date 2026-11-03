from django.contrib import admin
from django.urls import path, include
from django.shortcuts import redirect
from rest_framework.routers import DefaultRouter
from rest_framework.authtoken.views import obtain_auth_token
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

from core import views
from core.api_views import RegistroViewSet

# Router automático para la API RESTful (Criterio 3.1.1 · Criterio 3.1.4)
router = DefaultRouter()
router.register(r"registros", RegistroViewSet, basename="registro")

urlpatterns = [
    # Panel de administración de Django (Fase 2)
    path("admin/", admin.site.urls),

    # ── API RESTful (Unidad 3 · ES3) ──
    # Documentación interactiva Swagger / OpenAPI 3.0 (Criterio 3.1.4)
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),

    # Endpoint para emisión de token de autenticación (Criterio 3.1.2)
    path("api/token/", obtain_auth_token, name="api_token"),

    # Endpoints RESTful para recursos (Criterio 3.1.1, 3.1.3, 3.1.4)
    path("api/", include(router.urls)),

    # ── Vistas HTML de la ES2 (se conservan intactas) ──
    # Raíz redirige al listado principal de registros
    path("", lambda r: redirect("lista"), name="home"),

    # Autenticación HTML (Fase 4 · Criterio 2.1.4)
    path("login/", views.vista_login, name="login"),
    path("logout/", views.vista_logout, name="logout"),

    # Las cuatro operaciones CRUD en HTML (Fase 3 · Criterio 2.1.3)
    path("registros/", views.lista, name="lista"),
    path("registros/crear/", views.crear, name="crear"),
    path("registros/<int:pk>/editar/", views.editar, name="editar"),
    path("registros/<int:pk>/eliminar/", views.eliminar, name="eliminar"),

    # Alias directos para comodidad
    path("crear/", views.crear),
    path("editar/<int:pk>/", views.editar),
    path("eliminar/<int:pk>/", views.eliminar),

    # Funcionalidad original de verificación con APIs de imágenes
    path("verificar/", views.verificar_carta, name="verificar_carta"),
    path("resumen/", views.verificar_carta, name="resumen"),
]
