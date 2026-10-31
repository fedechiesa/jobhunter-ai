import type { Job } from '../types';

interface Props {
  job: Job;
  busy: boolean;
  matching: boolean;
  hasProfile: boolean;
  onMatch: (id: number) => void;
}

export function JobCard({ job, busy, matching, hasProfile, onMatch }: Props) {
  const score = job.match_score;
  const mode: Record<string, string> = {
    remote: 'Remoto',
    hybrid: 'Híbrido',
    onsite: 'Presencial',
    unknown: 'Modalidad sin especificar',
  };
  return (
    <article className="job-card">
      <div className="job-main">
        <div className="discovery-meta">
          {job.compatibility && (
            <strong>
              {
                (
                  {
                    argentina_priority: 'Prioritaria Argentina',
                    international_alternative: 'Alternativa internacional',
                    review_needed: 'Revisión necesaria',
                    deprioritized: 'Despriorizada',
                  } as Record<string, string>
                )[job.compatibility]
              }
            </strong>
          )}
          <span>{job.provider ?? 'manual'}</span>
          {job.first_discovered_at && (
            <span>
              Descubierta: {new Date(job.first_discovered_at).toLocaleDateString('es-AR')}
            </span>
          )}
          {job.availability === 'potentially_inactive' && (
            <span className="availability-warning">Potencialmente inactiva</span>
          )}
          {job.search_priority !== undefined && (
            <span>Prioridad de búsqueda: {job.search_priority.toFixed(0)}/100</span>
          )}
        </div>
        <div className="job-heading">
          <span className="company-mark" aria-hidden="true">
            {job.company.charAt(0).toUpperCase()}
          </span>
          <div>
            <p className="company-name">{job.company}</p>
            <h3>{job.title}</h3>
          </div>
        </div>
        <p className="job-meta">
          {job.workplace_type
            ? (mode[job.workplace_type] ?? job.workplace_type)
            : job.remote
              ? 'Remoto'
              : 'Presencial / sin especificar'}
          <span>·</span>
          {job.location || 'Ubicación no especificada'}
          <span>·</span>
          {job.experience_years_known === false
            ? 'Experiencia sin precisar'
            : `${job.experience_years} años de experiencia`}
        </p>
        <p className="job-description">{job.description}</p>
        {job.published_at && (
          <p>Publicada: {new Date(job.published_at).toLocaleDateString('es-AR')}</p>
        )}
        {job.assessment?.reasons && (
          <details>
            <summary>Razones y evidencia</summary>
            {!!job.assessment.hard_requirements?.length && (
              <div>
                <p>Posibles requisitos excluyentes (inferidos; revisar texto original)</p>
                <ul>
                  {job.assessment.hard_requirements.map((item, i) => (
                    <li key={i}>{item.evidence}</li>
                  ))}
                </ul>
              </div>
            )}
            <ul>
              {job.assessment.reasons.map((reason, i) => (
                <li key={i}>{reason}</li>
              ))}
            </ul>
            <dl>
              {Object.entries(job.assessment)
                .filter(([key]) =>
                  [
                    'geography',
                    'seniority',
                    'language',
                    'experience',
                    'posting_language',
                    'workplace',
                  ].includes(key),
                )
                .map(([key, evidence]) => {
                  const item = evidence as import('../types').Evidence;
                  const labels: Record<string, string> = {
                    geography: 'Geografía',
                    seniority: 'Seniority',
                    language: 'Idioma requerido',
                    experience: 'Experiencia',
                    posting_language: 'Idioma de publicación',
                    workplace: 'Modalidad',
                  };
                  return (
                    <div key={key}>
                      <dt>{labels[key]}</dt>
                      <dd>
                        {item.value ?? 'Desconocido'} ·{' '}
                        {
                          (
                            {
                              confirmed: 'confirmado por la fuente',
                              inferred: 'inferido',
                              unknown: 'desconocido',
                            } as Record<string, string>
                          )[item.status]
                        }
                        {item.evidence && `: ${item.evidence}`}
                      </dd>
                    </div>
                  );
                })}
            </dl>
          </details>
        )}
        <div className="tags">
          {job.required_skills.map((skill) => (
            <span key={skill}>{skill}</span>
          ))}
        </div>
        {job.requirements_inferred && (
          <p className="inferred-note">
            Tecnologías detectadas en el texto; pueden incluir menciones opcionales. Revisá los
            requisitos y las restricciones geográficas en la publicación original.
          </p>
        )}
        {job.url && (
          <a className="source-link" href={job.url} target="_blank" rel="noopener noreferrer">
            Ver publicación original ↗
          </a>
        )}
        {job.apply_url && job.apply_url !== job.url && (
          <a
            className="source-link"
            style={{ marginLeft: 14 }}
            href={job.apply_url}
            target="_blank"
            rel="noopener noreferrer"
          >
            Ir al sitio para postular ↗
          </a>
        )}
      </div>
      <div className="match-panel">
        {score ? (
          <>
            <div className="score-number">
              {score.score.toFixed(0)}
              <span>/100</span>
            </div>
            <span className="score-label">Compatibilidad</span>
            <meter
              min={0}
              max={100}
              value={score.score}
              aria-label={`Compatibilidad de ${job.title}`}
            />
            <details>
              <summary>Ver desglose</summary>
              <dl>
                <div>
                  <dt>Habilidades · 70%</dt>
                  <dd>{score.skill_score}%</dd>
                </div>
                <div>
                  <dt>Experiencia · 20%</dt>
                  <dd>{score.experience_score}%</dd>
                </div>
                <div>
                  <dt>Ubicación · 10%</dt>
                  <dd>{score.location_score}%</dd>
                </div>
              </dl>
              <p>Coinciden: {score.matched_skills.join(', ') || 'ninguna'}</p>
              <p>Por cubrir: {score.missing_skills.join(', ') || 'ninguna'}</p>
            </details>
          </>
        ) : (
          <>
            <span className="unscored" aria-hidden="true">
              —
            </span>
            <span className="score-label">Sin evaluar</span>
          </>
        )}
        <button
          className="secondary"
          disabled={busy || !hasProfile}
          onClick={() => onMatch(job.id)}
        >
          {matching ? 'Calculando…' : score ? 'Recalcular' : 'Calcular match'}
        </button>
        {!hasProfile && <small>Guardá tu perfil para evaluar.</small>}
      </div>
    </article>
  );
}
