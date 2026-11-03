<<<<<<< HEAD
# 🃏 Verificador de Stock de Cartas TCG · API RESTful
**Evaluación 3 (ES3) · Programación Back End (TI3V41)**  
*INACAP* · **Estudiante:** Josue Quezada · **Docente:** Juan Pablo Díaz S.

Sistema web y API RESTful desarrollado en **Django** y **Django REST Framework (DRF)** para la gestión, verificación de disponibilidad de stock y registro de transacciones de cartas coleccionables (TCG como Pokémon, Yu-Gi-Oh! y Magic: The Gathering).

> [!NOTE]
> **Coexistencia ES2 y ES3:**  
> Las vistas HTML originales de la ES2 se conservan intactas en sus rutas (`/`, `/login/`, `/registros/`, etc.).  
> La API RESTful de la ES3 vive en paralelo bajo el prefijo `/api/`, compartiendo los mismos modelos, lógica de negocio (`solucion.py`) y base de datos.

---

## ⚙️ Justificación de la Configuración de DRF (Criterio 3.1.1)

En `miproyecto/settings.py`, el bloque `REST_FRAMEWORK` fue configurado de manera explícita:

1. **`TokenAuthentication` vs. Sesión por Cookie:**
   Las APIs RESTful deben ser inherentemente **stateless** (sin estado en el servidor). La autenticación por sesión (`SessionAuthentication`) depende de cookies y navegador, siendo vulnerable a CSRF y rígida para clientes no-web. `TokenAuthentication` permite a clientes móviles, scripts `curl`, clientes HTTP y aplicaciones frontend desacopladas identificarse mediante la cabecera estándar `Authorization: Token <key>`, garantizando portabilidad y seguridad sin estado.

2. **`PAGE_SIZE: 10` y `PageNumberPagination`:**
   Entregar listados paginados de 10 en 10 optimiza el ancho de banda, reduce drásticamente el consumo de memoria en el servidor y protege la base de datos ante ataques DoS por consultas masivas. El cliente recibe una estructura estándar con metadatos (`count`, enlaces a `next` y `previous`, y el arreglo `results`).

3. **`IsAuthenticated` por Defecto:**
   Se aplica el principio de **menor privilegio** (*deny by default*). Ningún endpoint de la API queda expuesto públicamente a internet por descuido; cualquier acceso sin token válido es rechazado inmediatamente con `401 Unauthorized`.

---

## 📋 Tabla de Endpoints de la API RESTful (Criterio 3.1.4)

Todas las rutas utilizan sustantivos en plural y los métodos HTTP estándar (convención RESTful estricta sin verbos en las URLs):

| Método | Endpoint | Rol Mínimo Requerido | Código HTTP | Descripción |
|---|---|:---:|:---:|---|
| **POST** | `/api/token/` | Cualquiera (con credenciales) | `200 OK` / `400 Bad Request` | Obtiene el token de autenticación enviando `username` y `password`. |
| **GET** | `/api/registros/` | `viewer` | `200 OK` / `401 Unauthorized` | Lista paginada de registros activos (`eliminado=False`). |
| **POST** | `/api/registros/` | `normal` | `201 Created` / `403 Forbidden` / `400 Bad Request` | Crea un nuevo registro evaluando disponibilidad de stock en el servidor. |
| **GET** | `/api/registros/{id}/` | `viewer` | `200 OK` / `404 Not Found` | Obtiene el detalle de un registro específico. |
| **PUT** | `/api/registros/{id}/` | `admin` | `200 OK` / `403 Forbidden` / `400 Bad Request` | Reemplazo completo del registro y recálculo automático de stock. |
| **PATCH** | `/api/registros/{id}/` | `admin` | `200 OK` / `403 Forbidden` / `400 Bad Request` | Actualización parcial del registro y recálculo automático de stock. |
| **DELETE** | `/api/registros/{id}/` | `admin` | `204 No Content` / `403 Forbidden` | Borrado lógico (*soft delete*): marca `eliminado=True` y registra fecha. |
| **GET** | `/api/registros/disponibles/` | `viewer` | `200 OK` | Endpoint personalizado (`@action`) con registros con stock vendible. |
| **GET** | `/api/docs/` | Público | `200 OK` | Documentación interactiva Swagger UI generada con `drf-spectacular`. |
| **GET** | `/api/schema/` | Público | `200 OK` | Esquema OpenAPI 3.0 en formato YAML/JSON. |

---

## 🔐 Control de Acceso y Permisos Diferenciados (Criterio 3.1.2 · Nivel 4)

Implementado en `core/permissions.py` mediante la clase `PermisoPorRol(BasePermission)`:
- **Sin Token:** La petición es rechazada con `401 Unauthorized`.
- **Rol `viewer` (`lector1`):** Solo métodos de lectura segura (`GET`, `HEAD`, `OPTIONS`). Si intenta `POST`, `PUT`, `PATCH` o `DELETE`, recibe `403 Forbidden`.
- **Rol `normal` (`usuario1`):** Puede consultar (`GET`) y registrar consultas (`POST`), pero no puede alterar registros existentes ni eliminarlos (`PUT`, `PATCH`, `DELETE` devuelven `403 Forbidden`).
- **Rol `admin` (`admin1`) y Staff:** Acceso total CRUD (`GET`, `POST`, `PUT`, `PATCH`, `DELETE`).

---

## 🛠️ Instalación y Puesta en Marcha

### 1. Entorno Virtual e Instalación de Dependencias
```bash
python -m venv .venv
# En Windows (PowerShell):
.\.venv\Scripts\Activate.ps1
# En Linux/macOS:
source .venv/bin/activate

pip install -r requirements.txt
```

### 2. Configurar Variables de Entorno (`.env`)
Copia la plantilla `.env.example` para crear tu `.env`:
```bash
cp .env.example .env
```
Completa las claves necesarias:
```env
SECRET_KEY=clave_secreta_django_aqui
DEBUG=True
PASS_ADMIN=admin123
PASS_NORMAL=normal123
PASS_LECTOR=viewer123
PASS_VIEWER=viewer123
```

### 3. Migraciones e Inicialización de Usuarios
```bash
python manage.py migrate
python manage.py crear_grupos
```
Este comando inicializa los grupos (`admin`, `normal`, `viewer`) y crea los usuarios con sus tokens correspondientes.

### 4. Carga Inicial de Datos (Idempotente)
```bash
python manage.py shell < cargar_datos.py
```

### 5. Ejecución del Servidor
```bash
python manage.py runserver
```
- Vistas HTML ES2: [http://127.0.0.1:8000/login/](http://127.0.0.1:8000/login/)
- Documentación Swagger API: [http://127.0.0.1:8000/api/docs/](http://127.0.0.1:8000/api/docs/)

---

## 🧪 Pruebas con `curl` (Uso de Tokens Truncados)

### 1. Obtener Token (`POST /api/token/`)
```bash
curl -X POST http://127.0.0.1:8000/api/token/ \
  -H "Content-Type: application/json" \
  -d '{"username": "admin1", "password": "admin123"}'
```
*Respuesta (200 OK):*
```json
{
  "token": "1c96d64d..."
}
```

### 2. Listar Registros (`GET /api/registros/`)
```bash
curl -X GET http://127.0.0.1:8000/api/registros/ \
  -H "Authorization: Token 1c96d64d..."
```

### 3. Crear Registro (`POST /api/registros/`)
```bash
curl -X POST http://127.0.0.1:8000/api/registros/ \
  -H "Authorization: Token dd496ff5..." \
  -H "Content-Type: application/json" \
  -d '{"nombre_carta": "Pikachu", "expansion": "Crown Zenith", "cantidad_solicitada": 2}'
```
*Respuesta (201 Created):*
```json
{
  "id": 101,
  "nombre_carta": "Pikachu",
  "expansion": "Crown Zenith",
  "cantidad_solicitada": 2,
  "resultado": "Se puede vender. Stock disponible: 25.",
  "fecha": "2026-11-02T16:00:00Z"
}
```

### 4. Actualizar con Recálculo (`PATCH /api/registros/101/`)
```bash
curl -X PATCH http://127.0.0.1:8000/api/registros/101/ \
  -H "Authorization: Token 1c96d64d..." \
  -H "Content-Type: application/json" \
  -d '{"cantidad_solicitada": 99}'
```

### 5. Borrado Lógico (`DELETE /api/registros/101/`)
```bash
curl -X DELETE http://127.0.0.1:8000/api/registros/101/ \
  -H "Authorization: Token 1c96d64d..."
```
*Respuesta: 204 No Content.*

> [!TIP]
> Todas las evidencias y respuestas completas de cada código de estado HTTP se encuentran almacenadas en la carpeta `pruebas/`.

---

## 🚦 Batería de Pruebas Automatizadas

Para ejecutar la suite completa de pruebas unitarias (23 pruebas automatizadas cubriendo modelos, CRUD, roles, borrado lógico, validaciones, paginación, OpenAPI y TCGplayer):
```bash
python manage.py test
```
*Resultado esperado:*
```text
Ran 23 tests in 44.536s
OK
```

---

## 🃏 Integración de Precios e Ilustraciones Oficiales (TCGplayer API)

Para enriquecer la experiencia y brindar información de valor de mercado real, el sistema integra la API de **TCGplayer** ([TCGplayer Developer Portal](https://docs.tcgplayer.com/docs/getting-started)):
- **Precios de Mercado Oficiales:** Cada carta consultada o registrada refleja su valor de mercado en USD (`Market Price`), obtenido directamente de la cotización de TCGplayer.
- **Ilustraciones Oficiales en Alta Definición:** En la vista de registros (`/registros/`) y verificación (`/consultar/`), se muestran miniaturas interactivas que se expanden al pasar el cursor y enlazan directamente a la publicación del producto en TCGplayer.
- **Serialización en la API RESTful:** Los endpoints `/api/registros/` exponen los campos `precio_tcgplayer`, `tcgplayer_url` e `imagen_url` como campos de solo lectura.
- **Arquitectura de Resiliencia y Caché (`tcgplayer_cache.json`):** Los datos se gestionan mediante un cliente con soporte para autenticación Bearer OAuth2 de TCGplayer (`core/tcgplayer.py`) y una caché local de alta velocidad para garantizar respuesta instantánea y cero fallas ante límites de cuota externa.

---

## 🔒 Consideraciones de Seguridad para la Entrega
- De acuerdo a las instrucciones de la evaluación y al archivo `.gitignore`, **NO** se incluyen en la entrega `db.sqlite3` ni el archivo `.env`.
- Todos los tokens en la documentación y pruebas se presentan truncados (`1c96d64d...`).
- El comprimido de entrega final debe titularse `ES3_ApellidoNombre.zip` (ej. `ES3_QuezadaJosue.zip`).
=======
# Proyecto-Verificador-de-tienda-TCG
Parte 1 del proyecto del semestre
>>>>>>> 414e181eddee75b0112ca15022d1bf61cc74b558
