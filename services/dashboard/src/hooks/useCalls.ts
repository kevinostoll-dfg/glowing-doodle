import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { getCalls, getCall, updateCall } from "@/services/api";
import type { CallFilters } from "@/types";

export function useCalls(filters: CallFilters) {
  return useQuery({
    queryKey: ["calls", filters],
    queryFn: () => getCalls(filters),
    enabled: !!filters.shop_id,
    staleTime: 30_000,
    placeholderData: (previousData) => previousData,
  });
}

export function useCall(callId: string | undefined) {
  return useQuery({
    queryKey: ["call", callId],
    queryFn: () => getCall(callId!),
    enabled: !!callId,
    staleTime: 60_000,
  });
}

export function useUpdateCall(callId: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (updates: Parameters<typeof updateCall>[1]) =>
      updateCall(callId, updates),
    onSuccess: (updatedCall) => {
      queryClient.setQueryData(["call", callId], updatedCall);
      queryClient.invalidateQueries({ queryKey: ["calls"] });
    },
  });
}
