export interface Shop {
  id: string;
  name: string;
  phone_number: string;
  timezone: string;
  created_at: string;
  updated_at: string;
}

export interface CallParticipant {
  role: "advisor" | "customer";
  name: string;
  phone_number: string;
}

export interface TranscriptSegment {
  speaker: string;
  role: "advisor" | "customer";
  text: string;
  start_time: number;
  end_time: number;
  confidence: number;
}

export interface ScorecardCategory {
  name: string;
  score: number;
  max_score: number;
  weight: number;
  comments: string;
}

export interface CallMetrics {
  overall_score: number;
  sentiment: "positive" | "neutral" | "negative";
  talk_ratio: {
    advisor: number;
    customer: number;
  };
  silence_percentage: number;
  interruptions: number;
  keywords: string[];
  categories: ScorecardCategory[];
}

export interface Call {
  id: string;
  shop_id: string;
  direction: "inbound" | "outbound";
  caller_number: string;
  caller_name: string;
  participants: CallParticipant[];
  started_at: string;
  ended_at: string;
  duration_seconds: number;
  recording_url: string | null;
  transcript: TranscriptSegment[];
  metrics: CallMetrics | null;
  status: "processing" | "completed" | "failed";
  notes: string;
  tags: string[];
  created_at: string;
  updated_at: string;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export interface AnalyticsData {
  shop_id: string;
  period_start: string;
  period_end: string;
  total_calls: number;
  average_score: number;
  average_duration: number;
  sentiment_distribution: {
    positive: number;
    neutral: number;
    negative: number;
  };
  call_volume_by_day: Array<{
    date: string;
    inbound: number;
    outbound: number;
    total: number;
  }>;
  score_trend: Array<{
    date: string;
    average_score: number;
    call_count: number;
  }>;
  category_scores: Array<{
    category: string;
    average_score: number;
    max_score: number;
  }>;
  advisor_performance: Array<{
    advisor_name: string;
    total_calls: number;
    average_score: number;
    average_duration: number;
    sentiment_positive_pct: number;
  }>;
}

export interface CallFilters {
  shop_id?: string;
  page?: number;
  page_size?: number;
  direction?: "inbound" | "outbound";
  status?: "processing" | "completed" | "failed";
  date_from?: string;
  date_to?: string;
  search?: string;
  sort_by?: string;
  sort_order?: "asc" | "desc";
}

export interface DateRange {
  start: string;
  end: string;
}

export interface AuthState {
  apiKey: string | null;
  isAuthenticated: boolean;
  login: (key: string) => void;
  logout: () => void;
}

export interface ShopContextState {
  selectedShop: Shop | null;
  setSelectedShop: (shop: Shop | null) => void;
}
