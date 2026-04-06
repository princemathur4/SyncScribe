import { createContext, useCallback, useContext, useEffect, useState } from "react";
import { apiFetch } from "../api/client";

const AuthContext = createContext(null);

const TOKEN_KEY = "auth_token";

export function AuthProvider({ children }) {
  // Initialise token synchronously from localStorage so authFetch has the
  // correct token on the very first render — prevents a double-mount of the
  // editor caused by authFetch changing identity after async restoration.
  const [token, setToken] = useState(() => localStorage.getItem(TOKEN_KEY));
  const [user, setUser]   = useState(null);
  // Prevent the login screen from flashing while we validate a stored token.
  const [isInitialized, setIsInitialized] = useState(false);

  // On mount: if a token is stored, validate it via /api/auth/me and restore
  // the user object. If the token is expired/invalid, clear it.
  useEffect(() => {
    if (!token) {
      setIsInitialized(true);
      return;
    }

    apiFetch("/api/auth/me", {
      headers: { Authorization: `Bearer ${token}` },
    })
      .then((res) => (res.ok ? res.json() : null))
      .then((userData) => {
        if (userData) {
          setUser(userData);
        } else {
          localStorage.removeItem(TOKEN_KEY);
          setToken(null);
        }
      })
      .catch(() => {
        localStorage.removeItem(TOKEN_KEY);
        setToken(null);
      })
      .finally(() => setIsInitialized(true));
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  const login = (userData, accessToken) => {
    localStorage.setItem(TOKEN_KEY, accessToken);
    setToken(accessToken);
    setUser(userData);
  };

  const logout = () => {
    localStorage.removeItem(TOKEN_KEY);
    setToken(null);
    setUser(null);
  };

  const authFetch = useCallback(
    (path, options = {}) => {
      return apiFetch(path, {
        ...options,
        headers: {
          ...(token ? { Authorization: `Bearer ${token}` } : {}),
          ...options.headers,
        },
      });
    },
    [token]
  );

  return (
    <AuthContext.Provider value={{ user, token, login, logout, authFetch, isInitialized }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  return useContext(AuthContext);
}
