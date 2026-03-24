import type { FaceAnalysis } from "@/lib/types";

const FACE_SHAPE_LABELS: Record<string, string> = {
  oval: "계란형",
  round: "둥근형",
  square: "각진형",
  heart: "하트형",
  diamond: "다이아몬드형",
  oblong: "긴형",
  triangle: "삼각형",
};

interface Props {
  analysis: FaceAnalysis;
}

export default function FaceShapeCard({ analysis }: Props) {
  const label = FACE_SHAPE_LABELS[analysis.face_shape] || analysis.face_shape;
  const confidence = Math.round(analysis.face_shape_confidence * 100);

  return (
    <div className="bg-zinc-800/60 border border-zinc-700 rounded-2xl p-6 space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-xs text-zinc-500 uppercase tracking-wider mb-1">얼굴형</p>
          <p className="text-2xl font-semibold text-white">{label}</p>
        </div>
        <div className="text-right">
          <p className="text-xs text-zinc-500 mb-1">정확도</p>
          <p className="text-xl font-medium text-emerald-400">{confidence}%</p>
        </div>
      </div>

      <p className="text-zinc-300 text-sm leading-relaxed border-t border-zinc-700 pt-4">
        {analysis.consultation_summary}
      </p>

      <div className="flex flex-wrap gap-2 pt-1">
        {analysis.recommended_style_tags.map((tag) => (
          <span
            key={tag}
            className="px-2.5 py-1 rounded-full bg-emerald-900/40 border border-emerald-700/50 text-emerald-300 text-xs"
          >
            ✓ {tag}
          </span>
        ))}
        {analysis.avoid_style_tags.map((tag) => (
          <span
            key={tag}
            className="px-2.5 py-1 rounded-full bg-red-900/30 border border-red-800/50 text-red-400 text-xs"
          >
            ✗ {tag}
          </span>
        ))}
      </div>
    </div>
  );
}
