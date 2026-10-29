import { useEffect, useRef, useState } from 'react';
import type { FormEvent } from 'react';
import { api } from '../api';
import type { SearchPreferences, Source, SyncStatus } from '../types';

const dateLabel = (value: string | null) =>
  value ? new Date(value).toLocaleString('es-AR') : 'Sin ejecutar';
const statusLabel: Record<string, string> = {
  success: 'Completada',
  partial: 'Parcial: revisá errores por fuente',
  failed: 'Fallida',
  interrupted: 'Interrumpida',
  running: 'En curso',
};

export function DiscoveryPanel({ onRefresh }: { onRefresh: () => void }) {
  const [sources, setSources] = useState<Source[]>([]);
  const [status, setStatus] = useState<SyncStatus | null>(null);
  const [preferences, setPreferences] = useState<SearchPreferences | null>(null);
  const [busy, setBusy] = useState(false);
  const [syncing, setSyncing] = useState(false);
  const [error, setError] = useState('');
  const [message, setMessage] = useState('');
  const [expanded, setExpanded] = useState(false);
  const refreshRef = useRef(onRefresh);
  refreshRef.current = onRefresh;
  const latestRef = useRef<number | null>(null);
  const initializedRef = useRef(false);

  useEffect(() => {
    let active = true;
    async function load() {
      try {
        const [configured, current, prefs] = await Promise.all([
          api.sources(),
          api.syncStatus(),
          api.searchPreferences(),
        ]);
        if (!active) return;
        setSources(configured);
        setStatus(current);
        setPreferences((previous) => previous ?? prefs);
        const finishedId = current.latest?.finished_at ? current.latest.id : null;
        if (finishedId !== null && initializedRef.current && latestRef.current !== finishedId)
          refreshRef.current();
        if (finishedId !== null) latestRef.current = finishedId;
        initializedRef.current = true;
      } catch (reason) {
        if (active)
          setError(
            reason instanceof Error ? reason.message : 'No se pudieron consultar las fuentes.',
          );
      }
    }
    void load();
    const poll = setInterval(() => {
      void load();
    }, 10_000);
    return () => {
      active = false;
      clearInterval(poll);
    };
  }, []);

  async function synchronize() {
    setBusy(true);
    setSyncing(true);
    setError('');
    setMessage('');
    try {
      const result = await api.sync();
      latestRef.current = result.id;
      setStatus({ running: false, latest: result });
      setSources(await api.sources());
      const total = result.source_results.reduce((sum, source) => sum + (source.fetched ?? 0), 0);
      setMessage(
        `${statusLabel[result.status] ?? result.status}. ${total} ofertas leídas en esta ejecución.`,
      );
      refreshRef.current();
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : 'No se pudo sincronizar.');
    } finally {
      setBusy(false);
      setSyncing(false);
    }
  }

  async function toggle(source: Source) {
    setBusy(true);
    setError('');
    try {
      const updated = await api.updateSource(source.id, !source.enabled);
      setSources((current) => current.map((item) => (item.id === updated.id ? updated : item)));
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : 'No se pudo actualizar la fuente.');
    } finally {
      setBusy(false);
    }
  }

  async function save(event: FormEvent) {
    event.preventDefault();
    if (!preferences) return;
    setBusy(true);
    setError('');
    try {
      const clean = (values: string[]) => values.map((value) => value.trim()).filter(Boolean);
      setPreferences(
        await api.saveSearchPreferences({
          ...preferences,
          roles: clean(preferences.roles),
          technologies: clean(preferences.technologies),
          locations: clean(preferences.locations),
        }),
      );
      setMessage(
        'Preferencias guardadas. Se actualizó la prioridad de las ofertas; tu experiencia declarada no cambió.',
      );
      refreshRef.current();
    } catch (reason) {
      setError(
        reason instanceof Error ? reason.message : 'No se pudieron guardar las preferencias.',
      );
    } finally {
      setBusy(false);
    }
  }

  return (
    <section className="discovery-panel" aria-label="Descubrimiento de ofertas">
      <div className="section-heading">
        <div>
          <span className="eyebrow">FUENTES PÚBLICAS CONFIGURADAS</span>
          <h2>Descubrir oportunidades</h2>
        </div>
        <button
          className="primary"
          disabled={
            busy || !!status?.running || !status || !sources.some((source) => source.enabled)
          }
          onClick={() => {
            void synchronize();
          }}
        >
          {syncing || status?.running ? 'Sincronizando…' : 'Sincronizar ahora'}
        </button>
      </div>
      <p className="muted">
        Última sincronización:{' '}
        {status?.latest
          ? `${statusLabel[status.latest.status] ?? status.latest.status} · ${dateLabel(status.latest.finished_at ?? status.latest.started_at)}`
          : 'Sin ejecutar'}
        . Solo lectura; la postulación se hace en el sitio original.
      </p>
      {error && (
        <p role="alert" className="alert error">
          {error}
        </p>
      )}
      {message && (
        <p role="status" className="alert success">
          {message}
        </p>
      )}
      <div className="source-list">
        {sources.map((source) => (
          <div className="source-row" key={source.id}>
            <div>
              <strong>{source.name}</strong>
              <p>
                {source.last_error
                  ? `Error: ${source.last_error}`
                  : `Última lectura correcta: ${dateLabel(source.last_success_at)}`}
              </p>
              {source.last_result && (
                <p>
                  {source.last_result.fetched ?? 0} leídas · {source.last_result.new ?? 0} nuevas ·{' '}
                  {source.last_result.updated ?? 0} actualizadas ·{' '}
                  {source.last_result.unchanged ?? 0} sin cambios ·{' '}
                  {source.last_result.potentially_inactive ?? 0} ausentes
                </p>
              )}
            </div>
            <button
              className="secondary"
              disabled={busy || !!status?.running}
              aria-label={`${source.enabled ? 'Pausar' : 'Activar'} ${source.kind}`}
              onClick={() => {
                void toggle(source);
              }}
            >
              {source.enabled ? 'Pausar' : 'Activar'}
            </button>
          </div>
        ))}
      </div>
      <button
        className="text-button"
        aria-expanded={expanded}
        onClick={() => setExpanded((value) => !value)}
      >
        Preferencias de búsqueda {expanded ? '↑' : '↓'}
      </button>
      {expanded && preferences && (
        <form
          className="editor search-editor"
          aria-label="Preferencias de búsqueda"
          onSubmit={(event) => {
            void save(event);
          }}
        >
          <p className="muted">
            Estos son intereses para ordenar resultados. Las habilidades y la experiencia del
            candidato se declaran en Mi perfil. No se descartan requisitos ambiguos; senior se
            desprioriza.
          </p>
          <fieldset disabled={busy || !!status?.running}>
            <label>
              Roles (uno por línea)
              <textarea
                rows={5}
                value={preferences.roles.join('\n')}
                onChange={(e) =>
                  setPreferences({ ...preferences, roles: e.target.value.split('\n') })
                }
              />
            </label>
            <label>
              Tecnologías de interés (separadas por comas)
              <input
                value={preferences.technologies.join(', ')}
                onChange={(e) =>
                  setPreferences({
                    ...preferences,
                    technologies: e.target.value.split(',').map((value) => value.trim()),
                  })
                }
              />
            </label>
            <label>
              Ubicaciones de interés (separadas por comas)
              <input
                value={preferences.locations.join(', ')}
                onChange={(e) =>
                  setPreferences({
                    ...preferences,
                    locations: e.target.value.split(',').map((value) => value.trim()),
                  })
                }
              />
            </label>
            <label>
              Experiencia máxima priorizada
              <input
                type="number"
                min="0"
                max="80"
                required
                value={preferences.max_experience_years}
                onChange={(e) =>
                  setPreferences({ ...preferences, max_experience_years: e.target.valueAsNumber })
                }
              />
            </label>
            <label className="checkbox">
              <input
                type="checkbox"
                checked={preferences.deprioritize_senior}
                onChange={(e) =>
                  setPreferences({ ...preferences, deprioritize_senior: e.target.checked })
                }
              />
              Despriorizar puestos claramente senior
            </label>
            <button className="primary" type="submit">
              Guardar preferencias
            </button>
          </fieldset>
        </form>
      )}
    </section>
  );
}
