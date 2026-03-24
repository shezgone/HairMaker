"use client";
import { use, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { createAnalysisStream } from "@/lib/api";
import FaceShapeCard from "@/components/analysis/FaceShapeCard";
import StyleGrid from "@/components/styles/StyleGrid";
import NotesPanel from "@/components/consultation/NotesPanel";
import type { FaceAnalysis, HairStyle } from "@/lib/types";

interface Props {
  params: Promise<{ id: string }>;
}

type AnalysisState =
  | { phase: "loading" }
  | { phase: "analyzing"; chunk: string }
  | { phase: "done"; analysis: FaceAnalysis; styles: HairStyle[] }
  | { phase: "error"; message: string };

export default function SessionPage({ params }: Props) {
  const { id: sessionId } = use(params);
  const router = useRouter();
  const [state, setState] = useState<AnalysisState>({ phase: "loading" });
  const [selectedStyle, setSelectedStyle] = useState<HairStyle | null>(null);

  useEffect(() => {
    const es = createAnalysisStream(sessionId);

    es.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);

        if (data.error) {
          setState({ phase: "error", message: data.error });
          es.close();
          return;
        }

        if (data.done && data.analysis) {
          setState({ phase: "done", analysis: data.analysis, styles: data.styles || [] });
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
      setState({ phase: "error", message: "분석 중 오류가 발생했습니다." });
      es.close();
    };

    return () => es.close();
  }, [sessionId]);

  const handleSelectStyle = (style: HairStyle) => {
    setSelectedStyle(style);
  };

  const handlePreview = () => {
    if (!selectedStyle) return;
    router.push(`/session/${sessionId}/simulate?styleId=${selectedStyle.id}`);
  };

  return (
    <main className="min-h-screen bg-zinc-950 flex flex-col">
      <header className="border-b border-zinc-800 px-6 py-4 flex items-center gap-4">
        <a href="/" className="text-zinc-400 hover:text-white transition-colors text-sm">← 홈</a>
        <h1 className="text-white font-semibold">얼굴형 분석 & 스타일 추천</h1>
      </header>

      <div className="flex-1 p-6 space-y-6 max-w-2xl mx-auto w-full">
        {/* Analysis section */}
        {state.phase === "loading" && (
          <div className="flex flex-col items-center gap-4 py-12 text-center">
            <div className="w-16 h-16 rounded-full border-4 border-emerald-400 border-t-transparent animate-spin" />
            <p className="text-zinc-400">얼굴형을 분석하고 있습니다...</p>
          </div>
        )}

        {state.phase === "analyzing" && (
          <div className="flex flex-col items-center gap-4 py-8 text-center">
            <div className="w-12 h-12 rounded-full border-3 border-emerald-400 border-t-transparent animate-spin" />
            <p className="text-zinc-400 text-sm">AI가 분석 중입니다...</p>
            <div className="w-64 h-1 bg-zinc-800 rounded-full overflow-hidden">
              <div className="h-full bg-emerald-400 animate-pulse w-2/3" />
            </div>
          </div>
        )}

        {state.phase === "error" && (
          <div className="p-6 rounded-2xl bg-red-900/30 border border-red-700 text-center space-y-3">
            <p className="text-red-300 font-medium">분석 오류</p>
            <p className="text-red-400 text-sm">{state.message}</p>
            <button
              onClick={() => window.location.reload()}
              className="px-4 py-2 rounded-xl bg-zinc-800 text-zinc-300 text-sm hover:bg-zinc-700 transition-colors"
            >
              다시 시도
            </button>
          </div>
        )}

        {state.phase === "done" && (
          <>
            <FaceShapeCard analysis={state.analysis} />

            <div className="space-y-3">
              <h2 className="text-white font-semibold text-lg">추천 헤어스타일</h2>
              <StyleGrid
                styles={state.styles}
                onSelect={handleSelectStyle}
                selectedId={selectedStyle?.id}
              />
            </div>

            {selectedStyle && (
              <div className="sticky bottom-6 bg-zinc-900/95 border border-zinc-700 rounded-2xl p-4 flex items-center justify-between gap-4 backdrop-blur-sm shadow-xl">
                <div>
                  <p className="text-zinc-400 text-xs">선택된 스타일</p>
                  <p className="text-white font-semibold">{selectedStyle.name}</p>
                </div>
                <button
                  onClick={handlePreview}
                  className="px-6 py-3 rounded-xl bg-emerald-500 hover:bg-emerald-400 text-black font-bold transition-colors flex-shrink-0"
                >
                  미리보기 ✨
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
