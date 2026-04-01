import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import FaceShapeCard from "@/components/analysis/FaceShapeCard";
import type { FaceAnalysis } from "@/lib/types";

const mockAnalysis: FaceAnalysis = {
  face_shape: "oval",
  face_shape_confidence: 0.85,
  facial_features: {
    forehead_width: "medium",
    jaw_width: "narrow",
    cheekbone_prominence: "medium",
    face_length: "medium",
  },
  current_hair_estimate: "어깨 길이의 직모",
  recommended_style_tags: ["adds-volume", "frames-face"],
  avoid_style_tags: ["adds-width"],
  consultation_summary: "계란형 얼굴에 잘 어울리는 레이어드 컷을 추천드립니다.",
};

describe("FaceShapeCard", () => {
  it("renders face shape label in Korean", () => {
    render(<FaceShapeCard analysis={mockAnalysis} />);
    expect(screen.getByText("계란형")).toBeInTheDocument();
  });

  it("renders confidence percentage", () => {
    render(<FaceShapeCard analysis={mockAnalysis} />);
    expect(screen.getByText("85%")).toBeInTheDocument();
  });

  it("renders consultation summary", () => {
    render(<FaceShapeCard analysis={mockAnalysis} />);
    expect(
      screen.getByText("계란형 얼굴에 잘 어울리는 레이어드 컷을 추천드립니다.")
    ).toBeInTheDocument();
  });

  it("renders recommended style tags", () => {
    render(<FaceShapeCard analysis={mockAnalysis} />);
    expect(screen.getByText(/adds-volume/)).toBeInTheDocument();
    expect(screen.getByText(/frames-face/)).toBeInTheDocument();
  });

  it("renders avoid style tags", () => {
    render(<FaceShapeCard analysis={mockAnalysis} />);
    expect(screen.getByText(/adds-width/)).toBeInTheDocument();
  });

  it("renders round face shape correctly", () => {
    const roundAnalysis = { ...mockAnalysis, face_shape: "round" };
    render(<FaceShapeCard analysis={roundAnalysis} />);
    expect(screen.getByText("둥근형")).toBeInTheDocument();
  });

  it("renders unknown face shape as-is", () => {
    const unknownAnalysis = { ...mockAnalysis, face_shape: "pear" };
    render(<FaceShapeCard analysis={unknownAnalysis} />);
    expect(screen.getByText("pear")).toBeInTheDocument();
  });

  it("renders 100% confidence correctly", () => {
    const highConfidence = { ...mockAnalysis, face_shape_confidence: 1.0 };
    render(<FaceShapeCard analysis={highConfidence} />);
    expect(screen.getByText("100%")).toBeInTheDocument();
  });
});
