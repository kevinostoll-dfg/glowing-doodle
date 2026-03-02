import { useQuery } from "@tanstack/react-query";
import { getAnalytics, getTrends } from "@/services/api";
import type { DateRange } from "@/types";

export function useShopAnalytics(
  shopId: string | undefined,
  dateRange: DateRange
) {
  return useQuery({
    queryKey: ["analytics", shopId, dateRange],
    queryFn: () => getAnalytics(shopId!, dateRange.start, dateRange.end),
    enabled: !!shopId && !!dateRange.start && !!dateRange.end,
    staleTime: 60_000,
  });
}

export function useTrends(
  shopId: string | undefined,
  dateRange: DateRange
) {
  return useQuery({
    queryKey: ["trends", shopId, dateRange],
    queryFn: () => getTrends(shopId!, dateRange.start, dateRange.end),
    enabled: !!shopId && !!dateRange.start && !!dateRange.end,
    staleTime: 60_000,
  });
}
