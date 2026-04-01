"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { listSessions } from "@/lib/api";
import type { Session } from "@/lib/types";

function formatDate(dateStr: string): string {
  const d = new Date(dateStr);
  const month = d.getMonth() + 1;
  const day = d.getDate();
  const hours = d.getHours().toString().padStart(2, "0");
  const minutes = d.getMinutes().toString().padStart(2, "0");
  return `${month}/${day} ${hours}:${minutes}`;
}

function StatusBadge({ status }: { status: string }) {
  const styles: Record<string, string> = {
    active: "bg-blue-50 text-blue-600 border-blue-200",
    completed: "bg-green-50 text-green-600 border-green-200",
    archived: "bg-gray-100 text-gray-500 border-gray-200",
  };
  const labels: Record<string, string> = {
    active: "진행중",
    completed: "완료",
    archived: "보관",
  };
  return (
    <span className={`text-xs px-2 py-0.5 rounded-full border ${styles[status] || styles.active}`}>
      {labels[status] || status}
    </span>
  );
}

export default function HistoryPage() {
  const [sessions, setSessions] = useState<Session[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    listSessions({ limit: 50 })
      .then((res) => setSessions(res.sessions))
      .catch((err) => setError(err instanceof Error ? err.message : "목록을 불러올 수 없습니다."))
      .finally(() => setLoading(false));
  }, []);

  return (
    <main className="min-h-screen bg-gray-50 flex flex-col">
      <header className="bg-white border-b border-gray-200 px-5 py-4 flex items-center gap-4">
        <Link href="/" className="text-gray-400 hover:text-gray-700 transition-colors text-sm">
          ← 홈
        </Link>
        <h1 className="text-gray-900 font-semibold">상담 기록</h1>
      </header>

      <div className="flex-1 px-5 py-6 max-w-lg mx-auto w-full">
        {loading && (
          <div className="flex flex-col items-center gap-4 py-16">
            <div className="w-10 h-10 rounded-full border-4 border-violet-500 border-t-transparent animate-spin" />
            <p className="text-gray-400 text-sm">불러오는 중...</p>
          </div>
        )}

        {error && (
          <div className="p-4 rounded-xl bg-red-50 border border-red-200 text-red-600 text-sm text-center">
            {error}
          </div>
        )}

        {!loading && !error && sessions.length === 0 && (
          <div className="flex flex-col items-center gap-4 py-16 text-center">
            <span className="text-5xl">📋</span>
            <p className="text-gray-500 text-sm">아직 상담 기록이 없습니다.</p>
            <Link
              href="/session/new"
              className="px-6 py-2.5 rounded-xl bg-violet-600 text-white font-semibold text-sm hover:bg-violet-500 transition-colors"
            >
              새 상담 시작
            </Link>
          </div>
        )}

        {!loading && sessions.length > 0 && (
          <div className="space-y-3">
            {sessions.map((session) => (
              <Link
                key={session.id}
                href={session.status === "completed" ? `/session/${session.id}/summary` : `/session/${session.id}`}
                className="block p-4 bg-white rounded-2xl border border-gray-100 hover:border-violet-200 hover:shadow-sm transition-all"
              >
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center gap-2">
                    <span className="text-lg">{session.gender === "male" ? "👨" : "👩"}</span>
                    <span className="text-sm font-medium text-gray-900">
                      {session.gender === "male" ? "남성" : "여성"} 손님
                    </span>
                  </div>
                  <StatusBadge status={session.status} />
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-xs text-gray-400">{formatDate(session.created_at)}</span>
                  {session.face_analysis && (
                    <span className="text-xs text-gray-500">
                      {(session.face_analysis as unknown as Record<string, string>).face_shape || "분석완료"}
                    </span>
                  )}
                </div>
              </Link>
            ))}
          </div>
        )}
      </div>
    </main>
  );
}
