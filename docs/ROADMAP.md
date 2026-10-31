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

## Sprint 3A — Argentina First y perfil profesional (implementado)

- Ocho tableros verificados de Greenhouse, Lever y Ashby; cinco incorporados, sin APIs supuestas ni scraping.
- Geografía argentina, CABA/GBA, remoto restringido, seniority, experiencia e idioma con evidencia confirmada/inferida/desconocida.
- Clasificación Prioritaria Argentina / Alternativa internacional / Revisión necesaria / Despriorizada; razones visibles y matching determinista 70/20/10 reutilizado.
- Perfil editable con competencias y contexto, estudios, trabajos, proyectos, idiomas y objetivos. Datos iniciales declarados únicamente en archivo privado/base local, pendientes de confirmación; sin CV ni datos personales en Git.
- Dashboard existente extendido con filtros y orden recomendado; cooldown persistente y backoff por tablero.
- Migración aditiva y pruebas de preservación de Sprints 1 y 2, sincronización repetida, deduplicación, reglas, matching y persistencia.
- Medición real de 935 publicaciones: 116 Argentina explícita, 100 junior explícitas, 9 con ambos criterios (incluye roles no IT). Cierre: nueve ofertas verificadas y un falso positivo de prioridad corregido; 0 prioritarias y 82 para revisión. Ver `SPRINT_3A_RELEASE_VALIDATION.md`; el informe inicial conserva métricas previas a la corrección.

## Sprint 3B — Precisión y seguimiento (pendiente; no iniciado)

- Evaluar manualmente falsos positivos/negativos de geografía, experiencia, idioma y requisitos excluyentes con una muestra etiquetada.
- Continuar buscando fuentes junior de Argentina; evaluar el contrato de la API pública de Get on Board y condiciones antes de integrarla.
- Refinar roles, alias tecnológicos y restricciones solo con evidencia y tests. Evitar considerar una señal junior como elegibilidad suficiente.
- Evaluar edición/archivo y seguimiento personal de candidaturas, sin envíos.
- Completar revisión visual; mantener exclusión de scraping prohibido, elusión de restricciones y automatización de portales.

## Fase 4 — Asistencia de candidatura

- Importación voluntaria y privada del CV, retención y borrado.
- Importar un CV maestro local sobre el esquema profesional versionado, preservando procedencia y confirmaciones; comparar contra declaraciones existentes antes de aceptar cambios.
- Matching mejorado; LLMs optativos con evaluación y revisión de privacidad.
- Preparación de borradores de CV/carta con revisión humana.

## Fase 5 — Postulación por canales autorizados

- Conectores expresamente habilitados por usuario y proveedor.
- Vista previa y confirmación de cada envío, auditoría e idempotencia.
- Objetivo final: preparar candidaturas personalizadas desde el perfil/CV maestro, gestionar aprobaciones del usuario, enviar únicamente por canales autorizados y registrar envíos, respuestas y estado de cada proceso.
- Ningún envío real, generación de CV ni navegación automática de portales pertenece al Sprint 3A.

## Fase 6 — Orquestación multiagente, si se justifica

- Separar descubrimiento, análisis y preparación detrás de contratos existentes.
- Agentes con herramientas acotadas, permisos, presupuestos y evaluación.
- Colas/workers solo ante trabajos largos o concurrencia que lo requieran.
- Autenticación, autorización y aislamiento antes de un despliegue multiusuario.

Las fases futuras requieren revisión de alcance; no implican capacidades ya implementadas.
