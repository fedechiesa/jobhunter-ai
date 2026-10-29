import { fireEvent, render, screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import App from './App';
import { api } from './api';
import type { Job, MatchScore, Profile } from './types';

vi.mock('./api', () => ({
  PAGE_SIZE: 20,
  api: {
    jobs: vi.fn(),
    profile: vi.fn(),
    createJob: vi.fn(),
    saveProfile: vi.fn(),
    match: vi.fn(),
  },
}));
vi.mock('./components/DiscoveryPanel', () => ({ DiscoveryPanel: () => null }));

const profile: Profile = {
  id: 1,
  skills: ['python'],
  experience_years: 2,
  preferred_location: '',
  prefer_remote: true,
};
const score: MatchScore = {
  id: 1,
  job_id: 1,
  candidate_id: 1,
  score: 55,
  skill_score: 50,
  experience_score: 50,
  location_score: 100,
  matched_skills: ['python'],
  missing_skills: ['sql'],
  algorithm_version: 'deterministic-v1',
  created_at: '2026-01-01T00:00:00Z',
};
const job: Job = {
  id: 1,
  title: 'Backend Engineer',
  company: 'Example Labs',
  description: 'Fictional test opening.',
  location: 'Example City',
  remote: true,
  required_skills: ['python', 'sql'],
  experience_years: 4,
  url: 'https://example.com/jobs/1',
  source_id: 1,
  created_at: '2026-01-01T00:00:00Z',
  match_score: null,
};

beforeEach(() => {
  vi.resetAllMocks();
  vi.mocked(api.jobs).mockResolvedValue([]);
  vi.mocked(api.profile).mockResolvedValue(null);
});

describe('dashboard', () => {
  it('shows loading and then an empty state', async () => {
    render(<App />);
    expect(screen.getByText('Cargando oportunidades…')).toBeInTheDocument();
    expect(await screen.findByText('Un tablero lleno de posibilidades')).toBeInTheDocument();
  });

  it('shows API errors and retries', async () => {
    vi.mocked(api.jobs).mockRejectedValueOnce(new Error('No se pudo conectar con la API.'));
    render(<App />);
    expect(await screen.findByRole('alert')).toHaveTextContent('No se pudo conectar');
    await userEvent.click(screen.getByRole('button', { name: 'Reintentar carga' }));
    expect(await screen.findByText('Un tablero lleno de posibilidades')).toBeInTheDocument();
  });

  it('disables matching until a profile exists', async () => {
    vi.mocked(api.jobs).mockResolvedValue([job]);
    render(<App />);
    expect(await screen.findByRole('heading', { name: job.title })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Calcular match' })).toBeDisabled();
  });

  it('calculates and displays a score and its explanation', async () => {
    vi.mocked(api.jobs).mockResolvedValue([job]);
    vi.mocked(api.profile).mockResolvedValue(profile);
    vi.mocked(api.match).mockResolvedValue(score);
    render(<App />);
    await userEvent.click(await screen.findByRole('button', { name: 'Calcular match' }));
    expect(await screen.findByText('55', { exact: true })).toBeInTheDocument();
    expect(api.match).toHaveBeenCalledWith(1);
    expect(screen.getByText('Por cubrir: sql')).toBeInTheDocument();
  });

  it('keeps a failed match visible as an actionable error', async () => {
    vi.mocked(api.jobs).mockResolvedValue([job]);
    vi.mocked(api.profile).mockResolvedValue(profile);
    vi.mocked(api.match).mockRejectedValue(new Error('La base de datos no está disponible.'));
    render(<App />);
    await userEvent.click(await screen.findByRole('button', { name: 'Calcular match' }));
    expect(await screen.findByRole('alert')).toHaveTextContent(
      'La base de datos no está disponible.',
    );
    expect(screen.getByRole('heading', { name: job.title })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Calcular match' })).toBeEnabled();
  });

  it('saves a profile and invalidates displayed scores', async () => {
    vi.mocked(api.jobs).mockResolvedValue([{ ...job, match_score: score }]);
    vi.mocked(api.profile).mockResolvedValue(profile);
    vi.mocked(api.saveProfile).mockResolvedValue({ ...profile, skills: ['python', 'sql'] });
    render(<App />);
    await screen.findByText('55', { exact: true });
    await userEvent.click(screen.getByRole('button', { name: 'Mi perfil' }));
    const input = screen.getByLabelText('Habilidades, separadas por comas');
    await userEvent.clear(input);
    await userEvent.type(input, 'python, sql');
    await userEvent.click(screen.getByRole('button', { name: 'Guardar perfil' }));
    expect(await screen.findByText('Sin evaluar')).toBeInTheDocument();
    expect(api.saveProfile).toHaveBeenCalledWith({
      skills: ['python', 'sql'],
      experience_years: 2,
      preferred_location: '',
      prefer_remote: true,
    });
  });

  it('creates a manual job from the form', async () => {
    vi.mocked(api.createJob).mockImplementation(async () => {
      vi.mocked(api.jobs).mockResolvedValue([job]);
      return job;
    });
    render(<App />);
    await screen.findByText('Un tablero lleno de posibilidades');
    await userEvent.click(screen.getByRole('button', { name: '+ Agregar oferta' }));
    await userEvent.type(screen.getByLabelText('Puesto'), job.title);
    await userEvent.type(screen.getByLabelText('Empresa'), job.company);
    await userEvent.type(screen.getByLabelText('Descripción'), job.description);
    await userEvent.click(screen.getByRole('button', { name: 'Guardar oferta' }));
    expect(await screen.findByRole('heading', { name: job.title })).toBeInTheDocument();
    expect(api.createJob).toHaveBeenCalledWith(
      expect.objectContaining({ title: job.title, company: job.company, url: null }),
    );
  });

  it('paginates using the API instead of silently truncating results', async () => {
    vi.mocked(api.jobs).mockResolvedValue(
      Array.from({ length: 20 }, (_, index) => ({ ...job, id: index + 1 })),
    );
    render(<App />);
    await screen.findAllByRole('heading', { name: job.title });
    vi.mocked(api.jobs).mockResolvedValue([]);
    await userEvent.click(
      within(screen.getByRole('navigation')).getByRole('button', { name: 'Siguiente →' }),
    );
    expect(await screen.findByText('Llegaste al final')).toBeInTheDocument();
    await waitFor(() =>
      expect(api.jobs).toHaveBeenLastCalledWith(1, { sort: 'priority', availability: 'active' }),
    );
    expect(screen.getByRole('button', { name: 'Siguiente →' })).toBeDisabled();
  });

  it('shows pending state during matching', async () => {
    vi.mocked(api.jobs).mockResolvedValue([job]);
    vi.mocked(api.profile).mockResolvedValue(profile);
    vi.mocked(api.match).mockReturnValue(new Promise(() => {}));
    render(<App />);
    fireEvent.click(await screen.findByRole('button', { name: 'Calcular match' }));
    expect(screen.getByRole('button', { name: 'Calculando…' })).toBeDisabled();
  });
});
