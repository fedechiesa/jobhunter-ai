import { useState } from 'react';
import type { FormEvent } from 'react';
import type { JobInput, Profile, ProfileInput } from '../types';

const splitSkills = (value: string) =>
  value
    .split(',')
    .map((skill) => skill.trim())
    .filter(Boolean);

interface ProfileFormProps {
  profile: Profile | null;
  busy: boolean;
  onSave: (data: ProfileInput) => Promise<void>;
}

export function ProfileForm({ profile, busy, onSave }: ProfileFormProps) {
  const [skills, setSkills] = useState(profile?.skills.join(', ') ?? '');
  const [years, setYears] = useState(profile?.experience_years ?? 0);
  const [location, setLocation] = useState(profile?.preferred_location ?? '');
  const [remote, setRemote] = useState(profile?.prefer_remote ?? true);

  function submit(event: FormEvent) {
    event.preventDefault();
    void onSave({
      skills: splitSkills(skills),
      experience_years: years,
      preferred_location: location,
      prefer_remote: remote,
    });
  }

  return (
    <form onSubmit={submit} className="editor" aria-label="Perfil del candidato">
      <div className="section-heading">
        <div>
          <span className="eyebrow">TU PUNTO DE PARTIDA</span>
          <h2>Perfil profesional</h2>
        </div>
      </div>
      <p className="muted">
        Definí tus habilidades y preferencias para evaluar cada oportunidad. Al guardar, los scores
        anteriores quedan pendientes de recalcular.
      </p>
      <fieldset disabled={busy}>
        <label>
          Habilidades, separadas por comas
          <input
            value={skills}
            onChange={(e) => setSkills(e.target.value)}
            placeholder="Python, SQL, React"
            maxLength={8000}
          />
        </label>
        <div className="form-grid">
          <label>
            Años de experiencia
            <input
              type="number"
              min="0"
              max="80"
              step="1"
              required
              value={years}
              onChange={(e) => setYears(e.target.valueAsNumber)}
            />
          </label>
          <label>
            Ubicación preferida
            <input
              maxLength={200}
              value={location}
              onChange={(e) => setLocation(e.target.value)}
              placeholder="Sin preferencia"
            />
          </label>
        </div>
        <label className="checkbox">
          <input type="checkbox" checked={remote} onChange={(e) => setRemote(e.target.checked)} />
          Aceptar remoto en cualquier ubicación
        </label>
        <button className="primary" type="submit">
          {busy ? 'Guardando…' : 'Guardar perfil'}
        </button>
      </fieldset>
    </form>
  );
}

interface JobFormProps {
  busy: boolean;
  onSave: (data: JobInput) => Promise<void>;
}

export function JobForm({ busy, onSave }: JobFormProps) {
  const [title, setTitle] = useState('');
  const [company, setCompany] = useState('');
  const [description, setDescription] = useState('');
  const [skills, setSkills] = useState('');
  const [years, setYears] = useState(0);
  const [location, setLocation] = useState('');
  const [remote, setRemote] = useState(false);
  const [url, setUrl] = useState('');

  function submit(event: FormEvent) {
    event.preventDefault();
    void onSave({
      title,
      company,
      description,
      required_skills: splitSkills(skills),
      experience_years: years,
      location,
      remote,
      url: url.trim() || null,
    });
  }

  return (
    <form onSubmit={submit} className="editor" aria-label="Nueva oferta">
      <span className="eyebrow">CARGA MANUAL</span>
      <h2>Una nueva oportunidad</h2>
      <fieldset disabled={busy}>
        <div className="form-grid">
          <label>
            Puesto
            <input
              required
              maxLength={200}
              value={title}
              onChange={(e) => setTitle(e.target.value)}
            />
          </label>
          <label>
            Empresa
            <input
              required
              maxLength={200}
              value={company}
              onChange={(e) => setCompany(e.target.value)}
            />
          </label>
        </div>
        <label>
          Descripción
          <textarea
            required
            maxLength={20000}
            rows={3}
            value={description}
            onChange={(e) => setDescription(e.target.value)}
          />
        </label>
        <label>
          Habilidades requeridas, separadas por comas
          <input maxLength={8000} value={skills} onChange={(e) => setSkills(e.target.value)} />
        </label>
        <div className="form-grid">
          <label>
            Experiencia requerida en años
            <input
              type="number"
              min="0"
              max="80"
              step="1"
              required
              value={years}
              onChange={(e) => setYears(e.target.valueAsNumber)}
            />
          </label>
          <label>
            Ubicación
            <input maxLength={200} value={location} onChange={(e) => setLocation(e.target.value)} />
          </label>
        </div>
        <label>
          URL de la oferta (opcional)
          <input
            type="url"
            maxLength={2048}
            pattern="https?://.*"
            value={url}
            onChange={(e) => setUrl(e.target.value)}
            placeholder="https://…"
          />
        </label>
        <label className="checkbox">
          <input type="checkbox" checked={remote} onChange={(e) => setRemote(e.target.checked)} />
          Trabajo remoto
        </label>
        <button className="primary" type="submit">
          {busy ? 'Guardando…' : 'Guardar oferta'}
        </button>
      </fieldset>
    </form>
  );
}
