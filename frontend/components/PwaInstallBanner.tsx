"use client";
import { useEffect, useState } from "react";

export default function PwaInstallBanner() {
  const [show, setShow] = useState(false);
  const [isIOS, setIsIOS] = useState(false);

  useEffect(() => {
    // 이미 설치된 경우 (standalone 모드) 숨김
    if (window.matchMedia("(display-mode: standalone)").matches) return;
    // 이미 닫은 경우 숨김
    if (localStorage.getItem("pwa-banner-dismissed")) return;

    const ios = /iphone|ipad|ipod/i.test(navigator.userAgent);
    setIsIOS(ios);
    setShow(true);
  }, []);

  if (!show) return null;

  const dismiss = () => {
    localStorage.setItem("pwa-banner-dismissed", "1");
    setShow(false);
  };

  return (
    <div className="fixed bottom-4 left-4 right-4 z-50 bg-zinc-800 border border-zinc-600 rounded-2xl p-4 shadow-xl flex items-start gap-3">
      <div className="w-10 h-10 rounded-xl bg-emerald-500 flex items-center justify-center flex-shrink-0 text-black font-bold text-lg">
        H
      </div>
      <div className="flex-1 min-w-0">
        <p className="text-white text-sm font-semibold">홈 화면에 추가하기</p>
        {isIOS ? (
          <p className="text-zinc-400 text-xs mt-0.5">
            Safari 하단 공유 버튼 → <strong className="text-zinc-300">홈 화면에 추가</strong>
          </p>
        ) : (
          <p className="text-zinc-400 text-xs mt-0.5">
            브라우저 메뉴 → <strong className="text-zinc-300">앱 설치</strong> 또는 <strong className="text-zinc-300">홈 화면에 추가</strong>
          </p>
        )}
        <p className="text-zinc-500 text-xs mt-0.5">앱처럼 전체화면으로 실행됩니다.</p>
      </div>
      <button
        onClick={dismiss}
        className="text-zinc-500 hover:text-zinc-300 text-lg leading-none flex-shrink-0"
        aria-label="닫기"
      >
        ✕
      </button>
    </div>
  );
}
