# JobHunter AI

Plataforma personal para organizar ofertas y analizar su compatibilidad con un perfil técnico. **Sprint 1: carga manual y matching determinista**, local y de un solo usuario.

No realiza scraping, llamadas a LLM, envío de CV ni postulaciones. No automatiza LinkedIn o Indeed. Las futuras integraciones deberán usar canales autorizados.

## Stack real

- Python 3.12+, FastAPI, Pydantic 2, Pydantic Settings, SQLAlchemy 2 y Psycopg 3.
- PostgreSQL 17 en Docker Compose, migraciones Alembic.
- React 19, TypeScript strict y Vite 8.
- pytest, Vitest 5, Testing Library, Ruff y Prettier.

## Estructura

```text
backend/
  app/
    api/                 # health, ofertas y perfil
    core/                # configuración
    services/            # matching puro
    db.py                # engine y sesiones
    models.py            # cuatro entidades persistentes
    schemas.py           # contratos y validación
    factory.py           # construcción de la API
    main.py              # punto de entrada ASGI
  alembic/versions/       # migraciones versionadas
  tests/                 # unitarios e integración PostgreSQL
  constraints.txt        # versiones Python verificadas
frontend/
  src/components/        # formularios y oferta con score
  src/api.ts             # cliente HTTP
  src/App.tsx            # dashboard
docs/                    # arquitectura, roadmap y validación
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

   Abrí <http://127.0.0.1:5173>. Guardá **Mi perfil**, agregá una oferta y pulsá **Calcular match**. El resultado se guarda en PostgreSQL y aparece al recargar.

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

El matching pondera habilidades 70%, experiencia 20% y ubicación 10%, con total 0–100 y desglose. Skills por igualdad exacta normalizada; no se extraen de la descripción. Reglas y decisiones en [ARCHITECTURE.md](docs/ARCHITECTURE.md).

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

`lint` verifica TypeScript estricto en app, tests y configuración. `build` verifica tipos y genera `frontend/dist/`, ignorado. Vitest cubre carga, vacío, error/reintento, formularios, score, invalidación, paginación y cliente HTTP. [VALIDATION.md](docs/VALIDATION.md) registra los resultados. CI reproduce los controles en Linux con Python 3.12 y Node 24.

## Estado y límites

Operativos: crear/listar/consultar ofertas, perfil persistente, fuente manual, score persistido, dashboard adaptable a móvil y paginación. Las métricas corresponden a la página actual.

Sin autenticación, edición/borrado de ofertas, filtros, deduplicación, CV, fuentes externas, historial de scores, LLMs ni agentes. El remoto no valida permisos laborales o restricciones de país. Uso exclusivamente local: no está preparado para un despliegue público o multiusuario. Las URLs solo se abren por decisión del usuario.

Próxima fase recomendada: organización y calidad de datos (edición/archivo, búsqueda y deduplicación), según [ROADMAP.md](docs/ROADMAP.md). No se implementó el Sprint 2.
