import type { PersonalColor } from "@/lib/types";

const SEASON_CONFIG = {
  spring: {
    label: "봄 웜톤",
    emoji: "🌸",
    badge: "bg-amber-50 border-amber-200 text-amber-700",
    accent: "text-amber-600",
  },
  summer: {
    label: "여름 쿨톤",
    emoji: "🌊",
    badge: "bg-sky-50 border-sky-200 text-sky-700",
    accent: "text-sky-600",
  },
  autumn: {
    label: "가을 웜톤",
    emoji: "🍂",
    badge: "bg-orange-50 border-orange-200 text-orange-700",
    accent: "text-orange-600",
  },
  winter: {
    label: "겨울 쿨톤",
    emoji: "❄️",
    badge: "bg-indigo-50 border-indigo-200 text-indigo-700",
    accent: "text-indigo-600",
  },
} as const;

interface Props {
  personalColor: PersonalColor;
}

export default function PersonalColorCard({ personalColor }: Props) {
  const config = SEASON_CONFIG[personalColor.season];

  return (
    <div className="bg-white border border-gray-200 rounded-2xl p-6 space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-xs text-gray-400 uppercase tracking-wider mb-1">퍼스널컬러</p>
          <div className="flex items-center gap-2">
            <span className="text-2xl">{config.emoji}</span>
            <p className={`text-2xl font-semibold ${config.accent}`}>{config.label}</p>
          </div>
        </div>
        <span
          className={`px-3 py-1.5 rounded-full border text-sm font-medium ${config.badge}`}
        >
          {personalColor.tone === "warm" ? "웜톤" : "쿨톤"}
        </span>
      </div>

      <p className="text-gray-600 text-sm leading-relaxed border-t border-gray-100 pt-4">
        {personalColor.color_summary}
      </p>

      <div className="space-y-2">
        <p className="text-xs text-gray-400 uppercase tracking-wider">추천 헤어컬러</p>
        <div className="flex flex-wrap gap-2">
          {personalColor.recommended_hair_colors.map((color) => (
            <div
              key={color.name}
              className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-gray-50 border border-gray-200"
            >
              <span
                className="w-3.5 h-3.5 rounded-full flex-shrink-0 border border-gray-300"
                style={{ backgroundColor: color.hex }}
              />
              <span className="text-gray-700 text-xs font-medium">{color.name}</span>
            </div>
          ))}
        </div>
      </div>

      {personalColor.avoid_hair_colors.length > 0 && (
        <div className="space-y-2">
          <p className="text-xs text-gray-400 uppercase tracking-wider">피해야 할 컬러</p>
          <div className="flex flex-wrap gap-2">
            {personalColor.avoid_hair_colors.map((color) => (
              <div
                key={color.name}
                className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-gray-50 border border-gray-200 opacity-60"
              >
                <span
                  className="w-3.5 h-3.5 rounded-full flex-shrink-0 border border-gray-300"
                  style={{ backgroundColor: color.hex }}
                />
                <span className="text-gray-400 text-xs line-through">{color.name}</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
