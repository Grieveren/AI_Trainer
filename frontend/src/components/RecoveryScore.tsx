import React from "react";

export interface ComponentScores {
  hrv_score: number | null;
  hr_score: number | null;
  sleep_score: number | null;
  acwr_score: number | null;
}

export interface RecoveryScoreData {
  date: string;
  overall_score: number;
  status: "green" | "yellow" | "red";
  components: ComponentScores;
  explanation: string;
  cached_at: string;
  is_expired: boolean;
}

interface RecoveryScoreProps {
  data: RecoveryScoreData;
}

const RecoveryScore: React.FC<RecoveryScoreProps> = ({ data }) => {
  const statusColors = {
    green: "bg-green-500",
    yellow: "bg-yellow-500",
    red: "bg-red-500",
  };

  const formatDate = (dateStr: string): string => {
    const date = new Date(dateStr);
    return date.toLocaleDateString("en-US", {
      year: "numeric",
      month: "long",
      day: "numeric",
    });
  };

  const componentLabels = {
    hrv_score: "HRV",
    hr_score: "Resting HR",
    sleep_score: "Sleep",
    acwr_score: "Training Load",
  };

  return (
    <div
      role="region"
      aria-labelledby="recovery-score-heading"
      className="bg-white rounded-lg shadow-md p-6 space-y-6"
    >
      {/* Header with Score and Status */}
      <div className="flex items-center justify-between">
        <div>
          <h2
            id="recovery-score-heading"
            className="text-sm font-medium text-gray-600 uppercase tracking-wide"
          >
            Recovery Score
          </h2>
          <p className="text-xs text-gray-500 mt-1">{formatDate(data.date)}</p>
        </div>
        <div className="flex items-center space-x-4">
          <div
            aria-label={`Recovery score: ${data.overall_score} out of 100`}
            className="text-5xl font-bold text-gray-900"
          >
            {data.overall_score}
          </div>
          <div
            data-testid="recovery-status"
            className={`w-4 h-4 rounded-full ${statusColors[data.status]}`}
            aria-label={`Status: ${data.status}`}
          />
        </div>
      </div>

      {/* Explanation */}
      <div className="prose prose-sm max-w-none">
        <p className="text-gray-700 whitespace-pre-wrap">{data.explanation}</p>
      </div>

      {/* Component Breakdown */}
      <div className="border-t border-gray-200 pt-4">
        <h3 className="text-sm font-medium text-gray-700 mb-3">
          Component Breakdown
        </h3>
        <div className="grid grid-cols-2 gap-4">
          {Object.entries(data.components).map(([key, value]) => {
            if (value === null) return null;

            return (
              <div key={key} className="flex items-center justify-between">
                <span className="text-sm text-gray-600">
                  {componentLabels[key as keyof ComponentScores]}
                </span>
                <span className="text-sm font-semibold text-gray-900">
                  {value}
                </span>
              </div>
            );
          })}
        </div>
      </div>

      {/* Cache Status */}
      {data.is_expired && (
        <div className="bg-yellow-50 border border-yellow-200 rounded p-3">
          <p className="text-sm text-yellow-800">
            Score is updating... Data may be slightly outdated.
          </p>
        </div>
      )}
    </div>
  );
};

export default RecoveryScore;
