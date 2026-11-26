# 🌊 MAREVA — Agencia de Viajes Digital

> Plataforma web para la organización de planes vacacionales personalizados en Colombia.

---

## 1. ¿Qué Problema Resuelve?

Hoy organizar unas vacaciones obliga a abrir decenas de pestañas: una para el tiquete, otra para el hotel, otra para las actividades. El resultado es desorden, tiempo perdido y gastos innecesarios.

**MAREVA** centraliza todo en un solo lugar: el usuario elige un destino, selecciona el paquete turístico, agrega servicios extra (buceo, kayak, senderismo nocturno…), aplica su seguro de viaje y confirma su reserva, sin salir de la plataforma. El administrador gestiona el catálogo desde el mismo sistema.

---

## 2. Usuarios del Sistema

| Rol | Descripción |
|---|---|
| **Cliente / Viajero** | Navega destinos, reserva paquetes, gestiona su perfil, guarda favoritos y acumula insignias |
| **Administrador** | Gestiona paquetes, destinos, proveedores, guías, niveles, reportes y audita el sistema |
| **Guía turístico** | Consulta su panel de viajes y actualiza el estado de las reservas asignadas |
| **Proveedor** | Consulta contratos y solicitudes de servicios |

---

## 3. Estructura del Proyecto

```
Mareva_Sustentacion/
├── backend/            → Aplicación Flask (N-Capas)
│   ├── config/         → Conexión a PostgreSQL
│   ├── controllers/    → Lógica de presentación (Flask)
│   ├── models/         → Entidades POO (Abstract Base Class + Factory)
│   ├── repositories/   → Persistencia (consultas SQL directas)
│   ├── routes/         → Definición de URLs (blueprints)
│   ├── services/       → Reglas de negocio
│   └── main.py         → Punto de entrada del servidor
|
├── frontend/           → HTML5 · CSS3 · JavaScript (Jinja2)
│   ├── static/         → CSS, JS, imágenes y videos
│   └── templates/      → Plantillas HTML
```

---

## 4. Instalación y Ejecución

### Requisitos previos

- Python 3.10+
- PostgreSQL (se usan `psycopg[binary]` 3.x)
- Las dependencias del proyecto (`requirements.txt`)

### 4.1 Crear la base de datos

1. Crea una base de datos PostgreSQL (por ejemplo `mareva`).
2. Ejecuta el script de creación completo:

```sql
psql -U tu_usuario -d mareva -f database/base_de_datos_mareva.sql
```

3. Si vienes de una base existente , aplica la migración:

```sql
psql -U tu_usuario -d mareva -f database/migracion_2026.sql
```

(Puedes encontrar las bases de datos en la carpeta docs, en la rama desarrollo-backend o en el main)

### 4.2 Crear y activar el entorno virtual

Entra a la carpeta del proyecto:

```bash
cd Mareva_Sustentacion
```

#### Windows (PowerShell)

```powershell
python -m venv venv
venv\Scripts\Activate.ps1
```

#### Windows (CMD)

```bat
python -m venv venv
venv\Scripts\activate
```

#### Linux / macOS

```bash
python3 -m venv venv
source venv/bin/activate
```

Cuando el entorno esté activo, verás el nombre `(venv)` al inicio de la terminal.

### 4.3 Instalar las dependencias

```bash
pip install -r requirements.txt
```

### 4.4 Configurar `.env`

Crea un archivo `.env` en la raíz de proyecto:

```env
DB_HOST= Servidor o maquina en donde esta alojada tu base de datos (ej: localhost)
DB_PORT= Puerto de red por el que se conecta la base de datos (ej: Postgres tiene su puerto 5432 predeterminado)
DB_NAME= Nombre especifico de la base de datos (ej: mareva, dbmareva, el que colocaste)
DB_USER= Nombre especifico del usuario de base de datos con permisos para modificar los datos (ej: postgres, mareva_user.)
DB_PASSWORD= Contraseña correspondiente de la base de datos que creaste.

GOOGLE_PROJECT_ID= Identificador unico en texto del proyecto creado en Google Cloud Console.
GOOGLE_PROJECT_NUMBER= Numero interno unico que Google asigna a ese mismo proyecto en la nube.
GOOGLE_CLIENT_ID= Clave publica que identifica a tu aplicacion ante google para servicios como OAuth o APIs de Google.
GOOGLE_CLIENT_SECRET= Clave secreta que valida tu aplicacion frente a Google, no publiques esta clave a nadie.
GOOGLE_REDIRECT_URI= Es la URL exacta de tu aplicacion a la que Google redirige al usuario despues de que autoriza o inicia sesion.

SMTP_HOST: Es la dirección del servidor de correo saliente que enviará los emails desde la plataforma (por ejemplo, smtp.gmail.com).
SMTP_PORT: Es el puerto que usa el servidor de correo saliente (comúnmente 587 para TLS o 465 para SSL).
SMTP_USER: Es la cuenta de correo o usuario autenticado desde el cual se envían los mensajes.
SMTP_PASSWORD: Es la contraseña de esa cuenta o una contraseña de aplicación (App Password) generada para permitir el envío automático.
SMTP_ADMIN_EMAIL: Es el correo del administrador que recibirá avisos, alertas o copias importantes del sistema.
SMTP_FROM_NAME: Es el nombre visible que verá quien recibe el correo como remitente (por ejemplo, MAREVA).
SMTP_REPLY_TO: Es la dirección de correo a la que irán las respuestas si el destinatario responde el mensaje.
SMTP_USE_SSL: Indica si la conexión con el servidor de correo debe usar cifrado SSL (true o false).
```


### 4.5 Ejecutar la aplicación

El servidor se inicia desde la carpeta `backend/`:

```bash
cd backend
python main.py
```

### 4.6 Abrir el proyecto

Una vez iniciado el servidor, visita en tu navegador:

```
http://127.0.0.1:5000/
```

## 5. Usuarios de Prueba

| Rol | Correo | Contraseña |
|---|---|---|
| Administrador | `nicoll@mareva.co` (o `cesar@mareva.co`, `andres@mareva.co`, `laura@mareva.co`, `sofia@mareva.co`) | `Admin_mareva01` |
| Cliente | `yadira@test.co` | `cliente_prueba` |
| Guia Turistica |`andres.guia@mareva.co` | `Guia123` |
| Proveedor | `reservas@lasamericas.co` | `Proveedor_mareva01` |

---

## 6. Funcionalidades Principales

- Registro e inicio de sesión con hash de contraseña (werkzeug) y bloqueo por intentos fallidos
- Catálogo de **20 paquetes turísticos** con búsqueda, filtros (categoría, destino, duración, precio, incluye) y ordenamiento
- Detalle del paquete con calendario de salidas, servicios incluidos y extras opcionales
- **Comparador de paquetes** (hasta 3)
- **Favoritos**: agregar/quitar desde el catálogo, página de lista y contador en el navbar
- Flujo de reserva completo: selección de fecha, alojamiento, alimentación, transporte, actividades, seguro y extras
- Gestión de viajeros por reserva, confirmación en pantalla y **descarga de la reserva en PDF**
- Panel de administración: paquetes, destinos, niveles de gamificación, encuestas, reportes y reservas
- Perfil de usuario con nivel de gamificación e insignias
- Historial de búsqueda reutilizable
- **Encuestas de satisfacción** post-viaje
- Roles de guía turístico y proveedor (contratos y solicitudes)

---

## 7. Tecnologías Utilizadas

### 7.1 Frontend

| Tecnología | Versión / Detalle | Uso en el proyecto |
|---|---|---|
| **HTML5** | Estándar | Estructura semántica de todas las vistas (etiquetas `<section>`, `<article>`, `<main>`, `data-*`) |
| **CSS3** | Variables CSS (`:root`) + Flexbox + Grid | Sistema de diseño con paleta MAREVA en `frontend/static/css/` |
| **JavaScript** | Vanilla JS (ES6+) | Interactividad: catálogo, comparador, favoritos, reserva, dashboard y reportes. Sin frameworks |
| **Jinja2** | Motor de plantillas de Flask | Reutilización con `{% extends "base.html" %}` y `{% block %}`; renderizado de paquetes, destinos, reservas y paneles |
| **Manrope** | Google Fonts | Tipografía principal (importada en `styles.css` y `dashboard.css`) |
| **intl-tel-input** | v25.3.1 (CDN jsDelivr) | Validación y selección de prefijo telefónico en registro y formularios (usa `utils.js`) |
| **Emojis / símbolos Unicode** | — | Iconografía del sitio (♥, ✈️, 🏨, 🍽️, 🚌…) sin librerías de iconos externas |

**Archivos JS** (`frontend/static/js/`):

| Archivo | Responsabilidad |
|---|---|
| `app.js` | Comportamiento global: navbar, menús y utilidades |
| `paquetes.js` | Filtros del catálogo, tarjetas clicables y **comparador** |
| `comparar.js` | Lógica de la vista de comparación de paquetes |
| `favoritos.js` | **Botones de favorito** (`.favorite-button` y `.package-favorite-btn`) + contador del navbar (AJAX) |
| `reserva.js` | Formulario de reserva: cálculo en vivo de precios por persona y total |
| `reserva_confirmar.js` | Confirmación de reserva |
| `registro.js` | Validación de registro + integración con `intl-tel-input` |
| `home_promos.js` | Carrusel de promociones de la página principal |
| `dashboard.js` | Paneles del administrador |
| `reportes.js` | Filtros de reportes |
| `gamificacion_*.js` | (si aplica) Niveles e insignias |

**Archivos CSS** (`frontend/static/css/`)

| Archivo | Responsabilidad |
|---|---|
| `styles.css` | Estilos generales y base del sistema de diseño |
| `index.css` | Estilos de la página principal (inicio) |
| `auth.css` | Estilos de inicio de sesión y registro |
| `paquetes.css` | Estilos del catálogo y detalle de paquetes turísticos |
| `mareva_redesign.css` | Estilos del rediseño visual de MAREVA |
| `reserva_flow.css` | Estilos del flujo y pasos de reserva |
| `dashboard.css` | Estilos de los paneles del administrador |
| `reportes.css` | Estilos de la vista y filtros de reportes |
| `perfil.css` | Estilos del perfil de usuario |
| `niveles.css` | Estilos de la vista de niveles |
| `gamificacion.css` | Estilos del módulo de gamificación e insignias |
| `gamificario.css` | Estilos complementarios o variantes de gamificación |
| `guia.css` | Estilos del panel y vistas del guía turístico |

### 7.2 Backend

| Tecnología | Versión / Detalle | Uso en el proyecto |
|---|---|---|
| **Python** | 3.10+ | Lenguaje de implementación de todo el backend |
| **Flask** | 3.1.3 | Microframework web: rutas (`blueprints`), templates, sesiones, `before_request` y `context_processor` |
| **psycopg** | 3.3.4 (`psycopg[binary]`) | Driver PostgreSQL moderno (conexión en `backend/config/conexion.py`) |
| **Werkzeug** | (núcleo de Flask) `check_password_hash` / `generate_password_hash` | **Hash de contraseñas** (`pbkdf2:`/`scrypt:`) en `auth_services.py` |
| **ReportLab** | 4.x (`reportlab`) | **Generación de PDF** de la reserva en `services/pdf_services.py` (A4, platypus) |
| **openpyxl** | 3.1.5 | **Exportación de reportes a Excel** (`reporte_services.py`) con estilos (fuentes, relleno, bordes) |
| **phonenumbers** | 9.0.36 | Validación de números de teléfono (Colombia) en `auth_controllers.py` y `proveedor_services.py` |
| **python-dotenv** | 1.2.2 | Carga de credenciales desde `.env` (`DB_HOST`, `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_PORT`) |
| **Jinja2** | (motor de Flask) | Templates HTML servidos por Flask (carpeta `frontend/templates`) |

**Arquitectura backend (N-Capas):**

| Capa | Carpeta | Responsabilidad |
|---|---|---|
| **Routes** | `backend/routes/` | Blueprints Flask por módulo: `auth`, `home`, `paquetes`, `destinos`, `reserva`, `favoritos`, `encuesta`, `gamificacion`, `guia`, `proveedores`, `reporte`, `dashboard` |
| **Controllers** | `backend/controllers/` | Reciben peticiones, orquestan servicios y renderizan/re-direccionan |
| **Services** | `backend/services/` | Reglas de negocio: `auth_services`, `paquete_services`, `reserva_services`, `reporte_services`, `pdf_services`, `proveedor_services`, `gamificacion_services`, `destinos_services`, `historial_services`, `guia_services`, `encuesta_services`, `dashboard_services` |
| **Models** | `backend/models/` | POO: `PaqueteBase` (ABC) + `Playa`, `Aventura`, `Ecoturismo`, `Cultural`, `Ciudad` + `factory_paquete()`; clase `Cliente` |
| **Repositories** | `backend/repositories/` | Consultas SQL directas a PostgreSQL por entidad (`auth`, `paquete`, `reserva`, `reporte`, `proveedor`, `destino`, `guia`, `encuesta`, `gamificacion`, `historial`, `salida`, `dashboard`) |
| **Config** | `backend/config/` | Clase `Conexion` (pool de conexiones a PostgreSQL) |

### 7.3 Versiones exactas (`requirements.txt`)

```
Flask==3.1.0
python-dotenv==1.0.1
requests==2.32.3
google-auth==2.62.0
openpyxl==3.1.5
phonenumbers==9.0.36
pip==24.0
psycopg[binary]==3.3.4
reportlab==5.0.1
websocket-client==1.9.0
```

| Capa | Resumen |
|---|---|
| **Frontend** | HTML5 · CSS3 · JavaScript vanilla · Jinja2 · Manrope · intl-tel-input |
| **Backend** | Python 3.10+ · Flask 3.1.3 · psycopg 3 |
| **Base de Datos** | PostgreSQL (psycopg 3) |
| **Seguridad** | Werkzeug (hash de contraseñas), intentos fallidos + bloqueo temporal |
| **PDF / Reportes** | ReportLab (PDF) · openpyxl (Excel) |
| **Validación** | phonenumbers · intl-tel-input |
| **Patrón Backend** | Arquitectura N-Capas (Routes → Controllers → Services → Models → Repositories → BD) |
| **Patrón OOP** | Abstract Base Class + Factory Method (clases `Playa`, `Aventura`, `Ecoturismo`, `Cultural`, `Ciudad`) |
| **Control de versiones** | Git / GitHub |
| **Gestión del proyecto** | GitHub Projects (Scrum) |

---

## 8. Arquitectura — N-Capas

El sistema está dividido en **6 capas**, agrupadas en FrontEnd y BackEnd:

```
╔══════════════════════════════════════════════════════╗
║  FRONTEND                                            ║
║  ┌───────────────────────────────────────────────┐  ║
║  │  Capa de Presentación  │  HTML5 · CSS3 · JS   │  ║
║  └───────────────────────────────────────────────┘  ║
╠══════════════════════════════════════════════════════╣
║  BACKEND                                             ║
║  ┌───────────────────────────────────────────────┐  ║
║  │  Capa de Aplicación    │  Flask (routes +     │  ║
║  │                        │  controllers)        │  ║
║  ├───────────────────────────────────────────────┤  ║
║  │  Capa de Negocio       │  Python · Flask      │  ║
║  │  (Services)            │                      │  ║
║  ├───────────────────────────────────────────────┤  ║
║  │  Capa de Datos         │  Python · POO        │  ║
║  │  (Models)              │                      │  ║
║  ├───────────────────────────────────────────────┤  ║
║  │  Capa de Persistencia  │  PostgreSQL          │  ║
║  │  (Repositories)        │                      │  ║
║  └───────────────────────────────────────────────┘  ║
╚══════════════════════════════════════════════════════╝
```

### Descripción de cada capa

| Capa | Ubicación | Responsabilidad |
|---|---|---|
| **Presentación** | `frontend/` (HTML · CSS · JS) | Muestra la interfaz y gestiona la interacción visual |
| **Aplicación** | `backend/routes/` y `backend/controllers/` | Define las URLs y recibe las solicitudes HTTP |
| **Negocio (Services)** | `backend/services/` | Reglas de negocio: validaciones, cálculos y procesamiento |
| **Datos (Models)** | `backend/models/` | Entidades POO del dominio (paquetes, clientes) |
| **Persistencia (Repositories)** | `backend/repositories/` | Comunicación directa con PostgreSQL |
| **Servicios Externos** | APIs de terceros | Conectores con el mundo exterior (en esta versión, proveedores y guías viven en la BD) |

### ¿Por qué elegimos Arquitectura N-Capas?

El equipo optó por esta arquitectura por dos razones fundamentales:

**1. Modificabilidad sin efecto cascada**
Al separar cada responsabilidad en su propia capa, cualquier cambio queda contenido sin propagarse al resto del sistema. Si se cambia PostgreSQL por otro motor de base de datos, solo se toca la capa de Persistencia. Si se rediseña la interfaz, la lógica de negocio y los repositorios permanecen intactos. Esto fue clave para un equipo de 5 personas trabajando en paralelo: cada integrante podía modificar su módulo sin romper el trabajo de los demás.

**2. Optimización y rendimiento del sistema**
La separación de responsabilidades permite identificar y optimizar cada capa de forma independiente. Si hay lentitud en las consultas, se interviene únicamente en los repositorios sin tocar los servicios ni las rutas. Esto hace que el sistema sea más fácil de auditar, depurar y escalar.

Esto garantiza:
- **Separación de responsabilidades** — los cambios en la BD no afectan la vista ni los servicios
- **Mantenibilidad** — cada módulo puede actualizarse de forma independiente
- **Escalabilidad** — nuevas funciones se agregan en la capa correcta sin romper las demás
- **Trabajo en equipo eficiente** — cada integrante trabaja sobre su capa sin generar conflictos

---

## 9. Base de Datos — Módulos

La base de datos final en PostgreSQL tiene **13 módulos** y más de **35 tablas**:

| # | Módulo | Tablas principales |
|---|---|---|
| 1 | **Gamificación** | `nivel`, `insignia`, `cliente_insignia` |
| 2 | **Clientes** | `cliente`, `referido` |
| 3 | **Destinos** | `destino` |
| 4 | **Proveedores** | `proveedor`, `metodo_pago_proveedor` |
| 5 | **Guías Turísticos** | `guia_turistico` |
| 6 | **Seguros** | `tipo_seguro`, `seguro`, `seguro_servicio` |
| 7 | **Servicios** | `alojamiento`, `alimentacion`, `transporte`, `actividad_turistica` |
| 8 | **Paquetes Turísticos** | `paquete_turistico`, `paquete_*` (4 tablas N:M), `servicio_extra` |
| 9 | **Promociones** | `promocion`, `promocion_insignia`, `promocion_nivel` |
| 10 | **Reservas** | `reserva`, `reserva_seguro`, `reserva_servicio_extra`, `viajero_reserva`, `itinerario_viaje`, `itinerario_actividad` |
| 11 | **Funcionalidades Cliente** | `favoritos`, `lista_suenos`, `historial_busqueda`, `notificacion` |
| 12 | **Encuestas** | `encuesta_pregunta`, `encuesta_respuesta` |
| 13 | **Auditoría** | `auditoria_admin` |

**Datos iniciales cargados:**
- 4 niveles de gamificación: Explorador → Aventurero → Viajero Elite → Embajador
- 5 insignias: Primera Aventura, Playero, Montañista, Viajero Frecuente, Referidor Estrella
- 20 destinos colombianos
- 20 paquetes turísticos
- 5 administradores + 1 cliente de prueba (`yadira@test.co`)
- Proveedores, guías turísticos, promociones y encuestas base

---

## 10. Patrón POO en el Backend

`backend/models/paquete.py` implementa **Abstract Base Class + Factory Method**:

```python
class PaqueteBase(ABC):
    @abstractmethod
    def calcular_precio_final(self): pass

class Playa(PaqueteBase):
    def calcular_precio_final(self): return self._data["precio"] * 1.10

class Aventura(PaqueteBase):
    def calcular_precio_final(self): return self._data["precio"] * 1.15

class Ecoturismo(PaqueteBase):
    def calcular_precio_final(self): return self._data["precio"] * 1.08

class Cultural(PaqueteBase):
    def calcular_precio_final(self): return self._data["precio"] * 0.95

def factory_paquete(paquete_dict):
    # retorna la subclase correcta según categoría
```

Cada categoría aplica un ajuste de precio diferente, y la factory decide qué clase instanciar sin que el resto del código lo sepa.

---

## 11. Rutas Flask Implementadas

| Método | Ruta | Descripción |
|---|---|---|
| GET | `/` | Página principal (destacados, destinos, promociones) |
| GET | `/paquetes` | Catálogo con búsqueda, filtros y ordenamiento |
| GET | `/paquetes/<slug>` | Detalle de un paquete |
| GET | `/comparar` | Comparador de paquetes |
| GET/POST | `/login` | Inicio de sesión |
| GET/POST | `/registro` | Registro de nuevo usuario |
| GET | `/logout` | Cierra sesión |
| GET | `/favoritos` | Lista de paquetes favoritos |
| POST | `/favoritos/<id_paquete>/alternar` | Agrega/quita un favorito (AJAX) |
| GET | `/destinos` | Listado de destinos |
| GET | `/destinos/<id_destino>` | Detalle de un destino |
| GET | `/reserva/<slug>` | Formulario de reserva (requiere login) |
| POST | `/reserva/preparar/<slug>` | Prepara y valida la selección de la reserva |
| POST | `/reserva/guardar/<slug>` | Guarda la reserva |
| GET | `/reserva/confirmacion` | Confirmación de reserva |
| GET | `/reserva/confirmacion/pdf` | Descarga la reserva en PDF |
| GET | `/perfil` | Perfil del usuario logueado (reservas, historial, niveles) |
| GET | `/admin/dashboard` | Panel del administrador |
| POST | `/admin/paquetes/suspender` | Suspende/activa paquetes |
| POST | `/admin/reservas/<id_reserva>/reembolso` | Marca reembolso de una reserva |
| GET | `/admin/encuestas/reporte` | Reporte de encuestas |

---

## 12. Metodología de Desarrollo

**Scrum**

El desarrollo de **MAREVA** se gestionó bajo el marco de trabajo ágil **Scrum**, organizando el trabajo en ciclos cortos e iterativos (*sprints*) para entregar funcionalidades de forma incremental y continua.

- **Planificación y seguimiento:** Gestión de tareas, historias de usuario y avance del equipo mediante tableros Kanban en **GitHub Projects**.
- **Trabajo colaborativo:** Distribución de responsabilidades por módulos y capas de la arquitectura, con revisiones constantes para asegurar la calidad e integración del código.
- **Entrega incremental:** Validación temprana de cada funcionalidad (autenticación, catálogo, reservas, paneles y reportes) antes de pasar a la siguiente iteración.
---

## 13. Integrantes

| Nombre | Rol |
|---|---|
| Nicoll Valeria Sabogal | Lider del proyecto |
| Sofía Munevar | Tester |
| Laura Rubiano | Análisis de requisitos |
| César Uzcátegui | Diseñadora UX/UI |
| Andrés Aroca | Desarrollador |

---

## 14. Estado Actual del Proyecto

✅ Requisitos funcionales y no funcionales  
✅ Historias de usuario  
✅ Modelo Entidad-Relación (MER) y modelo lógico  
✅ Script SQL final PostgreSQL (13 módulos, 35+ tablas, datos iniciales)  
✅ Aplicación Flask conectada a PostgreSQL  
✅ Sistema de autenticación con hash de contraseñas y bloqueo por intentos fallidos  
✅ Catálogo de paquetes con Factory Method  
✅ Flujo completo de reservas con persistencia en BD y PDF  
✅ Favoritos, comparador, historial y perfil de cliente  
✅ Paneles de administración, guía y proveedor  
✅ Encuestas post-viaje y reportes  
✅ Repositorio colaborativo en GitHub

---

**SENA — Arquitectura de Software**  
Inicio: 25 de abril de 2026
