# Validación del Sprint 1

Validación inicial ejecutada el **29 de octubre de 2026** en Windows, Python 3.12.10, Node 24.22.2 portable y Docker Desktop con motor Linux. Este documento conserva la evidencia del Sprint 1; las validaciones nuevas están en `SPRINT_2_VALIDATION.md`.

| Control | Resultado |
| --- | --- |
| `docker compose --profile test up -d --wait` | Desarrollo y testing saludables. PostgreSQL 17, puertos 5432 y 5433 limitados a `127.0.0.1`. |
| `python -m alembic -c backend/alembic.ini upgrade head` | Migración de desarrollo aplicada. |
| `python -m alembic -c backend/alembic.ini check` | Sin diferencias entre modelos y migraciones. |
| `python -m pytest backend` | **40 passed**, sin advertencias en la ejecución final. |
| `python -m pytest backend -m "not integration"` | **32 passed**, 8 de integración deseleccionados. |
| `python -m ruff check backend scripts` | Sin errores. |
| `python -m ruff format --check backend scripts` | Formato correcto. |
| `python -m pip check` | Sin incompatibilidades. |
| `npm test` | **14 passed**, 2 archivos. |
| `npm run lint` | TypeScript strict correcto en app, tests y configuración. |
| `npm run format:check` | Prettier correcto. |
| `npm run build` | Build de producción Vite correcto. |
| `npm audit` | **0 vulnerabilidades reportadas** al momento de la verificación. |
| `git diff --check` | Sin errores de whitespace. |
| Exclusión de secretos/artefactos | `.env`, `.local`, `.venv`, node_modules, dist y cachés ignorados. Las credenciales generadas no aparecen en archivos versionables ni en el bundle. |

## Cobertura funcional

Backend: health sin DB, DB saludable/no disponible, CORS local, validación Pydantic, creación/listado/detalle/paginación de ofertas, fuente inválida, 404, perfil faltante, persistencia desde otra conexión, matching parcial/completo/cero, normalización, determinismo, actualización del score sin duplicados e invalidación al cambiar el perfil. El guard de testing rechaza URLs sin DB `_test` y el mismo destino que desarrollo.

Los tests de integración ejecutan migraciones `upgrade → downgrade → upgrade → check` en un esquema temporal de la base de testing. Usan datos ficticios y limpian el esquema.

Frontend: carga, estado vacío, errores y reintento, alta de oferta, guardado de perfil, invalidación visual de scores, matching pendiente/exitoso/fallido, paginación, manejo de perfil 404, métodos/payloads HTTP y mensajes ante fallas de red/validación/DB.

## Verificación HTTP real

Además de pytest, se inició una instancia temporal de Uvicorn en `127.0.0.1:8001` apuntada a un esquema exclusivo dentro de `jobhunter_test`. Se verificaron por HTTP los ocho endpoints, creación, consultas, persistencia de score **55**, repetición idéntica, actualización de perfil, invalidación y nuevo score **100**. La instancia y su esquema se eliminaron al terminar. No se insertaron datos de prueba en desarrollo.

Vite respondió HTTP 200 para el HTML y el módulo cliente de API. Se verificó que no incluyeran las credenciales de PostgreSQL. La API de desarrollo se inició y respondió en `127.0.0.1:8000`.

## Límites de la verificación

No se completó la inspección visual ni un flujo extremo a extremo en navegador real: el host de Browser Use no estaba disponible y el acceso alternativo a Chrome mediante computer-use agotó la espera de autorización. Los tests de interfaz se ejecutaron en jsdom; no sustituyen una revisión visual de escritorio/móvil.

En el cierre posterior solicitado por el usuario se volvieron a ejecutar los 40 tests backend y 14 frontend, lint, typecheck y build. Se publicó el commit [`9a92362`](https://github.com/fedechiesa/jobhunter-ai/commit/9a92362a70fb0774776922d7bdeca1ff51cf4392) en `origin/main`, después de comprobar que coincidía con la rama remota y revisar secretos. [GitHub Actions completó correctamente](https://github.com/fedechiesa/jobhunter-ai/actions/runs/40949892356). No se validó un despliegue público: está fuera del alcance y la aplicación carece de autenticación.

Se corrigieron las vulnerabilidades inicialmente reportadas por npm actualizando Vite/Vitest y usando Node 24 LTS, sin modificar el Node global instalado. Los comandos reproducibles y los requisitos están en el README.
