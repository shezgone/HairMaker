import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import PersonalColorCard from "@/components/analysis/PersonalColorCard";
import type { PersonalColor } from "@/lib/types";

const mockSpringColor: PersonalColor = {
  season: "spring",
  tone: "warm",
  skin_tone: "밝은 아이보리",
  undertone_description: "따뜻한 톤",
  recommended_hair_colors: [
    { name: "골드브라운", hex: "#A0522D" },
    { name: "카라멜", hex: "#C68E17" },
  ],
  avoid_hair_colors: [
    { name: "블루블랙", hex: "#1C1C2E" },
  ],
  color_summary: "봄 웜톤으로 따뜻한 컬러가 잘 어울립니다.",
};

describe("PersonalColorCard", () => {
  it("renders season label for spring", () => {
    render(<PersonalColorCard personalColor={mockSpringColor} />);
    expect(screen.getByText("봄 웜톤")).toBeInTheDocument();
  });

  it("renders tone badge", () => {
    render(<PersonalColorCard personalColor={mockSpringColor} />);
    expect(screen.getByText("웜톤")).toBeInTheDocument();
  });

  it("renders color summary", () => {
    render(<PersonalColorCard personalColor={mockSpringColor} />);
    expect(
      screen.getByText("봄 웜톤으로 따뜻한 컬러가 잘 어울립니다.")
    ).toBeInTheDocument();
  });

  it("renders recommended hair colors", () => {
    render(<PersonalColorCard personalColor={mockSpringColor} />);
    expect(screen.getByText("골드브라운")).toBeInTheDocument();
    expect(screen.getByText("카라멜")).toBeInTheDocument();
  });

  it("renders avoid hair colors", () => {
    render(<PersonalColorCard personalColor={mockSpringColor} />);
    expect(screen.getByText("블루블랙")).toBeInTheDocument();
  });

  it("renders winter cool tone correctly", () => {
    const winterColor: PersonalColor = {
      ...mockSpringColor,
      season: "winter",
      tone: "cool",
    };
    render(<PersonalColorCard personalColor={winterColor} />);
    expect(screen.getByText("겨울 쿨톤")).toBeInTheDocument();
    expect(screen.getByText("쿨톤")).toBeInTheDocument();
  });

  it("renders summer cool tone correctly", () => {
    const summerColor: PersonalColor = {
      ...mockSpringColor,
      season: "summer",
      tone: "cool",
    };
    render(<PersonalColorCard personalColor={summerColor} />);
    expect(screen.getByText("여름 쿨톤")).toBeInTheDocument();
  });

  it("renders autumn warm tone correctly", () => {
    const autumnColor: PersonalColor = {
      ...mockSpringColor,
      season: "autumn",
      tone: "warm",
    };
    render(<PersonalColorCard personalColor={autumnColor} />);
    expect(screen.getByText("가을 웜톤")).toBeInTheDocument();
  });

  it("hides avoid section when no colors to avoid", () => {
    const noAvoid: PersonalColor = {
      ...mockSpringColor,
      avoid_hair_colors: [],
    };
    render(<PersonalColorCard personalColor={noAvoid} />);
    expect(screen.queryByText("피해야 할 컬러")).not.toBeInTheDocument();
  });

  it("renders color swatches with correct hex", () => {
    const { container } = render(
      <PersonalColorCard personalColor={mockSpringColor} />
    );
    const swatches = container.querySelectorAll(
      "[style*='background-color']"
    );
    expect(swatches.length).toBeGreaterThan(0);
  });
});
