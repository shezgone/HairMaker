import { createClient } from "@supabase/supabase-js";

const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL ?? "";
const supabaseAnonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY ?? "";

// 빌드 타임에는 환경 변수가 없을 수 있으므로 빈 문자열 허용
// 런타임(브라우저)에서는 반드시 환경 변수가 설정되어 있어야 함
if (typeof window !== "undefined") {
  if (!supabaseUrl) {
    console.error("[supabase] NEXT_PUBLIC_SUPABASE_URL 환경변수가 설정되지 않았습니다.");
  }
  if (!supabaseAnonKey) {
    console.error("[supabase] NEXT_PUBLIC_SUPABASE_ANON_KEY 환경변수가 설정되지 않았습니다.");
  }
}

export const supabase = createClient(
  supabaseUrl || "https://placeholder.supabase.co",
  supabaseAnonKey || "placeholder-anon-key"
);
