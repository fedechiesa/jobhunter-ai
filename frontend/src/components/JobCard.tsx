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
  return (
    <article className="job-card">
      <div className="job-main">
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
          {job.remote ? 'Remoto' : 'Presencial / sin especificar'}
          <span>·</span>
          {job.location || 'Ubicación no especificada'}
          <span>·</span>
          {job.experience_years} años de experiencia
        </p>
        <p className="job-description">{job.description}</p>
        <div className="tags">
          {job.required_skills.map((skill) => (
            <span key={skill}>{skill}</span>
          ))}
        </div>
        {job.url && (
          <a className="source-link" href={job.url} target="_blank" rel="noopener noreferrer">
            Ver publicación original ↗
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
