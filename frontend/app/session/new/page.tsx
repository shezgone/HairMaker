"use client";
import { useRouter } from "next/navigation";
import { useState } from "react";
import CameraCapture from "@/components/camera/CameraCapture";
import { createSession, uploadPhoto } from "@/lib/api";

// Demo salon/designer IDs — in production these come from auth
const DEMO_SALON_ID = "00000000-0000-0000-0000-000000000001";
const DEMO_DESIGNER_ID = "00000000-0000-0000-0000-000000000001";

export default function NewSessionPage() {
  const router = useRouter();
  const [gender, setGender] = useState<"male" | "female" | null>(null);
  const [status, setStatus] = useState<"idle" | "uploading" | "error">("idle");
  const [error, setError] = useState<string | null>(null);

  const handleCapture = async (blob: Blob) => {
    if (!gender) return;
    setStatus("uploading");
    setError(null);
    try {
      const session = await createSession(DEMO_SALON_ID, DEMO_DESIGNER_ID, gender);
      await uploadPhoto(session.id, blob);
      router.push(`/session/${session.id}`);
    } catch (err) {
      setError(`오류: ${err instanceof Error ? err.message : "사진 업로드에 실패했습니다."}`);
      setStatus("error");
    }
  };

  return (
    <main className="min-h-screen bg-zinc-950 flex flex-col">
      <header className="border-b border-zinc-800 px-6 py-4 flex items-center gap-4">
        <a href="/" className="text-zinc-400 hover:text-white transition-colors text-sm">
          ← 홈
        </a>
        <h1 className="text-white font-semibold">새 손님</h1>
      </header>

      <div className="flex-1 flex flex-col items-center justify-center gap-6 p-6">
        {/* Step 1: Gender selection */}
        {!gender && (
          <div className="flex flex-col items-center gap-8 w-full max-w-sm">
            <div className="text-center space-y-2">
              <h2 className="text-2xl font-bold text-white">손님 성별 선택</h2>
              <p className="text-zinc-400 text-sm">성별에 맞는 헤어스타일을 추천해드립니다.</p>
            </div>
            <div className="grid grid-cols-2 gap-4 w-full">
              <button
                onClick={() => setGender("female")}
                className="flex flex-col items-center gap-3 p-8 rounded-2xl border-2 border-zinc-700 hover:border-emerald-400 hover:bg-emerald-400/5 transition-all active:scale-95"
              >
                <span className="text-5xl">👩</span>
                <span className="text-white font-semibold text-lg">여성</span>
              </button>
              <button
                onClick={() => setGender("male")}
                className="flex flex-col items-center gap-3 p-8 rounded-2xl border-2 border-zinc-700 hover:border-emerald-400 hover:bg-emerald-400/5 transition-all active:scale-95"
              >
                <span className="text-5xl">👨</span>
                <span className="text-white font-semibold text-lg">남성</span>
              </button>
            </div>
          </div>
        )}

        {/* Step 2: Camera */}
        {gender && (
          <>
            <div className="text-center space-y-2 mb-2">
              <div className="flex items-center justify-center gap-2 mb-1">
                <span className="text-sm px-3 py-1 rounded-full bg-zinc-800 text-zinc-400">
                  {gender === "female" ? "👩 여성" : "👨 남성"}
                </span>
                <button
                  onClick={() => setGender(null)}
                  className="text-xs text-zinc-500 hover:text-zinc-300 transition-colors underline"
                >
                  변경
                </button>
              </div>
              <h2 className="text-2xl font-bold text-white">손님 사진 촬영</h2>
              <p className="text-zinc-400 text-sm">
                정면을 바라보고, 얼굴이 타원 안에 오도록 위치시켜 주세요.
              </p>
            </div>

            {status === "uploading" ? (
              <div className="flex flex-col items-center gap-4 py-12">
                <div className="w-16 h-16 rounded-full border-4 border-emerald-400 border-t-transparent animate-spin" />
                <p className="text-zinc-400">사진을 분석 준비 중입니다...</p>
              </div>
            ) : (
              <CameraCapture onCapture={handleCapture} />
            )}
          </>
        )}

        {error && (
          <div className="p-4 rounded-xl bg-red-900/30 border border-red-700 text-red-300 text-sm text-center max-w-sm">
            {error}
          </div>
        )}
      </div>
    </main>
  );
}
