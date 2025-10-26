import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import "@testing-library/jest-dom";
import RecoveryScore from "./RecoveryScore";

describe("RecoveryScore Component", () => {
  const mockRecoveryData = {
    date: "2025-10-24",
    overall_score: 85,
    status: "green" as const,
    components: {
      hrv_score: 90,
      hr_score: 85,
      sleep_score: 80,
      acwr_score: 85,
    },
    explanation:
      "Excellent recovery (Score: 85/100)\nYou are well-recovered and ready for high-intensity training.",
    cached_at: "2025-10-24T06:30:00Z",
    is_expired: false,
  };

  it("renders recovery score correctly", () => {
    render(<RecoveryScore data={mockRecoveryData} />);

    expect(screen.getByText("85")).toBeInTheDocument();
    expect(screen.getByText(/recovery score/i)).toBeInTheDocument();
  });

  it("displays status color indicator", () => {
    render(<RecoveryScore data={mockRecoveryData} />);

    const statusElement = screen.getByTestId("recovery-status");
    expect(statusElement).toHaveClass("bg-green-500");
  });

  it("shows component breakdown", () => {
    render(<RecoveryScore data={mockRecoveryData} />);

    expect(screen.getByText(/HRV/i)).toBeInTheDocument();
    expect(screen.getByText("90")).toBeInTheDocument();
    expect(screen.getByText(/Resting HR/i)).toBeInTheDocument();
    expect(screen.getByText("85")).toBeInTheDocument();
    expect(screen.getByText(/Sleep/i)).toBeInTheDocument();
    expect(screen.getByText("80")).toBeInTheDocument();
  });

  it("displays explanation text", () => {
    render(<RecoveryScore data={mockRecoveryData} />);

    expect(screen.getByText(/Excellent recovery/i)).toBeInTheDocument();
    expect(screen.getByText(/well-recovered/i)).toBeInTheDocument();
  });

  it("shows expired indicator when cache is expired", () => {
    const expiredData = { ...mockRecoveryData, is_expired: true };
    render(<RecoveryScore data={expiredData} />);

    expect(screen.getByText(/updating/i)).toBeInTheDocument();
  });

  it("renders yellow status correctly", () => {
    const yellowData = {
      ...mockRecoveryData,
      status: "yellow" as const,
      overall_score: 60,
    };
    render(<RecoveryScore data={yellowData} />);

    const statusElement = screen.getByTestId("recovery-status");
    expect(statusElement).toHaveClass("bg-yellow-500");
  });

  it("renders red status correctly", () => {
    const redData = {
      ...mockRecoveryData,
      status: "red" as const,
      overall_score: 30,
    };
    render(<RecoveryScore data={redData} />);

    const statusElement = screen.getByTestId("recovery-status");
    expect(statusElement).toHaveClass("bg-red-500");
  });

  it("is accessible with proper ARIA labels", () => {
    render(<RecoveryScore data={mockRecoveryData} />);

    expect(screen.getByLabelText(/recovery score/i)).toBeInTheDocument();
    expect(screen.getByRole("region")).toBeInTheDocument();
  });

  it("displays date in readable format", () => {
    render(<RecoveryScore data={mockRecoveryData} />);

    expect(screen.getByText(/October 24, 2025/i)).toBeInTheDocument();
  });
});
