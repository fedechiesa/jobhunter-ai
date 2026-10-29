import { useEffect, useState } from 'react';
import { api, PAGE_SIZE } from './api';
import { JobForm, ProfileForm } from './components/Forms';
import { JobCard } from './components/JobCard';
import { DiscoveryPanel } from './components/DiscoveryPanel';
import { JobFilters } from './components/JobFilters';
import type { Job, JobFilters as Filters, JobInput, Profile, ProfileInput } from './types';

export default function App() {
  const [jobs, setJobs] = useState<Job[]>([]);
  const [profile, setProfile] = useState<Profile | null>(null);
  const [loading, setLoading] = useState(true);
  const [loadFailed, setLoadFailed] = useState(false);
  const [error, setError] = useState('');
  const [notice, setNotice] = useState('');
  const [editor, setEditor] = useState<'profile' | 'job' | null>(null);
  const [busy, setBusy] = useState(false);
  const [matchingId, setMatchingId] = useState<number | null>(null);
  const [page, setPage] = useState(0);
  const [refresh, setRefresh] = useState(0);
  const [filters, setFilters] = useState<Filters>({ sort: 'priority', availability: 'active' });

  useEffect(() => {
    let active = true;
    setLoading(true);
    setLoadFailed(false);
    setError('');
    Promise.all([api.jobs(page, filters), api.profile()])
      .then(([offers, candidate]) => {
        if (active) {
          setJobs(offers);
          setProfile(candidate);
        }
      })
      .catch((reason: unknown) => {
        if (active) {
          setLoadFailed(true);
          setError(reason instanceof Error ? reason.message : 'No se pudieron cargar los datos.');
        }
      })
      .finally(() => {
        if (active) setLoading(false);
      });
    return () => {
      active = false;
    };
  }, [page, refresh, filters]);

  async function mutate(action: () => Promise<void>) {
    setBusy(true);
    setError('');
    setNotice('');
    try {
      await action();
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : 'No se pudo guardar el cambio.');
    } finally {
      setBusy(false);
      setMatchingId(null);
    }
  }

  async function saveProfile(data: ProfileInput) {
    await mutate(async () => {
      const saved = await api.saveProfile(data);
      setProfile(saved);
      setJobs((current) => current.map((job) => ({ ...job, match_score: null })));
      setEditor(null);
      setNotice('Perfil guardado. Podés calcular la compatibilidad de tus ofertas.');
    });
  }

  async function saveJob(data: JobInput) {
    await mutate(async () => {
      const saved = await api.createJob(data);
      setJobs((current) => [saved, ...current].slice(0, PAGE_SIZE));
      setPage(0);
      setRefresh((value) => value + 1);
      setEditor(null);
      setNotice('Oferta guardada. Tu próxima oportunidad ya está en el tablero.');
    });
  }

  function matchJob(id: number) {
    setMatchingId(id);
    void mutate(async () => {
      const score = await api.match(id);
      setJobs((current) =>
        current.map((job) => (job.id === id ? { ...job, match_score: score } : job)),
      );
      setNotice('Compatibilidad calculada y guardada.');
    });
  }

  const scored = jobs.flatMap((job) => (job.match_score ? [job.match_score.score] : []));
  const average = scored.length
    ? Math.round(scored.reduce((sum, score) => sum + score, 0) / scored.length)
    : null;
  const ready = !loading && !loadFailed;

  return (
    <>
      <header className="topbar">
        <div className="topbar-inner">
          <a className="brand" href="/">
            <span className="brand-icon" aria-hidden="true">
              ↗
            </span>
            JobHunter <strong>AI</strong>
          </a>
          <span className="local-badge">
            <i />
            Espacio local · personal
          </span>
        </div>
      </header>
      <main>
        <section className="hero">
          <div>
            <span className="eyebrow">TU BÚSQUEDA, CON DIRECCIÓN</span>
            <h1>
              Tu próxima oportunidad
              <br />
              <em>empieza acá.</em>
            </h1>
            <p>Organizá tus ofertas y descubrí dónde encaja tu perfil.</p>
          </div>
          <div className="hero-note">
            <span aria-hidden="true">✳</span>
            <p>
              Un paso a la vez.
              <br />
              <strong>Una decisión mejor informada.</strong>
            </p>
          </div>
        </section>
        <div className="stats" aria-label="Resumen de la página">
          <div>
            <span>Ofertas en esta página</span>
            <strong>{ready ? jobs.length.toString().padStart(2, '0') : '—'}</strong>
          </div>
          <div>
            <span>Ofertas evaluadas</span>
            <strong>{ready ? scored.length.toString().padStart(2, '0') : '—'}</strong>
          </div>
          <div>
            <span>Compatibilidad promedio</span>
            <strong>{ready && average !== null ? `${average}%` : '—'}</strong>
          </div>
        </div>
        <DiscoveryPanel
          onRefresh={() => {
            setPage(0);
            setRefresh((value) => value + 1);
          }}
        />
        <section className="workspace" aria-labelledby="opportunities-title">
          <div className="section-heading">
            <div>
              <span className="eyebrow">TU TABLERO</span>
              <h2 id="opportunities-title">Oportunidades</h2>
            </div>
            <div className="actions">
              <button
                className="secondary"
                disabled={busy || loading}
                aria-expanded={editor === 'profile'}
                onClick={() => setEditor(editor === 'profile' ? null : 'profile')}
              >
                {editor === 'profile' ? 'Cerrar perfil' : 'Mi perfil'}
              </button>
              <button
                className="primary"
                disabled={busy || loading}
                aria-expanded={editor === 'job'}
                onClick={() => setEditor(editor === 'job' ? null : 'job')}
              >
                {editor === 'job' ? 'Cerrar formulario' : '+ Agregar oferta'}
              </button>
            </div>
          </div>
          {error && (
            <div role="alert" className="alert error">
              <p>{error}</p>
              <button
                className="secondary"
                disabled={busy || loading}
                onClick={() => setRefresh((value) => value + 1)}
              >
                Reintentar carga
              </button>
            </div>
          )}
          {notice && (
            <p role="status" className="alert success">
              {notice}
            </p>
          )}
          {editor === 'profile' && (
            <ProfileForm profile={profile} busy={busy || loading} onSave={saveProfile} />
          )}
          {editor === 'job' && <JobForm busy={busy || loading} onSave={saveJob} />}
          <JobFilters
            disabled={busy || loading}
            onApply={(next) => {
              setPage(0);
              setFilters(next);
            }}
          />
          {loading ? (
            <div className="empty-state" role="status">
              <span className="loader" />
              Cargando oportunidades…
            </div>
          ) : (
            !loadFailed && (
              <>
                {!profile && (
                  <div className="profile-prompt">
                    <span>Completá tu perfil para descubrir la compatibilidad de cada oferta.</span>
                    <button
                      className="text-button"
                      disabled={busy}
                      onClick={() => setEditor('profile')}
                    >
                      Configurar perfil →
                    </button>
                  </div>
                )}
                {jobs.length ? (
                  <div className="job-list">
                    {jobs.map((job) => (
                      <JobCard
                        key={job.id}
                        job={job}
                        busy={busy}
                        matching={matchingId === job.id}
                        hasProfile={!!profile}
                        onMatch={matchJob}
                      />
                    ))}
                  </div>
                ) : (
                  <div className="empty-state">
                    <div className="empty-icon" aria-hidden="true">
                      ↗
                    </div>
                    <h3>{page ? 'Llegaste al final' : 'Un tablero lleno de posibilidades'}</h3>
                    <p>
                      {page
                        ? 'No hay más ofertas para mostrar en esta página.'
                        : 'No hay ofertas para estos filtros. Sincronizá las fuentes, cambiá la búsqueda o agregá una oferta manual.'}
                    </p>
                    {!page && (
                      <button className="primary" disabled={busy} onClick={() => setEditor('job')}>
                        Agregar mi primera oferta
                      </button>
                    )}
                  </div>
                )}
                <nav className="pagination" aria-label="Paginación de ofertas">
                  <button
                    className="secondary"
                    disabled={page === 0 || busy}
                    onClick={() => setPage((value) => value - 1)}
                  >
                    ← Anterior
                  </button>
                  <span>Página {page + 1}</span>
                  <button
                    className="secondary"
                    disabled={jobs.length < PAGE_SIZE || busy}
                    onClick={() => setPage((value) => value + 1)}
                  >
                    Siguiente →
                  </button>
                </nav>
              </>
            )
          )}
        </section>
        <footer>
          <span>
            JobHunter AI <span className="footer-dot">/</span> Discovery Engine
          </span>
          <span>Matching por reglas · 100% local</span>
        </footer>
      </main>
    </>
  );
}
