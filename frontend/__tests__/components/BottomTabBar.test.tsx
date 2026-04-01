import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import BottomTabBar from "@/components/BottomTabBar";

// We need to be able to change pathname per test
let mockPathname = "/";
vi.mock("next/navigation", async () => {
  return {
    useRouter: () => ({
      push: vi.fn(),
      replace: vi.fn(),
      back: vi.fn(),
      prefetch: vi.fn(),
      refresh: vi.fn(),
    }),
    usePathname: () => mockPathname,
    useSearchParams: () => new URLSearchParams(),
  };
});

describe("BottomTabBar", () => {
  it("renders all tab labels", () => {
    mockPathname = "/";
    render(<BottomTabBar />);
    expect(screen.getByText("홈")).toBeInTheDocument();
    expect(screen.getByText("스타일북")).toBeInTheDocument();
    expect(screen.getByText("새 상담")).toBeInTheDocument();
    expect(screen.getByText("내 기록")).toBeInTheDocument();
    expect(screen.getByText("마이")).toBeInTheDocument();
  });

  it("renders tab links with correct hrefs", () => {
    mockPathname = "/";
    render(<BottomTabBar />);
    expect(screen.getByText("홈").closest("a")).toHaveAttribute("href", "/");
    expect(screen.getByText("스타일북").closest("a")).toHaveAttribute("href", "/admin/catalog");
    expect(screen.getByText("새 상담").closest("a")).toHaveAttribute("href", "/session/new");
  });

  it("returns null on login page", () => {
    mockPathname = "/login";
    const { container } = render(<BottomTabBar />);
    expect(container.innerHTML).toBe("");
  });

  it("returns null on register page", () => {
    mockPathname = "/register";
    const { container } = render(<BottomTabBar />);
    expect(container.innerHTML).toBe("");
  });

  it("returns null on auth callback page", () => {
    mockPathname = "/auth/callback";
    const { container } = render(<BottomTabBar />);
    expect(container.innerHTML).toBe("");
  });
});
