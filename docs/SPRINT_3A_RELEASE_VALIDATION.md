# Validación y cierre del Sprint 3A

31 de octubre de 2026, America/Buenos_Aires. Alcance: revisar la implementación local y una muestra real antes de publicar en main. Sin Sprint 3B, CV, LLMs ni postulaciones. Este informe acompaña el commit `feat: prioritize Argentina jobs and structured candidate profile`; el SHA, la verificación remota y el resultado de CI se informan al finalizar la publicación.

## Método y límites de revisión

Se seleccionaron **nueve ofertas**: la única prioritaria inicial, siete para revisión con ubicación argentina explícita/inferida y una graduate global como control. Se leyó el texto completo normalizado de las nueve y se contrastó con los feeds actuales de cinco tableros (Canonical, Sezzle, Silver.dev, RYZ Labs y Mutt Data). Las nueve continuaban listadas y sus descripciones no habían cambiado. No se extrapola esta revisión a las otras 926 publicaciones.

Verificación directa de enlaces terminada a las **15:26:56 -03:00**: **9/9 HTTP 200**, sin redirección a otra URL. También se abrieron las páginas públicas para comprobar el contenido cuando estaba disponible. Las dos páginas de Ashby devuelven una estructura que requiere JavaScript: se verificó enlace y presencia/texto en la API pública, **sin afirmar renderizado o revisión visual del portal**. No se completó, envió ni automatizó ningún formulario.

Los contenidos completos y respuestas de comprobación quedan únicamente en `.local/sprint3a-release-sample.json` y `.local/sprint3a-release-live.json`, ignorados por Git. Aquí se publican solo conclusiones, enlaces y requisitos laborales públicos resumidos.

## Muestra y utilidad real

| Oferta y enlace | Comprobación / contenido | Resultado de revisión |
| --- | --- | --- |
| [RYZ Labs — Software Engineer – Product Quality & Reliability](https://jobs.lever.co/RyzLabs/339d15f4-0877-4127-ac42-4593620998a9) | HTTP 200 + feed vigente; software/fullstack, remoto LATAM, Buenos Aires; experiencia de 2–4 años en aplicaciones de producción y comunicación sólida en inglés | **Falso positivo de prioridad.** El mínimo de dos años se interpretaba como junior sin considerar el extremo superior. Pasa a revisión; no se recomienda como primera experiencia sin aclaración del empleador |
| [Sezzle — Fraud Data Analyst, Argentina](https://job-boards.greenhouse.io/sezzle/jobs/7985449003) | HTTP 200 + feed; análisis de datos con SQL/Python; mínimo de dos años en fraude y dos en esas tecnologías; CV en inglés | **Afinidad técnica, pero no oportunidad inicial acreditada.** Había un error de extracción: la notación palabra + dígito entre paréntesis quedaba desconocida. Corregido a dos años y requisito específico de fraude, sin convertirlo en prioritaria |
| [Sezzle — Junior Software Engineer with Accounting Experience, Argentina](https://job-boards.greenhouse.io/sezzle/jobs/6668066003) | HTTP 200 + feed; desarrollo de software, remoto Argentina, requiere antecedentes como contador o analista financiero | Junior real, **falso positivo si se lo interpreta como adecuado por título/país solamente**. La clasificación de revisión era correcta. La experiencia administrativa/comercial no acredita el requisito contable |
| [Silver.dev — Opportunity in Tech Company — Backend Engineer](https://jobs.ashbyhq.com/silver/b35ced58-0a04-4a93-854c-80b717e7ec53) | HTTP 200; texto vigente comprobado por API; Buenos Aires/híbrido, Java, sistemas distribuidos en producción; sin años explícitos | Backend real y local, pero **experiencia productiva pendiente de aclaración**. No se confunde actitud de aprendizaje con una vacante trainee. Permanece en revisión |
| [Silver.dev — Ramp — Software Engineer](https://jobs.ashbyhq.com/silver/0c7fc4c6-4870-4258-8b27-e0c7d32ce7f8) | HTTP 200; texto vigente comprobado por API; remoto con Argentina en ubicaciones; backend Python/Go/TypeScript, PostgreSQL y responsabilidad de extremo a extremo | **Pista secundaria por tecnologías y geografía**. No hay años mínimos numéricos ni señal junior; el alcance exige autonomía. Mantener para consultar seniority, sin recomendarla como encaje confirmado |
| [RYZ Labs — AI-First Frontend Software Engineer](https://jobs.lever.co/RyzLabs/34d126be-b8fa-4291-8bc4-924031455850) | HTTP 200 + feed; remoto Argentina, React/TypeScript, experiencia sólida frontend y herramientas de programación con IA | Es IT, pero **no es AI/Data Science Trainee**: IA describe el flujo de desarrollo. Afinidad parcial con frontend, no evidencia de primera experiencia. Revisión correcta |
| [Mutt Data — Data Developer](https://jobs.lever.co/muttdata/50007942-3c59-493c-b2bc-cc269067c3e1) | HTTP 200 + feed; remoto Argentina, SQL/Python y proyectos de ingeniería de datos/ML; exige competencia en inglés, sin nivel CEFR ni años explícitos | **Pista más razonable para investigar de la muestra**, por aceptar experiencia en proyectos sin exigir remuneración explícita. Hay que confirmar seniority, alcance de proyectos e inglés. No se marca compatible ni junior confirmado |
| [Mutt Data — Machine Learning Engineer](https://jobs.lever.co/muttdata/8d40f420-1d29-4e94-a87a-6a271ebe3937) | HTTP 200 + feed; Argentina/remoto, implementación de sistemas ML, ciclo de modelos, MLOps y cloud; sin años explícitos | Data/ML real, pero **no trainee acreditado**. Los requisitos de implementación/MLOps superan conocimientos básicos declarados; no se inventa experiencia para cubrirlos. Mantener para revisión de seniority, con baja utilidad inmediata |
| [Canonical — Graduate Software Engineer, Open Source and Linux](https://job-boards.greenhouse.io/canonical/jobs/8249005) | HTTP 200 + feed; graduate real, remoto global, Linux/Python y otros lenguajes, cohorte de graduación 2025/2026, inglés profesional y viajes | **Opción internacional condicionada**, sin admisión de Argentina acreditada por país ni equivalencia académica/fecha confirmada. Worldwide no se convierte en elegibilidad; no es una alternativa internacional confirmada |

Conclusión: **ninguna de las nueve quedó confirmada sin reservas como adecuada para primera experiencia IT**. Data Developer es un contacto potencial para aclarar requisitos; Ramp/Backend son pistas de segundo orden. No se declara que un empleador haya aceptado al candidato ni que las ofertas garanticen entrevista. Un enlace HTTP 200 y una publicación en feed no prueban por sí solos disponibilidad definitiva del proceso.

## Correcciones de cierre dentro de 3A

Reglas `argentina-v1.1`, sin ampliar proveedores ni incorporar automatizaciones:

- Un rango que excede el máximo objetivo queda para revisión; su mínimo no basta para inferir junior. Se conserva el rango completo.
- Reconocimiento de números redundantes concordantes como palabra/dígito entre paréntesis. Si se contradicen, se mantiene desconocido.
- Comunicación profesional/proficiency en inglés se registra como requisito con nivel exacto no especificado; no se atribuye inglés avanzado al candidato ni se asume ausencia de requisito.
- Los antecedentes de fraude se distinguen de skills de análisis; no se promueve una oferta por SQL/Python únicamente.
- La lista de posibles excluyentes recoge requisitos de sus secciones y omite encabezados y frases negativas de experiencia no requerida.
- Se agregaron seis casos unitarios y una integración de sync repetido, persistencia y matching para estos hallazgos.

## Métricas corregidas y persistencia

[SPRINT_3A_RELEASE_METRICS.json](SPRINT_3A_RELEASE_METRICS.json) aplica las reglas corregidas a los **mismos snapshots de 935 publicaciones** de la auditoría de las 14:38:44 -03:00, sin inventar una nueva lectura completa. Incluye versión de clasificación y modo `offline_reclassification`. La muestra de nueve sí fue comprobada nuevamente en vivo.

| Métrica | Resultado de cierre |
| --- | ---: |
| Publicaciones | 935 |
| Argentina explícita | 116 |
| Argentina inferida adicional | 58 |
| Junior/trainee explícito (incluye áreas no IT) | 100 |
| Argentina + junior explícitos | 9 |
| Junior inferido | 35 |
| Geografía desconocida | 276 |
| Seniority desconocido | 378 |
| Geografía o seniority desconocidos (unión) | 529 |
| Años requeridos desconocidos | 629 |
| Prioritaria Argentina | **0** |
| Alternativa internacional confirmada | **0** |
| Revisión necesaria | **82** |
| Despriorizadas | **853** |

El informe y JSON iniciales conservan sus resultados previos como evidencia histórica; README y ROADMAP reflejan el cierre corregido. Las cifras son publicaciones, antes de deduplicación entre fuentes, no oportunidades únicas ni compatibles por completo.

Una nueva sincronización real (run 8, **15:29:51–15:30:32 -03:00**) terminó correctamente en **8/8 fuentes**: 935 publicaciones sin cambios de contenido, cero nuevas, cero duplicados nuevos y 935 scores recalculados. Las reglas/evidencias se actualizan aunque el hash del contenido no cambie. No se borraron ofertas ni se modificó el perfil durante esa sincronización.

## Privacidad, validación técnica y publicación

El singleton profesional se leyó desde otra sesión de PostgreSQL y validó contra `ProfileInput`; se verificaron esquema y presencia de secciones sin imprimir sus contenidos. Los datos iniciales residen en DB y `private/profile.json`, ignorados por Git. La auditoría del conjunto candidato a publicación no encontró credenciales locales ni detalles privados de estudios/proyectos; `.env`, `private/`, `.local/`, datos y uploads no están versionados. Tests y fixtures contienen información ficticia. La comprobación se repite sobre el índice exacto antes del commit.

Validaciones locales de cierre: **144 tests backend** (122 unitarios y 22 integraciones PostgreSQL) y **26 frontend**, total **170**; siete casos adicionales respecto de los 163 iniciales. Migraciones `upgrade head` y `check`, reversibilidad/preservación en esquema temporal, Ruff lint/formato, TypeScript, Prettier, build, `pip check`, `npm audit` y `git diff --check`. La auditoría npm reportó cero vulnerabilidades. Un intento unitario dentro del sandbox encontró permisos insuficientes sobre la carpeta temporal heredada; la suite completa con acceso autorizado aprobó.

Sigue pendiente la revisión visual desktop/móvil por el timeout de autorización registrado en el informe inicial. No se declara validada esa parte. Se verificaron componentes con Testing Library y endpoints por HTTP; esta limitación no impide comprobar el contenido público de las nueve ofertas por las vías descritas.

Se revisaron README, ARCHITECTURE, ROADMAP y el informe inicial para distinguir resultados históricos de correcciones. Publicación prevista exclusivamente por fast-forward normal a `origin/main`, sin force push, con comprobación posterior de SHA remoto, árbol limpio y CI. No se avanza a Sprint 3B ni se implementan postulaciones.
