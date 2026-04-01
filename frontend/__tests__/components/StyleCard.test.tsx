import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import StyleCard from "@/components/styles/StyleCard";
import type { HairStyle } from "@/lib/types";

const mockStyle: HairStyle = {
  id: "style-001",
  salon_id: "salon-001",
  name: "내추럴 레이어드 컷",
  description: "자연스러운 레이어드 컷",
  style_tags: ["adds-volume", "frames-face"],
  face_shapes: ["oval", "round"],
  face_shape_scores: { oval: 0.9, round: 0.7 },
  hair_length: "medium",
  maintenance_level: 2,
  reference_image_url: "https://example.com/style.jpg",
  reference_images: [],
  simulation_prompt: "a natural layered cut",
  is_active: true,
  gender: "female",
};

describe("StyleCard", () => {
  it("renders style name", () => {
    render(<StyleCard style={mockStyle} isSelected={false} onSelect={vi.fn()} />);
    expect(screen.getByText("내추럴 레이어드 컷")).toBeInTheDocument();
  });

  it("renders hair length", () => {
    render(<StyleCard style={mockStyle} isSelected={false} onSelect={vi.fn()} />);
    expect(screen.getByText("medium")).toBeInTheDocument();
  });

  it("renders maintenance level label", () => {
    render(<StyleCard style={mockStyle} isSelected={false} onSelect={vi.fn()} />);
    expect(screen.getByText(/관리 보통/)).toBeInTheDocument();
  });

  it("renders reference image when available", () => {
    render(<StyleCard style={mockStyle} isSelected={false} onSelect={vi.fn()} />);
    const img = screen.getByAltText("내추럴 레이어드 컷");
    expect(img).toBeInTheDocument();
    expect(img).toHaveAttribute("src", "https://example.com/style.jpg");
  });

  it("renders placeholder when no reference image", () => {
    const noImageStyle = { ...mockStyle, reference_image_url: "" };
    render(<StyleCard style={noImageStyle} isSelected={false} onSelect={vi.fn()} />);
    expect(screen.queryByRole("img")).not.toBeInTheDocument();
  });

  it("shows check mark when selected", () => {
    render(<StyleCard style={mockStyle} isSelected={true} onSelect={vi.fn()} />);
    expect(screen.getByText("✓")).toBeInTheDocument();
  });

  it("does not show check mark when not selected", () => {
    render(<StyleCard style={mockStyle} isSelected={false} onSelect={vi.fn()} />);
    expect(screen.queryByText("✓")).not.toBeInTheDocument();
  });

  it("calls onSelect when clicked", () => {
    const onSelect = vi.fn();
    render(<StyleCard style={mockStyle} isSelected={false} onSelect={onSelect} />);
    fireEvent.click(screen.getByRole("button"));
    expect(onSelect).toHaveBeenCalledTimes(1);
  });

  it("applies selected ring style", () => {
    const { container } = render(
      <StyleCard style={mockStyle} isSelected={true} onSelect={vi.fn()} />
    );
    const button = container.querySelector("button");
    expect(button?.className).toContain("ring-violet-500");
  });
});
