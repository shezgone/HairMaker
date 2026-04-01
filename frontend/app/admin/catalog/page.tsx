"use client";
import { useEffect, useRef, useState } from "react";
import { useAuth } from "@/lib/auth-context";
import type { HairStyle } from "@/lib/types";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

function getAuthHeaders(): Record<string, string> {
  const token = typeof window !== "undefined" ? localStorage.getItem("access_token") : null;
  if (token) return { Authorization: `Bearer ${token}` };
  return {};
}

async function fetchStyles(): Promise<HairStyle[]> {
  const r = await fetch(`${API_BASE}/api/v1/styles?limit=50`, {
    headers: { ...getAuthHeaders() },
  });
  if (!r.ok) throw new Error("스타일 목록을 불러올 수 없습니다.");
  const data = await r.json();
  return data.styles || [];
}

async function uploadImage(styleId: string, file: File, angle: "front" | "side"): Promise<string> {
  const form = new FormData();
  form.append("file", file);
  const r = await fetch(`${API_BASE}/api/v1/styles/${styleId}/image?angle=${angle}`, {
    method: "POST",
    headers: { ...getAuthHeaders() },
    body: form,
  });
  if (!r.ok) throw new Error("업로드 실패");
  const data = await r.json();
  return data.url;
}

async function createStyleApi(data: {
  name: string;
  description?: string;
  gender: string;
  hair_length?: string;
}): Promise<HairStyle> {
  const r = await fetch(`${API_BASE}/api/v1/styles`, {
    method: "POST",
    headers: { "Content-Type": "application/json", ...getAuthHeaders() },
    body: JSON.stringify(data),
  });
  if (!r.ok) {
    const err = await r.json().catch(() => ({ detail: "생성 실패" }));
    throw new Error(err.detail || "생성 실패");
  }
  return r.json();
}

async function updateStyleApi(
  styleId: string,
  data: { name?: string; description?: string; gender?: string; hair_length?: string }
): Promise<HairStyle> {
  const r = await fetch(`${API_BASE}/api/v1/styles/${styleId}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json", ...getAuthHeaders() },
    body: JSON.stringify(data),
  });
  if (!r.ok) {
    const err = await r.json().catch(() => ({ detail: "수정 실패" }));
    throw new Error(err.detail || "수정 실패");
  }
  return r.json();
}

async function deleteStyleApi(styleId: string): Promise<void> {
  const r = await fetch(`${API_BASE}/api/v1/styles/${styleId}`, {
    method: "DELETE",
    headers: { ...getAuthHeaders() },
  });
  if (!r.ok) throw new Error("삭제 실패");
}

function ImageSlot({
  label,
  url,
  uploading,
  onFileChange,
}: {
  label: string;
  url: string;
  uploading: boolean;
  onFileChange: (e: React.ChangeEvent<HTMLInputElement>) => void;
}) {
  const inputRef = useRef<HTMLInputElement>(null);
  return (
    <div className="flex flex-col items-center gap-1">
      <span className="text-gray-400 text-xs">{label}</span>
      <div
        className="w-16 h-20 rounded-xl overflow-hidden bg-gray-100 flex-shrink-0 cursor-pointer relative group"
        onClick={() => inputRef.current?.click()}
      >
        {url ? (
          // eslint-disable-next-line @next/next/no-img-element
          <img src={url} alt={label} loading="lazy" className="w-full h-full object-cover object-top" />
        ) : (
          <div className="w-full h-full flex items-center justify-center text-gray-300 text-2xl">+</div>
        )}
        <div className="absolute inset-0 bg-black/40 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center text-white text-xs font-medium">
          {uploading ? "..." : "변경"}
        </div>
      </div>
      <input
        ref={inputRef}
        type="file"
        accept="image/*"
        className="hidden"
        onChange={onFileChange}
      />
    </div>
  );
}

function StyleRow({
  style,
  onUpdated,
  onDeleted,
}: {
  style: HairStyle;
  onUpdated: (s: HairStyle) => void;
  onDeleted: (id: string) => void;
}) {
  const [uploading, setUploading] = useState<"front" | "side" | null>(null);
  const [frontUrl, setFrontUrl] = useState(style.reference_images?.[0] || style.reference_image_url || "");
  const [sideUrl, setSideUrl] = useState(style.reference_images?.[1] || "");
  const [deleting, setDeleting] = useState(false);

  // 수정 모드 상태
  const [editing, setEditing] = useState(false);
  const [editName, setEditName] = useState(style.name);
  const [editDescription, setEditDescription] = useState(style.description || "");
  const [editGender, setEditGender] = useState<string>(style.gender || "female");
  const [editHairLength, setEditHairLength] = useState<string>(style.hair_length || "medium");
  const [saving, setSaving] = useState(false);
  const [editError, setEditError] = useState("");

  const handleFileChange = (angle: "front" | "side") => async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setUploading(angle);
    try {
      const url = await uploadImage(style.id, file, angle);
      if (angle === "front") {
        setFrontUrl(url);
        onUpdated({ ...style, reference_image_url: url, reference_images: [url, sideUrl] });
      } else {
        setSideUrl(url);
        onUpdated({ ...style, reference_images: [frontUrl, url] });
      }
    } catch {
      alert("업로드에 실패했습니다.");
    } finally {
      setUploading(null);
      e.target.value = "";
    }
  };

  const handleDelete = async () => {
    if (!confirm(`"${style.name}" 스타일을 삭제하시겠습니까?`)) return;
    setDeleting(true);
    try {
      await deleteStyleApi(style.id);
      onDeleted(style.id);
    } catch {
      alert("삭제에 실패했습니다.");
      setDeleting(false);
    }
  };

  const handleEditStart = () => {
    setEditName(style.name);
    setEditDescription(style.description || "");
    setEditGender(style.gender || "female");
    setEditHairLength(style.hair_length || "medium");
    setEditError("");
    setEditing(true);
  };

  const handleEditCancel = () => {
    setEditing(false);
    setEditError("");
  };

  const handleEditSave = async () => {
    if (!editName.trim()) {
      setEditError("스타일 이름은 필수입니다.");
      return;
    }
    setSaving(true);
    setEditError("");
    try {
      const updates: Record<string, string> = {};
      if (editName.trim() !== style.name) updates.name = editName.trim();
      if ((editDescription.trim() || "") !== (style.description || "")) updates.description = editDescription.trim();
      if (editGender !== (style.gender || "female")) updates.gender = editGender;
      if (editHairLength !== (style.hair_length || "medium")) updates.hair_length = editHairLength;

      if (Object.keys(updates).length === 0) {
        setEditing(false);
        return;
      }

      const updated = await updateStyleApi(style.id, updates);
      onUpdated(updated);
      setEditing(false);
    } catch (err) {
      setEditError(err instanceof Error ? err.message : "수정에 실패했습니다.");
    } finally {
      setSaving(false);
    }
  };

  const genderLabel = style.gender || "female";
  const hasAll = !!frontUrl && !!sideUrl;
  const hasNone = !frontUrl && !sideUrl;

  // 수정 모드 UI
  if (editing) {
    return (
      <div className="p-4 rounded-2xl bg-white border border-violet-200 space-y-3">
        <div className="flex items-center justify-between">
          <span className="text-gray-900 font-semibold text-sm">스타일 수정</span>
          <button
            onClick={handleEditCancel}
            className="text-gray-400 hover:text-gray-600 transition-colors text-sm"
          >
            취소
          </button>
        </div>

        <div>
          <label className="text-gray-600 text-xs font-medium">스타일 이름 *</label>
          <input
            type="text"
            value={editName}
            onChange={(e) => setEditName(e.target.value)}
            placeholder="예: 레이어드 컷"
            className="w-full mt-1 px-4 py-2.5 rounded-xl border border-gray-200 text-gray-900 text-sm focus:outline-none focus:ring-2 focus:ring-violet-500"
            required
          />
        </div>

        <div>
          <label className="text-gray-600 text-xs font-medium">설명 (시뮬레이션 프롬프트)</label>
          <textarea
            value={editDescription}
            onChange={(e) => setEditDescription(e.target.value)}
            placeholder="이 스타일의 특징을 설명해주세요. 시뮬레이션 프롬프트로도 사용됩니다."
            rows={3}
            className="w-full mt-1 px-4 py-2.5 rounded-xl border border-gray-200 text-gray-900 text-sm focus:outline-none focus:ring-2 focus:ring-violet-500 resize-none"
          />
        </div>

        <div className="flex gap-3">
          <div className="flex-1">
            <label className="text-gray-600 text-xs font-medium">성별</label>
            <select
              value={editGender}
              onChange={(e) => setEditGender(e.target.value)}
              className="w-full mt-1 px-4 py-2.5 rounded-xl border border-gray-200 text-gray-900 text-sm focus:outline-none focus:ring-2 focus:ring-violet-500"
            >
              <option value="female">여성</option>
              <option value="male">남성</option>
              <option value="unisex">공용</option>
            </select>
          </div>
          <div className="flex-1">
            <label className="text-gray-600 text-xs font-medium">기장</label>
            <select
              value={editHairLength}
              onChange={(e) => setEditHairLength(e.target.value)}
              className="w-full mt-1 px-4 py-2.5 rounded-xl border border-gray-200 text-gray-900 text-sm focus:outline-none focus:ring-2 focus:ring-violet-500"
            >
              <option value="short">숏</option>
              <option value="medium">미디엄</option>
              <option value="long">롱</option>
            </select>
          </div>
        </div>

        {editError && <p className="text-red-500 text-xs">{editError}</p>}

        <div className="flex justify-end">
          <button
            onClick={handleEditSave}
            disabled={saving || !editName.trim()}
            className="px-6 py-2 rounded-xl bg-violet-600 hover:bg-violet-500 disabled:bg-gray-300 text-white font-semibold text-sm transition-colors"
          >
            {saving ? "저장 중..." : "저장"}
          </button>
        </div>
      </div>
    );
  }

  // 기본 표시 모드 UI
  return (
    <div className="flex items-center gap-4 p-4 rounded-2xl bg-white border border-gray-200">
      {/* 정면 / 측면 이미지 슬롯 */}
      <div className="flex gap-2 flex-shrink-0">
        <ImageSlot
          label="정면"
          url={frontUrl}
          uploading={uploading === "front"}
          onFileChange={handleFileChange("front")}
        />
        <ImageSlot
          label="측면"
          url={sideUrl}
          uploading={uploading === "side"}
          onFileChange={handleFileChange("side")}
        />
      </div>

      {/* 스타일 정보 */}
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2">
          <span className="text-gray-900 font-semibold">{style.name}</span>
          <span className={`text-xs px-2 py-0.5 rounded-full ${
            genderLabel === "male" ? "bg-blue-50 text-blue-600" :
            genderLabel === "unisex" ? "bg-gray-100 text-gray-500" :
            "bg-pink-50 text-pink-600"
          }`}>
            {genderLabel === "male" ? "남성" : genderLabel === "unisex" ? "공용" : "여성"}
          </span>
          <span className="text-xs px-2 py-0.5 rounded-full bg-gray-100 text-gray-500">
            {style.hair_length}
          </span>
        </div>
        <p className="text-gray-500 text-sm mt-0.5 truncate">{style.description}</p>
        <p className={`text-xs mt-1 ${hasAll ? "text-green-600" : hasNone ? "text-red-500" : "text-amber-500"}`}>
          {hasAll ? "정면 + 측면 완료" : hasNone ? "이미지 없음" : "이미지 1장 누락"}
        </p>
      </div>

      {/* 수정 / 삭제 버튼 */}
      <div className="flex flex-col gap-1 flex-shrink-0">
        <button
          onClick={handleEditStart}
          className="text-gray-400 hover:text-violet-600 transition-colors text-sm p-2"
          title="스타일 수정"
        >
          수정
        </button>
        <button
          onClick={handleDelete}
          disabled={deleting}
          className="text-gray-300 hover:text-red-500 transition-colors text-sm p-2"
          title="스타일 삭제"
        >
          {deleting ? "..." : "삭제"}
        </button>
      </div>
    </div>
  );
}

function CreateStyleModal({
  onCreated,
  onClose,
}: {
  onCreated: (s: HairStyle) => void;
  onClose: () => void;
}) {
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [gender, setGender] = useState("female");
  const [hairLength, setHairLength] = useState("medium");
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!name.trim()) return;
    setSaving(true);
    setError("");
    try {
      const created = await createStyleApi({
        name: name.trim(),
        description: description.trim() || undefined,
        gender,
        hair_length: hairLength,
      });
      onCreated(created);
      onClose();
    } catch (err) {
      setError(err instanceof Error ? err.message : "생성에 실패했습니다.");
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm p-4">
      <form
        onSubmit={handleSubmit}
        className="bg-white rounded-2xl p-6 w-full max-w-md space-y-4 shadow-xl"
      >
        <h2 className="text-gray-900 font-semibold text-lg">새 스타일 추가</h2>

        <div>
          <label className="text-gray-600 text-sm font-medium">스타일 이름 *</label>
          <input
            type="text"
            value={name}
            onChange={(e) => setName(e.target.value)}
            placeholder="예: 레이어드 컷"
            className="w-full mt-1 px-4 py-2.5 rounded-xl border border-gray-200 text-gray-900 focus:outline-none focus:ring-2 focus:ring-violet-500"
            required
          />
        </div>

        <div>
          <label className="text-gray-600 text-sm font-medium">설명</label>
          <input
            type="text"
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            placeholder="스타일에 대한 간단한 설명"
            className="w-full mt-1 px-4 py-2.5 rounded-xl border border-gray-200 text-gray-900 focus:outline-none focus:ring-2 focus:ring-violet-500"
          />
        </div>

        <div className="flex gap-4">
          <div className="flex-1">
            <label className="text-gray-600 text-sm font-medium">성별</label>
            <select
              value={gender}
              onChange={(e) => setGender(e.target.value)}
              className="w-full mt-1 px-4 py-2.5 rounded-xl border border-gray-200 text-gray-900 focus:outline-none focus:ring-2 focus:ring-violet-500"
            >
              <option value="female">여성</option>
              <option value="male">남성</option>
              <option value="unisex">공용</option>
            </select>
          </div>
          <div className="flex-1">
            <label className="text-gray-600 text-sm font-medium">기장</label>
            <select
              value={hairLength}
              onChange={(e) => setHairLength(e.target.value)}
              className="w-full mt-1 px-4 py-2.5 rounded-xl border border-gray-200 text-gray-900 focus:outline-none focus:ring-2 focus:ring-violet-500"
            >
              <option value="short">숏</option>
              <option value="medium">미디엄</option>
              <option value="long">롱</option>
            </select>
          </div>
        </div>

        {error && <p className="text-red-500 text-sm">{error}</p>}

        <div className="flex gap-3 pt-2">
          <button
            type="button"
            onClick={onClose}
            className="flex-1 py-2.5 rounded-xl border border-gray-200 text-gray-600 hover:bg-gray-50 transition-colors text-sm font-medium"
          >
            취소
          </button>
          <button
            type="submit"
            disabled={saving || !name.trim()}
            className="flex-1 py-2.5 rounded-xl bg-violet-600 hover:bg-violet-500 disabled:bg-gray-300 text-white font-bold transition-colors text-sm"
          >
            {saving ? "생성 중..." : "추가"}
          </button>
        </div>
      </form>
    </div>
  );
}

export default function CatalogAdminPage() {
  const { user, loading: authLoading } = useAuth();
  const [styles, setStyles] = useState<HairStyle[]>([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState<"all" | "male" | "female" | "missing">("all");
  const [showCreate, setShowCreate] = useState(false);

  useEffect(() => {
    if (authLoading) return;
    if (!user) {
      setLoading(false);
      return;
    }
    fetchStyles()
      .then((data) => {
        setStyles(data);
        setLoading(false);
      })
      .catch(() => setLoading(false));
  }, [user, authLoading]);

  const handleUpdated = (updated: HairStyle) => {
    setStyles((prev) => prev.map((s) => (s.id === updated.id ? updated : s)));
  };

  const handleDeleted = (id: string) => {
    setStyles((prev) => prev.filter((s) => s.id !== id));
  };

  const handleCreated = (created: HairStyle) => {
    setStyles((prev) => [created, ...prev]);
  };

  const filtered = styles.filter((s) => {
    const g = s.gender || "female";
    if (filter === "male") return g === "male";
    if (filter === "female") return g === "female" || g === "unisex";
    if (filter === "missing") return !s.reference_image_url && !(s.reference_images?.length);
    return true;
  });

  if (!authLoading && !user) {
    return (
      <main className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center space-y-4">
          <p className="text-gray-500">카탈로그 관리는 로그인이 필요합니다.</p>
          <a href="/login" className="text-violet-600 font-medium hover:underline">로그인하기</a>
        </div>
      </main>
    );
  }

  return (
    <main className="min-h-screen bg-gray-50">
      <header className="bg-white border-b border-gray-200 px-5 py-4 flex items-center justify-between">
        <div className="flex items-center gap-4">
          <a href="/" className="text-gray-400 hover:text-gray-700 transition-colors text-sm">← 홈</a>
          <h1 className="text-gray-900 font-semibold">헤어스타일 카탈로그 관리</h1>
        </div>
        <div className="flex items-center gap-3">
          <span className="text-gray-400 text-sm">{styles.length}개 스타일</span>
          <button
            onClick={() => setShowCreate(true)}
            className="px-4 py-1.5 rounded-full bg-violet-600 text-white text-sm font-medium hover:bg-violet-500 transition-colors"
          >
            + 새 스타일
          </button>
        </div>
      </header>

      <div className="max-w-2xl mx-auto p-5 space-y-4">
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
                  ? "bg-violet-600 text-white font-medium"
                  : "bg-white border border-gray-200 text-gray-500 hover:text-gray-700"
              }`}
            >
              {f.label}
            </button>
          ))}
        </div>

        <p className="text-gray-400 text-xs">
          이미지를 클릭하면 참고 사진을 교체할 수 있습니다. 매장별로 독립적인 카탈로그가 관리됩니다.
        </p>

        {loading ? (
          <div className="py-20 text-center text-gray-400">불러오는 중...</div>
        ) : (
          <div className="space-y-3">
            {filtered.length === 0 ? (
              <div className="py-12 text-center text-gray-400 space-y-2">
                <p>등록된 스타일이 없습니다.</p>
                <button
                  onClick={() => setShowCreate(true)}
                  className="text-violet-600 font-medium hover:underline"
                >
                  첫 스타일을 추가해보세요
                </button>
              </div>
            ) : (
              filtered.map((style) => (
                <StyleRow
                  key={style.id}
                  style={style}
                  onUpdated={handleUpdated}
                  onDeleted={handleDeleted}
                />
              ))
            )}
          </div>
        )}
      </div>

      {showCreate && (
        <CreateStyleModal
          onCreated={handleCreated}
          onClose={() => setShowCreate(false)}
        />
      )}
    </main>
  );
}
