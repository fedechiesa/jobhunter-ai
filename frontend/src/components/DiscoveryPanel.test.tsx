import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { beforeEach, expect, it, vi } from 'vitest';
import { api } from '../api';
import { DiscoveryPanel } from './DiscoveryPanel';
import { JobFilters } from './JobFilters';
import type { SearchPreferences, Source, SyncRun } from '../types';

vi.mock('../api', () => ({
  api: {
    sources: vi.fn(),
    syncStatus: vi.fn(),
    sync: vi.fn(),
    updateSource: vi.fn(),
    searchPreferences: vi.fn(),
    saveSearchPreferences: vi.fn(),
  },
}));
const source: Source = {
  id: 2,
  name: 'Example Labs (greenhouse/example)',
  kind: 'greenhouse',
  board_token: 'example',
  region: 'global',
  enabled: true,
  last_attempt_at: null,
  last_success_at: null,
  last_error: null,
  last_result: null,
};
const preferences: SearchPreferences = {
  roles: ['Python Developer Junior'],
  technologies: ['Python', 'SQL'],
  locations: ['Argentina'],
  max_experience_years: 2,
  deprioritize_senior: true,
};
const run: SyncRun = {
  id: 1,
  status: 'success',
  started_at: '2026-01-01T00:00:00Z',
  finished_at: '2026-01-01T00:00:01Z',
  source_results: [
    {
      source_id: 2,
      provider: 'greenhouse',
      board: 'example',
      status: 'success',
      fetched: 3,
      new: 3,
    },
  ],
};

beforeEach(() => {
  vi.resetAllMocks();
  vi.mocked(api.sources).mockResolvedValue([source]);
  vi.mocked(api.syncStatus).mockResolvedValue({ running: false, latest: null });
  vi.mocked(api.searchPreferences).mockResolvedValue(preferences);
});

it('synchronizes and refreshes the dashboard', async () => {
  vi.mocked(api.sync).mockResolvedValue(run);
  const refresh = vi.fn();
  render(<DiscoveryPanel onRefresh={refresh} />);
  await waitFor(() =>
    expect(screen.getByRole('button', { name: 'Sincronizar ahora' })).toBeEnabled(),
  );
  await userEvent.click(screen.getByRole('button', { name: 'Sincronizar ahora' }));
  expect(await screen.findByText(/3 ofertas leídas/)).toBeInTheDocument();
  expect(refresh).toHaveBeenCalledOnce();
});

it('prevents a second click while synchronizing', async () => {
  vi.mocked(api.sync).mockReturnValue(new Promise(() => {}));
  render(<DiscoveryPanel onRefresh={vi.fn()} />);
  await waitFor(() =>
    expect(screen.getByRole('button', { name: 'Sincronizar ahora' })).toBeEnabled(),
  );
  await userEvent.click(screen.getByRole('button', { name: 'Sincronizar ahora' }));
  expect(screen.getByRole('button', { name: 'Sincronizando…' })).toBeDisabled();
  expect(api.sync).toHaveBeenCalledOnce();
});

it('disables sync when another worker owns the lock', async () => {
  vi.mocked(api.syncStatus).mockResolvedValue({
    running: true,
    latest: { ...run, status: 'running', finished_at: null },
  });
  render(<DiscoveryPanel onRefresh={vi.fn()} />);
  expect(await screen.findByRole('button', { name: 'Sincronizando…' })).toBeDisabled();
});

it('shows sync failures and allows pausing a source', async () => {
  vi.mocked(api.sync).mockRejectedValue(new Error('Ya hay una sincronización en curso.'));
  vi.mocked(api.updateSource).mockResolvedValue({ ...source, enabled: false });
  render(<DiscoveryPanel onRefresh={vi.fn()} />);
  await waitFor(() =>
    expect(screen.getByRole('button', { name: 'Sincronizar ahora' })).toBeEnabled(),
  );
  await userEvent.click(screen.getByRole('button', { name: 'Sincronizar ahora' }));
  expect(await screen.findByRole('alert')).toHaveTextContent('Ya hay una sincronización');
  await userEvent.click(screen.getByRole('button', { name: 'Pausar greenhouse' }));
  expect(await screen.findByRole('button', { name: 'Activar greenhouse' })).toBeInTheDocument();
  expect(api.updateSource).toHaveBeenCalledWith(2, false);
});

it('saves search interests independently of candidate experience', async () => {
  vi.mocked(api.saveSearchPreferences).mockResolvedValue(preferences);
  render(<DiscoveryPanel onRefresh={vi.fn()} />);
  await screen.findByText(source.name);
  await userEvent.click(screen.getByRole('button', { name: /Preferencias de búsqueda/ }));
  fireEvent.change(screen.getByLabelText('Roles (uno por línea)'), {
    target: { value: 'Python Developer Junior\n\n' },
  });
  await userEvent.click(screen.getByRole('button', { name: 'Guardar preferencias' }));
  await waitFor(() => expect(api.saveSearchPreferences).toHaveBeenCalledWith(preferences));
  expect(await screen.findByText(/tu experiencia declarada no cambió/)).toBeInTheDocument();
});

it('submits search filters with UTC dates and numeric score', async () => {
  const apply = vi.fn();
  render(<JobFilters onApply={apply} disabled={false} />);
  await userEvent.type(screen.getByLabelText('Palabra clave'), 'Python');
  await userEvent.selectOptions(screen.getByLabelText('Proveedor'), 'lever');
  fireEvent.change(screen.getByLabelText('Descubiertas desde'), {
    target: { value: '2026-01-01' },
  });
  await userEvent.type(screen.getByLabelText('Compatibilidad mínima'), '70');
  await userEvent.click(screen.getByRole('button', { name: 'Aplicar filtros' }));
  expect(apply).toHaveBeenCalledWith(
    expect.objectContaining({
      q: 'Python',
      provider: 'lever',
      discovered_after: '2026-01-01T00:00:00Z',
      min_score: '70',
    }),
  );
});
