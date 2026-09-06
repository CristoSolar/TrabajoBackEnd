# Catálogo de Biblioteca — Django

Aplicación web para gestionar el catálogo de una biblioteca (autores y libros),
desarrollada para el módulo **Desarrollo de aplicaciones del lado del servidor**.
Django 5.2 (LTS) + SQLite, con vistas basadas en clase, formularios validados,
plantillas con herencia y datos de prueba generados con IA mediante Faker.

---

## 1. Instalación y ejecución

Requisitos: Python 3.12+ y git.

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
│   ├── urls.py                   # Enrutador raíz: /admin/ y la app catalogo
│   ├── wsgi.py                   # Entrada para servidores WSGI (producción)
│   └── asgi.py                   # Entrada para servidores ASGI
└── catalogo/                     # Aplicación principal
    ├── models.py                 # Modelos Autor y Libro
    ├── views.py                  # Vistas basadas en clase (CRUD + listados)
    ├── forms.py                  # LibroForm con validación de ISBN
    ├── urls.py                   # Rutas de la app (namespace "catalogo")
    ├── admin.py                  # Registro de modelos en el admin
    ├── tests.py                  # Pruebas de modelos, formularios y vistas
    ├── migrations/               # Migraciones versionadas (0001_initial.py)
    ├── management/commands/
    │   └── seed.py               # Comando para generar datos de prueba
    └── templates/catalogo/
        ├── base.html             # Plantilla base: bloques titulo y contenido
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
| **Faker** | Genera datos realistas en español (`es_ES`): nombres, países, ISBN. Soporta semilla fija para reproducibilidad. | Listas de datos escritas a mano: poco variadas y laboriosas de mantener. |

SQLite no es un paquete: viene incluido en Python y es el motor por defecto de
Django, suficiente para desarrollo y evaluación (ver sección 7 para producción).

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

## 7. Protocolos, hosting y dominios

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
| Base de datos | SQLite (archivo local, ignorado por git) | PostgreSQL (concurrencia, respaldos) |
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

## 8. Bitácora de uso de IA

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
- `python manage.py test` → **7 pruebas, todas pasan**, incluida la que recorre
  las rutas de la aplicación verificando código 200 con el test client.
- `git status` antes del primer commit → `db.sqlite3` y `.venv/` ausentes.
