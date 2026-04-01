"use client";

import { createContext, useContext, useState, useEffect, useCallback, useRef } from "react";
import type { AuthUser } from "./types";
import { getMe, socialLogin, refreshAccessToken } from "./api";
import { supabase } from "./supabase";

interface AuthContextValue {
  user: AuthUser | null;
  token: string | null;
  loading: boolean;
  setAuth: (token: string, user: AuthUser) => void;
  logout: () => void;
}

const AuthContext = createContext<AuthContextValue>({
  user: null,
  token: null,
  loading: true,
  setAuth: () => {},
  logout: () => {},
});

// 토큰 갱신 주기 (50분 — Supabase 기본 만료 60분보다 여유)
const REFRESH_INTERVAL_MS = 50 * 60 * 1000;

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<AuthUser | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const refreshTimerRef = useRef<ReturnType<typeof setInterval> | null>(null);
  // 소셜 로그인 콜백 페이지가 직접 처리 중인 세션은 중복 처리 방지
  const socialHandledRef = useRef(false);

  const setAuth = useCallback((newToken: string, newUser: AuthUser) => {
    localStorage.setItem("access_token", newToken);
    localStorage.setItem("user", JSON.stringify(newUser));
    setToken(newToken);
    setUser(newUser);
  }, []);

  const logout = useCallback(() => {
    localStorage.removeItem("access_token");
    localStorage.removeItem("refresh_token");
    localStorage.removeItem("user");
    setToken(null);
    setUser(null);
    if (refreshTimerRef.current) {
      clearInterval(refreshTimerRef.current);
      refreshTimerRef.current = null;
    }
    supabase.auth.signOut().catch(() => {});
  }, []);

  // [P1-3] 토큰 자동 갱신
  const refreshToken = useCallback(async () => {
    const savedRefreshToken = localStorage.getItem("refresh_token");
    if (!savedRefreshToken) return;

    try {
      const res = await refreshAccessToken(savedRefreshToken);
      localStorage.setItem("access_token", res.access_token);
      if (res.refresh_token) {
        localStorage.setItem("refresh_token", res.refresh_token);
      }
      setToken(res.access_token);
    } catch {
      // 갱신 실패 시 로그아웃
      logout();
    }
  }, [logout]);

  // 토큰 갱신 타이머 설정
  useEffect(() => {
    if (token) {
      // 기존 타이머 정리
      if (refreshTimerRef.current) {
        clearInterval(refreshTimerRef.current);
      }
      refreshTimerRef.current = setInterval(refreshToken, REFRESH_INTERVAL_MS);
    }
    return () => {
      if (refreshTimerRef.current) {
        clearInterval(refreshTimerRef.current);
        refreshTimerRef.current = null;
      }
    };
  }, [token, refreshToken]);

  // 초기 로드: 로컬 스토리지의 자체 JWT로 복원
  useEffect(() => {
    const savedToken = localStorage.getItem("access_token");
    if (!savedToken) {
      setLoading(false);
      return;
    }

    getMe(savedToken)
      .then((res) => {
        setToken(savedToken);
        setUser(res.user);
      })
      .catch(async () => {
        // 토큰 만료 시 갱신 시도
        const savedRefreshToken = localStorage.getItem("refresh_token");
        if (savedRefreshToken) {
          try {
            const refreshRes = await refreshAccessToken(savedRefreshToken);
            localStorage.setItem("access_token", refreshRes.access_token);
            if (refreshRes.refresh_token) {
              localStorage.setItem("refresh_token", refreshRes.refresh_token);
            }
            const meRes = await getMe(refreshRes.access_token);
            setToken(refreshRes.access_token);
            setUser(meRes.user);
            return;
          } catch {
            // 갱신도 실패하면 로그아웃
          }
        }
        localStorage.removeItem("access_token");
        localStorage.removeItem("refresh_token");
        localStorage.removeItem("user");
      })
      .finally(() => setLoading(false));
  }, []);

  // Supabase 소셜 로그인 세션 변경 감지
  useEffect(() => {
    const { data: { subscription } } = supabase.auth.onAuthStateChange(
      async (event, session) => {
        // 이미 자체 JWT로 로그인된 상태면 무시
        if (token) return;
        // /auth/callback 페이지가 직접 처리할 예정이면 무시
        if (socialHandledRef.current) return;

        if (event === "SIGNED_IN" && session) {
          const pathname = window.location.pathname;
          if (pathname === "/auth/callback") return;

          try {
            const res = await socialLogin(session.access_token, session.refresh_token ?? undefined);
            setAuth(res.access_token, res.user);
          } catch {
            // 소셜 로그인 백엔드 연동 실패는 무시
          }
        }
      }
    );

    return () => {
      subscription.unsubscribe();
    };
  }, [token, setAuth]);

  return (
    <AuthContext.Provider value={{ user, token, loading, setAuth, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  return useContext(AuthContext);
}
