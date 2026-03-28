import type { PersonalColor } from "@/lib/types";

const SEASON_CONFIG = {
  spring: {
    label: "봄 웜톤",
    emoji: "🌸",
    badge: "bg-amber-500/20 border-amber-500/40 text-amber-300",
    accent: "text-amber-400",
  },
  summer: {
    label: "여름 쿨톤",
    emoji: "🌊",
    badge: "bg-sky-500/20 border-sky-500/40 text-sky-300",
    accent: "text-sky-400",
  },
  autumn: {
    label: "가을 웜톤",
    emoji: "🍂",
    badge: "bg-orange-700/20 border-orange-600/40 text-orange-300",
    accent: "text-orange-400",
  },
  winter: {
    label: "겨울 쿨톤",
    emoji: "❄️",
    badge: "bg-indigo-500/20 border-indigo-500/40 text-indigo-300",
    accent: "text-indigo-400",
  },
} as const;

interface Props {
  personalColor: PersonalColor;
}

export default function PersonalColorCard({ personalColor }: Props) {
  const config = SEASON_CONFIG[personalColor.season];

  return (
    <div className="bg-zinc-800/60 border border-zinc-700 rounded-2xl p-6 space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-xs text-zinc-500 uppercase tracking-wider mb-1">퍼스널컬러</p>
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

      <p className="text-zinc-300 text-sm leading-relaxed border-t border-zinc-700 pt-4">
        {personalColor.color_summary}
      </p>

      <div className="space-y-2">
        <p className="text-xs text-zinc-500 uppercase tracking-wider">추천 헤어컬러</p>
        <div className="flex flex-wrap gap-2">
          {personalColor.recommended_hair_colors.map((color) => (
            <div
              key={color.name}
              className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-zinc-700/50 border border-zinc-600"
            >
              <span
                className="w-3.5 h-3.5 rounded-full flex-shrink-0 border border-zinc-500"
                style={{ backgroundColor: color.hex }}
              />
              <span className="text-zinc-200 text-xs font-medium">{color.name}</span>
            </div>
          ))}
        </div>
      </div>

      {personalColor.avoid_hair_colors.length > 0 && (
        <div className="space-y-2">
          <p className="text-xs text-zinc-500 uppercase tracking-wider">피해야 할 컬러</p>
          <div className="flex flex-wrap gap-2">
            {personalColor.avoid_hair_colors.map((color) => (
              <div
                key={color.name}
                className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-zinc-800 border border-zinc-700 opacity-60"
              >
                <span
                  className="w-3.5 h-3.5 rounded-full flex-shrink-0 border border-zinc-600"
                  style={{ backgroundColor: color.hex }}
                />
                <span className="text-zinc-400 text-xs line-through">{color.name}</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
