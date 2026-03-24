"use client";
import { useEffect, useRef, useState } from "react";
import type { HairStyle } from "@/lib/types";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

async function fetchStyles(): Promise<HairStyle[]> {
  const r = await fetch(`${API_BASE}/api/v1/styles?limit=50`);
  const data = await r.json();
  return data.styles || [];
}

async function uploadImage(styleId: string, file: File): Promise<string> {
  const form = new FormData();
  form.append("file", file);
  const r = await fetch(`${API_BASE}/api/v1/styles/${styleId}/image`, {
    method: "POST",
    body: form,
  });
  if (!r.ok) throw new Error("업로드 실패");
  const data = await r.json();
  return data.reference_image_url;
}

function StyleRow({ style, onUpdated }: { style: HairStyle; onUpdated: (s: HairStyle) => void }) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [uploading, setUploading] = useState(false);
  const [previewUrl, setPreviewUrl] = useState(style.reference_image_url || "");

  const handleFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setUploading(true);
    try {
      const url = await uploadImage(style.id, file);
      setPreviewUrl(url);
      onUpdated({ ...style, reference_image_url: url });
    } catch {
      alert("업로드에 실패했습니다.");
    } finally {
      setUploading(false);
      if (inputRef.current) inputRef.current.value = "";
    }
  };

  const MALE_STYLE_NAMES = ["투블럭컷","리젠트컷","애즈펌","쉐도우펌","댄디컷","크롭컷","슬릭백","울프컷 (남성)","가르마컷","버즈컷","애즈펌 (남성)","투블럭 (남성)","리젠트 컷 (남성)"];
  const genderLabel = (style as HairStyle & { gender?: string }).gender || (MALE_STYLE_NAMES.includes(style.name) ? "male" : "female");

  return (
    <div className="flex items-center gap-4 p-4 rounded-2xl bg-zinc-900 border border-zinc-800">
      {/* 참고 이미지 */}
      <div
        className="w-20 h-24 rounded-xl overflow-hidden bg-zinc-800 flex-shrink-0 cursor-pointer relative group"
        onClick={() => inputRef.current?.click()}
      >
        {previewUrl ? (
          // eslint-disable-next-line @next/next/no-img-element
          <img src={previewUrl} alt={style.name} className="w-full h-full object-cover object-top" />
        ) : (
          <div className="w-full h-full flex items-center justify-center text-zinc-600 text-3xl">✂</div>
        )}
        <div className="absolute inset-0 bg-black/50 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center text-white text-xs font-medium">
          {uploading ? "업로드 중..." : "사진 변경"}
        </div>
      </div>

      {/* 스타일 정보 */}
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2">
          <span className="text-white font-semibold">{style.name}</span>
          {genderLabel && (
            <span className={`text-xs px-2 py-0.5 rounded-full ${
              genderLabel === "male" ? "bg-blue-900/60 text-blue-300" :
              genderLabel === "female" ? "bg-pink-900/60 text-pink-300" :
              "bg-zinc-700 text-zinc-400"
            }`}>
              {genderLabel === "male" ? "남성" : genderLabel === "female" ? "여성" : "공용"}
            </span>
          )}
          <span className="text-xs px-2 py-0.5 rounded-full bg-zinc-800 text-zinc-400">
            {style.hair_length}
          </span>
        </div>
        <p className="text-zinc-500 text-sm mt-0.5 truncate">{style.description}</p>
        <p className="text-zinc-600 text-xs mt-1 truncate">
          {previewUrl ? "✓ 참고 이미지 있음" : "⚠ 참고 이미지 없음"}
        </p>
      </div>

      {/* 업로드 버튼 */}
      <button
        onClick={() => inputRef.current?.click()}
        disabled={uploading}
        className="flex-shrink-0 px-4 py-2 rounded-xl bg-zinc-800 border border-zinc-600 text-zinc-300 text-sm hover:bg-zinc-700 transition-colors disabled:opacity-50"
      >
        {uploading ? "업로드 중..." : "이미지 업로드"}
      </button>

      <input
        ref={inputRef}
        type="file"
        accept="image/*"
        className="hidden"
        onChange={handleFileChange}
      />
    </div>
  );
}

export default function CatalogAdminPage() {
  const [styles, setStyles] = useState<HairStyle[]>([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState<"all" | "male" | "female" | "missing">("all");

  useEffect(() => {
    fetchStyles().then((data) => {
      setStyles(data);
      setLoading(false);
    });
  }, []);

  const handleUpdated = (updated: HairStyle) => {
    setStyles((prev) => prev.map((s) => (s.id === updated.id ? updated : s)));
  };

  // gender 컬럼이 없을 경우 스타일 이름으로 판별
  const MALE_STYLE_NAMES = ["투블럭컷","리젠트컷","애즈펌","쉐도우펌","댄디컷","크롭컷","슬릭백","울프컷 (남성)","가르마컷","버즈컷","애즈펌 (남성)","투블럭 (남성)","리젠트 컷 (남성)"];

  const getGender = (s: HairStyle) => {
    const g = (s as HairStyle & { gender?: string }).gender;
    if (g) return g;
    return MALE_STYLE_NAMES.includes(s.name) ? "male" : "female";
  };

  const filtered = styles.filter((s) => {
    const g = getGender(s);
    if (filter === "male") return g === "male";
    if (filter === "female") return g === "female" || g === "unisex";
    if (filter === "missing") return !s.reference_image_url;
    return true;
  });

  return (
    <main className="min-h-screen bg-zinc-950">
      <header className="border-b border-zinc-800 px-6 py-4 flex items-center justify-between">
        <div className="flex items-center gap-4">
          <a href="/" className="text-zinc-400 hover:text-white transition-colors text-sm">← 홈</a>
          <h1 className="text-white font-semibold">헤어스타일 카탈로그 관리</h1>
        </div>
        <span className="text-zinc-500 text-sm">{styles.length}개 스타일</span>
      </header>

      <div className="max-w-2xl mx-auto p-6 space-y-4">
        {/* 필터 */}
        <div className="flex gap-2">
          {[
            { id: "all", label: "전체" },
            { id: "female", label: "여성" },
            { id: "male", label: "남성" },
            { id: "missing", label: "이미지 없음" },
          ].map((f) => (
            <button
              key={f.id}
              onClick={() => setFilter(f.id as typeof filter)}
              className={`px-4 py-1.5 rounded-full text-sm transition-colors ${
                filter === f.id
                  ? "bg-emerald-500 text-black font-medium"
                  : "bg-zinc-800 text-zinc-400 hover:text-white"
              }`}
            >
              {f.label}
            </button>
          ))}
        </div>

        <p className="text-zinc-500 text-xs">
          이미지를 클릭하거나 "이미지 업로드" 버튼을 눌러 참고 사진을 교체할 수 있습니다.
        </p>

        {loading ? (
          <div className="py-20 text-center text-zinc-500">불러오는 중...</div>
        ) : (
          <div className="space-y-3">
            {filtered.map((style) => (
              <StyleRow key={style.id} style={style} onUpdated={handleUpdated} />
            ))}
          </div>
        )}
      </div>
    </main>
  );
}
