import { getApiKey, setApiKey } from '../lib/sessionState';
import type { ErrorResponse, ResultsResponse, ReviewRequest, ReviewResponse, RetryResponse, RunConfig, SubmitResponse, Variant } from './types';

export class ApiError extends Error {
  readonly status: number;
  readonly code: string;
  constructor(status: number, code: string, message: string) {
    super(message); this.name = 'ApiError'; this.status = status; this.code = code;
  }
}
export function errorMessage(error: unknown): string {
  return error instanceof ApiError ? error.message : 'The request could not be completed. Please try again.';
}
export function createApiClient(options: {
  key?: () => string | null; unauthorized?: () => void; fetch?: typeof fetch;
} = {}) {
  const transport = options.fetch ?? ((...args: Parameters<typeof fetch>) => fetch(...args));
  const key = options.key ?? getApiKey;
  const unauthorized = options.unauthorized ?? (() => setApiKey(null));
  function headers(extra: HeadersInit = {}) {
    const result = new Headers(extra);
    const value = key();
    if (value) result.set('X-API-Key', value);
    return result;
  }
  async function checked(url: string, init: RequestInit = {}) {
    const response = await transport(url, { ...init, headers: headers(init.headers) });
    if (!response.ok) {
      if (response.status === 401) unauthorized();
      let body: Partial<ErrorResponse> = {};
      try { body = await response.json() as Partial<ErrorResponse>; } catch { /* Safe fixed fallback. */ }
      throw new ApiError(response.status,
        typeof body.error === 'string' ? body.error : 'request_failed',
        typeof body.message === 'string' ? body.message : 'The request could not be completed.');
    }
    return response;
  }
  async function json<T>(url: string, init?: RequestInit): Promise<T> {
    return await (await checked(url, init)).json() as T;
  }
  const base = (id: string) => `/api/pipeline/${encodeURIComponent(id)}`;
  return {
    headers,
    openStream: (id: string, signal: AbortSignal, cursor?: number) => checked(`${base(id)}/stream`, {
      signal, headers: cursor === undefined ? {} : { 'Last-Event-ID': String(cursor) },
    }),
    submitRun: (text: string, config: RunConfig = {}) => json<SubmitResponse>('/api/pipeline/run', {
      method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ text, config }),
    }),
    getResults: (id: string, signal?: AbortSignal) => json<ResultsResponse>(`${base(id)}/results`, { signal }),
    review: (id: string, variant: Variant, request: ReviewRequest) => json<ReviewResponse | RetryResponse>(`${base(id)}/packages/${variant}/review`, {
      method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(request),
    }),
    download: async (id: string, variant: Variant) => {
      const response = await checked(`${base(id)}/download/${variant}`);
      return { blob: await response.blob(), filename: response.headers.get('Content-Disposition')?.match(/filename="([^"]+)"/)?.[1] ?? `infraarch-${variant}.zip` };
    },
  };
}
export const api = createApiClient();
export async function saveDownload(id: string, variant: Variant) {
  const { blob, filename } = await api.download(id, variant);
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  try {
    link.href = url; link.download = filename; document.body.append(link); link.click();
  } finally { link.remove(); URL.revokeObjectURL(url); }
}
