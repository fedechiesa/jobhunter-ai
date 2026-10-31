import { useState } from 'react';
import type { FormEvent } from 'react';
import type { JobFilters as Filters, Source } from '../types';

export function JobFilters({
  onApply,
  disabled,
  sources = [],
}: {
  onApply: (filters: Filters) => void;
  disabled: boolean;
  sources?: Source[];
}) {
  const [q, setQ] = useState('');
  const [location, setLocation] = useState('');
  const [provider, setProvider] = useState('');
  const [mode, setMode] = useState('');
  const [since, setSince] = useState('');
  const [score, setScore] = useState('');
  const [sort, setSort] = useState('recommended');
  const [availability, setAvailability] = useState('active');
  const [country, setCountry] = useState('');
  const [seniority, setSeniority] = useState('');
  const [compatibility, setCompatibility] = useState('');
  const [published, setPublished] = useState('');
  const [source, setSource] = useState('');
  function submit(event: FormEvent) {
    event.preventDefault();
    onApply({
      q,
      location,
      provider,
      workplace_type: mode,
      discovered_after: since ? `${since}T00:00:00Z` : '',
      min_score: score,
      sort,
      availability,
      country,
      seniority,
      compatibility,
      published_after: published ? `${published}T00:00:00Z` : '',
      source_id: source,
    });
  }
  return (
    <form className="filter-form" aria-label="Filtros de ofertas" onSubmit={submit}>
      <fieldset disabled={disabled}>
        <div className="filter-grid">
          <label>
            País de la oferta
            <select value={country} onChange={(e) => setCountry(e.target.value)}>
              <option value="">Todos</option>
              <option value="AR">Argentina (explícita o inferida)</option>
              <option value="other">Otro país</option>
              <option value="unknown">Desconocido</option>
            </select>
          </label>
          <label>
            Seniority
            <select value={seniority} onChange={(e) => setSeniority(e.target.value)}>
              <option value="">Todos</option>
              <option value="junior">Junior / Trainee</option>
              <option value="senior">Senior / superior</option>
              <option value="unknown">Desconocido</option>
            </select>
          </label>
          <label>
            Clasificación
            <select value={compatibility} onChange={(e) => setCompatibility(e.target.value)}>
              <option value="">Todas</option>
              <option value="argentina_priority">Prioritaria Argentina</option>
              <option value="international_alternative">Alternativa internacional</option>
              <option value="review_needed">Revisión necesaria</option>
              <option value="deprioritized">Despriorizada</option>
            </select>
          </label>
          <label>
            Publicadas desde
            <input type="date" value={published} onChange={(e) => setPublished(e.target.value)} />
          </label>
          <label>
            Fuente
            <select value={source} onChange={(e) => setSource(e.target.value)}>
              <option value="">Todas</option>
              {sources.map((item) => (
                <option key={item.id} value={item.id}>
                  {item.name}
                </option>
              ))}
            </select>
          </label>
          <label>
            Palabra clave
            <input
              value={q}
              maxLength={200}
              onChange={(e) => setQ(e.target.value)}
              placeholder="Python, Data Analyst…"
            />
          </label>
          <label>
            Ubicación
            <input
              value={location}
              maxLength={200}
              onChange={(e) => setLocation(e.target.value)}
              placeholder="Argentina, Buenos Aires…"
            />
          </label>
          <label>
            Proveedor
            <select value={provider} onChange={(e) => setProvider(e.target.value)}>
              <option value="">Todos</option>
              <option value="greenhouse">Greenhouse</option>
              <option value="lever">Lever</option>
              <option value="ashby">Ashby</option>
              <option value="manual">Manual</option>
            </select>
          </label>
          <label>
            Modalidad
            <select value={mode} onChange={(e) => setMode(e.target.value)}>
              <option value="">Todas</option>
              <option value="remote">Remoto</option>
              <option value="hybrid">Híbrido</option>
              <option value="onsite">Presencial</option>
              <option value="unknown">Sin especificar</option>
            </select>
          </label>
          <label>
            Descubiertas desde
            <input type="date" value={since} onChange={(e) => setSince(e.target.value)} />
          </label>
          <label>
            Compatibilidad mínima
            <input
              type="number"
              min="0"
              max="100"
              step="any"
              value={score}
              onChange={(e) => setScore(e.target.value)}
              placeholder="Sin mínimo"
            />
          </label>
          <label>
            Ordenar por
            <select value={sort} onChange={(e) => setSort(e.target.value)}>
              <option value="recommended">Mejores oportunidades primero</option>
              <option value="priority">Prioridad de búsqueda</option>
              <option value="newest">Más recientes</option>
              <option value="score">Compatibilidad</option>
            </select>
          </label>
          <label>
            Disponibilidad
            <select value={availability} onChange={(e) => setAvailability(e.target.value)}>
              <option value="active">Observadas activas</option>
              <option value="potentially_inactive">Potencialmente inactivas</option>
              <option value="">Todas (historial)</option>
            </select>
          </label>
        </div>
        <button type="submit" className="secondary">
          Aplicar filtros
        </button>
      </fieldset>
    </form>
  );
}
