# PLAN DE SOLUCIÓN · EVALUACIÓN 2
**Proyecto:** Verificador de disponibilidad de cartas para la venta  
**Asignatura:** Programación Back End (TI3V41) · INACAP  
**Estudiante:** Josue Quezada  

---

## 1. NEGOCIO

### 1.1 Problema
En la primera entrega (ES1), el sistema leía los datos directamente desde un archivo `stock.json` plano en modo de solo lectura. Esto impedía almacenar un histórico de consultas, corregir registros, dar de baja consultas obsoletas o restringir quién podía operar sobre el sistema. Cualquier usuario con acceso a la pantalla podía ver la misma información sin trazabilidad ni seguridad.

### 1.2 Solución y Propuesta de Valor
Evolucionar la aplicación hacia una plataforma web con persistencia en base de datos SQLite, operaciones CRUD completas, borrado lógico para auditoría y control de acceso robusto basado en roles (`admin`, `normal`, `viewer`) mediante grupos de Django. La regla de negocio central (`evaluar_disponibilidad` / `decidir`) se mantiene intacta desde la ES1, pero ahora se integra en el flujo de creación y edición con recálculo automático.

---

### 1.3 Alcance Real (Actualizado Eva 2)

#### Incluye:
- **Base de datos relacional SQLite** integrada mediante el ORM de Django.
- **Modelo de datos `Registro`**: almacena nombre de la carta, expansión, cantidad solicitada, resultado de la regla, fecha y estado de borrado lógico.
- **Cuatro operaciones CRUD completas**:
  - *Create*: Registro de nueva consulta evaluando la disponibilidad con la regla intacta de la ES1.
  - *Read*: Listado de registros activos filtrando aquellos marcados como eliminados.
  - *Update*: Modificación de parámetros de consulta con recálculo mandatorio del resultado para evitar discrepancias.
  - *Delete*: Borrado lógico (*soft delete*) marcando `eliminado=True` y registrando `fecha_eliminacion` sin destruir datos históricos.
- **Sistema de Autenticación y Autorización de Django**:
  - Vistas de `login` y `logout`.
  - Tres roles implementados mediante grupos de Django: `admin`, `normal` y `viewer`.
  - Protección en servidor mediante decoradores (`@login_required`, `@requiere_rol`), evitando vulnerabilidades por acceso directo a URLs.
- **Panel de administración de Django** (`RegistroAdmin`) con buscador, filtros y campos de solo lectura.
- **Variables de entorno** gestionadas con `python-decouple` (`.env` protegido y plantilla `.env.example`).

#### No incluye:
- Pasarela de pago o transacciones monetarias reales.
- Motores de bases de datos externos complejos cliente-servidor (PostgreSQL / MySQL) innecesarios para el alcance de esta entrega.
- Registro abierto al público (*sign-up* sin aprobación previa).

---

### 1.4 Priorización MoSCoW (Actualizada Eva 2)

| Prioridad | Requerimiento | Justificación |
|---|---|---|
| **MUST** (Imprescindible) | **Persistencia en SQLite con ORM de Django** | Reemplaza definitivamente la lectura estática de `datos.json`/`stock.json`. |
| **MUST** (Imprescindible) | **Cuatro operaciones CRUD funcionales** | Crear, listar, editar y eliminar con validación en formularios y protección CSRF. |
| **MUST** (Imprescindible) | **Sistema de Login y control de roles en servidor** | Se traslada desde *Won't* a *Must*. Autenticación nativa y decoradores que restringen vistas. |
| **MUST** (Imprescindible) | **Borrado lógico (*Soft Delete*)** | Conservar la integridad referencial y auditoría sin pérdida física de registros. |
| **MUST** (Imprescindible) | **Reutilización intacta de la regla de la ES1** | Se importa `evaluar_disponibilidad` / `decidir` desde `solucion.py` y se recalcula en edición. |
| **SHOULD** (Debería) | **Panel Django Admin optimizado** | `list_display`, `list_filter`, `search_fields` y `readonly_fields` para gestión interna. |
| **SHOULD** (Debería) | **Adaptación visual por rol en interfaz** | Botones de edición y eliminación visibles únicamente para perfiles con permisos suficientes. |
| **COULD** (Podría) | **Script de migración de datos previos** | `cargar_datos.py` para sembrar los registros iniciales desde el JSON histórico. |
| **COULD** (Podría) | **Comando de inicialización de usuarios y grupos** | `crear_usuarios.py` / `python manage.py crear_grupos` automatizando la configuración de pruebas. |
| **WON'T** (No por ahora) | **Carrito de compras o compras multi-ítem** | Fuera del foco de la unidad curricular. |
| **WON'T** (No por ahora) | **Base de datos remota en la nube / PostgreSQL** | No requerido para evaluación local en SQLite. |
