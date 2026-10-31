# Sprint 3A — Argentina First y perfil profesional

Validación inicial local del **31 de octubre de 2026**, zona America/Buenos_Aires, antes de commit/push. Sprint 3B no iniciado. **Informe histórico de implementación:** las cifras y categorías siguientes corresponden a `argentina-v1`, antes de revisar la muestra de cierre. El resultado corregido (`argentina-v1.1`: 0 prioritarias, 82 para revisión, 144 tests backend y 26 frontend) está en [SPRINT_3A_RELEASE_VALIDATION.md](SPRINT_3A_RELEASE_VALIDATION.md).

## Inspección inicial

Se inspeccionaron estado Git (limpio), README, ARCHITECTURE, ROADMAP, modelos, contratos, matching, proveedores, normalización, sincronización, migraciones, worker, dashboard y tests antes de editar. La base inicial tenía 85 tests backend: 68 unitarios aprobados y 17 integraciones inicialmente bloqueadas por PostgreSQL/Docker apagado. Se inició Docker y la base de pruebas aislada; los 85 tests originales aprobaron antes de ampliar la suite.

Se conservan Greenhouse, Lever y Ashby, normalización, referencias externas, deduplicación por URL/empresa/título, disponibilidad e historial. No se agregó un proveedor de scraping ni se asumió una API por tener página de empleos.

## Fuentes investigadas y decisiones

Acceso: únicamente GET de APIs públicas documentadas, sin credenciales, formularios, endpoints de aplicación ni navegación de postulaciones. Referencias primarias: [Greenhouse Job Board API](https://docs.greenhouse.io/job-board.html), [Lever Postings API](https://github.com/lever/postings-api) y [Ashby Job Postings API](https://developers.ashbyhq.com/docs/public-job-posting-api). Las tres documentan lectura de publicaciones por tablero; no son buscadores globales. Las APIs privadas de recruiting/Harvest no se usaron.

| Empresa / tablero público | Resultado de verificación | Calidad / cobertura observada | Decisión |
| --- | --- | --- | --- |
| [Canonical](https://job-boards.greenhouse.io/canonical) / `canonical` | Greenhouse, feed completo válido, 313 publicaciones | Cobertura global/Americas, sin Argentina explícita; 13 títulos junior | Conservar integración existente; pistas regionales requieren revisión |
| [dLocal](https://jobs.lever.co/dlocal) / `dlocal` | Lever, 26 vacantes tras excluir Talent Pools | 7 ubicaciones argentinas inferidas, ningún título junior; modalidad estructurada | Conservar; primer muestreo tuvo timeout, auditoría final y sync correctos |
| [Ashby](https://jobs.ashbyhq.com/Ashby) / `Ashby` | Ashby, 74 publicaciones | Sin Argentina explícita ni junior explícito; modalidad y países estructurados disponibles | Conservar proveedor/tablero e históricos |
| [Sezzle](https://job-boards.greenhouse.io/sezzle) / `sezzle` | Greenhouse, 273 publicaciones | 33 Argentina explícita, 9 Argentina + junior; muchos roles de operaciones/marketing | Integrar; no confundir junior con IT o compatibilidad completa |
| [Despegar](https://jobs.lever.co/despegar) / `despegar` | Lever, paginación verificada: 125 publicaciones | 1 Argentina explícita y 37 inferidas; 2 junior en otros países; fuerte presencia comercial y senior | Integrar cobertura regional, conservar sin inflar relevancia |
| [Silver.dev](https://jobs.ashbyhq.com/silver) / `silver` | Ashby, 39 publicaciones | 35 Argentina explícita, modalidad/country estructurados; ningún junior explícito | Integrar como fuente técnica local; requisitos ambiguos requieren revisión |
| [RYZ Labs](https://jobs.lever.co/RyzLabs) / `RyzLabs` | Lever, 49 publicaciones | 31 Argentina explícita y 8 inferidas; un rol técnico con mínimo de 2 años | Integrar; no etiquetar ese rol como junior explícito |
| [Mutt Data](https://jobs.lever.co/muttdata) / `muttdata` | Lever, 36 publicaciones | 16 Argentina explícita y 6 inferidas; datos/ML/Python, predominio senior | Integrar; Data Developer/ML con nivel desconocido quedan para revisión |
| [Power Digital](https://job-boards.greenhouse.io/powerdigitalmarketing) / `powerdigitalmarketing` | Lectura Greenhouse válida: 265 publicaciones en muestreo exploratorio | Abundante marketing; la vacante Junior Software Engineer encontrada en el índice web no apareció como tal en la respuesta medida | No agregar al conjunto configurado; el índice web no demuestra vacante vigente |
| [Get on Board](https://www.getonbrd.com/user-manual/get-on-board-s-api) | El proveedor documenta API pública y privada; [referencia técnica](https://www.getonbrd.com/api-doc.html) consultada | Potencial regional; no se validaron contrato, paginación ni cobertura real mediante un adaptador | Evaluado, sin integración; no asumir contrato ni inventar métricas |
| [Ualá](https://www.uala.com.ar/trabajar-en-uala), [Pomelo fintech](https://pomelo.la/empresa/trabaja-con-nosotros) | Páginas oficiales consultadas | No se verificó un tablero/API laboral compatible con el pipeline en esta investigación | Sin integración ni crawling; una página de carreras o un parámetro `gh_jid` no basta |
| LinkedIn / Indeed y otros portales generales | Fuera de las fuentes de lectura autorizadas implementadas | No se usaron credenciales, scraping ni elusión | Sin integración |

La frecuencia real de actualización del empleador es **desconocida**: una lectura puntual no permite medirla y no se encontró un SLA aplicable. El worker local consulta por defecto cada hora. Lever y Ashby aportan modalidad estructurada cuando existe; Greenhouse en estos tableros suele requerir inferirla de la ubicación. Las fechas son las entregadas por cada proveedor; no se usan fechas de actualización como publicación inventada. Todos los registros de la auditoría final traían fecha, lo que no demuestra que sean recientes ni que el empleador siga aceptando candidaturas.

Se agregaron **cinco tableros**, manteniendo los tres anteriores: ocho en total y tres proveedores. Nuevas empresas argentinas/regionales verificadas por su presencia laboral local: Despegar, Silver.dev, RYZ Labs y Mutt Data. Sezzle aporta contratación internacional con ubicación Argentina explícita. La verificación acredita publicaciones y acceso técnico público, sin afirmar permisos de trabajo, aceptación final del candidato o nacionalidad societaria no investigada.

## Cobertura real medida

Auditoría final: **2026-10-31 14:38:44 -03:00** (17:38:44 UTC). Artefacto público agregado: [SPRINT_3A_METRICS.json](SPRINT_3A_METRICS.json). Snapshots normalizados de esa lectura: `.local/sprint3a-snapshots/`, ignorados por Git. El muestreo exploratorio de Power Digital no se suma a los ocho tableros configurados.

| Tablero | Obtenidas | Argentina explícita | Junior/trainee explícito | Ambos explícitos | Geografía desconocida | Seniority desconocido |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Canonical | 313 | 0 | 13 | 0 | 128 | 141 |
| dLocal | 26 | 0 | 0 | 0 | 14 | 12 |
| Ashby | 74 | 0 | 0 | 0 | 10 | 21 |
| Sezzle | 273 | 33 | 85 | 9 | 57 | 63 |
| Despegar | 125 | 1 | 2 | 0 | 57 | 77 |
| Silver.dev | 39 | 35 | 0 | 0 | 0 | 24 |
| RYZ Labs | 49 | 31 | 0 | 0 | 6 | 26 |
| Mutt Data | 36 | 16 | 0 | 0 | 4 | 6 |
| **Total** | **935** | **116** | **100** | **9** | **276** | **370** |

Definiciones: Argentina explícita requiere `geography.status=confirmed` y valor Argentina/remoto explícito desde Argentina. Junior explícito requiere señal literal junior/trainee/intern/pasante/graduate/entry level en título. Esas cifras incluyen todas las áreas laborales, no solo roles IT. No se cuentan países desconocidos, Worldwide, LATAM o ciudades inferidas como Argentina explícita.

Otros resultados:

- **58** ubicaciones argentinas inferidas, separadas de las 116 explícitas.
- **43** niveles junior inferidos por experiencia mínima, separados de los 100 explícitos.
- **525** registros con geografía o seniority desconocidos (unión, no suma de columnas).
- **635** registros con años requeridos desconocidos; no se interpretan como cero declarado.
- **0** fechas de publicación faltantes en esta lectura; el sistema y tests igualmente soportan fechas desconocidas.
- Clasificación de la lectura: **1 Prioritaria Argentina, 0 Alternativa internacional, 81 Revisión necesaria, 853 Despriorizadas**.

Se reprodujeron los resultados sin acceso a red mediante `audit_sources.py --snapshots`: coinciden exactamente todas las métricas por fuente, las categorías y los totales con la lectura real guardada.

Los conteos corresponden a publicaciones antes de deduplicación entre fuentes, no a vacantes únicas del mercado. La auditoría utiliza las reglas provisionales de Argentina, hasta dos años e inglés intermedio; no carga datos profesionales privados. Las nueve publicaciones Argentina + junior no son nueve oportunidades adecuadas para el candidato.

Ejemplos revisados:

- Sezzle, **Junior Software Engineer with Accounting Experience (Argentina)**, [publicación](https://job-boards.greenhouse.io/sezzle/jobs/6668066003): país y junior explícitos, pero solicita experiencia como contador/analista financiero. Queda **Revisión necesaria**, sin atribuir esa experiencia a partir de antecedentes administrativos/comerciales.
- RYZ Labs, **Software Engineer – Product Quality & Reliability**: inicialmente Prioritaria Argentina por tomar el mínimo de dos años; **falso positivo corregido durante el cierre**. El texto exige 2–4 años en aplicaciones de producción y comunicación sólida en inglés; ahora queda Revisión necesaria y seniority desconocido. El score técnico 80/100 no acredita adecuación para primera experiencia. Ver informe de cierre.
- Mutt Data, **Data Developer**: Argentina explícita, seniority desconocido; permanece para revisión. Las opciones de seniority de un formulario no se usan como prueba de que la vacante sea junior: no se consultan formularios para clasificar.

## Sincronización, persistencia y perfil local

Se aplicó `0003_argentina_first` y `alembic check` no encontró diferencias de esquema. La migración es aditiva: no borra ofertas, perfiles, fuentes ni scores históricos. La reclasificación explícita inicial alcanzó 406 ofertas existentes. Al guardar el perfil se invalidaron scores anteriores conforme al contrato ya existente; luego se calcularon nuevamente.

La sincronización real del worker (run 7, 14:44–14:45 -03:00) completó **8/8 fuentes**, leyó **935** publicaciones, creó **533**, actualizó **402**, encontró **0 aliases nuevos** y marcó **1 ausencia** como potencialmente inactiva. Hubo **935 scores calculados** con el perfil estructurado. Los hashes cambiaron en la primera lectura por la incorporación de evidencia completa, conservando referencias externas y primeras observaciones.

Conteo posterior en DB: **939 filas históricas**, **936 activas** (incluye una oferta manual previa) y **3 potencialmente inactivas**. Entre las activas: 1 prioritaria, 81 para revisión y 854 despriorizadas; la diferencia respecto de la auditoría de feeds es la oferta manual. No se borraron publicaciones históricas.

El perfil inicial usa exclusivamente declaraciones del usuario y reside en DB y `private/profile.json`, ambos fuera de Git. Se separaron estudios, trabajos no IT y proyectos; años IT remunerados iniciales: cero. Competencias y detalles se dejaron pendientes de confirmación, sin agregar fechas, empleadores, logros, niveles de dominio ni datos de contacto. La confirmación de usuario es distinta de una verificación externa. El idioma intermedio declarado no se eleva a avanzado.

El frontend permite editar y validar esas secciones sin PDF ni LinkedIn. `schema_version`/`origin` preparan procedencia para un CV maestro local futuro; no se implementó importación, generación ni almacenamiento de un CV.

## Validaciones

Comandos ejecutados desde la raíz con Python 3.12 y Node portable 24.22.2:

```powershell
docker compose --profile test up -d --wait db-test
.\.venv\Scripts\python.exe -m alembic -c backend/alembic.ini upgrade head
.\.venv\Scripts\python.exe -m alembic -c backend/alembic.ini check
.\.venv\Scripts\python.exe -m pytest backend --tb=short -p no:cacheprovider
.\.venv\Scripts\python.exe -m ruff check backend scripts
.\.venv\Scripts\python.exe -m ruff format --check backend scripts
.\.venv\Scripts\python.exe -m pip check
npm.cmd --prefix frontend test
npm.cmd --prefix frontend run lint
npm.cmd --prefix frontend run format:check
npm.cmd --prefix frontend run build
npm.cmd --prefix frontend audit
```

Resultados finales: **137 tests backend aprobados** (116 unitarios y 21 integraciones PostgreSQL), **26 tests frontend aprobados**, Ruff lint y formato aprobados, TypeScript y Prettier aprobados, build de producción aprobado, `pip check` sin dependencias rotas, `npm audit` con **0 vulnerabilidades**, `alembic check` sin diferencias y `git diff --check` correcto. Se verificó además que `private/profile.json` y los artefactos `.local/` están ignorados por Git.

La suite integra PostgreSQL real con esquema temporal, `upgrade → downgrade → upgrade → check`, pruebas de preservación de Sprints 1 y 2, commit/lectura desde otra conexión, sync repetido, aliases, ausencias y fallos. Se agregaron casos de país/modo, CABA/GBA, junior/senior, rangos/años escritos/opcionales, ambigüedad, inglés, roles técnicos cercanos y dominios específicos, perfil estructurado y borrador privado, filtros y cooldown persistente. Los tests usan exclusivamente datos ficticios y mocks de proveedores; las lecturas reales se midieron aparte.

El sandbox inicial bloqueó conexión a Docker, red y procesos auxiliares de Vite. Se ejecutaron los comandos necesarios con escalación autorizada, sin cambiar configuración de seguridad ni exponer servicios fuera de loopback. La cache pytest heredada no era escribible: se ejecutó con `-p no:cacheprovider`, sin alterar ni eliminar esa carpeta.

La verificación HTTP real aprobó `/health/db`, lectura del perfil estructurado y `/jobs?sort=recommended&availability=active`; el primer resultado fue la oportunidad prioritaria con score 80. El formulario se verificó mediante Testing Library, incluyendo edición de cada sección y validaciones de entradas vacías. **Revisión visual pendiente:** la herramienta de computer use devolvió `Computer Use app approval timed out`; no se afirma aprobación visual ni revisión en móvil.

## Límites y próximos pasos

- Las reglas no hacen interpretación semántica completa ni verifican autorizaciones laborales. Requisitos y negaciones no reconocidos pueden producir falsos positivos/negativos; revisar siempre la publicación original.
- Países agrupados en Argentina/otros/desconocido; ciudades y familias de roles usan vocabulario acotado. Múltiples ubicaciones y contradicciones conservan evidencia para revisión.
- Score técnico y clasificación son métricas distintas. Los años desconocidos conservan la convención numérica anterior de matching y quedan explícitos como desconocidos en evidencia/UI; no son experiencia cero confirmada.
- La evidencia de modalidad distingue campos estructurados de inferencia por ubicación; Greenhouse no siempre ofrece modalidad estructurada. La prosa en español se prefiere dentro de cada categoría sin descartar inglés intermedio.
- Los perfiles legados conservan matching v1.1 hasta extenderlos; el perfil inicial de esta sesión ya usa v1.2-ar. Los históricos sin reclasificar comienzan en revisión y no se promocionan automáticamente por migración.
- No hay medición de precisión/recall sobre una muestra humana etiquetada ni SLA de actualización. La baja cantidad de oportunidades prioritarias es un resultado real, no un fallo que se oculte agregando publicaciones.
- Recomendado para una fase posterior: revisar la oportunidad prioritaria y los roles de datos ambiguos, confirmar competencias/detalles desde el formulario, etiquetar una muestra y evaluar Get on Board con su contrato/condiciones antes de ampliar proveedores.
- Completar revisión visual cuando la herramienta tenga autorización disponible. Uso exclusivamente local; autenticación y multiusuario siguen fuera del alcance.
- No se implementaron CV, LLMs, generación de documentos, aplicaciones reales, navegación automática de portales ni envíos. El objetivo final de candidaturas personalizadas, aprobaciones, canales autorizados y registro de respuestas está documentado en ROADMAP; no se avanzó a Sprint 3B.
