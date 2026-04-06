import { API_BASE_URL } from "../config";

export function apiUrl(path) {
  const p = path.startsWith("/") ? path : `/${path}`;
  return `${API_BASE_URL}${p}`;
}

/** Unauthenticated API requests (login, register, public endpoints). */
export function apiFetch(path, options = {}) {
  return fetch(apiUrl(path), {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...options.headers,
    },
  });
}
