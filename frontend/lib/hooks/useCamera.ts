"use client";
import { useState, useRef, useCallback } from "react";

export function useCamera() {
  const videoRef = useRef<HTMLVideoElement>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isActive, setIsActive] = useState(false);

  const startCamera = useCallback(async () => {
    try {
      const mediaStream = await navigator.mediaDevices.getUserMedia({
        video: { width: { ideal: 1280 }, height: { ideal: 720 } },
      });
      streamRef.current = mediaStream;
      if (videoRef.current) {
        const video = videoRef.current;
        video.srcObject = mediaStream;
        await new Promise<void>((resolve) => {
          video.onloadedmetadata = () => resolve();
        });
        await video.play();
      }
      setIsActive(true);
      setError(null);
    } catch (err: unknown) {
      const name = err instanceof Error ? err.name : "";
      if (name === "NotAllowedError" || name === "PermissionDeniedError") {
        setError("카메라 권한이 거부되었습니다. 브라우저 주소창 왼쪽 자물쇠 아이콘을 클릭해 카메라를 허용해주세요.");
      } else if (name === "NotFoundError" || name === "DevicesNotFoundError") {
        setError("카메라 장치를 찾을 수 없습니다. 카메라가 연결되어 있는지 확인해주세요.");
      } else if (name === "NotReadableError") {
        setError("카메라가 다른 앱에서 사용 중입니다. 다른 앱을 종료 후 다시 시도해주세요.");
      } else {
        setError(`카메라 오류: ${err instanceof Error ? err.message : String(err)}`);
      }
    }
  }, []);

  const stopCamera = useCallback(() => {
    streamRef.current?.getTracks().forEach((track) => track.stop());
    streamRef.current = null;
    setIsActive(false);
  }, []);

  const capturePhoto = useCallback((): Promise<Blob | null> => {
    return new Promise((resolve) => {
      if (!videoRef.current) return resolve(null);
      const canvas = document.createElement("canvas");
      canvas.width = videoRef.current.videoWidth;
      canvas.height = videoRef.current.videoHeight;
      const ctx = canvas.getContext("2d");
      if (!ctx) return resolve(null);
      ctx.drawImage(videoRef.current, 0, 0);
      canvas.toBlob(resolve, "image/jpeg", 0.92);
    });
  }, []);

  return { videoRef, isActive, error, startCamera, stopCamera, capturePhoto };
}
