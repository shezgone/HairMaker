"use client";
import { useState, useEffect, useRef } from "react";
import { updateNotes } from "@/lib/api";

interface Props {
  sessionId: string;
  initialNotes?: string;
}

type SaveStatus = "saved" | "saving" | "error";

export default function NotesPanel({ sessionId, initialNotes = "" }: Props) {
  const [notes, setNotes] = useState(initialNotes);
  const [saveStatus, setSaveStatus] = useState<SaveStatus>("saved");
  const saveTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const retryCountRef = useRef(0);

  useEffect(() => {
    if (notes === initialNotes) return;
    setSaveStatus("saving");
    if (saveTimeoutRef.current) clearTimeout(saveTimeoutRef.current);
    saveTimeoutRef.current = setTimeout(async () => {
      try {
        await updateNotes(sessionId, notes);
        setSaveStatus("saved");
        retryCountRef.current = 0;
      } catch {
        setSaveStatus("error");
        retryCountRef.current += 1;
        // Auto-retry once after 5s
        if (retryCountRef.current <= 2) {
          saveTimeoutRef.current = setTimeout(async () => {
            try {
              await updateNotes(sessionId, notes);
              setSaveStatus("saved");
              retryCountRef.current = 0;
            } catch {
              setSaveStatus("error");
            }
          }, 5000);
        }
      }
    }, 2000);
  }, [notes, sessionId, initialNotes]);

  return (
    <div className="bg-zinc-800/60 border border-zinc-700 rounded-2xl p-4 space-y-3">
      <div className="flex items-center justify-between">
        <h3 className="text-white font-medium text-sm">상담 메모</h3>
        <span className={`text-xs ${
          saveStatus === "saved" ? "text-zinc-500" :
          saveStatus === "saving" ? "text-yellow-500" :
          "text-red-400"
        }`}>
          {saveStatus === "saved" && "✓ 저장됨"}
          {saveStatus === "saving" && "저장 중..."}
          {saveStatus === "error" && "⚠ 저장 실패 — 다시 입력하면 재시도"}
        </span>
      </div>
      <textarea
        value={notes}
        onChange={(e) => setNotes(e.target.value)}
        placeholder="손님과 합의한 내용을 기록해두세요... (결정된 스타일, 특별 요청사항 등)"
        className={`w-full h-32 bg-zinc-900/60 border rounded-xl p-3 text-zinc-200 text-sm placeholder-zinc-600 resize-none focus:outline-none transition-colors ${
          saveStatus === "error"
            ? "border-red-600 focus:border-red-500"
            : "border-zinc-700 focus:border-emerald-500"
        }`}
      />
    </div>
  );
}
