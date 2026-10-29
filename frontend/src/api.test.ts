import { afterEach, describe, expect, it, vi } from 'vitest';
import { api } from './api';

afterEach(() => vi.unstubAllGlobals());

describe('API client', () => {
  it('treats a missing profile as the first-run state', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({ ok: false, status: 404 }));
    await expect(api.profile()).resolves.toBeNull();
  });

  it('reports database errors instead of treating them as an empty profile', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({ ok: false, status: 503 }));
    await expect(api.profile()).rejects.toThrow('La base de datos no está disponible');
  });

  it('sends the expected method and JSON payload', async () => {
    const fetchMock = vi.fn().mockResolvedValue({ ok: true, json: async () => ({ id: 1 }) });
    vi.stubGlobal('fetch', fetchMock);
    const data = {
      skills: ['sql'],
      experience_years: 0,
      preferred_location: '',
      prefer_remote: true,
    };
    await api.saveProfile(data);
    expect(fetchMock).toHaveBeenCalledWith(
      expect.stringContaining('/profile'),
      expect.objectContaining({
        method: 'PUT',
        body: JSON.stringify(data),
        headers: { 'Content-Type': 'application/json' },
      }),
    );
  });

  it('maps network failures to a useful message', async () => {
    vi.stubGlobal('fetch', vi.fn().mockRejectedValue(new TypeError('Failed to fetch')));
    await expect(api.jobs()).rejects.toThrow('Revisá que el backend esté iniciado');
  });

  it('maps validation errors without echoing input data', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({ ok: false, status: 422 }));
    await expect(api.match(1)).rejects.toThrow('Revisá los campos');
  });
});
