"use client";
import { useRouter } from "next/navigation";
import { useState } from "react";
import CameraCapture from "@/components/camera/CameraCapture";
import { createSession, uploadPhoto } from "@/lib/api";
import { useAuth } from "@/lib/auth-context";

export default function NewSessionPage() {
  const router = useRouter();
  const { user } = useAuth();
  const [gender, setGender] = useState<"male" | "female" | null>(null);
  const [status, setStatus] = useState<"idle" | "uploading" | "error">("idle");
  const [error, setError] = useState<string | null>(null);

  const handleCapture = async (blob: Blob) => {
    if (!gender || !user) return;
    setStatus("uploading");
    setError(null);
    try {
      const session = await createSession(gender);
      await uploadPhoto(session.id, blob);
      router.push(`/session/${session.id}`);
    } catch (err) {
      setError(`오류: ${err instanceof Error ? err.message : "사진 업로드에 실패했습니다."}`);
      setStatus("error");
    }
  };

  return (
    <main className="min-h-screen bg-gray-50 flex flex-col">
      <header className="bg-white border-b border-gray-200 px-5 py-4 flex items-center gap-4">
        <a href="/" className="text-gray-400 hover:text-gray-700 transition-colors text-sm">
          ← 홈
        </a>
        <h1 className="text-gray-900 font-semibold">새 손님</h1>
      </header>

      <div className="flex-1 flex flex-col items-center justify-center gap-6 p-6">
        {/* Step 1: Gender selection */}
        {!gender && (
          <div className="flex flex-col items-center gap-8 w-full max-w-sm">
            <div className="text-center space-y-2">
              <h2 className="text-2xl font-bold text-gray-900">손님 성별 선택</h2>
              <p className="text-gray-500 text-sm">성별에 맞는 헤어스타일을 추천해드립니다.</p>
            </div>
            <div className="grid grid-cols-2 gap-4 w-full">
              <button
                onClick={() => setGender("female")}
                className="flex flex-col items-center gap-3 p-8 rounded-2xl border-2 border-gray-200 hover:border-violet-400 hover:bg-violet-50 transition-all active:scale-95 bg-white"
              >
                <span className="text-5xl">👩</span>
                <span className="text-gray-900 font-semibold text-lg">여성</span>
              </button>
              <button
                onClick={() => setGender("male")}
                className="flex flex-col items-center gap-3 p-8 rounded-2xl border-2 border-gray-200 hover:border-violet-400 hover:bg-violet-50 transition-all active:scale-95 bg-white"
              >
                <span className="text-5xl">👨</span>
                <span className="text-gray-900 font-semibold text-lg">남성</span>
              </button>
            </div>
          </div>
        )}

        {/* Step 2: Camera */}
        {gender && (
          <>
            <div className="text-center space-y-2 mb-2">
              <div className="flex items-center justify-center gap-2 mb-1">
                <span className="text-sm px-3 py-1 rounded-full bg-gray-100 text-gray-600">
                  {gender === "female" ? "👩 여성" : "👨 남성"}
                </span>
                <button
                  onClick={() => setGender(null)}
                  className="text-xs text-gray-400 hover:text-gray-600 transition-colors underline"
                >
                  변경
                </button>
              </div>
              <h2 className="text-2xl font-bold text-gray-900">손님 사진 촬영</h2>
              <p className="text-gray-500 text-sm">
                정면을 바라보고, 얼굴이 타원 안에 오도록 위치시켜 주세요.
              </p>
            </div>

            {status === "uploading" ? (
              <div className="flex flex-col items-center gap-4 py-12">
                <div className="w-16 h-16 rounded-full border-4 border-violet-500 border-t-transparent animate-spin" />
                <p className="text-gray-500">사진을 분석 준비 중입니다...</p>
              </div>
            ) : (
              <CameraCapture onCapture={handleCapture} />
            )}
          </>
        )}

        {error && (
          <div className="p-4 rounded-xl bg-red-50 border border-red-200 text-red-600 text-sm text-center max-w-sm">
            {error}
          </div>
        )}
      </div>
    </main>
  );
}
