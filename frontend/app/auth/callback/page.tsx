"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { supabase } from "@/lib/supabase";
import { socialLogin } from "@/lib/api";
import { useAuth } from "@/lib/auth-context";

export default function AuthCallbackPage() {
  const router = useRouter();
  const { setAuth } = useAuth();

  useEffect(() => {
    const handleCallback = async () => {
      const { data: { session }, error } = await supabase.auth.getSession();

      if (error || !session) {
        router.replace("/login?error=social_login_failed");
        return;
      }

      try {
        const res = await socialLogin(session.access_token, session.refresh_token ?? undefined);
        setAuth(res.access_token, res.user);
        router.replace("/");
      } catch {
        router.replace("/login?error=social_login_failed");
      }
    };

    handleCallback();
  }, [router, setAuth]);

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50">
      <div className="text-center">
        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-violet-500 mx-auto mb-4" />
        <p className="text-gray-500">로그인 처리 중...</p>
      </div>
    </div>
  );
}
