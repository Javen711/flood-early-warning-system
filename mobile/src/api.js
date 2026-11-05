import { API_URL } from './config';
import { firstError } from './format';

const TIMEOUT_MS = 12000;

// Thrown for every failure, with a message that is safe to show to the user.
export class ApiError extends Error {
  constructor(message, { status = 0, errors = null } = {}) {
    super(message);
    this.status = status;
    this.errors = errors;
  }
}

async function request(url, { method = 'GET', body, token } = {}) {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), TIMEOUT_MS);
  let response;
  try {
    response = await fetch(url, {
      method,
      headers: {
        'Content-Type': 'application/json',
        Accept: 'application/json',
        ...(token ? { Authorization: `Token ${token}` } : {}),
      },
      body: body ? JSON.stringify(body) : undefined,
      signal: controller.signal,
    });
  } catch (e) {
    throw new ApiError(
      "Can't reach the server. Check that your phone and laptop are on the same Wi-Fi and that the server is running.",
    );
  } finally {
    clearTimeout(timer);
  }

  const data = response.status === 204 ? null : await response.json().catch(() => null);
  if (!response.ok) {
    const message = data?.detail || firstError(data?.errors) || `Something went wrong (${response.status}).`;
    throw new ApiError(message, { status: response.status, errors: data?.errors });
  }
  return data;
}

const at = (path) => `${API_URL}${path}`;

export const api = {
  zones: () => request(at('/zones/')),
  register: (fields) => request(at('/auth/register/'), { method: 'POST', body: fields }),
  login: (username, password) => request(at('/auth/login/'), { method: 'POST', body: { username, password } }),
  logout: (token) => request(at('/auth/logout/'), { method: 'POST', token }),
  me: (token) => request(at('/me/'), { token }),
  myZone: (token) => request(at('/my-zone/'), { token }),
  // `pageUrl` is the full "next" link from the previous page; omit it for the first page.
  alerts: (token, pageUrl) => request(pageUrl || at('/alerts/'), { token }),
  sendFeedback: (token, alertId, rating) =>
    request(at(`/alerts/${alertId}/feedback/`), { method: 'POST', token, body: { rating } }),
};
