import type {
  Job,
  JobFilters,
  JobInput,
  MatchScore,
  Profile,
  ProfileInput,
  SearchPreferences,
  Source,
  SyncRun,
  SyncStatus,
} from './types';

const BASE = (import.meta.env.VITE_API_BASE_URL ?? 'http://127.0.0.1:8000').replace(/\/$/, '');
export const PAGE_SIZE = 20;

export class ApiError extends Error {
  constructor(
    public status: number,
    message: string,
  ) {
    super(message);
  }
}

async function request<T>(path: string, options?: RequestInit, timeoutMs = 10_000): Promise<T> {
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), timeoutMs);
  try {
    const response = await fetch(`${BASE}${path}`, {
      ...options,
      headers: options?.body ? { 'Content-Type': 'application/json' } : undefined,
      signal: controller.signal,
    });
    if (!response.ok) {
      const messages: Record<number, string> = {
        404: 'No se encontró el registro solicitado.',
        409:
          path === '/sync'
            ? 'Ya hay una sincronización en curso. Esperá a que termine.'
            : 'Guardá tu perfil antes de calcular compatibilidad.',
        422: 'Revisá los campos: hay valores inválidos o demasiado largos.',
        503: 'La base de datos no está disponible. Revisá PostgreSQL e intentá de nuevo.',
      };
      throw new ApiError(
        response.status,
        messages[response.status] ?? 'No se pudo completar la operación.',
      );
    }
    return (await response.json()) as T;
  } catch (error) {
    if (error instanceof ApiError) throw error;
    throw new Error('No se pudo conectar con la API. Revisá que el backend esté iniciado.');
  } finally {
    clearTimeout(timeout);
  }
}

export const api = {
  jobs: (page = 0, filters: JobFilters = {}) => {
    const params = new URLSearchParams({
      limit: String(PAGE_SIZE),
      offset: String(page * PAGE_SIZE),
    });
    Object.entries(filters).forEach(([key, value]) => {
      if (value) params.set(key, value);
    });
    return request<Job[]>(`/jobs?${params}`);
  },
  createJob: (data: JobInput) =>
    request<Job>('/jobs', { method: 'POST', body: JSON.stringify(data) }),
  profile: async () => {
    try {
      return await request<Profile>('/profile');
    } catch (error) {
      if (error instanceof ApiError && error.status === 404) return null;
      throw error;
    }
  },
  saveProfile: (data: ProfileInput) =>
    request<Profile>('/profile', { method: 'PUT', body: JSON.stringify(data) }),
  match: (id: number) => request<MatchScore>(`/jobs/${id}/match`, { method: 'POST' }),
  sources: () => request<Source[]>('/sources'),
  updateSource: (id: number, enabled: boolean) =>
    request<Source>(`/sources/${id}`, { method: 'PATCH', body: JSON.stringify({ enabled }) }),
  syncStatus: () => request<SyncStatus>('/sync/status'),
  sync: () => request<SyncRun>('/sync', { method: 'POST' }, 180_000),
  searchPreferences: () => request<SearchPreferences>('/search-preferences'),
  saveSearchPreferences: (data: SearchPreferences) =>
    request<SearchPreferences>('/search-preferences', {
      method: 'PUT',
      body: JSON.stringify(data),
    }),
};
