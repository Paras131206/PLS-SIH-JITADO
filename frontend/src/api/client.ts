/**
 * API Client with in-memory JWT storage and httpOnly cookie credentials support.
 * Conforms to Phase 1 requirements:
 * 1. Token kept in memory (closure), never persisted in localStorage.
 * 2. Requests routed to MSW when VITE_USE_MOCKS !== 'false', else to real backend.
 */

let memoryJwtToken: string | null = null;

export const setAuthToken = (token: string | null) => {
  memoryJwtToken = token;
};

export const getAuthToken = (): string | null => {
  return memoryJwtToken;
};

export const clearAuthToken = () => {
  memoryJwtToken = null;
};

const getBaseUrl = (): string => {
  // If mocks are active, use relative path so MSW intercepts
  if (import.meta.env.VITE_USE_MOCKS !== 'false') {
    return '/v1';
  }
  return import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/v1';
};

export async function apiFetch<T = any>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const baseUrl = getBaseUrl();
  const cleanEndpoint = endpoint.startsWith('/') ? endpoint : `/${endpoint}`;
  const url = `${baseUrl}${cleanEndpoint}`;

  const headers = new Headers(options.headers || {});

  // Add Authorization header if in-memory token exists
  if (memoryJwtToken && !headers.has('Authorization')) {
    headers.set('Authorization', `Bearer ${memoryJwtToken}`);
  }

  // Set default JSON Content-Type unless FormData (browser sets boundary automatically)
  if (!(options.body instanceof FormData) && !headers.has('Content-Type')) {
    headers.set('Content-Type', 'application/json');
  }

  // Include credentials for httpOnly refresh cookies
  const config: RequestInit = {
    ...options,
    headers,
    credentials: 'include',
  };

  const response = await fetch(url, config);

  if (!response.ok) {
    let errorMsg = `HTTP Error ${response.status}: ${response.statusText}`;
    try {
      const errorJson = await response.json();
      if (errorJson.message) errorMsg = errorJson.message;
      else if (errorJson.detail) errorMsg = errorJson.detail;
    } catch {
      // Ignore json parse error
    }
    throw new Error(errorMsg);
  }

  // Handle 204 No Content
  if (response.status === 204) {
    return {} as T;
  }

  return response.json();
}
