import { useState, useMemo } from "react";
import { Link } from "react-router-dom";
import { useCalls } from "@/hooks/useCalls";
import { useShopContext } from "@/hooks/useShop";
import ScoreBadge from "@/components/ScoreBadge";
import type { CallFilters } from "@/types";

function formatDuration(seconds: number): string {
  const mins = Math.floor(seconds / 60);
  const secs = seconds % 60;
  return `${mins}:${secs.toString().padStart(2, "0")}`;
}

function formatDate(dateStr: string): string {
  return new Date(dateStr).toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
    hour: "numeric",
    minute: "2-digit",
  });
}

export default function CallList() {
  const { selectedShop } = useShopContext();
  const [page, setPage] = useState(1);
  const [direction, setDirection] = useState<string>("");
  const [status, setStatus] = useState<string>("");
  const [search, setSearch] = useState("");
  const [dateFrom, setDateFrom] = useState("");
  const [dateTo, setDateTo] = useState("");

  const filters: CallFilters = useMemo(
    () => ({
      shop_id: selectedShop?.id,
      page,
      page_size: 20,
      direction: direction as CallFilters["direction"] || undefined,
      status: status as CallFilters["status"] || undefined,
      search: search || undefined,
      date_from: dateFrom || undefined,
      date_to: dateTo || undefined,
      sort_by: "started_at",
      sort_order: "desc",
    }),
    [selectedShop?.id, page, direction, status, search, dateFrom, dateTo]
  );

  const { data, isLoading, isError } = useCalls(filters);

  if (!selectedShop) {
    return (
      <div className="flex items-center justify-center py-20 text-surface-500">
        Please select a shop to view calls.
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-surface-900">Calls</h1>
        {data && (
          <span className="text-sm text-surface-500">
            {data.total} total calls
          </span>
        )}
      </div>

      {/* Filters */}
      <div className="card">
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-5">
          <div>
            <label htmlFor="search" className="label">
              Search
            </label>
            <input
              id="search"
              type="text"
              value={search}
              onChange={(e) => {
                setSearch(e.target.value);
                setPage(1);
              }}
              placeholder="Caller name or number..."
              className="input"
            />
          </div>

          <div>
            <label htmlFor="direction" className="label">
              Direction
            </label>
            <select
              id="direction"
              value={direction}
              onChange={(e) => {
                setDirection(e.target.value);
                setPage(1);
              }}
              className="input"
            >
              <option value="">All</option>
              <option value="inbound">Inbound</option>
              <option value="outbound">Outbound</option>
            </select>
          </div>

          <div>
            <label htmlFor="status" className="label">
              Status
            </label>
            <select
              id="status"
              value={status}
              onChange={(e) => {
                setStatus(e.target.value);
                setPage(1);
              }}
              className="input"
            >
              <option value="">All</option>
              <option value="completed">Completed</option>
              <option value="processing">Processing</option>
              <option value="failed">Failed</option>
            </select>
          </div>

          <div>
            <label htmlFor="dateFrom" className="label">
              From
            </label>
            <input
              id="dateFrom"
              type="date"
              value={dateFrom}
              onChange={(e) => {
                setDateFrom(e.target.value);
                setPage(1);
              }}
              className="input"
            />
          </div>

          <div>
            <label htmlFor="dateTo" className="label">
              To
            </label>
            <input
              id="dateTo"
              type="date"
              value={dateTo}
              onChange={(e) => {
                setDateTo(e.target.value);
                setPage(1);
              }}
              className="input"
            />
          </div>
        </div>
      </div>

      {/* Table */}
      <div className="card overflow-hidden p-0">
        {isLoading ? (
          <div className="flex items-center justify-center py-20">
            <svg
              className="h-8 w-8 animate-spin text-brand-600"
              viewBox="0 0 24 24"
              fill="none"
            >
              <circle
                className="opacity-25"
                cx="12"
                cy="12"
                r="10"
                stroke="currentColor"
                strokeWidth="4"
              />
              <path
                className="opacity-75"
                fill="currentColor"
                d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"
              />
            </svg>
          </div>
        ) : isError ? (
          <div className="flex items-center justify-center py-20 text-red-500">
            Failed to load calls. Please try again.
          </div>
        ) : !data || data.items.length === 0 ? (
          <div className="flex items-center justify-center py-20 text-surface-500">
            No calls found.
          </div>
        ) : (
          <>
            <div className="overflow-x-auto">
              <table className="w-full text-left text-sm">
                <thead className="border-b border-surface-200 bg-surface-50 text-xs uppercase text-surface-500">
                  <tr>
                    <th className="px-6 py-3 font-medium">Date</th>
                    <th className="px-6 py-3 font-medium">Caller</th>
                    <th className="px-6 py-3 font-medium">Direction</th>
                    <th className="px-6 py-3 font-medium">Duration</th>
                    <th className="px-6 py-3 font-medium">Score</th>
                    <th className="px-6 py-3 font-medium">Status</th>
                    <th className="px-6 py-3 font-medium" />
                  </tr>
                </thead>
                <tbody className="divide-y divide-surface-100">
                  {data.items.map((call) => (
                    <tr
                      key={call.id}
                      className="hover:bg-surface-50 transition-colors"
                    >
                      <td className="whitespace-nowrap px-6 py-4 text-surface-900">
                        {formatDate(call.started_at)}
                      </td>
                      <td className="px-6 py-4">
                        <div className="text-surface-900">
                          {call.caller_name || "Unknown"}
                        </div>
                        <div className="text-xs text-surface-500">
                          {call.caller_number}
                        </div>
                      </td>
                      <td className="px-6 py-4">
                        <span
                          className={`inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-xs font-medium ${
                            call.direction === "inbound"
                              ? "bg-blue-50 text-blue-700"
                              : "bg-purple-50 text-purple-700"
                          }`}
                        >
                          {call.direction === "inbound" ? (
                            <svg
                              className="h-3 w-3"
                              fill="none"
                              viewBox="0 0 24 24"
                              strokeWidth={2}
                              stroke="currentColor"
                            >
                              <path
                                strokeLinecap="round"
                                strokeLinejoin="round"
                                d="M19.5 13.5L12 21m0 0l-7.5-7.5M12 21V3"
                              />
                            </svg>
                          ) : (
                            <svg
                              className="h-3 w-3"
                              fill="none"
                              viewBox="0 0 24 24"
                              strokeWidth={2}
                              stroke="currentColor"
                            >
                              <path
                                strokeLinecap="round"
                                strokeLinejoin="round"
                                d="M4.5 10.5L12 3m0 0l7.5 7.5M12 3v18"
                              />
                            </svg>
                          )}
                          {call.direction}
                        </span>
                      </td>
                      <td className="whitespace-nowrap px-6 py-4 text-surface-600">
                        {formatDuration(call.duration_seconds)}
                      </td>
                      <td className="px-6 py-4">
                        {call.metrics ? (
                          <ScoreBadge score={call.metrics.overall_score} />
                        ) : (
                          <span className="text-surface-400">--</span>
                        )}
                      </td>
                      <td className="px-6 py-4">
                        <span
                          className={`inline-flex rounded-full px-2 py-0.5 text-xs font-medium ${
                            call.status === "completed"
                              ? "bg-green-50 text-green-700"
                              : call.status === "processing"
                              ? "bg-yellow-50 text-yellow-700"
                              : "bg-red-50 text-red-700"
                          }`}
                        >
                          {call.status}
                        </span>
                      </td>
                      <td className="px-6 py-4">
                        <Link
                          to={`/calls/${call.id}`}
                          className="text-sm font-medium text-brand-600 hover:text-brand-700"
                        >
                          View
                        </Link>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {/* Pagination */}
            {data.total_pages > 1 && (
              <div className="flex items-center justify-between border-t border-surface-200 bg-white px-6 py-3">
                <div className="text-sm text-surface-500">
                  Page {data.page} of {data.total_pages}
                </div>
                <div className="flex gap-2">
                  <button
                    onClick={() => setPage((p) => Math.max(1, p - 1))}
                    disabled={page <= 1}
                    className="btn-secondary text-xs"
                  >
                    Previous
                  </button>
                  <button
                    onClick={() =>
                      setPage((p) => Math.min(data.total_pages, p + 1))
                    }
                    disabled={page >= data.total_pages}
                    className="btn-secondary text-xs"
                  >
                    Next
                  </button>
                </div>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
}
