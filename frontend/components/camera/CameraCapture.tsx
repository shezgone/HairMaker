"use client";
import { useEffect, useRef, useState, useCallback } from "react";
import { useCamera } from "@/lib/hooks/useCamera";

interface Props {
  onCapture: (blob: Blob) => void;
}

export default function CameraCapture({ onCapture }: Props) {
  const { videoRef, isActive, error, startCamera, stopCamera, capturePhoto } = useCamera();
  const [faceDetected, setFaceDetected] = useState(false);
  const [capturedPreview, setCapturedPreview] = useState<string | null>(null);
  const detectIntervalRef = useRef<NodeJS.Timeout | null>(null);
  // Reuse a single offscreen canvas for face detection to avoid GC churn
  const detectCanvasRef = useRef<HTMLCanvasElement | null>(null);

  useEffect(() => {
    startCamera();
    return () => stopCamera();
  }, [startCamera, stopCamera]);

  // Lightweight face detection using improved skin color heuristic
  // Supports a wider range of skin tones (light to dark)
  useEffect(() => {
    if (!isActive) return;

    if (!detectCanvasRef.current) {
      detectCanvasRef.current = document.createElement("canvas");
      detectCanvasRef.current.width = 80;
      detectCanvasRef.current.height = 60;
    }
    const canvas = detectCanvasRef.current;

    detectIntervalRef.current = setInterval(() => {
      if (!videoRef.current) return;
      const ctx = canvas.getContext("2d");
      if (!ctx) return;
      ctx.drawImage(videoRef.current, 0, 0, 80, 60);
      const data = ctx.getImageData(0, 0, 80, 60).data;
      let skinPixels = 0;
      const totalPixels = 80 * 60;
      for (let i = 0; i < data.length; i += 4) {
        const r = data[i], g = data[i + 1], b = data[i + 2];
        // Improved skin detection supporting diverse skin tones:
        // Rule 1: General skin (lighter tones) — original + relaxed thresholds
        // Rule 2: Darker skin tones — lower absolute values, warm bias
        const isLightSkin = r > 80 && g > 30 && b > 15 && r > g && (r - g) > 10 && r > b;
        const isDarkSkin = r > 45 && g > 25 && b > 10 && r > b && (r - b) > 5 && g < r * 0.95;
        if (isLightSkin || isDarkSkin) {
          skinPixels++;
        }
      }
      // Require at least ~4% of pixels to be skin-like
      setFaceDetected(skinPixels > totalPixels * 0.04);
    }, 500);

    return () => {
      if (detectIntervalRef.current) clearInterval(detectIntervalRef.current);
    };
  }, [isActive, videoRef]);

  const handleCapture = useCallback(async () => {
    const blob = await capturePhoto();
    if (!blob) return;
    // Revoke any previous preview URL before creating a new one
    if (capturedPreview) URL.revokeObjectURL(capturedPreview);
    const url = URL.createObjectURL(blob);
    setCapturedPreview(url);
    onCapture(blob);
    stopCamera();
  }, [capturePhoto, onCapture, stopCamera, capturedPreview]);

  const handleRetake = () => {
    if (capturedPreview) URL.revokeObjectURL(capturedPreview);
    setCapturedPreview(null);
    startCamera();
  };

  // Cleanup object URL on unmount
  useEffect(() => {
    return () => {
      if (capturedPreview) URL.revokeObjectURL(capturedPreview);
    };
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  if (capturedPreview) {
    return (
      <div className="flex flex-col items-center gap-6">
        <div className="relative rounded-2xl overflow-hidden shadow-2xl">
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img src={capturedPreview} alt="촬영된 사진" className="w-full max-w-sm" />
        </div>
        <div className="flex gap-4">
          <button
            onClick={handleRetake}
            className="px-6 py-3 rounded-xl border border-zinc-600 text-zinc-300 hover:bg-zinc-800 transition-colors"
          >
            다시 촬영
          </button>
          <div className="px-6 py-3 rounded-xl bg-zinc-700 text-zinc-400 text-sm flex items-center gap-2">
            <span className="animate-pulse">●</span> 분석 중...
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="flex flex-col items-center gap-6">
      {error ? (
        <div className="p-6 rounded-xl bg-red-900/30 border border-red-700 text-red-300 text-center space-y-4 max-w-sm">
          <p className="text-lg font-medium">카메라 오류</p>
          <p className="text-sm leading-relaxed">{error}</p>
          <div className="text-xs text-red-400 leading-relaxed text-left bg-red-950/50 rounded-lg p-3">
            <p className="font-medium mb-1">크롬 브라우저 해결 방법:</p>
            <p>① 주소창 왼쪽 자물쇠/카메라 아이콘 클릭</p>
            <p>② &quot;항상 허용&quot; 선택 후 페이지 새로고침</p>
          </div>
          <button
            onClick={startCamera}
            className="w-full py-2.5 rounded-xl bg-red-700 hover:bg-red-600 text-white text-sm font-medium transition-colors"
          >
            다시 시도
          </button>
        </div>
      ) : (
        <div className="relative rounded-2xl overflow-hidden shadow-2xl bg-zinc-900 w-80 h-[480px]">
          <video
            ref={videoRef}
            autoPlay
            playsInline
            muted
            className="w-full h-full object-cover"
            style={{ transform: "scaleX(-1)" }}
          />
          {/* Face guide overlay */}
          <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
            <div
              className={`w-48 h-64 rounded-full border-4 transition-colors duration-300 ${
                faceDetected ? "border-green-400" : "border-white/40"
              }`}
            />
          </div>
          {/* Status indicator */}
          <div className="absolute bottom-4 left-0 right-0 flex justify-center">
            <span
              className={`px-4 py-1.5 rounded-full text-sm font-medium transition-colors ${
                faceDetected
                  ? "bg-green-500/90 text-white"
                  : "bg-black/60 text-white/70"
              }`}
            >
              {faceDetected ? "얼굴 인식됨 ✓" : "얼굴을 타원 안에 위치시켜 주세요"}
            </span>
          </div>
        </div>
      )}

      <button
        onClick={handleCapture}
        disabled={!isActive}
        className={`w-20 h-20 rounded-full border-4 transition-all ${
          faceDetected
            ? "border-white bg-white hover:bg-zinc-100 shadow-lg shadow-white/20"
            : "border-zinc-500 bg-zinc-700 cursor-not-allowed opacity-50"
        }`}
        aria-label="사진 촬영"
      >
        <span className="block w-14 h-14 rounded-full bg-zinc-900 mx-auto" />
      </button>
    </div>
  );
}
