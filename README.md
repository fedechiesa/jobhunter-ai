# JobHunter AI

Plataforma personal para descubrir ofertas desde APIs públicas, organizarlas y analizar compatibilidad con un perfil técnico. **Sprints 1, 2 y 3A (Argentina First) implementados.** Uso local y de un solo usuario.

Solo consulta APIs de lectura de Greenhouse, Lever y Ashby para tableros de empresas configuradas. No realiza scraping, llamadas a LLM, envío de CV ni postulaciones. No automatiza LinkedIn o Indeed.

## Stack real

- Python 3.12+, FastAPI, Pydantic 2, Pydantic Settings, SQLAlchemy 2 y Psycopg 3.
- HTTPX2 para lectura de APIs públicas, sin claves ni cuentas externas.
- PostgreSQL 17 en Docker Compose, migraciones Alembic.
- React 19, TypeScript strict y Vite 8.
- pytest, Vitest 5, Testing Library, Ruff y Prettier.

## Estructura

```text
backend/
  app/
    api/                 # health, ofertas, perfil y descubrimiento
    core/                # configuración
    services/            # matching puro
    discovery/           # proveedores, normalización, preferencias y sincronización
    db.py                # engine y sesiones
    models.py            # entidades persistentes y estado de sincronización
    schemas.py           # contratos y validación
    factory.py           # construcción de la API
    main.py              # punto de entrada ASGI
    worker.py            # sincronización periódica independiente
  alembic/versions/       # migraciones versionadas
  tests/                 # unitarios e integración PostgreSQL
  constraints.txt        # versiones Python verificadas
frontend/
  src/components/        # formularios y oferta con score
  src/api.ts             # cliente HTTP
  src/App.tsx            # dashboard
docs/                    # arquitectura, roadmap y validación
config/sources.json      # tableros públicos y empresas configuradas
scripts/setup_env.py     # genera .env con credenciales aleatorias
compose.yaml             # PostgreSQL dev y test
.env.example             # plantilla sin secretos reales
```

## Requisitos

Python 3.12+, **Node 24 LTS** (también rama 22 desde 22.12, o 26+), npm y Docker con motor Linux/Compose disponible. El requisito de Node proviene de [Vitest 5](https://vitest.dev/guide/migration/) y [Vite](https://vite.dev/guide/). Node 20.12 no sirve para este frontend.

Comandos para PowerShell desde la raíz. Se usa `npm.cmd` para evitar restricciones de scripts de PowerShell. No es necesario activar el virtualenv.

## Ejecutar

1. Preparar dependencias y configuración:

   ```powershell
   py -3.12 -m venv .venv
   .\.venv\Scripts\python.exe -m pip install -c backend/constraints.txt -e "./backend[dev]"
   .\.venv\Scripts\python.exe scripts/setup_env.py
   ```

   El script crea `.env` con dos passwords aleatorios distintos y sus URLs. Si `.env` existe, no lo modifica: omití ese paso en ejecuciones posteriores. No publiques su contenido. Alternativamente, copiá `.env.example` y reemplazá los placeholders; no son credenciales recomendadas para uso real.

2. Iniciar PostgreSQL y aplicar migraciones:

   ```powershell
   docker compose up -d --wait db
   .\.venv\Scripts\python.exe -m alembic -c backend/alembic.ini upgrade head
   .\.venv\Scripts\python.exe -m alembic -c backend/alembic.ini check
   ```

3. Iniciar la API:

   ```powershell
   .\.venv\Scripts\python.exe -m uvicorn app.main:app --app-dir backend --host 127.0.0.1 --port 8000 --reload
   ```

   API: <http://127.0.0.1:8000/health>, DB: <http://127.0.0.1:8000/health/db>, Swagger: <http://127.0.0.1:8000/docs>.

4. En otra terminal, iniciar el frontend:

   ```powershell
   node --version
   cd frontend
   npm.cmd ci
   npm.cmd run dev
   ```

   Abrí <http://127.0.0.1:5173>. Pulsá **Sincronizar ahora** para consultar los tableros configurados. También podés agregar ofertas manualmente. Guardá **Mi perfil** con tus habilidades y experiencia declaradas y pulsá **Calcular match**, o volvé a sincronizar para evaluar las ofertas descubiertas. Los resultados persisten al recargar.

En esta copia de trabajo hay Node 24.22.2 portable en `.local/`, ignorado por Git. Para usarlo, desde la raíz y antes de `cd frontend`:

```powershell
$env:Path = "$PWD\.local\node-v24.22.2-win-x64;$env:Path"
```

La descarga portable es un recurso local de esta sesión. En un clon nuevo instalá Node 24 LTS o usá `.nvmrc`. En Linux/macOS usá `python3.12 -m venv .venv`, reemplazá `.\.venv\Scripts\python.exe` por `.venv/bin/python` y `npm.cmd` por `npm`. Las restricciones Python fijan versiones verificadas; pip puede incorporar dependencias de plataforma como uvloop.

Para detener: `Ctrl+C` en API/frontend y `docker compose --profile test down`. El volumen de desarrollo se conserva. No agregues `--volumes` si querés conservar ofertas. Cambiar passwords en `.env` no cambia los de un volumen ya inicializado: conservá esa configuración o administrá explícitamente su rotación.

## Variables de entorno

Backend/Alembic leen `.env` raíz independientemente del directorio actual; el entorno del proceso tiene precedencia. Compose usa ese archivo al ejecutarse desde la raíz. Vite usa `envDir` raíz y solo expone `VITE_*` al navegador.

| Variable | Uso |
| --- | --- |
| `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB` | Inicialización de PostgreSQL de desarrollo. |
| `POSTGRES_PORT` | Puerto loopback de desarrollo, default 5432. |
| `DATABASE_URL` | URL SQLAlchemy obligatoria con driver `postgresql+psycopg`. |
| `TEST_POSTGRES_PASSWORD` | Password propio del contenedor de pruebas. |
| `TEST_POSTGRES_PORT` | Puerto loopback de pruebas, default 5433. |
| `TEST_DATABASE_URL` | DB de integración, nombre terminado en `_test`. |
| `CORS_ORIGINS` | Array JSON de orígenes locales permitidos. |
| `VITE_API_BASE_URL` | URL pública de API, default `http://127.0.0.1:8000`. Reiniciar Vite/recompilar si cambia. |
| `SOURCES_FILE` | Ruta absoluta opcional al JSON de tableros; default `config/sources.json` raíz. |
| `SYNC_INTERVAL_SECONDS` | Espera entre ejecuciones del worker; default 3600, mínimo 60. |
| `PROVIDER_TIMEOUT_SECONDS` | Timeout HTTP por fase de conexión/lectura; default 10, máximo 30. |
| `PROVIDER_MAX_ATTEMPTS` | Intentos por request, default 2, máximo 3. |
| `PROVIDER_REQUEST_DELAY_SECONDS` | Pausa entre requests, default 0.3, mínimo 0.25 segundos. |
| `SOURCE_MIN_INTERVAL_SECONDS` | Espera persistente por tablero después de una lectura correcta; default 60. |
| `SOURCE_ERROR_BACKOFF_SECONDS` | Espera inicial tras error, default 60; crece exponencialmente hasta 24 horas. |
| `PROFILE_DRAFT_FILE` | Borrador profesional privado, default `private/profile.json`. Nunca se versiona. |

Si cambiás puertos o nombres, actualizá las URLs. Codificá caracteres especiales de passwords al construir URLs manualmente; el generador usa caracteres seguros para URL. `.env`, datos privados, CVs, dumps, node_modules, virtualenv, cobertura y builds se excluyen de Git.

## API disponible

| Método | Ruta | Resultado |
| --- | --- | --- |
| GET | `/health` | Liveness sin conexión a DB. |
| GET | `/health/db` | `SELECT 1`; 503 sin DB. No valida migraciones. |
| GET | `/jobs?limit=20&offset=0` | Ofertas nuevas primero, límite 1–100 (default 100), con score guardado o `null`. |
| POST | `/jobs` | Crea oferta manual, 201. |
| GET | `/jobs/{id}` | Detalle; 404 si no existe. |
| POST | `/jobs/{id}/match` | Calcula/actualiza score; 409 sin perfil, 404 sin oferta. Sin body. |
| GET | `/profile` | Perfil; 404 antes del primer guardado. |
| GET | `/profile/draft` | Valida y devuelve el borrador local explícito; 404 si no existe, 422 si es inválido. No lee CVs ni guarda automáticamente. |
| PUT | `/profile` | Crea/actualiza singleton e invalida scores previos. |
| GET | `/sources` | Configuración persistida de tableros y resultado de cada fuente. Registra nuevos tableros del JSON de forma idempotente. |
| PATCH | `/sources/{id}` | Pausa/reactiva una fuente con `{"enabled": false/true}`. |
| GET | `/sync/status` | Bloqueo de sincronización activo y última ejecución. |
| POST | `/sync` | Sincronización manual, sin body; 409 si otra ejecución tiene el bloqueo. |
| GET / PUT | `/search-preferences` | Consulta/edita intereses de búsqueda, separados del perfil profesional. |

Ejemplo ficticio para `PUT /profile`:

```json
{"skills": ["python", "sql"], "experience_years": 2, "preferred_location": "Example City", "prefer_remote": true}
```

Ejemplo ficticio para `POST /jobs`:

```json
{
  "title": "Backend Engineer",
  "company": "Example Labs",
  "description": "Oferta ficticia para probar el flujo local.",
  "location": "Example City",
  "remote": true,
  "required_skills": ["python", "sql"],
  "experience_years": 4,
  "url": "https://example.com/jobs/1",
  "source_id": 1
}
```

El matching mantiene habilidades 70%, experiencia 20% y ubicación 10%. La versión `deterministic-v1.1` reconoce alternativas explícitas de ciudades y etiquetas de modalidad en la ubicación. Para ofertas importadas se detectan menciones explícitas de tecnologías y años mediante reglas; el dashboard las identifica como inferencias, que pueden incluir requisitos opcionales. No se atribuye experiencia ni habilidades al candidato. Sin perfil guardado no se genera score. La **prioridad de búsqueda** es otra métrica, basada en intereses; no es compatibilidad ni elegibilidad geográfica. Detalles en [ARCHITECTURE.md](docs/ARCHITECTURE.md).

## Fuentes, filtros y sincronización

`config/sources.json` contiene ocho tableros verificados: Canonical y Sezzle (Greenhouse), dLocal, Despegar, RYZ Labs y Mutt Data (Lever), Ashby y Silver.dev (Ashby). Se conservaron los tres proveedores existentes; no hay búsqueda global ni descubrimiento automático de empresas. Antes de agregar otro tablero, verificá su URL pública, API documentada, respuesta y restricciones; luego agregá `provider`, `board_token`, `company`, `region` (`global`, o `eu` solo para Lever) y `enabled`. La evidencia y decisiones de integración están en [SPRINT_3A_VALIDATION.md](docs/SPRINT_3A_VALIDATION.md).

El archivo admite hasta 20 tableros, con identificadores alfanuméricos, guiones y guiones bajos. La aplicación construye URLs únicamente en hosts oficiales; no acepta endpoints arbitrarios. Nuevos tableros se registran al consultar fuentes o sincronizar. Las pausas hechas en la interfaz persisten en DB. `enabled: false` en el archivo fuerza la pausa; quitar una entrada pausa su historial sin borrarlo. Volver a habilitar requiere que esté presente con `enabled: true` y activarla desde la interfaz/API. Los cambios de nombre de empresa se recogen en la próxima lectura.

La migración agrega campos sin borrar ofertas, perfiles ni scores existentes. Cada referencia externa es única por proveedor/tablero. Las repeticiones actualizan la misma fila. Entre fuentes se detectan duplicados únicamente con URL de postulación normalizada, empresa y título exactamente iguales; los alias conservan historial y se ocultan del listado por defecto. `include_duplicates=true` permite auditarlos.

Una lectura completa y válida permite marcar ausencias como **potencialmente inactivas**. No se borran ni se afirman cerradas. Timeouts, errores HTTP, datos inválidos o paginación incompleta conservan el estado anterior. Errores 401/403/404 o regiones no soportadas pausan solo esa fuente. Revisá el error antes de reactivarla. `next_allowed_at` y el contador de fallos persisten entre procesos; las ejecuciones durante la espera reportan `deferred` y no marcan ausencias. Se respeta también `Retry-After` largo o expresado como fecha.

Se excluyen entradas explícitas de Talent Pool/bolsa de talento de todos los proveedores y prospect posts de Greenhouse. Si se habían importado antes de esta corrección, conservan su historial y quedan fuera de las vacantes activas. Eso no significa que la bolsa de talento haya cerrado.

La interfaz filtra por palabra clave, ubicación textual, país (Argentina, otros o desconocido), seniority, clasificación, tablero, proveedor, modalidad, publicación, descubrimiento, disponibilidad y score mínimo. El orden inicial `recommended` muestra Prioritaria Argentina, Alternativa internacional, Revisión necesaria y Despriorizada; dentro de cada grupo prioriza el idioma preferido y la prioridad de búsqueda. También siguen disponibles los órdenes por fecha, prioridad o score. Los filtros se combinan con AND; fechas de publicación desconocidas no coinciden con `published_after`.

```text
GET /jobs?q=python&location=Argentina&provider=lever&availability=active&sort=priority
GET /jobs?workplace_type=hybrid&discovered_after=2026-01-01T00:00:00Z
GET /jobs?min_score=70&sort=score
GET /jobs?country=AR&seniority=junior&compatibility=argentina_priority&sort=recommended
GET /jobs?source_id=119&published_after=2026-10-01T00:00:00Z
```

`min_score` requiere resultados previamente calculados. Las preferencias iniciales priorizan Data Analyst/BI Jr, Python Jr/Trainee, AI/Data Science Trainee y Backend/Fullstack Jr, Argentina/CABA/GBA y hasta dos años. Las preferencias ya guardadas se conservan. Los requisitos ambiguos quedan para revisión; los puestos claramente senior se despriorizan y se conservan. Worldwide/Americas/LATAM son pistas para revisar, nunca confirmación de admisión desde Argentina. `assessment` expone valor, estado (`confirmed`, `inferred`, `unknown`), fragmento de evidencia y razones; confirmación significa declaración de la fuente, no verificación legal de elegibilidad.

## Perfil profesional editable y privado

El singleton existente conserva `skills`, `experience_years`, `preferred_location` y `prefer_remote`. La extensión opcional `professional` contiene competencias con contexto y confirmación, estudios, trabajos, proyectos, idiomas, roles objetivo, país de residencia, idioma preferido y máximo de experiencia requerida. Los años del perfil representan experiencia IT remunerada; no se suman estudios, proyectos ni trabajos de otro sector. No se inventan fechas, logros, empleadores ni niveles de dominio. `pending` es el estado inicial de detalles no confirmados; `user_confirmed` significa confirmado por el usuario, sin validación externa.

En esta copia de trabajo, la información declarada se preparó exclusivamente en `private/profile.json` (ignorado por Git) y se guardó en la base local. Desde **Mi perfil** se pueden editar todas las secciones, agregar/quitar entradas y cambiar su confirmación; **Cargar borrador profesional local** carga ese archivo para revisión. No se necesita actualizar PDF o LinkedIn. Un clon nuevo no incluye información profesional privada: completá el formulario o creá explícitamente tu borrador con el contrato de `/docs`.

Después de aplicar migraciones, también se puede inicializar el perfil desde ese borrador:

```powershell
.\.venv\Scripts\python.exe scripts/setup_profile.py
.\.venv\Scripts\python.exe scripts/setup_profile.py --reclassify-only
```

El primer comando preserva un perfil existente; `--replace` permite reemplazarlo explícitamente. Reclasificar conserva ofertas y referencias históricas. Guardar el perfil invalida scores y recalcula categorías; el próximo match o sync calcula los scores con las nuevas entradas. El esquema versionado y `origin` preparan una futura importación local de CV, que no está implementada.

Se mantiene el matching 70/20/10. Con perfil estructurado usa `deterministic-v1.2-ar`: remoto desconocido/restringido no recibe puntos geográficos y presencial requiere ubicación compatible. El perfil antiguo conserva `v1.1` hasta completar su extensión, para no reinterpretar silenciosamente datos históricos. El score técnico no es elegibilidad ni probabilidad de contratación; años desconocidos conservan la convención de scoring anterior y se muestran explícitamente como desconocidos.

Auditoría reproducible de los tableros, sin DB ni datos del candidato:

```powershell
.\.venv\Scripts\python.exe scripts/audit_sources.py --save-snapshots .local/sprint3a-snapshots
.\.venv\Scripts\python.exe scripts/audit_sources.py --snapshots .local/sprint3a-snapshots --output .local/sprint3a-offline.json
```

La medición de este sprint obtuvo 935 publicaciones, 116 con Argentina explícita, 100 junior/trainee explícitas y 9 con ambos criterios. Esos nueve registros incluyen roles ajenos a IT. La revisión de cierre corrigió un falso positivo: un rango de 2–4 años y comunicación profesional en inglés no acreditan un puesto junior adecuado. Con `argentina-v1.1` quedan **0 prioritarias, 82 para revisión y 853 despriorizadas**, sin alternativas internacionales confirmadas. Data Developer de Mutt Data es una pista condicionada por inglés y seniority desconocidos, no una compatibilidad garantizada. Muestra de nueve ofertas, enlaces, requisitos y resultados en [SPRINT_3A_RELEASE_VALIDATION.md](docs/SPRINT_3A_RELEASE_VALIDATION.md).

## Automatización periódica

Desde la raíz, con la migración aplicada, ejecutá en una terminal independiente:

```powershell
.\.venv\Scripts\python.exe -m app.worker
```

Una sola ejecución o intervalo explícito:

```powershell
.\.venv\Scripts\python.exe -m app.worker --once
.\.venv\Scripts\python.exe -m app.worker --interval-seconds 3600
```

El worker ejecuta inmediatamente y luego espera el intervalo configurado desde el fin de cada ciclo. No depende de Uvicorn ni de `--reload`; `Ctrl+C` lo detiene. Un advisory lock de PostgreSQL compartido con `/sync` impide superposiciones entre procesos. Si otro proceso sincroniza, `--once` termina sin duplicar trabajo. Sale con código 1 ante resultado parcial/fallido o error de configuración/DB; 0 si termina correctamente o hay una ejecución activa. Errores fatales interrumpidos se registran como tales en el próximo ciclo.

En Windows podés configurar el Programador de tareas con el ejecutable absoluto `.venv\Scripts\python.exe`, argumentos `-m app.worker --once` y directorio inicial raíz. Usá una tarea cada hora, sin iniciar otra instancia mientras la anterior siga activa; el bloqueo de DB agrega protección. No se creó ninguna tarea de Windows automáticamente.

Para un despliegue posterior, ejecutá `python -m app.worker` como servicio supervisado independiente de la API, o programá `--once` con el scheduler del entorno. API y worker deben compartir DB y configuración. Aplicá migraciones antes de iniciarlos, mantené PostgreSQL en una red privada y agregá autenticación/seguridad antes de exponer la API. Todavía no se proporciona despliegue público.

Los logs de descubrimiento son JSON, con run ID, proveedor, contadores y códigos de error seguros. No registran cuerpos de ofertas ni credenciales. Los requests tienen timeout y reintentos limitados; se respeta `Retry-After` numérico corto y se difieren al próximo ciclo las esperas largas o expresadas como fecha. Máximo 20 páginas Lever de 100 ofertas: excederlo falla la fuente sin marcar ausencias. La sincronización HTTP es síncrona; el cliente espera hasta tres minutos, y puede consultarse `/sync/status` si la conexión se interrumpe.

## Tests, lint y build

Desde la raíz con dependencias instaladas:

```powershell
docker compose --profile test up -d --wait db-test
.\.venv\Scripts\python.exe -m pytest backend
.\.venv\Scripts\python.exe -m ruff check backend scripts
.\.venv\Scripts\python.exe -m ruff format --check backend scripts
.\.venv\Scripts\python.exe -m pip check
```

La integración usa PostgreSQL real, con otra DB, contenedor, password y puerto. Crea un esquema temporal, verifica migraciones reversibles y elimina solo ese esquema. Los tests fallan si falta la configuración; no omiten integración silenciosamente. Para unitarios sin PostgreSQL accesible:

```powershell
.\.venv\Scripts\python.exe -m pytest backend -m "not integration"
```

Desde `frontend/` con Node compatible:

```powershell
npm.cmd ci
npm.cmd test
npm.cmd run lint
npm.cmd run format:check
npm.cmd run build
npm.cmd audit
```

`lint` verifica TypeScript estricto en app, tests y configuración. `build` genera `frontend/dist/`, ignorado. Los tests normales usan datos ficticios y respuestas simuladas: nunca necesitan las APIs externas. La integración utiliza exclusivamente la base de testing. [VALIDATION.md](docs/VALIDATION.md) conserva el cierre del Sprint 1 y [SPRINT_2_VALIDATION.md](docs/SPRINT_2_VALIDATION.md) documenta resultados y lecturas reales del Sprint 2. CI reproduce los controles en Linux con Python 3.12 y Node 24.

## Estado y límites

Operativos: ofertas manuales y reales, tres proveedores y ocho tableros públicos verificados, normalización, deduplicación, evidencia geográfica y de requisitos, clasificación Argentina First, historial de sincronización, filtros, preferencias editables, perfil profesional estructurado y scores persistentes, dashboard con paginación, espera/pausa por fuente y worker independiente. Las métricas del dashboard corresponden a la página actual.

Sin autenticación, edición/borrado manual de ofertas, importación/generación de CV, historial de versiones de score, LLMs, agentes ni postulaciones automáticas. Las APIs cubren únicamente las empresas configuradas. Las reglas geográficas no validan permisos laborales; Ashby ahora aporta cobertura argentina mediante Silver.dev. Uso local; no está preparado para exposición pública o multiusuario. Las URLs se abren solo por decisión del usuario.

Sprint 3A cerrado dentro de su alcance; Sprint 3B pendiente según [ROADMAP.md](docs/ROADMAP.md). La evidencia actual está en [SPRINT_3A_VALIDATION.md](docs/SPRINT_3A_VALIDATION.md). La revisión visual quedó pendiente por timeout de autorización de la herramienta; tests de componentes y verificación HTTP aprobados. Los informes de Sprints 1 y 2 conservan sus resultados históricos.
