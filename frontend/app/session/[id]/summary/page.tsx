"use client";
import { use, useEffect, useState } from "react";
import { getSessionSummary, selectStyle } from "@/lib/api";
import type { Session, HairStyle } from "@/lib/types";
import Link from "next/link";

interface Props {
  params: Promise<{ id: string }>;
}

interface SimulationResult {
  job_id: string;
  result_url: string;
  style_id: string;
  status: string;
}

interface Summary {
  session: Session;
  selected_style: HairStyle | null;
  simulation_results: SimulationResult[];
}

export default function SummaryPage({ params }: Props) {
  const { id: sessionId } = use(params);
  const [summary, setSummary] = useState<Summary | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getSessionSummary(sessionId)
      .then(setSummary)
      .finally(() => setLoading(false));
  }, [sessionId]);

  if (loading) {
    return (
      <main className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="w-10 h-10 rounded-full border-4 border-violet-500 border-t-transparent animate-spin" />
      </main>
    );
  }

  return (
    <main className="min-h-screen bg-gray-50 flex flex-col print:bg-white">
      <header className="bg-white border-b border-gray-200 px-5 py-4 flex items-center justify-between print:hidden">
        <Link href="/" className="text-gray-400 hover:text-gray-700 transition-colors text-sm">← 홈</Link>
        <div className="flex gap-3">
          <button
            onClick={() => window.print()}
            className="px-4 py-2 rounded-xl border border-gray-200 text-gray-600 hover:bg-gray-100 text-sm transition-colors"
          >
            인쇄 / PDF
          </button>
          <Link
            href="/session/new"
            className="px-4 py-2 rounded-xl bg-violet-600 hover:bg-violet-500 text-white font-bold text-sm transition-colors"
          >
            새 손님
          </Link>
        </div>
      </header>

      <div className="flex-1 p-6 max-w-2xl mx-auto w-full space-y-5">
        {/* Header */}
        <div className="text-center space-y-1 pb-4 border-b border-gray-200 print:border-gray-300">
          <h1 className="text-2xl font-bold text-gray-900 print:text-black">
            HairMaker 상담 결과
          </h1>
          <p className="text-gray-500 text-sm print:text-gray-600">
            {summary?.session.created_at
              ? new Date(summary.session.created_at).toLocaleDateString("ko-KR", {
                  year: "numeric", month: "long", day: "numeric"
                })
              : "날짜 정보 없음"}
          </p>
        </div>

        {/* Face analysis */}
        {summary?.session.face_analysis && (
          <section className="space-y-3">
            <h2 className="text-gray-900 font-semibold print:text-black">얼굴형 분석</h2>
            <div className="bg-white border border-gray-200 rounded-2xl p-4 print:bg-gray-50 print:border-gray-200">
              <p className="text-violet-600 font-semibold print:text-violet-700">
                {summary.session.face_analysis.face_shape} 형
              </p>
              <p className="text-gray-600 text-sm mt-2 leading-relaxed print:text-gray-700">
                {summary.session.face_analysis.consultation_summary}
              </p>
            </div>
          </section>
        )}

        {/* Selected style */}
        {summary?.selected_style && (
          <section className="space-y-3">
            <h2 className="text-gray-900 font-semibold print:text-black">결정된 스타일</h2>
            <div className="bg-white border border-violet-200 rounded-2xl p-4 print:bg-gray-50 print:border-violet-200">
              <p className="text-violet-600 font-bold text-lg print:text-violet-700">
                {summary.selected_style.name}
              </p>
              {summary.selected_style.description && (
                <p className="text-gray-500 text-sm mt-1 print:text-gray-600">
                  {summary.selected_style.description}
                </p>
              )}
            </div>
          </section>
        )}

        {/* Simulation results */}
        {summary?.simulation_results && summary.simulation_results.length > 0 && (
          <section className="space-y-3">
            <h2 className="text-gray-900 font-semibold print:text-black">시뮬레이션 결과</h2>
            <div className="grid grid-cols-2 gap-4">
              {summary.simulation_results.map((result) => (
                <div key={result.job_id} className="rounded-2xl overflow-hidden aspect-[3/4] bg-gray-100">
                  {/* eslint-disable-next-line @next/next/no-img-element */}
                  <img
                    src={result.result_url}
                    alt="시뮬레이션 결과"
                    className="w-full h-full object-cover"
                  />
                </div>
              ))}
            </div>
          </section>
        )}

        {/* Consultation notes */}
        {summary?.session.consultation_notes && (
          <section className="space-y-3">
            <h2 className="text-gray-900 font-semibold print:text-black">상담 메모</h2>
            <div className="bg-white border border-gray-200 rounded-2xl p-4 print:bg-gray-50 print:border-gray-200">
              <p className="text-gray-600 text-sm whitespace-pre-wrap leading-relaxed print:text-gray-700">
                {summary.session.consultation_notes}
              </p>
            </div>
          </section>
        )}

        {/* Footer */}
        <div className="text-center pt-6 border-t border-gray-200 text-gray-400 text-xs print:border-gray-200 print:text-gray-400">
          HairMaker — AI 헤어 스타일 시뮬레이터
        </div>
      </div>
    </main>
  );
}
