"use client";
import { useState } from "react";

interface Props {
  originalUrl: string;
  resultUrl: string;
  styleName: string;
}

export default function SimulationResult({ originalUrl, resultUrl, styleName }: Props) {
  const [showOriginal, setShowOriginal] = useState(false);

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="text-gray-900 font-semibold text-lg">{styleName} 시뮬레이션</h3>
        <button
          onPointerDown={() => setShowOriginal(true)}
          onPointerUp={() => setShowOriginal(false)}
          onPointerLeave={() => setShowOriginal(false)}
          className="px-4 py-2 rounded-xl bg-gray-100 border border-gray-200 text-gray-600 text-sm hover:bg-gray-200 active:bg-gray-300 transition-colors select-none"
        >
          {showOriginal ? "원본 보기 중..." : "원본 비교 (꾹 누르기)"}
        </button>
      </div>

      <div className="relative rounded-2xl overflow-hidden shadow-lg aspect-[3/4] max-w-sm mx-auto">
        {/* eslint-disable-next-line @next/next/no-img-element */}
        <img
          src={resultUrl}
          alt="시뮬레이션 결과"
          className={`absolute inset-0 w-full h-full object-cover object-top transition-opacity duration-200 ${
            showOriginal ? "opacity-0" : "opacity-100"
          }`}
        />
        {/* eslint-disable-next-line @next/next/no-img-element */}
        <img
          src={originalUrl}
          alt="원본"
          className={`absolute inset-0 w-full h-full object-cover object-top transition-opacity duration-200 ${
            showOriginal ? "opacity-100" : "opacity-0"
          }`}
        />
        <div
          className={`absolute top-3 left-3 px-3 py-1 rounded-full text-xs font-medium transition-colors ${
            showOriginal
              ? "bg-gray-800/80 text-white"
              : "bg-violet-600/90 text-white"
          }`}
        >
          {showOriginal ? "원본" : "시뮬레이션"}
        </div>
      </div>
    </div>
  );
}
