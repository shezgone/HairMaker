"use client";
import { useState, useEffect, useRef, useCallback } from "react";
import { getSimulationStatus, startSimulation } from "../api";
import type { SimulationJob } from "../types";

export function useSimulation(sessionId: string) {
  const [jobs, setJobs] = useState<Map<string, SimulationJob>>(new Map());
  const intervalRef = useRef<Map<string, NodeJS.Timeout>>(new Map());
  const pollingJobIds = useRef<Set<string>>(new Set());

  const startPolling = useCallback((jobId: string) => {
    // Prevent duplicate polling for the same job
    if (pollingJobIds.current.has(jobId)) return;
    pollingJobIds.current.add(jobId);

    const interval = setInterval(async () => {
      try {
        const status = await getSimulationStatus(jobId);
        setJobs((prev) => new Map(prev).set(jobId, status));

        if (status.status === "done" || status.status === "error") {
          clearInterval(interval);
          intervalRef.current.delete(jobId);
          pollingJobIds.current.delete(jobId);
        }
      } catch {
        clearInterval(interval);
        intervalRef.current.delete(jobId);
        pollingJobIds.current.delete(jobId);
        setJobs((prev) => new Map(prev).set(jobId, {
          job_id: jobId,
          status: "error",
          error: "서버와의 연결이 끊어졌습니다.",
        }));
      }
    }, 2000);

    intervalRef.current.set(jobId, interval);
  }, []);

  const simulate = useCallback(async (styleId: string, model: "flux" | "flux-max" = "flux"): Promise<string> => {
    const { job_id } = await startSimulation(sessionId, styleId, model);
    setJobs((prev) => new Map(prev).set(job_id, { job_id, status: "pending" }));
    startPolling(job_id);
    return job_id;
  }, [sessionId, startPolling]);

  useEffect(() => {
    return () => {
      intervalRef.current.forEach((interval) => clearInterval(interval));
      intervalRef.current.clear();
      pollingJobIds.current.clear();
    };
  }, []);

  return { jobs, simulate };
}
