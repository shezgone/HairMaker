"use client";

import Link from "next/link";
import PwaInstallBanner from "@/components/PwaInstallBanner";
import { useAuth } from "@/lib/auth-context";

const QUICK_ACTIONS = [
  { icon: "📸", label: "새 상담", href: "/session/new" },
  { icon: "💇", label: "스타일북", href: "/admin/catalog" },
  { icon: "🔍", label: "얼굴분석", href: "/session/new" },
  { icon: "🎨", label: "컬러진단", href: "/session/new" },
  { icon: "✨", label: "AI 시뮬", href: "/session/new" },
  { icon: "📋", label: "상담기록", href: "/history" },
];

const FEATURES = [
  {
    icon: "🔍",
    title: "얼굴형 분석",
    desc: "AI가 정확하게 얼굴형을 분석합니다",
    color: "bg-violet-50 text-violet-600",
  },
  {
    icon: "💇",
    title: "스타일 추천",
    desc: "어울리는 스타일 12가지를 추천합니다",
    color: "bg-blue-50 text-blue-600",
  },
  {
    icon: "✨",
    title: "AI 미리보기",
    desc: "실제 얼굴에 헤어스타일을 합성합니다",
    color: "bg-amber-50 text-amber-600",
  },
];

export default function Dashboard() {
  const { user, logout } = useAuth();

  return (
    <main className="min-h-screen bg-gray-50 flex flex-col">
      {/* Header */}
      <header className="bg-white px-5 py-4 flex items-center justify-between shadow-sm">
        <div className="flex items-center gap-2.5">
          <div className="w-8 h-8 rounded-lg bg-violet-600 flex items-center justify-center text-white font-bold text-sm">
            H
          </div>
          <span className="text-lg font-bold text-gray-900">HairMaker</span>
        </div>
        {user && (
          <div className="flex items-center gap-2">
            <span className="text-xs text-gray-500">
              {user.salon_name}
            </span>
            <button
              onClick={logout}
              className="text-xs text-gray-400 hover:text-gray-600 transition-colors px-2.5 py-1.5 rounded-lg border border-gray-200 hover:border-gray-300"
            >
              로그아웃
            </button>
          </div>
        )}
      </header>

      <div className="flex-1 px-5 py-6 space-y-6 max-w-lg mx-auto w-full">
        {/* Welcome banner */}
        <div className="bg-gradient-to-r from-violet-600 to-violet-500 rounded-2xl p-5 text-white">
          <p className="text-sm opacity-90">안녕하세요, {user?.name || "디자이너"}님</p>
          <h1 className="text-xl font-bold mt-1">AI 헤어 스타일 시뮬레이터</h1>
          <p className="text-sm opacity-80 mt-2 leading-relaxed">
            손님 얼굴 사진으로 어울리는 헤어스타일을 추천하고 미리보기 합니다.
          </p>
          <Link
            href="/session/new"
            className="inline-block mt-4 px-6 py-2.5 rounded-xl bg-white text-violet-600 font-semibold text-sm hover:bg-violet-50 transition-colors"
          >
            새 상담 시작
          </Link>
        </div>

        {/* Quick actions grid */}
        <section>
          <h2 className="text-sm font-semibold text-gray-700 mb-3">빠른 실행</h2>
          <div className="grid grid-cols-3 gap-3">
            {QUICK_ACTIONS.map(({ icon, label, href }) => (
              <Link
                key={label}
                href={href}
                className="flex flex-col items-center gap-2 py-4 bg-white rounded-2xl border border-gray-100 hover:border-violet-200 hover:shadow-sm transition-all active:scale-95"
              >
                <span className="text-2xl">{icon}</span>
                <span className="text-xs font-medium text-gray-700">{label}</span>
              </Link>
            ))}
          </div>
        </section>

        {/* Feature highlights */}
        <section>
          <h2 className="text-sm font-semibold text-gray-700 mb-3">주요 기능</h2>
          <div className="space-y-3">
            {FEATURES.map(({ icon, title, desc, color }) => (
              <div
                key={title}
                className="flex items-center gap-4 p-4 bg-white rounded-2xl border border-gray-100"
              >
                <div className={`w-12 h-12 rounded-xl flex items-center justify-center text-xl flex-shrink-0 ${color}`}>
                  {icon}
                </div>
                <div className="min-w-0">
                  <p className="font-semibold text-gray-900 text-sm">{title}</p>
                  <p className="text-gray-500 text-xs mt-0.5 leading-relaxed">{desc}</p>
                </div>
              </div>
            ))}
          </div>
        </section>
      </div>

      <PwaInstallBanner />
    </main>
  );
}
