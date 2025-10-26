import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import "@testing-library/jest-dom";
import WorkoutRecommendation from "./WorkoutRecommendation";

describe("WorkoutRecommendation Component", () => {
  const mockRecommendation = {
    intensity: "hard",
    workout_type: "intervals",
    duration: 75,
    rationale:
      "Your recovery score of 85/100 indicates excellent recovery. You are ready for high-intensity training.",
    details: {
      duration: 60,
      zones: [4, 5],
      structure: "8x 5min @ Z4-5 / 3min rest",
      warmup: 10,
      cooldown: 10,
      work_duration: 5,
      rest_duration: 3,
      num_intervals: 8,
    },
    warnings: [],
  };

  const mockAlternatives = [
    {
      workout_type: "endurance",
      intensity: "moderate",
      duration: 90,
      rationale: "If you prefer a longer, easier session",
      details: null,
    },
  ];

  it("renders workout recommendation correctly", () => {
    render(
      <WorkoutRecommendation
        recommendation={mockRecommendation}
        alternatives={[]}
      />,
    );

    expect(screen.getByText(/intervals/i)).toBeInTheDocument();
    expect(screen.getByText(/hard/i)).toBeInTheDocument();
    expect(screen.getByText("75")).toBeInTheDocument();
  });

  it("displays rationale explanation", () => {
    render(
      <WorkoutRecommendation
        recommendation={mockRecommendation}
        alternatives={[]}
      />,
    );

    expect(screen.getByText(/excellent recovery/i)).toBeInTheDocument();
    expect(screen.getByText(/ready for high-intensity/i)).toBeInTheDocument();
  });

  it("shows workout details when provided", () => {
    render(
      <WorkoutRecommendation
        recommendation={mockRecommendation}
        alternatives={[]}
      />,
    );

    expect(screen.getByText(/8x 5min/i)).toBeInTheDocument();
    expect(screen.getByText(/Warmup: 10 min/i)).toBeInTheDocument();
    expect(screen.getByText(/Cooldown: 10 min/i)).toBeInTheDocument();
  });

  it("displays heart rate zones", () => {
    render(
      <WorkoutRecommendation
        recommendation={mockRecommendation}
        alternatives={[]}
      />,
    );

    expect(screen.getByText(/Zone 4-5/i)).toBeInTheDocument();
  });

  it("shows warnings when present", () => {
    const withWarnings = {
      ...mockRecommendation,
      warnings: [
        "You have trained hard 3 days in a row. Consider an easy day.",
      ],
    };
    render(
      <WorkoutRecommendation recommendation={withWarnings} alternatives={[]} />,
    );

    expect(screen.getByText(/trained hard 3 days/i)).toBeInTheDocument();
  });

  it("renders alternative workouts", () => {
    render(
      <WorkoutRecommendation
        recommendation={mockRecommendation}
        alternatives={mockAlternatives}
      />,
    );

    expect(screen.getByText(/alternatives/i)).toBeInTheDocument();
    expect(screen.getByText(/endurance/i)).toBeInTheDocument();
    expect(screen.getByText(/moderate/i)).toBeInTheDocument();
  });

  it("displays intensity badge with correct styling", () => {
    render(
      <WorkoutRecommendation
        recommendation={mockRecommendation}
        alternatives={[]}
      />,
    );

    const badge = screen.getByTestId("intensity-badge");
    expect(badge).toHaveClass("bg-red-100");
  });

  it("handles missing workout details gracefully", () => {
    const noDetails = { ...mockRecommendation, details: null };
    render(
      <WorkoutRecommendation recommendation={noDetails} alternatives={[]} />,
    );

    expect(screen.queryByText(/Warmup/i)).not.toBeInTheDocument();
  });

  it("is accessible with proper ARIA labels", () => {
    render(
      <WorkoutRecommendation
        recommendation={mockRecommendation}
        alternatives={[]}
      />,
    );

    expect(screen.getByRole("article")).toBeInTheDocument();
    expect(
      screen.getByLabelText(/workout recommendation/i),
    ).toBeInTheDocument();
  });

  it("displays duration in minutes", () => {
    render(
      <WorkoutRecommendation
        recommendation={mockRecommendation}
        alternatives={[]}
      />,
    );

    expect(screen.getByText(/75 min/i)).toBeInTheDocument();
  });
});
