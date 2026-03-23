type QueryValue = string | number | boolean | undefined | null;

export class ApiError extends Error {
  status: number;

  constructor(message: string, status: number) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}

interface RequestOptions {
  token?: string | null;
  query?: Record<string, QueryValue>;
  headers?: Record<string, string>;
  /** Override default request timeout in ms. Default 15000. Use 90000+ for long-running ops like draft generation. */
  timeoutMs?: number;
}

const DEFAULT_API_BASE_URL = "http://127.0.0.1:8000";

export function getApiBaseUrl() {
  return (process.env.NEXT_PUBLIC_API_BASE_URL || DEFAULT_API_BASE_URL).replace(/\/$/, "");
}

export function resolveApiUrl(path: string | null | undefined) {
  if (!path) {
    return "";
  }
  if (path.startsWith("http://") || path.startsWith("https://")) {
    return path;
  }
  return `${getApiBaseUrl()}${path.startsWith("/") ? path : `/${path}`}`;
}

function buildUrl(path: string, query?: Record<string, QueryValue>) {
  const url = new URL(resolveApiUrl(path));
  if (query) {
    for (const [key, value] of Object.entries(query)) {
      if (value !== undefined && value !== null && value !== "") {
        url.searchParams.set(key, String(value));
      }
    }
  }
  return url.toString();
}

async function parseResponse<T>(response: Response): Promise<T> {
  if (response.status === 204) {
    return undefined as T;
  }
  const contentType = response.headers.get("content-type") || "";
  if (!contentType.includes("application/json")) {
    if (!response.ok) {
      const text = await response.text();
      throw new ApiError(text || "Request failed", response.status);
    }
    return undefined as T;
  }

  const data = (await response.json()) as T | { detail?: string };
  if (!response.ok) {
    let message = "Request failed";
    const detail = (data as { detail?: unknown }).detail;
    if (detail !== undefined) {
      if (typeof detail === "string") {
        message = detail;
      } else if (Array.isArray(detail)) {
        message = detail
          .map((item) => {
            if (typeof item === "string") {
              return item;
            }
            if (item && typeof item === "object" && "msg" in item && typeof item.msg === "string") {
              return item.msg;
            }
            return "Request failed";
          })
          .join(", ");
      }
    }
    throw new ApiError(message, response.status);
  }
  return data as T;
}

const REQUEST_TIMEOUT_MS = 15000;

async function request<T>(
  method: string,
  path: string,
  body?: unknown,
  options?: RequestOptions,
): Promise<T> {
  const controller = new AbortController();
  const timeoutMs = options?.timeoutMs ?? REQUEST_TIMEOUT_MS;
  const timeoutId = setTimeout(() => controller.abort(), timeoutMs);

  try {
    // Only set JSON Content-Type when there is a body. Sending it on GET triggers an
    // extra CORS preflight; anonymous reads (e.g. library) can stay "simple" without it.
    const headers: Record<string, string> = {
      ...(body !== undefined ? { "Content-Type": "application/json" } : {}),
      ...(options?.token ? { Authorization: `Bearer ${options.token}` } : {}),
      ...(options?.headers ?? {}),
    };
    const response = await fetch(buildUrl(path, options?.query), {
      method,
      signal: controller.signal,
      headers,
      body: body === undefined ? undefined : JSON.stringify(body),
    });
    return await parseResponse<T>(response);
  } finally {
    clearTimeout(timeoutId);
  }
}

export function apiGet<T>(path: string, options?: RequestOptions) {
  return request<T>("GET", path, undefined, options);
}

export function apiPost<T>(path: string, body?: unknown, options?: RequestOptions) {
  return request<T>("POST", path, body, options);
}

export function apiPatch<T>(path: string, body?: unknown, options?: RequestOptions) {
  return request<T>("PATCH", path, body, options);
}

export function apiDelete<T>(path: string, options?: RequestOptions) {
  return request<T>("DELETE", path, undefined, options);
}
