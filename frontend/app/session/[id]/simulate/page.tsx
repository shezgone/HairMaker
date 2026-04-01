"use client";
import { use, useEffect, useState } from "react";
import { useSearchParams, useRouter } from "next/navigation";
import { getSession, getStyle, getPhotoSignedUrl } from "@/lib/api";
import { useSimulation } from "@/lib/hooks/useSimulation";
import SimulationProgress from "@/components/simulation/SimulationProgress";
import SimulationResult from "@/components/simulation/SimulationResult";
import type { Session, HairStyle } from "@/lib/types";

interface Props {
  params: Promise<{ id: string }>;
}

const MODELS = [
  {
    id: "flux" as const,
    name: "FLUX Kontext Pro",
    desc: "빠른 합성 · 15~25초",
    badge: "빠름",
  },
  {
    id: "flux-max" as const,
    name: "FLUX Kontext Max",
    desc: "얼굴 보존 최고 수준 · 25~40초",
    badge: "고품질",
  },
];

export default function SimulatePage({ params }: Props) {
  const { id: sessionId } = use(params);
  const searchParams = useSearchParams();
  const router = useRouter();
  const styleId = searchParams.get("styleId") || "";

  const [session, setSession] = useState<Session | null>(null);
  const [style, setStyle] = useState<HairStyle | null>(null);
  const [jobId, setJobId] = useState<string | null>(null);
  const [originalSignedUrl, setOriginalSignedUrl] = useState<string | null>(null);
  const [selectedModel, setSelectedModel] = useState<"flux" | "flux-max" | null>(null);
  const { jobs, simulate } = useSimulation(sessionId);

  useEffect(() => {
    if (!styleId) return;
    Promise.all([getSession(sessionId), getStyle(styleId), getPhotoSignedUrl(sessionId)]).then(([s, st, photoData]) => {
      setSession(s);
      setStyle(st);
      setOriginalSignedUrl(photoData.signed_url);
    });
  }, [sessionId, styleId]);

  const handleStartSimulation = async (model: "flux" | "flux-max") => {
    setSelectedModel(model);
    const id = await simulate(styleId, model);
    setJobId(id);
  };

  const job = jobId ? jobs.get(jobId) : null;

  return (
    <main className="min-h-screen bg-gray-50 flex flex-col">
      <header className="bg-white border-b border-gray-200 px-5 py-4 flex items-center gap-4">
        <button
          onClick={() => router.back()}
          className="text-gray-400 hover:text-gray-700 transition-colors text-sm"
        >
          ← 뒤로
        </button>
        <h1 className="text-gray-900 font-semibold">헤어 시뮬레이션</h1>
        {style && <span className="text-gray-400 text-sm">— {style.name}</span>}
      </header>

      <div className="flex-1 flex flex-col items-center justify-center p-6 max-w-lg mx-auto w-full space-y-6">

        {/* 모델 선택 (시작 전) */}
        {!selectedModel && style && (
          <div className="w-full space-y-4">
            <div className="text-center space-y-1">
              <h2 className="text-gray-900 font-semibold text-lg">AI 모델 선택</h2>
              <p className="text-gray-500 text-sm">시뮬레이션에 사용할 AI를 선택해주세요.</p>
            </div>
            <div className="space-y-3">
              {MODELS.map((m) => (
                <button
                  key={m.id}
                  onClick={() => handleStartSimulation(m.id)}
                  className="w-full flex items-center gap-4 p-4 rounded-2xl bg-white border border-gray-200 hover:border-violet-400 hover:bg-violet-50 transition-all active:scale-95 text-left"
                >
                  <div className="flex-1">
                    <div className="flex items-center gap-2">
                      <span className="text-gray-900 font-semibold">{m.name}</span>
                      <span className="text-xs px-2 py-0.5 rounded-full bg-violet-100 text-violet-600">{m.badge}</span>
                    </div>
                    <p className="text-gray-500 text-sm mt-0.5">{m.desc}</p>
                  </div>
                  <span className="text-gray-300 text-lg">→</span>
                </button>
              ))}
            </div>
          </div>
        )}

        {/* 진행 중 */}
        {selectedModel && (!job || job.status === "pending" || job.status === "processing") && style && (
          <SimulationProgress styleName={style.name} />
        )}

        {/* 완료 */}
        {job?.status === "done" && job.result_url && originalSignedUrl && style && (
          <>
            <SimulationResult
              originalUrl={originalSignedUrl}
              resultUrl={job.result_url}
              styleName={style.name}
            />

            <div className="flex gap-4 w-full">
              <button
                onClick={() => router.back()}
                className="flex-1 py-3 rounded-xl border border-gray-200 text-gray-600 hover:bg-gray-100 transition-colors text-sm font-medium"
              >
                다른 스타일 보기
              </button>
              <button
                onClick={() => router.push(`/session/${sessionId}/summary`)}
                className="flex-1 py-3 rounded-xl bg-violet-600 hover:bg-violet-500 text-white font-bold transition-colors text-sm"
              >
                이 스타일로 결정
              </button>
            </div>
          </>
        )}

        {/* 오류 */}
        {job?.status === "error" && (
          <div className="p-6 rounded-2xl bg-red-50 border border-red-200 text-center space-y-4">
            <p className="text-red-600 font-medium text-lg">시뮬레이션 실패</p>
            <p className="text-red-500 text-sm">{job.error || "알 수 없는 오류가 발생했습니다."}</p>
            <p className="text-gray-400 text-xs">AI 모델의 일시적 오류일 수 있습니다. 다시 시도하면 대부분 해결됩니다.</p>
            <div className="flex gap-3 justify-center">
              <button
                onClick={() => { setJobId(null); setSelectedModel(null); }}
                className="px-5 py-2.5 rounded-xl bg-gray-100 text-gray-700 text-sm hover:bg-gray-200 transition-colors font-medium"
              >
                다른 모델로 시도
              </button>
              {selectedModel && (
                <button
                  onClick={() => { setJobId(null); handleStartSimulation(selectedModel); }}
                  className="px-5 py-2.5 rounded-xl bg-violet-600 text-white text-sm hover:bg-violet-500 transition-colors font-medium"
                >
                  같은 모델로 재시도
                </button>
              )}
            </div>
          </div>
        )}
      </div>
    </main>
  );
}
