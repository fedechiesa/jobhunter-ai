# JobHunter AI

Plataforma personal para descubrir ofertas desde APIs públicas, organizarlas y analizar compatibilidad con un perfil técnico. **Foundation y Job Discovery Engine implementados (Sprints 1 y 2).** Uso local y de un solo usuario.

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

`config/sources.json` contiene Canonical/Greenhouse, dLocal/Lever y Ashby/Ashby. Los identificadores provienen de sus tableros públicos; no hay búsqueda global ni descubrimiento automático de empresas. Para agregar otro tablero, copiá el identificador de su URL pública y agregá un objeto con `provider`, `board_token`, `company`, `region` (`global`, o `eu` solo para Lever) y `enabled`.

El archivo admite hasta 20 tableros, con identificadores alfanuméricos, guiones y guiones bajos. La aplicación construye URLs únicamente en hosts oficiales; no acepta endpoints arbitrarios. Nuevos tableros se registran al consultar fuentes o sincronizar. Las pausas hechas en la interfaz persisten en DB. `enabled: false` en el archivo fuerza la pausa; quitar una entrada pausa su historial sin borrarlo. Volver a habilitar requiere que esté presente con `enabled: true` y activarla desde la interfaz/API. Los cambios de nombre de empresa se recogen en la próxima lectura.

La migración agrega campos sin borrar ofertas, perfiles ni scores existentes. Cada referencia externa es única por proveedor/tablero. Las repeticiones actualizan la misma fila. Entre fuentes se detectan duplicados únicamente con URL de postulación normalizada, empresa y título exactamente iguales; los alias conservan historial y se ocultan del listado por defecto. `include_duplicates=true` permite auditarlos.

Una lectura completa y válida permite marcar ausencias como **potencialmente inactivas**. No se borran ni se afirman cerradas. Timeouts, errores HTTP, datos inválidos o paginación incompleta conservan el estado anterior. Errores 401/403 o regiones no soportadas pausan solo esa fuente. Revisá el error antes de reactivarla.

Se excluyen entradas explícitas de Talent Pool/bolsa de talento de todos los proveedores y prospect posts de Greenhouse. Si se habían importado antes de esta corrección, conservan su historial y quedan fuera de las vacantes activas. Eso no significa que la bolsa de talento haya cerrado.

La interfaz filtra por palabra clave, ubicación textual, proveedor, modalidad, fecha de descubrimiento, disponibilidad y score mínimo; ordena por fecha, prioridad o compatibilidad. También se admite `published_after` y `min_priority` en API. Los filtros se combinan con AND; las fechas de publicación desconocidas no coinciden con `published_after`.

```text
GET /jobs?q=python&location=Argentina&provider=lever&availability=active&sort=priority
GET /jobs?workplace_type=hybrid&discovered_after=2026-01-01T00:00:00Z
GET /jobs?min_score=70&sort=score
```

`min_score` requiere resultados previamente calculados. Las preferencias iniciales priorizan roles junior/trainee de datos, Python, AI/LLM y QA, tecnologías indicadas por el usuario, Argentina/CABA/GBA y hasta dos años. Los requisitos ambiguos no se descartan; los puestos claramente senior reciben menor prioridad. Ubicaciones como Worldwide/Americas son pistas para revisar, no confirmación de que aceptan candidatos de Argentina.

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

Operativos: ofertas manuales y reales, tres proveedores públicos configurables, normalización, deduplicación, historial de sincronización, filtros, preferencias editables, perfil y scores persistentes, dashboard con paginación, pausa por fuente y worker independiente. Las métricas del dashboard corresponden a la página actual.

Sin autenticación, edición/borrado manual de ofertas, CV, historial de versiones de score, LLMs, agentes ni postulaciones automáticas. Las APIs cubren únicamente las empresas configuradas. El remoto no valida permisos laborales o restricciones de país; la lectura comprobada de Ashby no mostró ubicaciones explícitas de Argentina. Uso local; no está preparado para exposición pública o multiusuario. Las URLs se abren solo por decisión del usuario.

Próxima fase propuesta: mejorar cobertura de tableros y revisar la precisión de requisitos y ubicaciones, según [ROADMAP.md](docs/ROADMAP.md). No se implementó el Sprint 3. La validación de cierre y el muestreo real están en [SPRINT_2_RELEASE_VALIDATION.md](docs/SPRINT_2_RELEASE_VALIDATION.md); la revisión visual no pudo aprobarse por limitaciones de acceso al navegador.
