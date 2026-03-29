"use client";
import type { HairStyle } from "@/lib/types";

const MAINTENANCE_LABELS = ["", "쉬움", "보통", "약간 번거로움", "번거로움", "전문 관리 필요"];

interface Props {
  style: HairStyle;
  isSelected: boolean;
  onSelect: () => void;
}

export default function StyleCard({ style, isSelected, onSelect }: Props) {
  return (
    <button
      onClick={onSelect}
      className={`relative rounded-2xl overflow-hidden text-left transition-all active:scale-95 ${
        isSelected
          ? "ring-2 ring-emerald-400 shadow-lg shadow-emerald-400/20"
          : "ring-1 ring-zinc-700 hover:ring-zinc-500"
      }`}
    >
      <div className="aspect-[3/4] bg-zinc-800">
        {style.reference_image_url ? (
          // eslint-disable-next-line @next/next/no-img-element
          <img
            src={style.reference_image_url}
            alt={style.name}
            loading="lazy"
            className="w-full h-full object-cover"
          />
        ) : (
          <div className="w-full h-full flex items-center justify-center text-zinc-600 text-5xl">
            ✂
          </div>
        )}
      </div>

      {isSelected && (
        <div className="absolute top-3 right-3 w-7 h-7 rounded-full bg-emerald-400 flex items-center justify-center text-black text-sm font-bold">
          ✓
        </div>
      )}

      <div className="p-3 bg-zinc-900">
        <p className="font-semibold text-white text-sm truncate">{style.name}</p>
        <div className="flex items-center justify-between mt-1">
          <span className="text-xs text-zinc-500 capitalize">{style.hair_length}</span>
          <span className="text-xs text-zinc-400">
            관리 {MAINTENANCE_LABELS[style.maintenance_level] || style.maintenance_level}
          </span>
        </div>
      </div>
    </button>
  );
}
