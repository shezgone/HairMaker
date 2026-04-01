import { describe, it, expect } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import SimulationResult from "@/components/simulation/SimulationResult";

describe("SimulationResult", () => {
  const defaultProps = {
    originalUrl: "https://example.com/original.jpg",
    resultUrl: "https://example.com/result.jpg",
    styleName: "레이어드 컷",
  };

  it("renders style name in heading", () => {
    render(<SimulationResult {...defaultProps} />);
    expect(screen.getByText("레이어드 컷 시뮬레이션")).toBeInTheDocument();
  });

  it("renders result image", () => {
    render(<SimulationResult {...defaultProps} />);
    const img = screen.getByAltText("시뮬레이션 결과");
    expect(img).toHaveAttribute("src", "https://example.com/result.jpg");
  });

  it("renders original image", () => {
    render(<SimulationResult {...defaultProps} />);
    const img = screen.getByAltText("원본");
    expect(img).toHaveAttribute("src", "https://example.com/original.jpg");
  });

  it("shows compare button text", () => {
    render(<SimulationResult {...defaultProps} />);
    expect(screen.getByText("원본 비교 (꾹 누르기)")).toBeInTheDocument();
  });

  it("changes button text on pointer down", () => {
    render(<SimulationResult {...defaultProps} />);
    const button = screen.getByText("원본 비교 (꾹 누르기)");
    fireEvent.pointerDown(button);
    expect(screen.getByText("원본 보기 중...")).toBeInTheDocument();
  });

  it("reverts button text on pointer up", () => {
    render(<SimulationResult {...defaultProps} />);
    const button = screen.getByText("원본 비교 (꾹 누르기)");
    fireEvent.pointerDown(button);
    expect(screen.getByText("원본 보기 중...")).toBeInTheDocument();
    fireEvent.pointerUp(button);
    expect(screen.getByText("원본 비교 (꾹 누르기)")).toBeInTheDocument();
  });

  it("shows simulation label by default", () => {
    render(<SimulationResult {...defaultProps} />);
    expect(screen.getByText("시뮬레이션")).toBeInTheDocument();
  });
});
