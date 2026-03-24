"use client";
import { useState, useEffect, useRef } from "react";
import { getSimulationStatus, startSimulation } from "../api";
import type { SimulationJob } from "../types";

export function useSimulation(sessionId: string) {
  const [jobs, setJobs] = useState<Map<string, SimulationJob>>(new Map());
  const intervalRef = useRef<Map<string, NodeJS.Timeout>>(new Map());

  const simulate = async (styleId: string, model: "flux" | "flux-max" = "flux"): Promise<string> => {
    const { job_id } = await startSimulation(sessionId, styleId, model);
    setJobs((prev) => new Map(prev).set(job_id, { job_id, status: "pending" }));
    startPolling(job_id);
    return job_id;
  };

  const startPolling = (jobId: string) => {
    const interval = setInterval(async () => {
      try {
        const status = await getSimulationStatus(jobId);
        setJobs((prev) => new Map(prev).set(jobId, status));

        if (status.status === "done" || status.status === "error") {
          clearInterval(interval);
          intervalRef.current.delete(jobId);
        }
      } catch {
        clearInterval(interval);
        intervalRef.current.delete(jobId);
      }
    }, 2000);

    intervalRef.current.set(jobId, interval);
  };

  useEffect(() => {
    return () => {
      intervalRef.current.forEach((interval) => clearInterval(interval));
    };
  }, []);

  return { jobs, simulate };
}
