"use client";
import { useState, useEffect, useRef } from "react";
import { updateNotes } from "@/lib/api";

interface Props {
  sessionId: string;
  initialNotes?: string;
}

export default function NotesPanel({ sessionId, initialNotes = "" }: Props) {
  const [notes, setNotes] = useState(initialNotes);
  const [saved, setSaved] = useState(true);
  const saveTimeoutRef = useRef<NodeJS.Timeout | null>(null);

  useEffect(() => {
    if (notes === initialNotes) return;
    setSaved(false);
    if (saveTimeoutRef.current) clearTimeout(saveTimeoutRef.current);
    saveTimeoutRef.current = setTimeout(async () => {
      try {
        await updateNotes(sessionId, notes);
        setSaved(true);
      } catch {
        // Will retry on next change
      }
    }, 2000);
  }, [notes, sessionId, initialNotes]);

  return (
    <div className="bg-zinc-800/60 border border-zinc-700 rounded-2xl p-4 space-y-3">
      <div className="flex items-center justify-between">
        <h3 className="text-white font-medium text-sm">상담 메모</h3>
        <span className="text-xs text-zinc-500">
          {saved ? "✓ 저장됨" : "저장 중..."}
        </span>
      </div>
      <textarea
        value={notes}
        onChange={(e) => setNotes(e.target.value)}
        placeholder="손님과 합의한 내용을 기록해두세요... (결정된 스타일, 특별 요청사항 등)"
        className="w-full h-32 bg-zinc-900/60 border border-zinc-700 rounded-xl p-3 text-zinc-200 text-sm placeholder-zinc-600 resize-none focus:outline-none focus:border-emerald-500 transition-colors"
      />
    </div>
  );
}
