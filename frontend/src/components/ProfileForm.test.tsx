import { render, screen, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, expect, it, vi } from 'vitest';
import { ProfileForm } from './Forms';
import { JobFilters } from './JobFilters';
import { api } from '../api';
import { emptyProfessional } from './ProfessionalEditor';
import type { ProfileInput } from '../types';

vi.mock('../api', () => ({ api: { profileDraft: vi.fn() } }));

describe('structured professional profile', () => {
  it('loads explicit local declarations and edits all sections without inventing IT years', async () => {
    const draft: ProfileInput = {
      skills: ['python'],
      experience_years: 0,
      preferred_location: 'CABA',
      prefer_remote: true,
      professional: {
        ...emptyProfessional(),
        education: [
          {
            title: 'Fictional course',
            institution: '',
            status: 'unknown',
            confirmation: 'pending',
          },
        ],
        work_experience: [
          {
            role: 'Office assistant',
            details: '',
            is_it: false,
            paid: null,
            confirmation: 'pending',
          },
        ],
        projects: [
          { name: 'Example lab', description: '', technologies: [], confirmation: 'pending' },
        ],
        languages: [{ name: 'English', level: 'intermediate', confirmation: 'pending' }],
      },
    };
    vi.mocked(api.profileDraft).mockResolvedValue(draft);
    const onSave = vi.fn().mockResolvedValue(undefined);
    render(<ProfileForm profile={null} busy={false} onSave={onSave} />);
    await userEvent.click(
      screen.getByRole('button', { name: 'Cargar borrador profesional local' }),
    );
    const title = await screen.findByLabelText('Título');
    await userEvent.clear(title);
    await userEvent.type(title, 'Example qualification');
    await userEvent.type(screen.getByLabelText('Institución'), 'Fictional school');
    await userEvent.selectOptions(screen.getByLabelText('Estado'), 'completed');
    await userEvent.type(screen.getByLabelText('Detalles del trabajo'), 'Commercial work');
    await userEvent.type(screen.getByLabelText('Descripción del proyecto'), 'Academic lab');
    await userEvent.type(screen.getByLabelText('Tecnologías del proyecto'), 'python, sql');
    await userEvent.type(screen.getByLabelText('Contexto de python'), 'Declared coursework');
    await userEvent.selectOptions(screen.getByLabelText('Nivel declarado'), 'basic');
    await userEvent.selectOptions(
      within(screen.getByRole('group', { name: 'Idioma 1' })).getByLabelText('Confirmación'),
      'user_confirmed',
    );
    await userEvent.click(screen.getByRole('button', { name: 'Guardar perfil' }));
    expect(onSave).toHaveBeenCalledWith(
      expect.objectContaining({
        experience_years: 0,
        professional: expect.objectContaining({
          education: [
            expect.objectContaining({
              title: 'Example qualification',
              institution: 'Fictional school',
              confirmation: 'pending',
            }),
          ],
          work_experience: [
            expect.objectContaining({ is_it: false, paid: null, details: 'Commercial work' }),
          ],
          projects: [
            expect.objectContaining({
              description: 'Academic lab',
              technologies: ['python', 'sql'],
            }),
          ],
          languages: [expect.objectContaining({ level: 'basic', confirmation: 'user_confirmed' })],
          skills: [
            expect.objectContaining({
              name: 'python',
              details: 'Declared coursework',
              confirmation: 'pending',
            }),
          ],
        }),
      }),
    );
  });

  it('validates empty entries and allows removing them', async () => {
    const onSave = vi.fn().mockResolvedValue(undefined);
    render(<ProfileForm profile={null} busy={false} onSave={onSave} />);
    await userEvent.click(
      screen.getByRole('button', { name: 'Completar estudios, trabajos, proyectos e idiomas' }),
    );
    await userEvent.click(screen.getByRole('button', { name: 'Agregar estudio' }));
    await userEvent.click(screen.getByRole('button', { name: 'Guardar perfil' }));
    expect(onSave).not.toHaveBeenCalled();
    await userEvent.click(screen.getByRole('button', { name: 'Quitar estudio 1' }));
    await userEvent.click(screen.getByRole('button', { name: 'Guardar perfil' }));
    expect(onSave).toHaveBeenCalledOnce();
  });

  it('keeps the editor usable when no private draft is available', async () => {
    vi.mocked(api.profileDraft).mockRejectedValue(new Error('missing draft'));
    render(<ProfileForm profile={null} busy={false} onSave={vi.fn()} />);
    await userEvent.click(
      screen.getByRole('button', { name: 'Cargar borrador profesional local' }),
    );
    expect(await screen.findByRole('alert')).toHaveTextContent('No se pudo cargar');
    expect(screen.getByLabelText('Habilidades, separadas por comas')).toBeEnabled();
  });
});

it('sends combined Argentina, seniority, classification and publication filters', async () => {
  const onApply = vi.fn();
  render(<JobFilters onApply={onApply} disabled={false} />);
  await userEvent.selectOptions(screen.getByLabelText('País de la oferta'), 'AR');
  await userEvent.selectOptions(screen.getByLabelText('Seniority'), 'junior');
  await userEvent.selectOptions(screen.getByLabelText('Clasificación'), 'review_needed');
  await userEvent.click(screen.getByRole('button', { name: 'Aplicar filtros' }));
  expect(onApply).toHaveBeenCalledWith(
    expect.objectContaining({
      country: 'AR',
      seniority: 'junior',
      compatibility: 'review_needed',
      sort: 'recommended',
    }),
  );
});
