"use client";

import Link from "next/link";
import { useAuth } from "@/lib/auth-context";

export default function MyPage() {
  const { user, logout } = useAuth();

  return (
    <main className="min-h-screen bg-gray-50 flex flex-col">
      <header className="bg-white border-b border-gray-200 px-5 py-4 flex items-center gap-4">
        <Link href="/" className="text-gray-400 hover:text-gray-700 transition-colors text-sm">
          ← 홈
        </Link>
        <h1 className="text-gray-900 font-semibold">마이페이지</h1>
      </header>

      <div className="flex-1 px-5 py-6 max-w-lg mx-auto w-full space-y-6">
        {/* 프로필 카드 */}
        <div className="bg-white rounded-2xl border border-gray-100 p-6">
          <div className="flex items-center gap-4 mb-6">
            <div className="w-16 h-16 rounded-2xl bg-violet-100 flex items-center justify-center">
              <span className="text-2xl font-bold text-violet-600">
                {user?.name?.charAt(0) || "?"}
              </span>
            </div>
            <div>
              <h2 className="text-lg font-bold text-gray-900">{user?.name || "디자이너"}</h2>
              <p className="text-sm text-gray-500">{user?.email}</p>
            </div>
          </div>

          <div className="space-y-4">
            <div className="flex items-center justify-between py-3 border-t border-gray-100">
              <span className="text-sm text-gray-500">매장</span>
              <span className="text-sm font-medium text-gray-900">{user?.salon_name || "-"}</span>
            </div>
            <div className="flex items-center justify-between py-3 border-t border-gray-100">
              <span className="text-sm text-gray-500">역할</span>
              <span className="text-sm font-medium text-gray-900">
                {user?.role === "admin" ? "원장" : "디자이너"}
              </span>
            </div>
          </div>
        </div>

        {/* 메뉴 */}
        <div className="bg-white rounded-2xl border border-gray-100 overflow-hidden">
          <Link
            href="/admin/catalog"
            className="flex items-center justify-between px-5 py-4 hover:bg-gray-50 transition-colors border-b border-gray-100"
          >
            <div className="flex items-center gap-3">
              <span className="text-lg">💇</span>
              <span className="text-sm font-medium text-gray-900">스타일북 관리</span>
            </div>
            <span className="text-gray-300 text-sm">→</span>
          </Link>
          <Link
            href="/history"
            className="flex items-center justify-between px-5 py-4 hover:bg-gray-50 transition-colors"
          >
            <div className="flex items-center gap-3">
              <span className="text-lg">📋</span>
              <span className="text-sm font-medium text-gray-900">상담 기록</span>
            </div>
            <span className="text-gray-300 text-sm">→</span>
          </Link>
        </div>

        {/* 로그아웃 */}
        <button
          onClick={logout}
          className="w-full py-3 rounded-xl bg-white border border-gray-200 text-gray-500 hover:text-red-500 hover:border-red-200 font-medium text-sm transition-colors"
        >
          로그아웃
        </button>

        <p className="text-center text-xs text-gray-300 pt-4">
          HairMaker v1.0
        </p>
      </div>
    </main>
  );
}
