# REGISTRO DE USO DE INTELIGENCIA ARTIFICIAL · EVALUACIÓN 3
**Asignatura:** Programación Back End (TI3V41) · INACAP  
**Estudiante:** Josue Quezada  
**Docente:** Juan Pablo Díaz S.  

---

### 1. Herramienta Utilizada
- **Herramienta:** Asistente de IA (Antigravity / Claude 3.5 Sonnet / Gemini).

---

### 2. Consultas Textuales Realizadas

1. **Sobre Seguridad, Permisos y Autenticación en la API (Criterio 3.1.2):**
   > *"¿Cómo configuro las vistas de la API REST para probar los endpoints y evitar errores 403 Forbidden al hacer peticiones desde Postman o curl?"*

2. **Sobre Serialización y Exposición de Campos (Criterio 3.1.1 y 3.1.3):**
   > *"¿Cómo defino el ModelSerializer para el modelo Registro de cartas TCG asegurando que traduzca el modelo a JSON y valide los datos entrantes?"*

3. **Sobre Arquitectura de Endpoints y Convenciones REST (Criterio 3.1.4):**
   > *"¿Qué vistas debo implementar en DRF para exponer las operaciones CRUD completas y cómo registro sus rutas en urls.py?"*

---

### 3. Análisis Crítico y Decisiones Técnicas Aplicadas

#### Caso 1 · Permisos Diferenciados vs. Desactivar Seguridad con `AllowAny` (Criterio 3.1.2)
- **Qué respondió la IA:** Sugirió configurar `permission_classes = [AllowAny]` en el ViewSet y decorar la vista con `@csrf_exempt`, argumentando que *"así las pruebas desde curl o Postman funcionan inmediatamente sin lidiar con tokens"*.
- **Qué estaba mal:** Esta sugerencia anula por completo la seguridad del sistema: deja la API expuesta abiertamente a cualquier cliente no autenticado en internet, violando directamente el principio de mínimo privilegio y castigando el Criterio 3.1.2 con puntaje cero. Además, ignoraba por completo la estructura de roles (`admin`, `normal`, `viewer`) construida en la ES2.
- **Qué hice yo:** Rechacé tajantemente `AllowAny` y `@csrf_exempt`. Configuré `IsAuthenticated` como default global seguro en `REST_FRAMEWORK` dentro de `settings.py`. Diseñé la clase personalizada `PermisoPorRol(BasePermission)` en `core/permissions.py`:
  - Los usuarios no autenticados reciben `401 Unauthorized`.
  - El rol **viewer** únicamente puede consultar mediante métodos seguros (`GET`, `HEAD`, `OPTIONS`).
  - El rol **normal** puede consultar y crear (`GET`, `POST`), pero tiene bloqueada la edición y eliminación (`403 Forbidden`).
  - El rol **admin** y staff cuentan con acceso CRUD completo (`GET`, `POST`, `PUT`, `PATCH`, `DELETE`).
  Las pruebas se ejecutaron enviando siempre el token en la cabecera HTTP: `Authorization: Token <token>`.

#### Caso 2 · Definición Explícita de Serializador vs. `fields = '__all__'` (Criterio 3.1.1 y 3.1.3)
- **Qué respondió la IA:** Propuso serializar el modelo utilizando `class Meta: model = Registro; fields = '__all__'`.
- **Qué estaba mal:** Utilizar `__all__` es una mala práctica de seguridad (Mass Assignment). Exponía campos internos del borrado lógico (`eliminado`, `fecha_eliminacion`) y permitía que el cliente inyectara un valor arbitrario en el campo `resultado` en su JSON (ej. `{"resultado": "Se puede vender"}`), puenteando la regla de decisión de stock de la ES1.
- **Qué hice yo:** Descarté `fields = '__all__'`. Enumeré explícitamente los campos visibles en `core/serializers.py` y declaré `read_only_fields = ["id", "resultado", "fecha"]`. De esta forma, el cálculo de disponibilidad queda bajo control exclusivo del servidor en `perform_create` y `perform_update` mediante la función `evaluar_disponibilidad()`. Asimismo, implementé `validate_cantidad_solicitada` para validar el rango entre 1 y 10.000, evitando desbordes de memoria (`OverflowError` en SQLite).

#### Caso 3 · Arquitectura Uniforme con `ModelViewSet` vs. Mezcla Inconsistente de Vistas (Criterio 3.1.4)
- **Qué respondió la IA:** Planteó resolver el CRUD mezclando clases `APIView` con vistas genéricas `ListCreateAPIView` y `RetrieveUpdateDestroyAPIView`, definiendo cada URL a mano en `urls.py` con nombres como `/api/registros/crear/` o `/api/registros/editar/<id>/`.
- **Qué estaba mal:** Mezclar distintos estilos de vistas dificulta el mantenimiento y la defensa técnica del proyecto. Además, incluir verbos en las URLs viola las convenciones RESTful más fundamentales (las URLs deben identificar recursos en plural y los verbos HTTP deben determinar la acción).
- **Qué hice yo:** Rechacé la dispersión de vistas. Centralicé toda la lógica del recurso en una única clase `RegistroViewSet(viewsets.ModelViewSet)` en `core/api_views.py`. Utilicé `DefaultRouter` en `miproyecto/urls.py` para generar automáticamente los 5 endpoints canónicos (`GET /api/registros/`, `POST /api/registros/`, `GET /api/registros/<id>/`, `PUT/PATCH /api/registros/<id>/`, `DELETE /api/registros/<id>/`). Para consultas especializadas usé el decorador `@action(detail=False, methods=['get'])` (`/api/registros/disponibles/`) y documenté la API completa con estándares OpenAPI 3.0 mediante `drf-spectacular` en `/api/docs/`.
