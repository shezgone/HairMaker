import Link from "next/link";
import PwaInstallBanner from "@/components/PwaInstallBanner";

export default function Dashboard() {
  return (
    <main className="min-h-screen bg-zinc-950 flex flex-col">
      {/* Header */}
      <header className="border-b border-zinc-800 px-6 py-4 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <span className="text-2xl">✂</span>
          <span className="text-xl font-semibold text-white">HairMaker</span>
        </div>
        <div className="flex items-center gap-2 text-sm text-zinc-500">
          <span className="w-2 h-2 rounded-full bg-emerald-400 inline-block" />
          온라인
        </div>
      </header>

      <div className="flex-1 flex flex-col items-center justify-center gap-8 p-8">
        {/* Hero */}
        <div className="text-center space-y-3 max-w-md">
          <h1 className="text-4xl font-bold text-white">
            AI 헤어 스타일
            <span className="text-emerald-400"> 시뮬레이터</span>
          </h1>
          <p className="text-zinc-400 text-lg leading-relaxed">
            손님 얼굴 사진으로 어울리는 헤어스타일을 추천하고,
            <br />
            원하는 스타일을 직접 미리보기 합니다.
          </p>
        </div>

        {/* CTA */}
        <Link
          href="/session/new"
          className="px-10 py-5 rounded-2xl bg-emerald-500 hover:bg-emerald-400 active:bg-emerald-600 text-black font-bold text-xl transition-colors shadow-lg shadow-emerald-500/25"
        >
          새 손님 시작
        </Link>

        {/* Admin link */}
        <Link
          href="/admin/catalog"
          className="text-zinc-600 hover:text-zinc-400 text-sm transition-colors"
        >
          카탈로그 관리 →
        </Link>

        {/* Feature highlights */}
        <div className="grid grid-cols-3 gap-6 max-w-2xl mt-4">
          {[
            { icon: "🔍", title: "얼굴형 분석", desc: "AI가 정확하게 얼굴형을 분석합니다" },
            { icon: "💇", title: "스타일 추천", desc: "어울리는 스타일 12가지를 추천합니다" },
            { icon: "✨", title: "AI 미리보기", desc: "실제 얼굴에 헤어스타일을 합성합니다" },
          ].map(({ icon, title, desc }) => (
            <div key={title} className="bg-zinc-900 border border-zinc-800 rounded-2xl p-5 text-center space-y-2">
              <span className="text-3xl">{icon}</span>
              <p className="text-white font-semibold text-sm">{title}</p>
              <p className="text-zinc-500 text-xs leading-relaxed">{desc}</p>
            </div>
          ))}
        </div>
      </div>
      <PwaInstallBanner />
    </main>
  );
}
