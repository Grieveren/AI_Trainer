import axios, { AxiosError } from "axios";

// API Base URL from environment or default to localhost
const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL || "http://localhost:8000/api/v1";

// Create axios instance with default config
const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 10000,
  headers: {
    "Content-Type": "application/json",
  },
});

// Request interceptor to add auth token
apiClient.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem("auth_token");
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  },
);

// Response interceptor for error handling
apiClient.interceptors.response.use(
  (response) => response,
  (error: AxiosError) => {
    if (error.response) {
      // Server responded with error status
      const status = error.response.status;
      const data = error.response.data as { detail?: string };

      switch (status) {
        case 401:
          // Unauthorized - clear token and redirect to login
          localStorage.removeItem("auth_token");
          window.location.href = "/login";
          throw new Error("Authentication required. Please log in.");

        case 403:
          throw new Error("Access forbidden. You do not have permission.");

        case 404:
          throw new Error(data?.detail || "Resource not found.");

        case 422:
          throw new Error(data?.detail || "Invalid data provided.");

        case 429:
          throw new Error("Too many requests. Please try again later.");

        case 500:
          throw new Error("Server error. Please try again later.");

        default:
          throw new Error(data?.detail || "An unexpected error occurred.");
      }
    } else if (error.request) {
      // Request made but no response
      throw new Error("Network error. Please check your connection.");
    } else {
      // Something else happened
      throw new Error(error.message || "An unexpected error occurred.");
    }
  },
);

// Type definitions
export interface ComponentScores {
  hrv_score: number | null;
  hr_score: number | null;
  sleep_score: number | null;
  acwr_score: number | null;
}

export interface RecoveryScoreResponse {
  date: string;
  overall_score: number;
  status: "green" | "yellow" | "red";
  components: ComponentScores;
  explanation: string;
  cached_at: string;
  is_expired: boolean;
}

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

export interface WorkoutRecommendation {
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

export interface RecoveryWithRecommendation extends RecoveryScoreResponse {
  recommendation: WorkoutRecommendation;
  alternatives: AlternativeWorkout[];
}

export interface RecalculationResponse {
  task_id: string;
  message: string;
  status: string;
}

// API functions

/**
 * Get recovery score for a specific date
 */
export const getRecoveryByDate = async (
  date: string,
): Promise<RecoveryScoreResponse> => {
  const response = await apiClient.get<RecoveryScoreResponse>(
    `/recovery/${date}`,
  );
  return response.data;
};

/**
 * Get today's recovery score with workout recommendation
 */
export const getTodayRecovery =
  async (): Promise<RecoveryWithRecommendation> => {
    const response =
      await apiClient.get<RecoveryWithRecommendation>("/recovery/today");
    return response.data;
  };

/**
 * Trigger recalculation of recovery score for a specific date
 */
export const recalculateRecovery = async (
  date: string,
): Promise<RecalculationResponse> => {
  const response = await apiClient.post<RecalculationResponse>(
    `/recovery/${date}/recalculate`,
  );
  return response.data;
};

/**
 * Set authentication token
 */
export const setAuthToken = (token: string): void => {
  localStorage.setItem("auth_token", token);
};

/**
 * Clear authentication token
 */
export const clearAuthToken = (): void => {
  localStorage.removeItem("auth_token");
};

/**
 * Check if user is authenticated
 */
export const isAuthenticated = (): boolean => {
  return !!localStorage.getItem("auth_token");
};

export default apiClient;
