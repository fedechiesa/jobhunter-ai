# Sprint 2 — Validación de Job Discovery Engine

Este informe conserva la validación inicial y sus snapshots. La validación final, las correcciones encontradas al auditar 14 registros y el estado actualizado están en [SPRINT_2_RELEASE_VALIDATION.md](SPRINT_2_RELEASE_VALIDATION.md). Las referencias a cambios locales/sin publicar describen la entrega inicial, anterior al cierre solicitado por el usuario.

Fecha: **29 de octubre de 2026**, zona del usuario America/Argentina/Buenos_Aires. Entorno: Windows, Python 3.12.10, Node 24.22.2 y PostgreSQL 17 en Docker Desktop. El Sprint 3 no se implementó.

## Cierre y publicación del Sprint 1

Se revisaron rama, remoto, archivos versionables y exclusiones de secretos/artefactos. `HEAD` y `origin/main` coincidían antes del push. Se volvieron a aprobar 40 tests backend, 14 frontend, Ruff, formato, typecheck y build.

Commit publicado: [`9a92362 — feat: establish JobHunter AI foundation`](https://github.com/fedechiesa/jobhunter-ai/commit/9a92362a70fb0774776922d7bdeca1ff51cf4392). [GitHub Actions: success](https://github.com/fedechiesa/jobhunter-ai/actions/runs/40949892356). Sin force push ni sobrescritura de cambios remotos. **Todos los cambios del Sprint 2 quedan locales, sin commit ni push**, por lo que la CI remota citada valida solamente Sprint 1.

## Fuentes y selección de tableros

Se consultó documentación oficial vigente antes de implementar. Todas las llamadas de proveedores son GET, sin credenciales y sin endpoints de envío:

| Proveedor | Documentación y endpoint de lectura | Tablero configurado / selección |
| --- | --- | --- |
| Greenhouse | [Job Board API](https://docs.greenhouse.io/job-board), `GET https://boards-api.greenhouse.io/v1/boards/{token}/jobs?content=true` | `canonical`, empresa Canonical, a partir de [su tablero público](https://job-boards.greenhouse.io/canonical). Se eligió para comprobar roles técnicos y ubicaciones distribuidas. |
| Lever | [Postings API oficial](https://github.com/lever/postings-api), `GET https://api.lever.co/v0/postings/{site}?mode=json&skip=0&limit=100` | `dlocal`, empresa dLocal, de [su tablero público](https://jobs.lever.co/dlocal). Permite comprobar publicaciones con ubicaciones de Argentina/Buenos Aires. |
| Ashby | [Job Postings API](https://developers.ashbyhq.com/docs/public-job-posting-api), `GET https://api.ashbyhq.com/posting-api/job-board/{name}` | `Ashby`, empresa Ashby, de [su tablero público](https://jobs.ashbyhq.com/Ashby), también referenciado por la documentación oficial. Se eligió para validar el proveedor; no garantiza cobertura argentina. |

No se intentó búsqueda global. El identificador proviene del tablero de cada organización. Cambiar/agregar empresas requiere configurar `config/sources.json`; no se deducen tableros ni se crean cuentas.

## Lectura real y persistencia

Primero se hicieron tres lecturas controladas de las APIs para inspeccionar el contrato. Después se ejecutó el worker `--once` contra PostgreSQL de desarrollo, conservando los registros previos. Finalmente se ejecutó `POST /sync` mediante HTTP real para comprobar repetición.

| Fuente | Elementos de la lectura inicial | Ofertas válidas persistidas, run 1 | Nuevas en run 2 | Sin cambios en run 2 |
| --- | ---: | ---: | ---: | ---: |
| Canonical / Greenhouse | 314 | 313 | 0 | 313 |
| dLocal / Lever | 21 | 21 | 0 | 21 |
| Ashby / Ashby | 71 | 71 | 0 | 71 |
| **Total** | **406** | **405** | **0** | **405** |

La diferencia de Greenhouse corresponde a una entrada de prospect/talent pool (`internal_job_id=null`), excluida por no representar una vacante concreta. Los dos runs finalizaron `success`; el segundo no detectó actualizaciones, ausencias ni alias entre las tres fuentes. La ausencia de duplicados entre estas empresas no valida por sí sola la deduplicación cruzada: esa lógica se probó con fixtures sintéticas que comparten una URL.

El primer run se realizó aproximadamente de 17:43:08 a 17:43:19 y el segundo de 17:44:43 a 17:44:52, horario Buenos Aires. Son snapshots de ese momento; los tableros pueden cambiar. Los payloads de inspección se guardaron exclusivamente en `.local/`, ignorado por Git; no se versionan respuestas reales.

Se consultaron las filas persistidas mediante otra conexión. No había perfil de candidato declarado durante estas lecturas: **se guardaron 405 ofertas, con 0 matches automáticos**, conservando `match_score=null`. No se creó ni rellenó un perfil con las tecnologías de interés. Los flujos con perfil y score se verificaron con datos ficticios en la base aislada de testing.

## Cobertura Argentina y sus límites

La búsqueda textual sobre las ubicaciones persistidas encontró:

| Fuente | Menciones explícitas de Argentina o Buenos Aires | Menciones amplias de Worldwide/Americas/LATAM/Latin America |
| --- | ---: | ---: |
| Greenhouse / Canonical | 0 | 170 |
| Lever / dLocal | 8 | 0 |
| Ashby / Ashby | 0 | 0 |

No se afirma que las 8 ofertas sean junior, remotas o compatibles con el perfil, ni que las 170 menciones regionales permitan contratar desde Argentina. El filtro HTTP específico `provider=lever&location=Buenos` devolvió una oferta; las otras menciones pueden decir Argentina sin Buenos Aires. El tablero Ashby comprobado **no aporta cobertura argentina explícita**. Queda disponible como fuente verificable y puede pausarse; para ampliar cobertura hay que seleccionar otros tableros con evidencia.

## Funcionalidades verificadas

- Adaptadores de lectura, validación completa de snapshots, HTML a texto seguro, fechas opcionales y modalidades sin inventar información.
- URLs originales y de postulación, proveedor/empresa, referencias externas, primera y última observación, estado de disponibilidad e historial de runs.
- Idempotencia por fuente/referencia, actualización, reaparición y deduplicación conservadora con alias históricos.
- Errores temporales no marcan ofertas como cerradas ni potencialmente inactivas. Datos inválidos/paginación incompleta no se interpretan como un tablero vacío.
- Fuentes restringidas con 401/403 o región no soportada se pausan; otras fuentes siguen funcionando.
- Preferencias editables, prioridad junior/0–2 años, senior despriorizado y requisitos ambiguos conservados. Sin asignación implícita de experiencia profesional al candidato.
- Reutilización del matching determinista, guardado de scores e invalidación al editar perfil.
- Filtros combinados, paginación, fechas y orden; nuevas rutas y endpoints del Sprint 1 compatibles.
- Sincronización manual por HTTP y worker independiente. Lock PostgreSQL compartido; concurrencia devuelve 409. Ciclos periódicos y señales se prueban sin esperar tiempo real.
- Panel funcional de fuentes, pausa, preferencias, botón protegido, estado por fuente, filtros y metadatos en tarjetas. La UI consulta estado cada diez segundos y refresca al finalizar un run nuevo.

## Tests y calidad

| Comando | Resultado |
| --- | --- |
| `python -m pytest backend` | **73 passed**, sin warnings en la ejecución final. Incluye los tests anteriores. |
| `python -m ruff check backend scripts` | Correcto. |
| `python -m ruff format --check backend scripts` | Correcto. |
| `python -m alembic -c backend/alembic.ini upgrade head` | Migración aditiva aplicada. |
| `python -m alembic -c backend/alembic.ini check` | Sin diferencias de esquema. |
| `python -m pip check` | Sin incompatibilidades. |
| `npm test` | **22 passed**, 3 archivos. |
| `npm run lint` | TypeScript strict correcto. |
| `npm run format:check` | Correcto. |
| `npm run build` | Build de producción correcto. |
| `npm audit` | 0 vulnerabilidades reportadas al verificar. |
| HTTP real | Worker + sincronización manual, estado, fuentes y filtros correctos. |

Los tests normales no consultan APIs reales: usan MockTransport, fixtures ficticias y un JSON de configuración temporal. Integración usa `jobhunter_test` en otro contenedor/puerto y esquemas temporales. Se comprueba `upgrade → downgrade → upgrade → check` y un caso específico que migra ofertas/perfil de Sprint 1 conservando sus datos. No se ejecutó downgrade ni borrado sobre PostgreSQL de desarrollo.

La revisión visual en navegador real no se completó: las herramientas de Browser Use/desktop no estuvieron disponibles durante la validación previa. El frontend se verificó con jsdom, typecheck, build y contenido HTTP servido por Vite. No se presenta eso como un test visual extremo a extremo. La app queda disponible localmente para revisión del usuario.

## Límites de las APIs y decisiones

Greenhouse ofrece un tablero completo con contenido; Lever requiere paginación; Ashby publica un feed del tablero y puede omitir campos. No se presupone búsqueda global ni publicación de todas las ubicaciones, años o fechas. Cuando Lever no devuelve `createdAt`, `published_at` queda null; no se sustituye por la fecha de descubrimiento. Ashby puede omitir `id`: se usa como referencia estable el último segmento de su URL de oferta.

No se encontró una cuota numérica pública común para estas lecturas. Se usa pausa mínima, un solo ciclo concurrente, timeout por fase e intentos limitados. Se respeta Retry-After corto; esperas largas o de fecha se difieren en lugar de ignorarse. Lever tiene un tope local de 20 páginas; alcanzar el tope falla la fuente sin aplicar ausencias. Se pueden ajustar timeout/intentos/pausa dentro de límites definidos, sin evadir controles.

Las tecnologías detectadas pueden ser menciones opcionales o descriptivas. La extracción de años reconoce patrones sencillos; el resto queda desconocido. Las modalidades se toman del campo publicado o de pistas explícitas de ubicación, sin afirmar remoto cuando no se sabe. El score heredado no es una probabilidad de contratación ni una verificación de elegibilidad.

La sincronización manual es síncrona; el navegador espera hasta tres minutos. Un timeout del navegador no cancela necesariamente el trabajo en el servidor: consultar `/sync/status` antes de reintentar. Un cierre de proceso libera el advisory lock; el siguiente ciclo identifica el run interrumpido. No hay cola, scraping, autenticación, envío de CV, postulación automática ni despliegue público.

## Uso

Desde la raíz, con `.env` local existente:

```powershell
docker compose up -d --wait db
.\.venv\Scripts\python.exe -m pip install -c backend/constraints.txt -e "./backend[dev]"
.\.venv\Scripts\python.exe -m alembic -c backend/alembic.ini upgrade head
.\.venv\Scripts\python.exe -m uvicorn app.main:app --app-dir backend --host 127.0.0.1 --port 8000
```

En otra terminal, con Node 24:

```powershell
cd frontend
npm.cmd ci
npm.cmd run dev
```

Abrir <http://127.0.0.1:5173>, revisar **Preferencias de búsqueda**, guardar **Mi perfil** solo con habilidades/experiencia declaradas y usar **Sincronizar ahora**. Aplicar filtros; para calcular scores de ofertas ya descubiertas después de crear el perfil, volver a sincronizar o usar el botón de la tarjeta. Las postulaciones se abren en el sitio original y las realiza el usuario.

Para periodicidad, en una terminal independiente: `.\.venv\Scripts\python.exe -m app.worker`. Default 3600 segundos; `--interval-seconds 3600` lo explicita, `--once` permite Programador de tareas. Instrucciones Windows, configuración, pausa por fuente y despliegue posterior en el README. No se instaló una tarea ni un servicio del sistema automáticamente.

## Próximos pasos propuestos

Revisar manualmente precisión del ranking, requisitos detectados y geografía. Ampliar tableros solo después de comprobar cobertura de Argentina/junior. Evaluar mejor evidencia para restricciones remotas y estados de seguimiento personal. No se implementó ninguna fase posterior ni se publicaron los cambios del Sprint 2.
