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
    <div className="bg-white border border-gray-200 rounded-2xl p-4 space-y-3">
      <div className="flex items-center justify-between">
        <h3 className="text-gray-900 font-medium text-sm">상담 메모</h3>
        <span className={`text-xs ${
          saveStatus === "saved" ? "text-gray-400" :
          saveStatus === "saving" ? "text-amber-500" :
          "text-red-500"
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
        className={`w-full h-32 bg-gray-50 border rounded-xl p-3 text-gray-700 text-sm placeholder-gray-400 resize-none focus:outline-none transition-colors ${
          saveStatus === "error"
            ? "border-red-300 focus:border-red-400"
            : "border-gray-200 focus:border-violet-500"
        }`}
      />
    </div>
  );
}
