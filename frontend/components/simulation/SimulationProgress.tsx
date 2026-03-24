"use client";
import { useEffect, useState } from "react";

interface Props {
  styleName: string;
}

const MESSAGES = [
  "얼굴형을 분석하고 있어요...",
  "헤어스타일을 적용하고 있어요...",
  "자연스러운 결과를 생성하고 있어요...",
  "마무리 작업 중이에요...",
];

export default function SimulationProgress({ styleName }: Props) {
  const [messageIndex, setMessageIndex] = useState(0);

  useEffect(() => {
    const interval = setInterval(() => {
      setMessageIndex((i) => (i + 1) % MESSAGES.length);
    }, 5000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="flex flex-col items-center gap-6 py-8">
      <div className="relative w-24 h-24">
        <div className="absolute inset-0 rounded-full border-4 border-zinc-700" />
        <div className="absolute inset-0 rounded-full border-4 border-emerald-400 border-t-transparent animate-spin" />
        <div className="absolute inset-3 rounded-full bg-zinc-800 flex items-center justify-center text-2xl">
          ✂
        </div>
      </div>

      <div className="text-center space-y-2">
        <p className="text-white font-medium text-lg">{styleName}</p>
        <p className="text-zinc-400 text-sm transition-all">{MESSAGES[messageIndex]}</p>
        <p className="text-zinc-600 text-xs">약 15-30초 소요됩니다</p>
      </div>

      <div className="w-64 h-1.5 bg-zinc-800 rounded-full overflow-hidden">
        <div className="h-full bg-emerald-400 rounded-full animate-pulse w-3/4" />
      </div>
    </div>
  );
}
