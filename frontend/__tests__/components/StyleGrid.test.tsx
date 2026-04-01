import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import StyleGrid from "@/components/styles/StyleGrid";
import type { HairStyle } from "@/lib/types";

const createStyle = (id: string, name: string): HairStyle => ({
  id,
  salon_id: "salon-001",
  name,
  description: "",
  style_tags: [],
  face_shapes: [],
  face_shape_scores: {},
  hair_length: "medium",
  maintenance_level: 2,
  reference_image_url: "",
  reference_images: [],
  simulation_prompt: "",
  is_active: true,
  gender: "female",
});

describe("StyleGrid", () => {
  it("renders empty state message when no styles", () => {
    render(<StyleGrid styles={[]} onSelect={vi.fn()} />);
    expect(screen.getByText("추천 스타일을 불러오는 중입니다...")).toBeInTheDocument();
  });

  it("renders all style cards", () => {
    const styles = [
      createStyle("1", "레이어드 컷"),
      createStyle("2", "보브 컷"),
      createStyle("3", "숏 컷"),
    ];
    render(<StyleGrid styles={styles} onSelect={vi.fn()} />);
    expect(screen.getByText("레이어드 컷")).toBeInTheDocument();
    expect(screen.getByText("보브 컷")).toBeInTheDocument();
    expect(screen.getByText("숏 컷")).toBeInTheDocument();
  });

  it("highlights selected style", () => {
    const styles = [createStyle("1", "A"), createStyle("2", "B")];
    render(<StyleGrid styles={styles} onSelect={vi.fn()} selectedId="2" />);
    // Check mark should appear for selected item
    expect(screen.getByText("✓")).toBeInTheDocument();
  });

  it("calls onSelect with correct style when clicked", () => {
    const onSelect = vi.fn();
    const styles = [createStyle("1", "스타일 A"), createStyle("2", "스타일 B")];
    render(<StyleGrid styles={styles} onSelect={onSelect} />);
    fireEvent.click(screen.getByText("스타일 B"));
    expect(onSelect).toHaveBeenCalledWith(styles[1]);
  });
});
