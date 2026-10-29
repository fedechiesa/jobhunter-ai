# Sprint 2 — Validación final para publicación

Fecha: **29 de octubre de 2026**, horario Buenos Aires. Alcance: cierre del Sprint 2; sin desarrollo del Sprint 3.

## Git y calidad

La rama de trabajo es `main`, remoto `https://github.com/fedechiesa/jobhunter-ai.git`. Antes de preparar el commit se verificó `HEAD...origin/main = 0/0` mediante fetch, sin sobrescrituras ni force push. Se revisaron archivos modificados y nuevos. La configuración local de VS Code se conserva y se excluye de Git.

Validación local final: **85 tests backend y 22 frontend**, Ruff, formato Python/Prettier, TypeScript strict, build de producción, `pip check` y `npm audit` sin vulnerabilidades reportadas. La migración aplicada es `2e57c63bd9b7` (head), sin diferencias detectadas por `alembic check`. La suite verifica el ciclo completo de migraciones y preservación de datos del Sprint 1 en PostgreSQL aislado.

La validación de GitHub Actions corresponde al commit que se publique; su resultado y enlace se informan después del push. Los checks locales no se presentan como aprobación remota anticipada.

## Método de muestreo

Se seleccionaron **14 registros**: los 8 de dLocal que mencionaban Argentina/Buenos Aires, 3 de Canonical con mayor prioridad y 3 de Ashby con mayor prioridad. Se compararon título, ubicación, modalidad, referencias y enlaces con una lectura nueva de las APIs oficiales configuradas. Los 14 estaban presentes en el feed antes de aplicar los filtros corregidos.

Se consultaron por GET **25 URLs distintas**, originales y de postulación, sin completar ni enviar formularios. Todas respondieron HTTP 200 y se comprobó el título tras decodificar HTML. Un enlace de Legal Talent Pool agotó inicialmente el timeout; el único reintento respondió 200. Esto valida lectura y correspondencia, no envío de postulaciones ni disponibilidad futura.

No había perfil de candidato en la base. Los scores reales permanecieron null. Para auditar la aritmética se usó únicamente en memoria un perfil ficticio: skills Python/SQL, cero años, ubicación preferida Buenos Aires y aceptación de remoto en cualquier ubicación. Los scores de la tabla son **sintéticos**, no representan al usuario. Se comprobó determinismo y se recalculó la fórmula de forma independiente para las 13 vacantes; no se atribuyó ni persistió experiencia profesional al candidato.

## Hallazgos y correcciones dentro del Sprint 2

1. **Bolsas de talento:** Legal Talent Pool era una convocatoria de interés futuro, no una vacante concreta. Se excluyen títulos explícitos de Talent Pool/bolsa de talento en los tres proveedores, conservando el filtro de prospect posts de Greenhouse. La sincronización retiró dos bolsas de dLocal del conjunto activo sin borrar históricos. Su estado histórico potentially_inactive no significa que la convocatoria externa haya cerrado.
2. **Experiencia explícita:** frases como `3+ years in fraud prevention` y experiencia de ingeniería/software quedaban desconocidas. Se agregaron patrones acotados y pruebas contra menciones incidentales, sin inferir años del candidato. En la muestra quedaron detectados 3 años para Fraud Prevention Analyst II y 8 para los roles Staff AI.
3. **Ubicaciones alternativas:** Buenos Aires no coincidía con una lista explícita de varias ciudades. `deterministic-v1.1` conserva pesos 70/20/10 y normaliza alternativas y etiquetas de modalidad. No inventa país, sinónimos ni permiso para trabajar desde Argentina. Los resultados anteriores conservan su versión hasta ser recalculados.

## Resultado de los 14 registros

Todas las URLs de la tabla fueron verificadas por GET. Para cada vacante activa, las ciudades y modalidad coinciden con la API; en Ashby la ubicación agrega las alternativas publicadas. `unknown` significa que la etiqueta basada en título no determina el nivel: **no significa junior**. Los años proceden de reglas sobre texto y pueden requerir revisión semántica.

| Fuente / registro | Ubicación y modalidad comprobadas | Seniority de la app / evidencia | Estado final | Score ficticio v1.1 |
| --- | --- | --- | --- | ---: |
| lever · [Data-AI Architect](https://jobs.lever.co/dlocal/9152099e-3a47-48f0-8ab2-c68728012a79) | Montevideo / Buenos Aires / Sao Paulo / Barcelona / Madrid · hybrid | unknown · 8 años detectados | Activa: observada en API | 56.67 |
| lever · [Fraud Prevention Analyst II](https://jobs.lever.co/dlocal/2b55b780-a206-44df-9196-6b63dbbcf3c0) | Montevideo (Hybrid) / Buenos Aires / Sao Paulo (Hybrid) · hybrid | unknown · 3 años detectados | Activa: observada en API | 80.00 |
| lever · [Legal Talent Pool](https://jobs.lever.co/dlocal/b3312823-073a-40f0-8ffd-ea0b4e360333) | Montevideo (Hybrid) / Buenos Aires / Shanghai / London / Sao Paulo (Hybrid) / Madrid / Shenzhen · hybrid | unknown · años no determinados | Excluida: bolsa de talento; histórico preservado | No aplica |
| lever · [Platform Architect](https://jobs.lever.co/dlocal/69656039-9233-4406-94de-1dd729eaf8cc) | Madrid / Barcelona / Montevideo / Buenos Aires / Sao Paulo · hybrid | unknown · 5 años detectados | Activa: observada en API | 45.00 |
| lever · [Staff AI Engineer - AI Labs](https://jobs.lever.co/dlocal/e6c41d1a-c41b-4845-a40f-c75340874372) | Madrid / Barcelona / Bucharest / Montevideo / Sao Paulo / Buenos Aires · hybrid | senior · 8 años detectados | Activa: observada en API | 10.00 |
| lever · [Staff Engineer - Java](https://jobs.lever.co/dlocal/f3e9b742-9530-4f0c-b70c-83bf24cc602a) | Barcelona / Madrid / Buenos Aires / Sao Paulo (Hybrid) / Montevideo (Hybrid) · hybrid | senior · 7 años detectados | Activa: observada en API | 10.00 |
| lever · [Staff Engineer, AI R&D](https://jobs.lever.co/dlocal/9c8589af-057d-49e4-a542-b63ed92a972b) | Madrid / Barcelona / Buenos Aires / Montevideo / Sao Paulo / Bucharest · hybrid | senior · 8 años detectados | Activa: observada en API | 10.00 |
| lever · [Technical Account Manager](https://jobs.lever.co/dlocal/f0c3faec-8aff-4a66-bfd8-5d96137e390c) | Buenos Aires / Montevideo / Sao Paulo (Hybrid) · hybrid | senior · 4 años detectados | Activa: observada en API | 80.00 |
| greenhouse · [Python and Kubernetes Software Engineer - Data, Workflows, AI/ML & Analytics](https://job-boards.greenhouse.io/canonical/jobs/5703396) | Home based - Worldwide · remote | unknown · años no determinados | Activa: observada en API | 53.33 |
| greenhouse · [Python Engineer](https://job-boards.greenhouse.io/canonical/jobs/5143074) | Home based - Worldwide · remote | unknown · años no determinados | Activa: observada en API | 76.67 |
| greenhouse · [Software Engineer - Python and K8s](https://job-boards.greenhouse.io/canonical/jobs/3752633) | Home based - Worldwide · remote | unknown · años no determinados | Activa: observada en API | 65.00 |
| ashby · [Design Engineer - EU](https://jobs.ashbyhq.com/Ashby/188cc71b-a625-4022-94dc-7c43fa1a8b06) | Portugal / Spain / Italy / Switzerland / Croatia / Ireland / Stockholm / Romania / Barcelona / Berlin / Sweden / Estonia · remote | unknown · 2 años detectados | Activa: observada en API | 10.00 |
| ashby · [Design Engineer - UK](https://jobs.ashbyhq.com/Ashby/cb45928e-c7c7-4163-84d0-a962755a3593) | United Kingdom / Manchester / Oxford / London / Cambridge · remote | unknown · 2 años detectados | Activa: observada en API | 10.00 |
| ashby · [Design Engineer - Americas](https://jobs.ashbyhq.com/Ashby/fd86edd7-3af0-4977-a61a-215212c296fa) | Remote - US / Austin / Los Angeles / Portland / Boston / Seattle / New York / San Francisco / Denver / Chicago · remote | unknown · 2 años detectados | Activa: observada en API | 10.00 |

Los dos Architect de dLocal exigen 5–8 años aunque su título quede clasificado unknown. Los roles Staff están clasificados senior; Technical Account Manager también cae en la heurística de títulos, que puede confundir jerarquía con nombre de función. Fraud Prevention Analyst II exige 3 años: no se considera una vacante junior confirmada. Las páginas Design Engineer de Ashby incluyen varios niveles en su descripción; los registros auditados corresponden a Mid/Senior, y las reglas no resuelven toda esa semántica.

Las tres ofertas Ashby son remotas con ubicaciones EU/UK/US: **no se aprobó elegibilidad para Argentina**. El componente remoto del score ficticio refleja que ese perfil aceptaba remoto en cualquier ubicación, no una verificación legal/geográfica. Un score alto tampoco elimina requisitos de experiencia incumplidos; estos tienen un peso del 20%. Es una limitación explícita del matching determinista, no una probabilidad de contratación.

## Repetición segura y estado de los datos

Runs reales 3 y 4 consecutivos, antes de las correcciones: success, 405 sin cambios, cero nuevas/actualizadas/duplicados. Run 5 con correcciones: 313 Greenhouse + 19 Lever + 71 Ashby; dos bolsas de dLocal pasaron al histórico fuera del conjunto activo, sin borrados. Run 6 consecutivo posterior: **success, 403 sin cambios, cero nuevas, actualizadas, duplicados o nuevas ausencias**.

Estado final comprobado: **405 registros históricos, 403 vacantes activas**, incluyendo 19 activas de dLocal; 7 de estas mencionan Argentina/Buenos Aires. No se afirma que sean junior ni que todas permitan postular desde Argentina. PostgreSQL conserva los perfiles/ofertas previos. No se ejecutaron downgrades ni borrados sobre desarrollo.

## Seguridad y configuración

Desarrollo y testing están saludables y enlazados únicamente a `127.0.0.1:5432` y `127.0.0.1:5433`. API y Vite siguen en loopback. Se revisó Compose sin imprimir sus passwords. Las credenciales aleatorias no aparecen en archivos versionables ni en el bundle. `.env`, `.local`, VS Code, virtualenv, node_modules y dist están ignorados. No se versionaron payloads reales, datos del candidato, dumps o artefactos del muestreo. Tests y fixtures persistentes usan ejemplos ficticios.

Los proveedores usan solo APIs GET oficiales, sin credenciales, scraping ni creación de cuentas. No se hicieron envíos ni postulaciones. El servicio sigue careciendo de autenticación: no se aprueba exposición pública.

## Revisión visual pendiente

La revisión visual **no está aprobada**. Browser Use no expuso navegadores y reportó que su host no estaba disponible. El intento alternativo de seleccionar Chrome mediante computer-use fue detenido por la herramienta porque no pudo determinar la URL actual con confianza suficiente para aplicar su política. Se respetó ese bloqueo y no se intentó evadirlo.

Se aprobaron tests de UI en jsdom, typecheck, build y comprobaciones HTTP; no sustituyen una inspección visual real de escritorio/móvil. La limitación de acceso visual queda documentada para el usuario y no se presenta como test extremo a extremo aprobado. La aplicación queda localmente disponible para revisión manual.

## Uso y publicación

Instrucciones de ejecución, testing, migraciones y worker en el README. El usuario autorizó el commit `feat: add real job discovery and synchronization` y push normal a `origin/main` si no había bloqueos importantes. Los problemas puntuales encontrados en este muestreo se corrigieron y tienen regresiones; las limitaciones semánticas, de cobertura y visuales quedan explícitas. No se desarrolló el Sprint 3.
