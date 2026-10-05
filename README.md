# Catálogo de Biblioteca — Django

Aplicación web para gestionar el catálogo de una biblioteca (autores y libros),
desarrollada para el módulo **Desarrollo de aplicaciones del lado del servidor**.
Django 5.2 (LTS) + PostgreSQL (Docker) o SQLite (local), con vistas basadas en clase, formularios validados,
plantillas con herencia y datos de prueba generados con IA mediante Faker.
Incluye una **API RESTful** (Django REST Framework) con autenticación por token
en `/api/v1/` (ver sección 9).

---

## 1. Instalación y ejecución

### Opción A: Docker (recomendada, usa PostgreSQL)

Requisitos: Docker con Compose. Se levantan dos contenedores: `db`
(PostgreSQL 17) y `web` (Django: sitio + panel `/admin/`).

```bash
git clone <URL-del-repositorio>
cd TrabajoBackEnd
cp .env.example .env            # opcional: ajustar credenciales
docker compose up --build       # migra, crea superusuario y levanta el servidor
```

- Aplicación: <http://localhost:8000/>
- Admin: <http://localhost:8000/admin/> (usuario `admin`, clave `admin1234`
  por defecto; cambiar en `.env` con `DJANGO_SUPERUSER_*`).
- Datos de prueba y pruebas dentro del contenedor:

```bash
docker compose exec web python manage.py seed --autores 10 --libros 40
docker compose exec web python manage.py test
```

Los datos persisten en el volumen `pgdata`. `docker compose down -v` lo borra.

### Opción B: Local con SQLite

Requisitos: Python 3.12+ y git. Si `POSTGRES_HOST` no está definido,
`settings.py` usa SQLite automáticamente, así que no hace falta instalar
PostgreSQL para desarrollar o correr las pruebas.

```bash
# 1. Clonar el repositorio
git clone <URL-del-repositorio>
cd TrabajoBackEnd

# 2. Crear y activar un entorno virtual
python -m venv .venv
source .venv/bin/activate        # Linux/macOS
# .venv\Scripts\activate         # Windows

# 3. Instalar dependencias
pip install -r requirements.txt

# 4. Aplicar migraciones (crea db.sqlite3)
python manage.py migrate

# 5. Cargar datos de prueba
python manage.py seed --autores 10 --libros 40

# 6. Ejecutar las pruebas
python manage.py test

# 7. Levantar el servidor de desarrollo
python manage.py runserver
```

La aplicación queda disponible en <http://127.0.0.1:8000/>.
Para usar el panel de administración, crear un superusuario con
`python manage.py createsuperuser` y entrar a `/admin/`.

---

## 2. Estructura de archivos

```
TrabajoBackEnd/
├── manage.py                     # Punto de entrada de los comandos de Django
├── requirements.txt              # Dependencias del proyecto
├── config/                       # Configuración global del proyecto
│   ├── settings.py               # Apps instaladas, BD, plantillas, idioma
│   ├── urls.py                   # Enrutador raíz: /admin/, /api/v1/ y la app catalogo
│   ├── wsgi.py                   # Entrada para servidores WSGI (producción)
│   └── asgi.py                   # Entrada para servidores ASGI
└── catalogo/                     # Aplicación principal
    ├── models.py                 # Modelos Autor y Libro
    ├── views.py                  # Vistas basadas en clase (CRUD + listados)
    │                             # y mixin SoloBibliotecario (login + permisos)
    ├── forms.py                  # LibroForm con validación de ISBN
    ├── serializers.py            # Serializadores DRF de Autor y Libro (JSON)
    ├── api.py                    # ViewSets, login/logout por token y rutas /api/v1/
    ├── authentication.py         # TokenConExpiracion: token de DRF con vencimiento
    ├── urls.py                   # Rutas de la app (namespace "catalogo")
    ├── admin.py                  # Registro de modelos en el admin
    ├── tests.py                  # Pruebas de modelos, formularios, vistas, permisos y API
    ├── migrations/               # 0001_initial.py y 0002_grupo_bibliotecarios.py
    ├── management/commands/
    │   └── seed.py               # Comando para generar datos de prueba
    ├── templates/registration/
    │   ├── login.html            # Formulario de inicio de sesión
    │   └── logged_out.html       # Confirmación de cierre de sesión
    └── templates/catalogo/
        ├── base.html             # Base: bloques, estado de sesión y enlaces por permiso
        ├── _estado_badge.html    # Parcial reutilizado con {% include %}
        ├── libro_list.html       # Listado con búsqueda, filtro y paginación
        ├── libro_detail.html     # Detalle de libro
        ├── libro_form.html       # Alta y edición (comparten plantilla)
        ├── libro_confirm_delete.html
        ├── autor_list.html       # Autores con conteo de libros
        └── autor_detail.html     # Detalle de autor y sus libros
```

---

## 3. Correspondencia MVC → MVT

Django usa el patrón **MVT** (Model–View–Template), una variante de MVC donde
el framework mismo hace de controlador (el enrutamiento y el ciclo
petición/respuesta).

| MVC clásico | MVT en Django | En este proyecto |
|---|---|---|
| **Modelo** (datos y reglas de negocio) | **Model** | `catalogo/models.py`: `Autor` y `Libro`, con restricciones de unicidad y estados |
| **Vista** (presentación al usuario) | **Template** | `catalogo/templates/catalogo/*.html`: qué se muestra y cómo |
| **Controlador** (coordina entrada y salida) | **View** + URLconf | `catalogo/views.py` decide qué datos van a cada plantilla; `urls.py` mapea URL → vista |

Es decir: la "View" de Django **no** es la vista de MVC; corresponde al
controlador. La capa de presentación de MVC vive en las plantillas.

---

## 4. Justificación de paquetes externos

| Paquete | Por qué este | Alternativa descartada |
|---|---|---|
| **Django ≥ 5.2.8 (LTS)** | Framework completo: ORM, migraciones, admin, formularios y sistema de plantillas integrados; menos decisiones y menos código que ensamblar piezas sueltas. Se requiere **5.2.8 o superior** porque el entorno usa Python 3.14 y esa es la primera versión de la rama 5.2 que lo soporta (agregado en la release de mantenimiento 5.2.8; Django 5.1 no soporta 3.14 en absoluto). 5.2 es además la versión LTS (soporte extendido). | Flask: microframework, habría que elegir e integrar ORM, migraciones y formularios a mano. |
| **django-crispy-forms** | Renderiza formularios con estructura y clases correctas sin repetir HTML campo por campo. | Escribir el HTML de cada campo a mano: repetitivo y propenso a desalinearse con el formulario. |
| **crispy-bootstrap5** | Template pack que conecta crispy-forms con Bootstrap 5 (la versión usada en `base.html`). | crispy-bootstrap4: no corresponde a la versión de Bootstrap del proyecto. |
| **djangorestframework** | Estándar de facto para APIs en Django: serializadores, ViewSets, routers, autenticación por token, permisos, paginación y throttling, todo configurable desde `settings.REST_FRAMEWORK` según la documentación oficial. | `JsonResponse` a mano: habría que reimplementar validación, códigos HTTP, negociación de contenido y autenticación. |
| **Faker** | Genera datos realistas en español (`es_ES`): nombres, países, ISBN. Soporta semilla fija para reproducibilidad. | Listas de datos escritas a mano: poco variadas y laboriosas de mantener. |

SQLite no es un paquete: viene incluido en Python y es el motor por defecto de
Django, suficiente para desarrollo y evaluación (ver sección 8 para producción).

---

## 5. Decisiones de diseño de los modelos

- **`related_name="libros"`** en la FK de `Libro` → `Autor`: permite navegar la
  relación inversa como `autor.libros.all()` en lugar del nombre autogenerado
  `libro_set`, que es menos legible y no está en español como el resto del código.

- **`UniqueConstraint(fields=["titulo", "autor"])`**: un mismo título puede
  existir en el catálogo escrito por autores distintos, pero no duplicado para
  el mismo autor. La restricción vive en la base de datos, no solo en Python,
  así que protege también contra inserciones que no pasen por los formularios
  (admin, shell, seed).

- **`TextChoices` para el estado**: centraliza los valores válidos
  (Disponible / Prestado / Dado de baja) en un solo lugar, da etiquetas legibles
  con `get_estado_display()` y evita strings mágicos repartidos por el código.
  El valor se guarda como texto corto y estable (`"DISPONIBLE"`, `"PRESTADO"`,
  `"BAJA"`), independiente de la etiqueta mostrada.

- **`select_related("autor")`** en el listado de libros: el listado muestra el
  autor de cada libro; sin esto, Django haría una consulta por fila (problema
  N+1: 1 consulta para los libros + N para sus autores). Con `select_related`
  se resuelve todo con un único JOIN.

- **`annotate(total_libros=Count("libros"))`** en los listados de autores: el
  conteo lo hace la base de datos en la misma consulta, en lugar de llamar a
  `autor.libros.count()` por cada autor desde la plantilla (otra forma del
  mismo problema N+1).

- **`ordering` y `verbose_name` en `Meta`**: orden alfabético estable en
  listados y paginación (la paginación sin `ordering` produce resultados
  inconsistentes), y nombres en español en el admin.

- **`get_absolute_url`**: las vistas `CreateView`/`UpdateView` redirigen a él
  tras guardar, y las plantillas enlazan al detalle sin repetir la URL.

---

## 6. Comando `seed`

```bash
python manage.py seed --autores 10 --libros 40          # generar
python manage.py seed --autores 10 --libros 40 --limpiar # borrar y regenerar
```

Decisiones:

- **Semilla fija (`Faker.seed(2026)` y `random.seed(2026)`)**: cada ejecución
  sobre una base vacía produce exactamente los mismos datos. Esto hace la
  evaluación reproducible: el revisor ve lo mismo que el desarrollador, y
  cualquier captura o prueba manual se puede repetir.

- **Distribución ponderada de estados (65% disponible, 25% prestado, 10% baja)**:
  una distribución uniforme (un tercio cada una) no representa una biblioteca
  real, donde la mayoría del catálogo está en estantería y dar de baja es
  excepcional. Los datos de prueba deben parecerse a los datos reales para que
  el filtro por estado y los listados se vean como en producción.

- **Duplicados se saltan, no rompen**: antes de insertar se verifica la
  restricción (título, autor) y la unicidad del ISBN; un duplicado generado por
  azar se omite y se informa al final, en lugar de abortar el comando con un
  `IntegrityError`.

- **`@transaction.atomic`**: la generación completa es una sola transacción; si
  algo falla a mitad de camino no quedan datos parciales.

- **Locale `es_ES`**: nombres y países en español, coherentes con la interfaz.

---

## 7. Autenticación, sesiones y permisos

El catálogo es **público para consultar** (listados y detalle) y **restringido
para modificar**. Crear, editar y eliminar libros exige sesión iniciada y el
permiso correspondiente.

### Rutas de autenticación

| Ruta | Vista | Descripción |
|---|---|---|
| `/cuentas/login/` | `LoginView` de Django | Formulario de inicio de sesión (`registration/login.html`) |
| `/cuentas/logout/` | `LogoutView` de Django | Cierre de sesión por POST (Django ≥ 5 ya no acepta GET) |
| `/cuentas/password_change/` | `PasswordChangeView` | Incluida con `django.contrib.auth.urls` |
| `/admin/` | Django Admin | Requiere `is_staff` |

`config/urls.py` incluye `django.contrib.auth.urls`, de modo que no se reescribe
lógica de autenticación ya resuelta y probada por el framework.

### Política de sesiones

En `config/settings.py`:

| Ajuste | Valor | Motivo |
|---|---|---|
| `SESSION_COOKIE_AGE` | `1800` (30 min) | Caducidad de la sesión |
| `SESSION_SAVE_EVERY_REQUEST` | `True` | Renueva la cookie en cada petición: el plazo cuenta desde la **última actividad**, no desde el login |
| `SESSION_EXPIRE_AT_BROWSER_CLOSE` | `True` | La sesión no sobrevive al cierre del navegador |
| `SESSION_COOKIE_HTTPONLY` | `True` | La cookie no es legible desde JavaScript (mitiga robo de sesión por XSS) |
| `SESSION_COOKIE_SAMESITE` / `CSRF_COOKIE_SAMESITE` | `Lax` | Reduce la superficie de CSRF entre sitios |
| `SESSION_COOKIE_SECURE` / `CSRF_COOKIE_SECURE` | `True` si `DEBUG=False` | Las cookies solo viajan por HTTPS en producción |
| `SECURE_SSL_REDIRECT`, `SECURE_HSTS_*`, `X_FRAME_OPTIONS` | activos con `DJANGO_SSL_REDIRECT=1` | Redirección forzada a HTTPS y HSTS un año. Opt-in, porque exigir HTTPS en un entorno servido por HTTP plano deja la aplicación inaccesible |

`DJANGO_DEBUG` ahora vale `0` por defecto: un despliegue que olvide definir la
variable arranca en modo seguro, no en modo depuración.

### Perfiles de rol

La migración `catalogo/migrations/0002_grupo_bibliotecarios.py` crea el grupo
**Bibliotecarios** con los permisos `add_libro`, `change_libro`, `delete_libro`,
`add_autor` y `change_autor`. Al ser una migración de datos, el rol existe en
cualquier entorno recién levantado sin pasos manuales, y `reverse` lo elimina.

En `catalogo/views.py`, el mixin `SoloBibliotecario` combina
`LoginRequiredMixin` y `PermissionRequiredMixin`:

- usuario **anónimo** → redirección a `/cuentas/login/?next=…`;
- usuario **autenticado sin permiso** → `403 Forbidden`;
- usuario del grupo **Bibliotecarios** o superusuario → acceso.

Las plantillas consultan `perms.catalogo.*` para no mostrar botones que el
usuario no puede usar. El control real vive en las vistas: ocultar un enlace no
es una medida de seguridad, solo evita un error previsible.

Para asignar el rol: Django Admin → *Usuarios* → seleccionar el usuario →
*Grupos* → añadir **Bibliotecarios**.

### Pruebas de seguridad

`catalogo/tests.py` incluye `SesionYPermisosTests`, que verifica por ejecución:
redirección del anónimo, `403` del autenticado sin permiso, acceso del
bibliotecario, que un `POST` anónimo a la ruta de borrado **no** elimina el
libro, que `login`/`logout` crean y destruyen `_auth_user_id` en la sesión, y
que el grupo trae los permisos CRUD.

---

## 8. Protocolos, hosting y dominios

### Recorrido de una petición en producción

1. **DNS**: el navegador resuelve `www.mibiblioteca.cl` → dirección IP del
   servidor, consultando los servidores DNS del dominio.
2. **HTTPS (TLS)**: se establece una conexión cifrada sobre TCP (puerto 443).
   El certificado (por ejemplo, de Let's Encrypt) autentica al servidor.
3. **Nginx (servidor web / proxy inverso)**: recibe la petición HTTP, sirve
   directamente los archivos estáticos (CSS, imágenes) y reenvía las peticiones
   dinámicas al servidor de aplicación.
4. **WSGI (Gunicorn)**: traduce la petición HTTP al protocolo WSGI que Django
   entiende, y ejecuta varios procesos Python en paralelo (`config/wsgi.py` es
   el punto de entrada).
5. **Django**: resuelve la URL, ejecuta la vista, consulta la base de datos con
   el ORM, renderiza la plantilla y devuelve la respuesta, que recorre el
   camino inverso.

### Desarrollo vs producción

| Aspecto | Desarrollo (este repo) | Producción |
|---|---|---|
| Servidor | `runserver` (solo para desarrollo) | Nginx + Gunicorn |
| Protocolo | HTTP en localhost | HTTPS con certificado TLS |
| `DEBUG` | `True` | `False` (nunca `True`: expone información sensible) |
| `SECRET_KEY` | Clave de desarrollo en el código, marcada como tal | Variable de entorno, jamás en el repositorio |
| `ALLOWED_HOSTS` | vacío (localhost) | Dominio real, p. ej. `["mibiblioteca.cl"]` |
| Base de datos | PostgreSQL en contenedor `db` (o SQLite si no hay `POSTGRES_HOST`) | PostgreSQL gestionado, respaldos automáticos |
| Estáticos | Los sirve Django | `collectstatic` + Nginx |

### Alternativas de hosting

| Opción | Ejemplo | Ventajas | Desventajas |
|---|---|---|---|
| **PaaS** | Render, Railway, PythonAnywhere | Despliegue en minutos, TLS y dominio incluidos, sin administrar servidores | Menos control; el plan gratuito duerme o limita recursos |
| **VPS** | DigitalOcean, Hetzner, Linode | Control total (Nginx, Gunicorn, PostgreSQL a medida), costo fijo bajo | Hay que instalar, asegurar y mantener todo uno mismo |
| **Nube gestionada** | AWS (Elastic Beanstalk + RDS), Google Cloud | Escalado automático, servicios gestionados, alta disponibilidad | Complejidad y costos difíciles de prever para un proyecto pequeño |

Para un proyecto académico como este, un **PaaS** es la opción razonable: el
esfuerzo se concentra en la aplicación y no en la infraestructura. El dominio
se contrataría con un registrador (p. ej. NIC Chile para `.cl`) y se apuntaría
mediante registros DNS (A o CNAME) al proveedor de hosting.

---

## 9. API REST (Django REST Framework)

La API expone los mismos datos que la web, con las mismas reglas de permisos.
Todas las respuestas son JSON (`Content-Type: application/json`).

### Resumen de lo realizado (Unidad 3 – API RESTful)

| Indicador de la rúbrica | Qué se implementó | Dónde |
|---|---|---|
| 1. Configura DRF según documentación oficial | `rest_framework` y `rest_framework.authtoken` instalados; configuración global única en `REST_FRAMEWORK`; código separado en serializadores, vistas/rutas y autenticación | `config/settings.py`, `catalogo/serializers.py`, `catalogo/api.py`, `catalogo/authentication.py` |
| 2. Implementa autenticación | Login por usuario/contraseña que entrega token (`POST /auth/token/`), uso en cabecera `Authorization: Token …`, logout que lo revoca (`DELETE /auth/logout/`); sesión de Django para la API navegable | `catalogo/api.py`, `catalogo/authentication.py` |
| 3. Aplica recomendaciones de seguridad | Token con vencimiento, rotación en cada login, límite de 5 intentos/min en login, throttling general, escritura solo con permisos del grupo Bibliotecarios, solo JSON en producción, validación en serializadores | Tabla "Medidas de seguridad y por qué" más abajo |
| 4. Genera respuestas JSON | Formato consistente: paginado `count/next/previous/results`, campos de lectura útiles (`autor_nombre`, `estado_display`, `url`, `total_libros`), errores `{"detail": …}` o por campo | `catalogo/serializers.py`, `REST_FRAMEWORK` |
| 5. Implementa endpoints | CRUD completo de `/libros/` y `/autores/`, búsqueda, filtros, orden y paginación; raíz `/api/v1/` que lista los recursos | `catalogo/api.py` |
| 6. Características RESTful | Recursos en plural, rutas versionadas (`/api/v1/`), métodos HTTP según la acción (GET, POST, PUT, PATCH, DELETE) y códigos `200/201/204/400/401/403/404/429` | Tabla de endpoints más abajo |
| 7. Uso de IA como apoyo | Recomendaciones contrastadas, adaptadas o rechazadas y dos errores reales corregidos, con justificación | Sección 10, filas 14–20 |

Además: 13 pruebas automatizadas de la API (26 en total, todas pasan en
SQLite y en PostgreSQL vía Docker), la validación de ISBN se unificó en
`normalizar_isbn` para web y API, y se agregó la variable
`API_TOKEN_TTL_HORAS` a `.env.example` y `docker-compose.yml`.

### Configuración

- `rest_framework` y `rest_framework.authtoken` en `INSTALLED_APPS`
  (la segunda crea la tabla de tokens con `migrate`).
- Todo el comportamiento global vive en `REST_FRAMEWORK` dentro de
  `config/settings.py`: autenticación, permisos, renderizadores, parsers,
  paginación y límites de peticiones.
- Código organizado por responsabilidad: `serializers.py` (forma del JSON y
  validación), `api.py` (endpoints y rutas), `authentication.py` (token con
  vencimiento).

### Endpoints

Base: `http://localhost:8000/api/v1/` (`GET /api/v1/` lista los recursos).

| Método | Ruta | Acción | Quién | Respuesta |
|---|---|---|---|---|
| POST | `/auth/token/` | Obtener token (`username`, `password`) | Cualquiera | `201` token / `400` credenciales / `429` |
| DELETE | `/auth/logout/` | Revocar el token propio | Autenticado | `204` |
| GET | `/libros/` | Listar (paginado, 10 por página) | Público | `200` |
| POST | `/libros/` | Crear | Bibliotecario | `201` / `400` / `401` / `403` |
| GET | `/libros/{id}/` | Detalle | Público | `200` / `404` |
| PUT / PATCH | `/libros/{id}/` | Reemplazar / modificar parcialmente | Bibliotecario | `200` / `400` |
| DELETE | `/libros/{id}/` | Eliminar | Bibliotecario | `204` |
| GET | `/autores/` · `/autores/{id}/` | Listar / detalle (con `total_libros`) | Público | `200` / `404` |
| POST · PUT · PATCH | `/autores/` · `/autores/{id}/` | Crear / editar | Bibliotecario | `201` / `200` |
| DELETE | `/autores/{id}/` | Eliminar (borra sus libros en cascada) | Solo superusuario | `204` |

Parámetros de consulta en listados: `?page=2`, `?search=texto`,
`?ordering=-anio_publicacion`; en libros además `?estado=prestado` y
`?autor=<id>`.

### Formato de las respuestas

Listado (sobre paginado común a ambos recursos):

```json
{
  "count": 45,
  "next": "http://localhost:8000/api/v1/libros/?page=2",
  "previous": null,
  "results": [
    {
      "id": 91,
      "url": "http://localhost:8000/api/v1/libros/91/",
      "titulo": "Canto general",
      "autor": 14,
      "autor_nombre": "Pablo Neruda",
      "isbn": "9789560000001",
      "anio_publicacion": 1950,
      "paginas": 500,
      "estado": "DISPONIBLE",
      "estado_display": "Disponible",
      "fecha_creacion": "2026-10-05T18:00:20.409801-03:00"
    }
  ]
}
```

- `autor` se escribe y se lee como id; `autor_nombre` y `estado_display` son
  de solo lectura para que el cliente no tenga que hacer otra petición.
- `url` es el enlace al propio recurso (navegable).
- Errores: `{"detail": "..."}` para autenticación, permisos y 404; para
  validación, un objeto por campo, p. ej. `{"isbn": ["El ISBN debe tener 10 o 13 dígitos (se permiten guiones)."]}`.

### Uso con curl

```bash
# 1. Obtener token (usuario del grupo Bibliotecarios o superusuario)
curl -X POST http://localhost:8000/api/v1/auth/token/ \
     -H "Content-Type: application/json" \
     -d '{"username": "admin", "password": "admin1234"}'
# → {"token": "e887bc07...", "expira": "2026-10-06T02:00:20-03:00", "usuario": "admin"}

# 2. Crear un libro
curl -X POST http://localhost:8000/api/v1/libros/ \
     -H "Authorization: Token e887bc07..." -H "Content-Type: application/json" \
     -d '{"titulo": "Prueba", "autor": 1, "isbn": "978-956-00-0002-5", "anio_publicacion": 2020, "paginas": 100}'

# 3. Cambiar solo el estado
curl -X PATCH http://localhost:8000/api/v1/libros/1/ \
     -H "Authorization: Token e887bc07..." -H "Content-Type: application/json" \
     -d '{"estado": "PRESTADO"}'

# 4. Cerrar sesión (revoca el token)
curl -X DELETE http://localhost:8000/api/v1/auth/logout/ -H "Authorization: Token e887bc07..."
```

Con `DJANGO_DEBUG=1` las mismas URLs abiertas en el navegador muestran la
interfaz navegable de DRF.

### Medidas de seguridad y por qué

| Medida | Dónde | Justificación |
|---|---|---|
| Token por usuario en cabecera `Authorization` | `REST_FRAMEWORK` | Clientes externos (móvil, scripts) no manejan cookies ni CSRF; el token no viaja en la URL, así no queda en logs ni historial. |
| **Vencimiento del token** (8 h, `API_TOKEN_TTL_HORAS`) | `authentication.py` | El `TokenAuthentication` de DRF no expira nunca: un token filtrado serviría para siempre. Al vencer se borra y responde `401`. |
| **Rotación en cada login** y `DELETE /auth/logout/` | `api.py` | Iniciar sesión invalida el token anterior; el usuario puede revocarlo cuando quiera. |
| **Límite de intentos de login**: 5/min | scope `login` | Frena fuerza bruta de contraseñas; responde `429`. Además 60/min anónimo y 300/min autenticado en toda la API. |
| Lectura pública, escritura con permisos de modelo | `DjangoModelPermissionsOrAnonReadOnly` | Reutiliza el grupo **Bibliotecarios** de la web: un usuario sin rol recibe `403`. Autenticarse no basta para escribir. |
| Sesión + CSRF | `SessionAuthentication` | Permite usar la API navegable logueado; DRF exige token CSRF en escrituras por sesión, así que no abre un ataque CSRF. |
| Solo JSON en producción | `DEFAULT_RENDERER_CLASSES` | La interfaz navegable solo se activa con `DEBUG`; en producción no se expone una UI que facilite el reconocimiento de la API. |
| Solo se aceptan cuerpos JSON | `DEFAULT_PARSER_CLASSES` | Superficie mínima: sin formularios ni subida de archivos que la API no necesita. |
| Validación en el serializador | `serializers.py` | ISBN normalizado con la misma función que el formulario web (`normalizar_isbn`); unicidad título+autor validada antes de llegar a la BD (`400`, no `500`). |
| HTTPS, cookies seguras, HSTS | sección 7 | Fuera de `DEBUG` el token debe viajar cifrado; se reutiliza el endurecimiento ya configurado. |

Limitación conocida: el token se guarda en texto plano en la BD (diseño de
`rest_framework.authtoken`). Para mayor exigencia, la evolución natural es
JWT de corta vida (`djangorestframework-simplejwt`) o tokens con hash
(`django-rest-knox`).

### Pruebas de la API

`ApiTests` en `catalogo/tests.py` (13 pruebas, `APITestCase`) verifica: listado
público JSON y paginado, detalle y `404`, conteo de libros por autor, filtros
y búsqueda, `401` anónimo al escribir, `400` con credenciales malas, `403` sin
rol, CRUD completo del bibliotecario (`201`/`200`/`204`), errores de
validación por campo, token expirado rechazado y borrado, logout que revoca,
rotación del token en un nuevo login y `429` al sexto intento de login.

```bash
python manage.py test catalogo.tests.ApiTests
```

---

## 10. Bitácora de uso de IA

Proyecto desarrollado con asistencia de **Claude Code (Anthropic)**. La tabla
registra las interacciones relevantes y qué se hizo con cada sugerencia.

| # | Objetivo | Prompt (resumen) | Qué sugirió la IA | Decisión y justificación |
|---|---|---|---|---|
| 1 | Elegir versión de Django | Crear proyecto con Django 5.1 y SQLite | Detectó que el entorno tiene Python 3.14, que Django 5.1 no soporta, y propuso Django 5.2 LTS | **Adaptado y verificado**: el plan original decía 5.1, pero instalar 5.1 habría fallado con Python 3.14. No bastó con "5.2 funciona": se verificó en la documentación oficial de Django que el soporte para Python 3.14 se agregó recién en la release de mantenimiento **5.2.8**, y `requirements.txt` se fijó en `Django>=5.2.8,<6.0` para que una 5.2.x anterior no rompa la instalación en un entorno limpio |
| 2 | Diseñar los modelos | Modelos Autor y Libro con estados, ISBN único y unicidad título+autor | `TextChoices` para estados, `UniqueConstraint` en Meta, `related_name="libros"`, `get_absolute_url` | **Aceptado**: se revisó que los valores de estado fueran cortos y estables (`BAJA` en vez de `DADO_DE_BAJA` como valor en BD, por el `max_length`) |
| 3 | Validar ISBN | Validación: 10 o 13 dígitos tras quitar guiones | `clean_isbn` en el `ModelForm` usando `isdigit()` y `len() in (10, 13)` | **Aceptado**: se verificó con pruebas que rechaza letras, largos incorrectos, y que normaliza guiones antes de guardar |
| 4 | Evitar consultas N+1 | Listados eficientes | `select_related("autor")` en el listado de libros y `annotate(Count("libros"))` para el conteo por autor | **Aceptado**: alternativa (contar en la plantilla con `libros.count`) descartada por generar una consulta por autor |
| 5 | Plantillas | Herencia con bloques y un parcial reutilizado | `base.html` con bloques `titulo`/`contenido` y parcial `_estado_badge.html` incluido en 3 plantillas | **Adaptado**: la IA propuso el parcial para el badge de estado; se pidió además paleta propia (tonos papel/oliva/terracota) y tipografía Fraunces+Inter para no dejar el Bootstrap por defecto |
| 6 | Datos de prueba | Comando seed con Faker es_ES, reproducible | Semilla fija, distribución ponderada 65/25/10, verificación de duplicados antes de insertar, `@transaction.atomic` | **Aceptado con verificación**: se ejecutó y se comprobó la distribución real resultante (23/14/3 sobre 40 libros) consultando la BD con `annotate` |
| 7 | Pruebas automatizadas | Mínimo 5 pruebas: modelos, formulario y vistas | 7 pruebas: `__str__`, estado inicial, ISBN inválido/válido, listado 200, búsqueda filtra, y las 7 rutas responden 200 | **Aceptado**: se amplió lo pedido con la prueba de todas las rutas para cumplir el criterio de aceptación con evidencia, no supuestos |
| 8 | Mensajes al usuario | Feedback en crear/editar/eliminar | `messages.success` en `form_valid` de cada vista, mostrado como alertas en `base.html` | **Aceptado**: en `DeleteView` el mensaje va en `form_valid` (Django ≥ 4) y no en `delete()`, que ya no se invoca en el flujo normal |
| 9 | Estados vacíos | Que los listados vacíos orienten al usuario | Textos con la acción siguiente: enlace a crear libro, o instrucción de ejecutar el seed | **Aceptado**: cumple el requisito de no dejar solo "sin resultados" |
| 11 | Sesiones y autenticación | Cumplir el criterio de sesiones: proteger el CRUD | Proponía `LoginRequiredMixin` en todas las vistas | **Adaptado**: dejar el catálogo público y proteger solo escritura se ajusta mejor al caso de uso (una biblioteca se consulta sin cuenta). Se añadió `PermissionRequiredMixin` con permisos por modelo, que la sugerencia inicial no contemplaba |
| 12 | Perfiles de rol | Crear el grupo Bibliotecarios | Sugirió un comando de gestión a ejecutar manualmente | **Adaptado**: se implementó como migración de datos (`0002`), para que el rol exista en cualquier entorno sin un paso manual que se puede olvidar, y sea reversible |
| 13 | Endurecimiento HTTPS | Cookies seguras y HSTS en producción | `SECURE_SSL_REDIRECT=True` fijo cuando `DEBUG=False` | **Corregido tras fallo real**: con ese valor fijo, las pruebas devolvieron `301` en lugar de `200`, porque el test runner fuerza `DEBUG=False`. Se hizo opt-in con `DJANGO_SSL_REDIRECT`; el fallo confirmó que también habría roto cualquier despliegue tras HTTP plano |
| 14 | Configurar DRF | Agregar API REST al catálogo según documentación oficial | `rest_framework` + `authtoken` en `INSTALLED_APPS`, `REST_FRAMEWORK` con `TokenAuthentication` y `IsAuthenticated` global | **Adaptado**: `IsAuthenticated` global habría cerrado la lectura, que en la web es pública. Se usó `DjangoModelPermissionsOrAnonReadOnly` para mantener la misma regla en web y API (lectura libre, escritura solo con permisos del grupo Bibliotecarios) |
| 15 | Ubicar la autenticación | Token con vencimiento | Definir la clase `TokenConExpiracion` dentro de `api.py`, junto a las vistas | **Corregido tras fallo real**: `manage.py check` falló con *"Could not import 'catalogo.api.TokenConExpiracion' … circular import"*: DRF importa las clases de `REST_FRAMEWORK` al cargar sus vistas, y `api.py` importa esas vistas. Se movió a `authentication.py`, que es además la convención de DRF |
| 16 | Expiración del token | ¿Es seguro el `TokenAuthentication` de DRF? | Advirtió que los tokens no expiran nunca y propuso migrar a JWT (`simplejwt`) | **Adaptado**: JWT agrega una dependencia y el manejo de refresh tokens, excesivo para el alcance. Se cubrió el riesgo principal (token eterno) con 10 líneas: vencimiento configurable, borrado al expirar, rotación al hacer login y endpoint de logout. JWT queda documentado como evolución |
| 17 | Fuerza bruta | Proteger el endpoint de login | Throttling global anónimo/usuario | **Ampliado**: el límite global anónimo (60/min) permite demasiados intentos de contraseña. Se agregó un scope específico `login` de 5/min; hubo que declararlo explícitamente porque `ObtainAuthToken` trae `throttle_classes = ()` y anula el global (verificado leyendo el código fuente de DRF) |
| 18 | Validación compartida | Validar ISBN en la API | Copiar `clean_isbn` del formulario al serializador | **Rechazado el duplicado**: se extrajo `normalizar_isbn` a `models.py` y la usan formulario y serializador; una regla, un lugar |
| 19 | Pruebas de throttling | Probar el `429` | Escribir la prueba directamente | **Ajustado**: el contador de throttling vive en la caché y se comparte entre pruebas, lo que puede hacer fallar pruebas que no tienen relación. Se agregó `cache.clear()` en `setUp` |
| 20 | Interfaz navegable | ¿Dejar la UI navegable de DRF? | Dejarla activa siempre | **Adaptado**: solo con `DEBUG`; en producción se responde solo JSON para no ofrecer una UI de exploración |
| 10 | Seguridad del repo | No versionar secretos ni la BD | `.gitignore` antes del primer commit; `SECRET_KEY` reemplazada por una marcada como de desarrollo con comentario sobre variables de entorno | **Aceptado**: verificado con `git status` que `db.sqlite3` y `.venv/` no aparecen |

### Verificación de lo generado por IA

Todo el código sugerido se verificó ejecutando, no leyendo:

- `python manage.py check` → *System check identified no issues (0 silenced)*.
- `python manage.py migrate` → todas las migraciones aplican sin errores.
- `python manage.py seed --autores 10 --libros 40` → crea 10 autores y 40
  libros; distribución de estados comprobada por consulta: 23 disponibles,
  14 prestados, 3 dados de baja.
- `python manage.py seed --autores 3 --libros 5 --limpiar` → el flag `--limpiar`
  borra y regenera correctamente.
- `python manage.py test` → **26 pruebas, todas pasan**, incluidas las seis de
  sesión y permisos (anónimo redirigido, `403` sin permiso, acceso del
  bibliotecario, borrado anónimo bloqueado, ciclo login/logout y permisos del
  grupo) y las trece de la API (sección 9).
- Prueba manual de la API con `curl` contra `runserver`: `GET /api/v1/` lista
  los recursos, login devuelve `201` con token y vencimiento, `POST` crea
  (`201`), `DELETE` borra (`204`), `POST` anónimo da `401`, logout `204` e id
  inexistente `404`, todo con cuerpo JSON.
- `git status` antes del primer commit → `db.sqlite3` y `.venv/` ausentes.
