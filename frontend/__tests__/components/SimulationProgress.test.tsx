import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { render, screen, act } from "@testing-library/react";
import SimulationProgress from "@/components/simulation/SimulationProgress";

describe("SimulationProgress", () => {
  beforeEach(() => {
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it("renders style name", () => {
    render(<SimulationProgress styleName="레이어드 컷" />);
    expect(screen.getByText("레이어드 컷")).toBeInTheDocument();
  });

  it("shows initial message", () => {
    render(<SimulationProgress styleName="테스트" />);
    expect(screen.getByText("얼굴형을 분석하고 있어요...")).toBeInTheDocument();
  });

  it("shows time estimate", () => {
    render(<SimulationProgress styleName="테스트" />);
    expect(screen.getByText("약 15-30초 소요됩니다")).toBeInTheDocument();
  });

  it("cycles through messages", () => {
    render(<SimulationProgress styleName="테스트" />);
    expect(screen.getByText("얼굴형을 분석하고 있어요...")).toBeInTheDocument();

    act(() => {
      vi.advanceTimersByTime(5000);
    });
    expect(screen.getByText("헤어스타일을 적용하고 있어요...")).toBeInTheDocument();

    act(() => {
      vi.advanceTimersByTime(5000);
    });
    expect(screen.getByText("자연스러운 결과를 생성하고 있어요...")).toBeInTheDocument();
  });

  it("renders spinner animation element", () => {
    const { container } = render(<SimulationProgress styleName="테스트" />);
    const spinner = container.querySelector(".animate-spin");
    expect(spinner).toBeInTheDocument();
  });
});
