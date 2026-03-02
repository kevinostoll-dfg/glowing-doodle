import axios from "axios";
import type {
  Call,
  Shop,
  PaginatedResponse,
  AnalyticsData,
  CallFilters,
} from "@/types";

const api = axios.create({
  baseURL: "/api",
  headers: {
    "Content-Type": "application/json",
  },
});

// Interceptor to attach API key from localStorage
api.interceptors.request.use((config) => {
  const apiKey = localStorage.getItem("api_key");
  if (apiKey) {
    config.headers["X-API-Key"] = apiKey;
  }
  return config;
});

// Response interceptor for auth errors
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401 || error.response?.status === 403) {
      localStorage.removeItem("api_key");
      window.location.href = "/login";
    }
    return Promise.reject(error);
  }
);

// ---- Shops ----

export async function getShops(): Promise<Shop[]> {
  const { data } = await api.get<Shop[]>("/v1/shops");
  return data;
}

export async function getShop(shopId: string): Promise<Shop> {
  const { data } = await api.get<Shop>(`/v1/shops/${shopId}`);
  return data;
}

// ---- Calls ----

export async function getCalls(
  filters: CallFilters
): Promise<PaginatedResponse<Call>> {
  const params = new URLSearchParams();

  if (filters.shop_id) params.set("shop_id", filters.shop_id);
  if (filters.page) params.set("page", String(filters.page));
  if (filters.page_size) params.set("page_size", String(filters.page_size));
  if (filters.direction) params.set("direction", filters.direction);
  if (filters.status) params.set("status", filters.status);
  if (filters.date_from) params.set("date_from", filters.date_from);
  if (filters.date_to) params.set("date_to", filters.date_to);
  if (filters.search) params.set("search", filters.search);
  if (filters.sort_by) params.set("sort_by", filters.sort_by);
  if (filters.sort_order) params.set("sort_order", filters.sort_order);

  const { data } = await api.get<PaginatedResponse<Call>>(
    `/v1/calls?${params.toString()}`
  );
  return data;
}

export async function getCall(callId: string): Promise<Call> {
  const { data } = await api.get<Call>(`/v1/calls/${callId}`);
  return data;
}

export async function updateCall(
  callId: string,
  updates: Partial<Pick<Call, "notes" | "tags">>
): Promise<Call> {
  const { data } = await api.patch<Call>(`/v1/calls/${callId}`, updates);
  return data;
}

// ---- Analytics ----

export async function getAnalytics(
  shopId: string,
  startDate: string,
  endDate: string
): Promise<AnalyticsData> {
  const { data } = await api.get<AnalyticsData>(
    `/v1/analytics/${shopId}?start_date=${startDate}&end_date=${endDate}`
  );
  return data;
}

export async function getTrends(
  shopId: string,
  startDate: string,
  endDate: string
): Promise<AnalyticsData["score_trend"]> {
  const { data } = await api.get<AnalyticsData["score_trend"]>(
    `/v1/analytics/${shopId}/trends?start_date=${startDate}&end_date=${endDate}`
  );
  return data;
}

// ---- Auth ----

export async function validateApiKey(apiKey: string): Promise<boolean> {
  try {
    await api.get("/v1/shops", {
      headers: { "X-API-Key": apiKey },
    });
    return true;
  } catch {
    return false;
  }
}

export default api;
