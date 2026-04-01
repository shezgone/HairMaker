"use client";
import { use, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { createAnalysisStream, getStyles, getSession } from "@/lib/api";
import FaceShapeCard from "@/components/analysis/FaceShapeCard";
import PersonalColorCard from "@/components/analysis/PersonalColorCard";
import StyleGrid from "@/components/styles/StyleGrid";
import NotesPanel from "@/components/consultation/NotesPanel";
import type { FaceAnalysis, HairStyle, PersonalColor, Session } from "@/lib/types";

interface Props {
  params: Promise<{ id: string }>;
}

type AnalysisState =
  | { phase: "loading" }
  | { phase: "analyzing"; chunk: string }
  | { phase: "done"; analysis: FaceAnalysis; personalColor: PersonalColor | null }
  | { phase: "error"; message: string };

export default function SessionPage({ params }: Props) {
  const { id: sessionId } = use(params);
  const router = useRouter();
  const [state, setState] = useState<AnalysisState>({ phase: "loading" });
  const [session, setSession] = useState<Session | null>(null);
  const [catalogStyles, setCatalogStyles] = useState<HairStyle[]>([]);
  const [selectedStyle, setSelectedStyle] = useState<HairStyle | null>(null);

  // 세션 정보 가져오기 + 캐시된 분석 결과 확인
  useEffect(() => {
    getSession(sessionId).then((s) => {
      setSession(s);
      // 이미 분석 완료된 세션이면 캐시된 결과를 바로 사용
      if (s.face_analysis) {
        setState({
          phase: "done",
          analysis: s.face_analysis,
          personalColor: s.personal_color ?? null,
        });
      }
    }).catch(() => {});
  }, [sessionId]);

  // 분석 완료 시 매장 카탈로그 가져오기
  useEffect(() => {
    if (state.phase === "done" && session) {
      getStyles({ gender: session.gender || "female" })
        .then((data) => setCatalogStyles(data.styles))
        .catch(() => {});
    }
  }, [state.phase, session]);

  // 분석이 아직 안 된 세션만 SSE 스트림 시작
  useEffect(() => {
    // 세션 로딩 중이거나 이미 분석 완료면 SSE 불필요
    if (session === null) return;
    if (session.face_analysis) return;

    const es = createAnalysisStream(sessionId);

    const timeout = setTimeout(() => {
      setState({ phase: "error", message: "분석 시간이 초과되었습니다. 다시 시도해주세요." });
      es.close();
    }, 90_000);

    es.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);

        if (data.error) {
          clearTimeout(timeout);
          setState({ phase: "error", message: data.error });
          es.close();
          return;
        }

        if (data.done && data.analysis) {
          clearTimeout(timeout);
          setState({
            phase: "done",
            analysis: data.analysis,
            personalColor: data.personal_color ?? null,
          });
          es.close();
          return;
        }

        if (data.chunk) {
          setState({ phase: "analyzing", chunk: data.chunk });
        }
      } catch {
        // Ignore parse errors on partial chunks
      }
    };

    es.onerror = () => {
      clearTimeout(timeout);
      setState({ phase: "error", message: "분석 중 연결이 끊어졌습니다. 다시 시도해주세요." });
      es.close();
    };

    return () => {
      clearTimeout(timeout);
      es.close();
    };
  }, [sessionId, session]);

  const handleSelectStyle = (style: HairStyle) => {
    setSelectedStyle(style);
  };

  const handlePreview = () => {
    if (!selectedStyle) return;
    router.push(`/session/${sessionId}/simulate?styleId=${selectedStyle.id}`);
  };

  return (
    <main className="min-h-screen bg-gray-50 flex flex-col">
      <header className="bg-white border-b border-gray-200 px-5 py-4 flex items-center gap-4">
        <a href="/" className="text-gray-400 hover:text-gray-700 transition-colors text-sm">← 홈</a>
        <h1 className="text-gray-900 font-semibold">얼굴형 분석 & 스타일 추천</h1>
      </header>

      <div className="flex-1 p-5 space-y-5 max-w-2xl mx-auto w-full">
        {/* Analysis section */}
        {state.phase === "loading" && (
          <div className="flex flex-col items-center gap-4 py-12 text-center">
            <div className="w-16 h-16 rounded-full border-4 border-violet-500 border-t-transparent animate-spin" />
            <p className="text-gray-500">얼굴형을 분석하고 있습니다...</p>
          </div>
        )}

        {state.phase === "analyzing" && (
          <div className="flex flex-col items-center gap-4 py-8 text-center">
            <div className="w-12 h-12 rounded-full border-3 border-violet-500 border-t-transparent animate-spin" />
            <p className="text-gray-500 text-sm">AI가 분석 중입니다...</p>
            <div className="w-64 h-1 bg-gray-200 rounded-full overflow-hidden">
              <div className="h-full bg-violet-500 animate-pulse w-2/3" />
            </div>
          </div>
        )}

        {state.phase === "error" && (
          <div className="p-6 rounded-2xl bg-red-50 border border-red-200 text-center space-y-3">
            <p className="text-red-600 font-medium">분석 오류</p>
            <p className="text-red-500 text-sm">{state.message}</p>
            <button
              onClick={() => window.location.reload()}
              className="px-4 py-2 rounded-xl bg-gray-100 text-gray-700 text-sm hover:bg-gray-200 transition-colors"
            >
              다시 시도
            </button>
          </div>
        )}

        {state.phase === "done" && (
          <>
            <FaceShapeCard analysis={state.analysis} />

            {state.personalColor && (
              <PersonalColorCard personalColor={state.personalColor} />
            )}

            <div className="space-y-3">
              <h2 className="text-gray-900 font-semibold text-lg">헤어스타일 선택</h2>
              {catalogStyles.length > 0 ? (
                <StyleGrid
                  styles={catalogStyles}
                  onSelect={handleSelectStyle}
                  selectedId={selectedStyle?.id}
                />
              ) : (
                <div className="py-8 text-center text-gray-400 text-sm">
                  스타일 카탈로그를 불러오는 중...
                </div>
              )}
            </div>

            {selectedStyle && (
              <div className="sticky bottom-20 bg-white/95 border border-gray-200 rounded-2xl p-4 flex items-center justify-between gap-4 backdrop-blur-sm shadow-lg">
                <div>
                  <p className="text-gray-400 text-xs">선택된 스타일</p>
                  <p className="text-gray-900 font-semibold">{selectedStyle.name}</p>
                </div>
                <button
                  onClick={handlePreview}
                  className="px-6 py-3 rounded-xl bg-violet-600 hover:bg-violet-500 text-white font-bold transition-colors flex-shrink-0"
                >
                  미리보기
                </button>
              </div>
            )}

            <NotesPanel sessionId={sessionId} />
          </>
        )}
      </div>
    </main>
  );
}
