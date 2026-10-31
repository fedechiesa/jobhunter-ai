import type { Confirmation, ProfessionalDetails } from '../types';

export const emptyProfessional = (): ProfessionalDetails => ({
  schema_version: 1,
  origin: 'user_declared',
  skills: [],
  education: [],
  work_experience: [],
  projects: [],
  languages: [],
  target_roles: [],
  residence_country: 'AR',
  preferred_languages: ['es'],
  first_it_job: true,
  max_experience_years: 2,
});

function ConfirmationField({
  value,
  onChange,
}: {
  value: Confirmation;
  onChange: (value: Confirmation) => void;
}) {
  return (
    <label>
      Confirmación
      <select value={value} onChange={(e) => onChange(e.target.value as Confirmation)}>
        <option value="pending">Pendiente de confirmación</option>
        <option value="user_confirmed">Confirmado por mí</option>
      </select>
    </label>
  );
}

export function ProfessionalEditor({
  value,
  onChange,
}: {
  value: ProfessionalDetails;
  onChange: (value: ProfessionalDetails) => void;
}) {
  function field<K extends keyof ProfessionalDetails>(key: K, next: ProfessionalDetails[K]) {
    onChange({ ...value, [key]: next });
  }
  function collection<
    K extends 'skills' | 'education' | 'work_experience' | 'projects' | 'languages',
  >(key: K, index: number, patch: object) {
    field(
      key,
      value[key].map((row, i) =>
        i === index ? { ...row, ...patch } : row,
      ) as ProfessionalDetails[K],
    );
  }
  function remove<K extends 'skills' | 'education' | 'work_experience' | 'projects' | 'languages'>(
    key: K,
    index: number,
  ) {
    field(key, value[key].filter((_, i) => i !== index) as ProfessionalDetails[K]);
  }
  return (
    <div className="professional-editor">
      <p className="muted">
        Información declarada por vos. Pendiente no significa verificada por terceros. No incluyas
        datos de contacto ni información sensible. Estudios y proyectos no se cuentan como
        experiencia IT remunerada.
      </p>
      <div className="form-grid">
        <label>
          País de residencia (ISO, dos letras)
          <input
            required
            pattern="[A-Z]{2}"
            maxLength={2}
            value={value.residence_country}
            onChange={(e) => field('residence_country', e.target.value.toUpperCase())}
          />
        </label>
        <label>
          Máximo de años requeridos para priorizar
          <input
            required
            type="number"
            min={0}
            max={80}
            step={1}
            value={value.max_experience_years}
            onChange={(e) => field('max_experience_years', e.target.valueAsNumber)}
          />
        </label>
      </div>
      <label>
        Roles objetivo (uno por línea)
        <textarea
          maxLength={6000}
          value={value.target_roles.join('\n')}
          onChange={(e) => field('target_roles', e.target.value.split('\n'))}
        />
      </label>
      <label className="checkbox">
        <input
          type="checkbox"
          checked={value.first_it_job}
          onChange={(e) => field('first_it_job', e.target.checked)}
        />
        Busco mi primera experiencia IT
      </label>
      <label>
        Idioma preferido de publicación
        <select
          value={value.preferred_languages.join(',')}
          onChange={(e) =>
            field(
              'preferred_languages',
              e.target.value ? (e.target.value.split(',') as Array<'es' | 'en'>) : [],
            )
          }
        >
          <option value="es">Español</option>
          <option value="en">Inglés</option>
          <option value="es,en">Español e inglés</option>
          <option value="">Sin preferencia</option>
        </select>
      </label>
      <h3>Confirmación de competencias</h3>
      <p className="muted">
        La lista de habilidades de arriba se usa en el matching. Cada habilidad nueva queda
        pendiente; no asignamos niveles de dominio.
      </p>
      {value.skills.map((row, i) => (
        <div className="form-grid" key={i}>
          <span>{row.name}</span>
          <label>
            Contexto de {row.name}
            <input
              maxLength={1000}
              value={row.details ?? ''}
              onChange={(e) => collection('skills', i, { details: e.target.value })}
            />
          </label>
          <ConfirmationField
            value={row.confirmation}
            onChange={(confirmation) => collection('skills', i, { confirmation })}
          />
        </div>
      ))}
      <h3>Estudios</h3>
      {value.education.map((row, i) => (
        <fieldset key={i}>
          <legend>Estudio {i + 1}</legend>
          <label>
            Título
            <input
              required
              maxLength={200}
              value={row.title}
              onChange={(e) => collection('education', i, { title: e.target.value })}
            />
          </label>
          <label>
            Institución
            <input
              maxLength={200}
              value={row.institution}
              onChange={(e) => collection('education', i, { institution: e.target.value })}
            />
          </label>
          <label>
            Estado
            <select
              value={row.status}
              onChange={(e) => collection('education', i, { status: e.target.value })}
            >
              <option value="completed">Completado</option>
              <option value="in_progress">En curso</option>
              <option value="unknown">Por confirmar</option>
            </select>
          </label>
          <ConfirmationField
            value={row.confirmation}
            onChange={(confirmation) => collection('education', i, { confirmation })}
          />
          <button type="button" onClick={() => remove('education', i)}>
            Quitar estudio {i + 1}
          </button>
        </fieldset>
      ))}
      <button
        type="button"
        disabled={value.education.length >= 30}
        onClick={() =>
          field('education', [
            ...value.education,
            { title: '', institution: '', status: 'unknown', confirmation: 'pending' },
          ])
        }
      >
        Agregar estudio
      </button>
      <h3>Experiencia laboral</h3>
      {value.work_experience.map((row, i) => (
        <fieldset key={i}>
          <legend>Trabajo {i + 1}</legend>
          <label>
            Rol laboral
            <input
              required
              maxLength={200}
              value={row.role}
              onChange={(e) => collection('work_experience', i, { role: e.target.value })}
            />
          </label>
          <label>
            Detalles del trabajo
            <textarea
              maxLength={2000}
              value={row.details}
              onChange={(e) => collection('work_experience', i, { details: e.target.value })}
            />
          </label>
          <label className="checkbox">
            <input
              type="checkbox"
              checked={row.is_it}
              onChange={(e) => collection('work_experience', i, { is_it: e.target.checked })}
            />
            Trabajo IT
          </label>
          <label>
            Remuneración
            <select
              value={row.paid === null ? 'unknown' : String(row.paid)}
              onChange={(e) =>
                collection('work_experience', i, {
                  paid: e.target.value === 'unknown' ? null : e.target.value === 'true',
                })
              }
            >
              <option value="unknown">Por confirmar</option>
              <option value="true">Remunerado</option>
              <option value="false">No remunerado</option>
            </select>
          </label>
          <ConfirmationField
            value={row.confirmation}
            onChange={(confirmation) => collection('work_experience', i, { confirmation })}
          />
          <button type="button" onClick={() => remove('work_experience', i)}>
            Quitar trabajo {i + 1}
          </button>
        </fieldset>
      ))}
      <button
        type="button"
        disabled={value.work_experience.length >= 50}
        onClick={() =>
          field('work_experience', [
            ...value.work_experience,
            { role: '', details: '', is_it: false, paid: null, confirmation: 'pending' },
          ])
        }
      >
        Agregar trabajo
      </button>
      <h3>Proyectos personales y académicos</h3>
      {value.projects.map((row, i) => (
        <fieldset key={i}>
          <legend>Proyecto {i + 1}</legend>
          <label>
            Nombre del proyecto
            <input
              required
              maxLength={200}
              value={row.name}
              onChange={(e) => collection('projects', i, { name: e.target.value })}
            />
          </label>
          <label>
            Descripción del proyecto
            <textarea
              maxLength={2000}
              value={row.description}
              onChange={(e) => collection('projects', i, { description: e.target.value })}
            />
          </label>
          <label>
            Tecnologías del proyecto
            <input
              maxLength={8000}
              value={row.technologies.join(', ')}
              onChange={(e) =>
                collection('projects', i, {
                  technologies: e.target.value.split(',').map((s) => s.trim()),
                })
              }
            />
          </label>
          <ConfirmationField
            value={row.confirmation}
            onChange={(confirmation) => collection('projects', i, { confirmation })}
          />
          <button type="button" onClick={() => remove('projects', i)}>
            Quitar proyecto {i + 1}
          </button>
        </fieldset>
      ))}
      <button
        type="button"
        disabled={value.projects.length >= 50}
        onClick={() =>
          field('projects', [
            ...value.projects,
            { name: '', description: '', technologies: [], confirmation: 'pending' },
          ])
        }
      >
        Agregar proyecto
      </button>
      <h3>Idiomas</h3>
      {value.languages.map((row, i) => (
        <fieldset key={i}>
          <legend>Idioma {i + 1}</legend>
          <label>
            Idioma
            <input
              required
              maxLength={200}
              value={row.name}
              onChange={(e) => collection('languages', i, { name: e.target.value })}
            />
          </label>
          <label>
            Nivel declarado
            <select
              value={row.level}
              onChange={(e) => collection('languages', i, { level: e.target.value })}
            >
              <option value="unknown">Por confirmar</option>
              <option value="basic">Básico</option>
              <option value="intermediate">Intermedio</option>
              <option value="advanced">Avanzado</option>
              <option value="fluent">Fluido</option>
              <option value="native">Nativo</option>
            </select>
          </label>
          <ConfirmationField
            value={row.confirmation}
            onChange={(confirmation) => collection('languages', i, { confirmation })}
          />
          <button type="button" onClick={() => remove('languages', i)}>
            Quitar idioma {i + 1}
          </button>
        </fieldset>
      ))}
      <button
        type="button"
        disabled={value.languages.length >= 20}
        onClick={() =>
          field('languages', [
            ...value.languages,
            { name: '', level: 'unknown', confirmation: 'pending' },
          ])
        }
      >
        Agregar idioma
      </button>
    </div>
  );
}
