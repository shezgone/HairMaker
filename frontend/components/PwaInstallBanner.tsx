"use client";
import { useEffect, useState } from "react";

export default function PwaInstallBanner() {
  const [show, setShow] = useState(false);
  const [isIOS, setIsIOS] = useState(false);

  useEffect(() => {
    if (window.matchMedia("(display-mode: standalone)").matches) return;
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
    <div className="fixed bottom-20 left-4 right-4 z-40 bg-white border border-gray-200 rounded-2xl p-4 shadow-lg flex items-start gap-3">
      <div className="w-10 h-10 rounded-xl bg-violet-600 flex items-center justify-center flex-shrink-0 text-white font-bold text-lg">
        H
      </div>
      <div className="flex-1 min-w-0">
        <p className="text-gray-900 text-sm font-semibold">홈 화면에 추가하기</p>
        {isIOS ? (
          <p className="text-gray-500 text-xs mt-0.5">
            Safari 하단 공유 버튼 → <strong className="text-gray-700">홈 화면에 추가</strong>
          </p>
        ) : (
          <p className="text-gray-500 text-xs mt-0.5">
            브라우저 메뉴 → <strong className="text-gray-700">앱 설치</strong> 또는 <strong className="text-gray-700">홈 화면에 추가</strong>
          </p>
        )}
        <p className="text-gray-400 text-xs mt-0.5">앱처럼 전체화면으로 실행됩니다.</p>
      </div>
      <button
        onClick={dismiss}
        className="text-gray-400 hover:text-gray-600 text-lg leading-none flex-shrink-0"
        aria-label="닫기"
      >
        ✕
      </button>
    </div>
  );
}
