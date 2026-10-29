# Roadmap

## Sprint 1 — Foundation (implementado)

- PostgreSQL local con base de pruebas separada y healthchecks.
- FastAPI, SQLAlchemy, Alembic y contratos Pydantic.
- Ofertas manuales, perfil único y matching determinista persistente.
- Dashboard React con formularios, paginación, scores, carga, vacío y error.
- Tests backend/frontend, Ruff, TypeScript strict y build.

## Sprint 2 — Job Discovery Engine (implementado)

- Lectura de Greenhouse Job Board API, Lever Postings API y Ashby Job Postings API por tablero configurado.
- Normalización, referencias externas únicas, detección conservadora de alias e historial de disponibilidad.
- Intereses de búsqueda editables separados del perfil y matching determinista reutilizado.
- Filtros, modalidades, enlaces originales, fechas y estado por fuente en el dashboard.
- Sincronización manual y worker periódico con lock PostgreSQL, logs JSON, timeouts y reintentos.
- Tests con respuestas simuladas, migración preservando Sprint 1 y lecturas reales controladas.
- Sprint 1 publicado en `9a92362`; CI remota aprobada. Cierre del Sprint 2 con muestreo de 14 registros y correcciones de Talent Pool, años explícitos y ubicaciones alternativas; ver `SPRINT_2_RELEASE_VALIDATION.md`.

## Sprint 3 — Cobertura y precisión (solo propuesto; sin implementar)

- Seleccionar más tableros autorizados con evidencia de cobertura Argentina/junior.
- Revisar precisión de extracción de requisitos y restricciones geográficas, conservando incertidumbre.
- Mejorar deduplicación solo con evidencia, evaluación y trazabilidad.
- Evaluar edición/archivo de ofertas y seguimiento personal de candidaturas, sin envío.
- Mantener exclusión de LinkedIn/Indeed, scraping y elusión de controles.

## Fase 4 — Asistencia de candidatura

- Importación voluntaria y privada del CV, retención y borrado.
- Matching mejorado; LLMs optativos con evaluación y revisión de privacidad.
- Preparación de borradores de CV/carta con revisión humana.

## Fase 5 — Postulación por canales autorizados

- Conectores expresamente habilitados por usuario y proveedor.
- Vista previa y confirmación de cada envío, auditoría e idempotencia.
- Ningún envío real de CV o postulación pertenece al Sprint 1.

## Fase 6 — Orquestación multiagente, si se justifica

- Separar descubrimiento, análisis y preparación detrás de contratos existentes.
- Agentes con herramientas acotadas, permisos, presupuestos y evaluación.
- Colas/workers solo ante trabajos largos o concurrencia que lo requieran.
- Autenticación, autorización y aislamiento antes de un despliegue multiusuario.

Las fases futuras requieren revisión de alcance; no implican capacidades ya implementadas.
