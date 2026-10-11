export interface Identity {
  id: string;
  email: string;
  display_name: string;
  workspace_ids: string[];
  workspaces?: { id: string; name: string; demo_mode: boolean }[];
  csrf_token: string;
  authentication_method?: 'password' | 'mfa';
}
export interface Grant {
  function_code: string;
  product_scope: string;
  market_scope: string;
}
export interface Challenge { challenge_id: string; method: 'totp' | 'email'; expires_in: number }

export class ApiError extends Error {
  constructor(public status: number, message: string, public traceId?: string) {
    super(message);
  }
}

export async function api<T>(path: string, options: RequestInit & { timeoutMs?: number } = {}): Promise<T> {
  const { timeoutMs = 15000, ...init } = options;
  let response: Response;
  try {
    response = await fetch(`/api/v1${path}`, {
      ...init, credentials: 'same-origin', cache: 'no-store',
      headers: { ...(init.body ? { 'Content-Type': 'application/json' } : {}), ...init.headers },
      signal: init.signal
        ? AbortSignal.any([init.signal, AbortSignal.timeout(timeoutMs)])
        : AbortSignal.timeout(timeoutMs),
    });
  } catch (error) {
    if (error instanceof DOMException && error.name === 'AbortError') throw error;
    throw new ApiError(0, 'Cannot reach the API. Check that the API server is running, then try again.');
  }
  if (!response.ok) {
    const body = await response.json().catch(() => null);
    throw new ApiError(response.status,
      body?.error?.message ?? 'The request could not be completed. Please try again.',
      body?.error?.trace_id);
  }
  return response.status === 204 ? undefined as T : response.json() as Promise<T>;
}
