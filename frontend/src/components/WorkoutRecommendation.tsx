import React from "react";

export interface WorkoutDetails {
  duration: number | null;
  zones: number[] | null;
  structure: string | null;
  warmup: number | null;
  cooldown: number | null;
  work_duration: number | null;
  rest_duration: number | null;
  num_intervals: number | null;
}

export interface Recommendation {
  intensity: string;
  workout_type: string;
  duration: number | null;
  rationale: string;
  details: WorkoutDetails | null;
  warnings: string[];
}

export interface AlternativeWorkout {
  workout_type: string;
  intensity: string;
  duration: number | null;
  rationale: string;
  details: WorkoutDetails | null;
}

interface WorkoutRecommendationProps {
  recommendation: Recommendation;
  alternatives: AlternativeWorkout[];
}

const WorkoutRecommendation: React.FC<WorkoutRecommendationProps> = ({
  recommendation,
  alternatives,
}) => {
  const intensityColors = {
    hard: "bg-red-100 text-red-800 border-red-200",
    moderate: "bg-yellow-100 text-yellow-800 border-yellow-200",
    recovery: "bg-blue-100 text-blue-800 border-blue-200",
    rest: "bg-gray-100 text-gray-800 border-gray-200",
  };

  const getIntensityColor = (intensity: string): string => {
    return (
      intensityColors[intensity as keyof typeof intensityColors] ||
      intensityColors.moderate
    );
  };

  const formatZones = (zones: number[] | null): string => {
    if (!zones || zones.length === 0) return "";
    if (zones.length === 1) return `Zone ${zones[0]}`;
    return `Zone ${Math.min(...zones)}-${Math.max(...zones)}`;
  };

  return (
    <article
      role="article"
      aria-labelledby="workout-recommendation-heading"
      className="bg-white rounded-lg shadow-md p-6 space-y-6"
    >
      {/* Header */}
      <div className="flex items-start justify-between">
        <div className="flex-1">
          <h2
            id="workout-recommendation-heading"
            className="text-2xl font-bold text-gray-900 capitalize"
          >
            {recommendation.workout_type}
          </h2>
          <div className="flex items-center space-x-3 mt-2">
            <span
              data-testid="intensity-badge"
              className={`px-3 py-1 text-sm font-medium rounded-full border ${getIntensityColor(
                recommendation.intensity,
              )}`}
            >
              {recommendation.intensity}
            </span>
            {recommendation.duration && (
              <span className="text-sm text-gray-600">
                {recommendation.duration} min
              </span>
            )}
          </div>
        </div>
      </div>

      {/* Rationale */}
      <div className="prose prose-sm max-w-none">
        <p className="text-gray-700">{recommendation.rationale}</p>
      </div>

      {/* Warnings */}
      {recommendation.warnings.length > 0 && (
        <div className="bg-amber-50 border border-amber-200 rounded-lg p-4">
          <div className="flex items-start">
            <svg
              className="w-5 h-5 text-amber-600 mt-0.5 mr-3 flex-shrink-0"
              fill="currentColor"
              viewBox="0 0 20 20"
            >
              <path
                fillRule="evenodd"
                d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z"
                clipRule="evenodd"
              />
            </svg>
            <div className="flex-1">
              <h3 className="text-sm font-medium text-amber-800">
                Important Considerations
              </h3>
              <ul className="mt-2 text-sm text-amber-700 space-y-1">
                {recommendation.warnings.map((warning, index) => (
                  <li key={index}>{warning}</li>
                ))}
              </ul>
            </div>
          </div>
        </div>
      )}

      {/* Workout Details */}
      {recommendation.details && (
        <div className="border-t border-gray-200 pt-4 space-y-3">
          <h3 className="text-sm font-medium text-gray-700">
            Workout Structure
          </h3>

          {recommendation.details.structure && (
            <p className="text-base font-medium text-gray-900">
              {recommendation.details.structure}
            </p>
          )}

          {recommendation.details.zones &&
            recommendation.details.zones.length > 0 && (
              <p className="text-sm text-gray-600">
                Target: {formatZones(recommendation.details.zones)}
              </p>
            )}

          <div className="grid grid-cols-2 gap-4 mt-3">
            {recommendation.details.warmup && (
              <div className="text-sm">
                <span className="text-gray-600">Warmup:</span>{" "}
                <span className="font-medium text-gray-900">
                  {recommendation.details.warmup} min
                </span>
              </div>
            )}
            {recommendation.details.cooldown && (
              <div className="text-sm">
                <span className="text-gray-600">Cooldown:</span>{" "}
                <span className="font-medium text-gray-900">
                  {recommendation.details.cooldown} min
                </span>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Alternatives */}
      {alternatives.length > 0 && (
        <div className="border-t border-gray-200 pt-4">
          <h3 className="text-sm font-medium text-gray-700 mb-3">
            Alternative Workouts
          </h3>
          <div className="space-y-3">
            {alternatives.map((alt, index) => (
              <div key={index} className="bg-gray-50 rounded-lg p-4">
                <div className="flex items-center justify-between mb-2">
                  <h4 className="text-sm font-medium text-gray-900 capitalize">
                    {alt.workout_type}
                  </h4>
                  <span
                    className={`px-2 py-1 text-xs font-medium rounded-full border ${getIntensityColor(
                      alt.intensity,
                    )}`}
                  >
                    {alt.intensity}
                  </span>
                </div>
                <p className="text-sm text-gray-600">{alt.rationale}</p>
                {alt.duration && (
                  <p className="text-xs text-gray-500 mt-1">
                    {alt.duration} minutes
                  </p>
                )}
              </div>
            ))}
          </div>
        </div>
      )}
    </article>
  );
};

export default WorkoutRecommendation;
