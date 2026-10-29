# Roadmap

## Sprint 1 — Foundation (implementado)

- PostgreSQL local con base de pruebas separada y healthchecks.
- FastAPI, SQLAlchemy, Alembic y contratos Pydantic.
- Ofertas manuales, perfil único y matching determinista persistente.
- Dashboard React con formularios, paginación, scores, carga, vacío y error.
- Tests backend/frontend, Ruff, TypeScript strict y build.

## Sprint 2 — Organización y calidad de datos (propuesto; sin implementar)

- Editar/archivar ofertas, filtrar y buscar.
- Estados de seguimiento personal, sin envío de postulaciones.
- Deduplicación e importación de archivos aportados por el usuario.
- Metadatos de autorización y procedencia antes de integrar fuentes externas.
- Evaluar el matching con ejemplos sintéticos y feedback explícito.

## Fase 3 — Fuentes autorizadas

- APIs oficiales, feeds o integraciones permitidas, respetando términos y cuotas.
- Adaptadores por fuente, trazabilidad, reintentos y observabilidad.
- Sin automatización de LinkedIn/Indeed ni elusión de CAPTCHA o acceso.

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
