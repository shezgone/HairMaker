"use client";
import type { HairStyle } from "@/lib/types";
import StyleCard from "./StyleCard";

interface Props {
  styles: HairStyle[];
  onSelect: (style: HairStyle) => void;
  selectedId?: string;
}

export default function StyleGrid({ styles, onSelect, selectedId }: Props) {
  if (styles.length === 0) {
    return (
      <div className="py-12 text-center text-gray-400">
        추천 스타일을 불러오는 중입니다...
      </div>
    );
  }

  return (
    <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
      {styles.map((style) => (
        <StyleCard
          key={style.id}
          style={style}
          isSelected={style.id === selectedId}
          onSelect={() => onSelect(style)}
        />
      ))}
    </div>
  );
}
