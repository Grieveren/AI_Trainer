import React from "react";
import { useQuery } from "@tanstack/react-query";
import RecoveryScore, { RecoveryScoreData } from "../components/RecoveryScore";
import WorkoutRecommendation, {
  Recommendation,
  AlternativeWorkout,
} from "../components/WorkoutRecommendation";
import { getTodayRecovery } from "../services/api";

interface RecoveryWithRecommendation extends RecoveryScoreData {
  recommendation: Recommendation;
  alternatives: AlternativeWorkout[];
}

const Dashboard: React.FC = () => {
  const { data, isLoading, isError, error, refetch } =
    useQuery<RecoveryWithRecommendation>({
      queryKey: ["recovery", "today"],
      queryFn: getTodayRecovery,
      staleTime: 1000 * 60 * 5, // 5 minutes
      retry: 2,
    });

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div
            className="inline-block h-12 w-12 animate-spin rounded-full border-4 border-solid border-blue-600 border-r-transparent"
            role="status"
            aria-label="Loading"
          >
            <span className="sr-only">Loading...</span>
          </div>
          <p className="mt-4 text-gray-600">Loading your recovery data...</p>
        </div>
      </div>
    );
  }

  if (isError) {
    const errorMessage =
      error instanceof Error ? error.message : "Failed to load recovery data";

    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center p-4">
        <div
          className="bg-white rounded-lg shadow-md p-6 max-w-md w-full"
          role="alert"
          aria-live="assertive"
        >
          <div className="flex items-start">
            <svg
              className="w-6 h-6 text-red-600 mt-0.5 mr-3 flex-shrink-0"
              fill="currentColor"
              viewBox="0 0 20 20"
            >
              <path
                fillRule="evenodd"
                d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z"
                clipRule="evenodd"
              />
            </svg>
            <div className="flex-1">
              <h3 className="text-lg font-medium text-gray-900">
                Error Loading Data
              </h3>
              <p className="mt-2 text-sm text-gray-600">{errorMessage}</p>
              <button
                onClick={() => refetch()}
                className="mt-4 px-4 py-2 bg-blue-600 text-white text-sm font-medium rounded-lg hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 transition-colors"
              >
                Try Again
              </button>
            </div>
          </div>
        </div>
      </div>
    );
  }

  if (!data) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <p className="text-gray-600">No recovery data available</p>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Header */}
        <header className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900">
            Your Training Dashboard
          </h1>
          <p className="mt-2 text-gray-600">
            Track your recovery and get personalized workout recommendations
          </p>
        </header>

        {/* Main Content */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Recovery Score Card */}
          <div className="lg:col-span-1">
            <RecoveryScore data={data} />
          </div>

          {/* Workout Recommendation Card */}
          <div className="lg:col-span-1">
            <WorkoutRecommendation
              recommendation={data.recommendation}
              alternatives={data.alternatives}
            />
          </div>
        </div>

        {/* Refresh Button */}
        <div className="mt-6 flex justify-center">
          <button
            onClick={() => refetch()}
            className="px-6 py-2 bg-white text-gray-700 text-sm font-medium rounded-lg border border-gray-300 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 transition-colors shadow-sm"
            aria-label="Refresh recovery data"
          >
            <svg
              className="inline-block w-4 h-4 mr-2"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"
              />
            </svg>
            Refresh Data
          </button>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;
