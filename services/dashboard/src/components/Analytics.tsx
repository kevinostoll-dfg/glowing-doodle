import { useState, useMemo } from "react";
import {
  BarChart,
  Bar,
  LineChart,
  Line,
  PieChart,
  Pie,
  Cell,
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  Radar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from "recharts";
import { useShopAnalytics } from "@/hooks/useAnalytics";
import { useShopContext } from "@/hooks/useShop";
import ScoreBadge from "@/components/ScoreBadge";
import type { DateRange } from "@/types";

const SENTIMENT_COLORS = {
  positive: "#22c55e",
  neutral: "#eab308",
  negative: "#ef4444",
};

function getDefaultDateRange(): DateRange {
  const end = new Date();
  const start = new Date();
  start.setDate(start.getDate() - 30);
  return {
    start: start.toISOString().split("T")[0],
    end: end.toISOString().split("T")[0],
  };
}

export default function Analytics() {
  const { selectedShop } = useShopContext();
  const [dateRange, setDateRange] = useState<DateRange>(getDefaultDateRange);

  const { data, isLoading, isError } = useShopAnalytics(
    selectedShop?.id,
    dateRange
  );

  const sentimentData = useMemo(() => {
    if (!data) return [];
    return [
      { name: "Positive", value: data.sentiment_distribution.positive },
      { name: "Neutral", value: data.sentiment_distribution.neutral },
      { name: "Negative", value: data.sentiment_distribution.negative },
    ];
  }, [data]);

  const radarData = useMemo(() => {
    if (!data) return [];
    return data.category_scores.map((c) => ({
      category: c.category,
      score: c.average_score,
      fullMark: c.max_score,
    }));
  }, [data]);

  if (!selectedShop) {
    return (
      <div className="flex items-center justify-center py-20 text-surface-500">
        Please select a shop to view analytics.
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <h1 className="text-2xl font-bold text-surface-900">Analytics</h1>
        <div className="flex items-center gap-3">
          <div>
            <label htmlFor="analyticsFrom" className="sr-only">
              From
            </label>
            <input
              id="analyticsFrom"
              type="date"
              value={dateRange.start}
              onChange={(e) =>
                setDateRange((prev) => ({ ...prev, start: e.target.value }))
              }
              className="input"
            />
          </div>
          <span className="text-surface-400">to</span>
          <div>
            <label htmlFor="analyticsTo" className="sr-only">
              To
            </label>
            <input
              id="analyticsTo"
              type="date"
              value={dateRange.end}
              onChange={(e) =>
                setDateRange((prev) => ({ ...prev, end: e.target.value }))
              }
              className="input"
            />
          </div>
        </div>
      </div>

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
        <div className="card text-center text-red-500">
          Failed to load analytics. Please try again.
        </div>
      ) : !data ? (
        <div className="card text-center text-surface-500">
          No analytics data available for this period.
        </div>
      ) : (
        <>
          {/* Summary Cards */}
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
            <div className="card">
              <div className="text-sm text-surface-500">Total Calls</div>
              <div className="mt-1 text-3xl font-bold text-surface-900">
                {data.total_calls}
              </div>
            </div>
            <div className="card">
              <div className="text-sm text-surface-500">Average Score</div>
              <div className="mt-1 flex items-center gap-2">
                <span className="text-3xl font-bold text-surface-900">
                  {Math.round(data.average_score)}
                </span>
                <ScoreBadge score={data.average_score} />
              </div>
            </div>
            <div className="card">
              <div className="text-sm text-surface-500">Avg Duration</div>
              <div className="mt-1 text-3xl font-bold text-surface-900">
                {Math.floor(data.average_duration / 60)}m{" "}
                {Math.round(data.average_duration % 60)}s
              </div>
            </div>
            <div className="card">
              <div className="text-sm text-surface-500">
                Positive Sentiment
              </div>
              <div className="mt-1 text-3xl font-bold text-green-600">
                {data.total_calls > 0
                  ? Math.round(
                      (data.sentiment_distribution.positive / data.total_calls) *
                        100
                    )
                  : 0}
                %
              </div>
            </div>
          </div>

          {/* Charts Row 1 */}
          <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
            {/* Call Volume Bar Chart */}
            <div className="card">
              <h3 className="mb-4 text-lg font-semibold text-surface-900">
                Call Volume
              </h3>
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={data.call_volume_by_day}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                  <XAxis
                    dataKey="date"
                    tick={{ fontSize: 12 }}
                    tickFormatter={(d: string) =>
                      new Date(d).toLocaleDateString("en-US", {
                        month: "short",
                        day: "numeric",
                      })
                    }
                  />
                  <YAxis tick={{ fontSize: 12 }} />
                  <Tooltip
                    labelFormatter={(d: string) =>
                      new Date(d).toLocaleDateString("en-US", {
                        month: "long",
                        day: "numeric",
                        year: "numeric",
                      })
                    }
                  />
                  <Legend />
                  <Bar
                    dataKey="inbound"
                    name="Inbound"
                    fill="#3b82f6"
                    radius={[2, 2, 0, 0]}
                  />
                  <Bar
                    dataKey="outbound"
                    name="Outbound"
                    fill="#8b5cf6"
                    radius={[2, 2, 0, 0]}
                  />
                </BarChart>
              </ResponsiveContainer>
            </div>

            {/* Score Trend Line Chart */}
            <div className="card">
              <h3 className="mb-4 text-lg font-semibold text-surface-900">
                Score Trend
              </h3>
              <ResponsiveContainer width="100%" height={300}>
                <LineChart data={data.score_trend}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                  <XAxis
                    dataKey="date"
                    tick={{ fontSize: 12 }}
                    tickFormatter={(d: string) =>
                      new Date(d).toLocaleDateString("en-US", {
                        month: "short",
                        day: "numeric",
                      })
                    }
                  />
                  <YAxis tick={{ fontSize: 12 }} domain={[0, 100]} />
                  <Tooltip
                    labelFormatter={(d: string) =>
                      new Date(d).toLocaleDateString("en-US", {
                        month: "long",
                        day: "numeric",
                        year: "numeric",
                      })
                    }
                    formatter={(value: number) => [
                      Math.round(value),
                      "Avg Score",
                    ]}
                  />
                  <Legend />
                  <Line
                    type="monotone"
                    dataKey="average_score"
                    name="Avg Score"
                    stroke="#3b82f6"
                    strokeWidth={2}
                    dot={{ r: 3 }}
                    activeDot={{ r: 5 }}
                  />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* Charts Row 2 */}
          <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
            {/* Sentiment Pie Chart */}
            <div className="card">
              <h3 className="mb-4 text-lg font-semibold text-surface-900">
                Sentiment Distribution
              </h3>
              <ResponsiveContainer width="100%" height={300}>
                <PieChart>
                  <Pie
                    data={sentimentData}
                    cx="50%"
                    cy="50%"
                    innerRadius={60}
                    outerRadius={100}
                    paddingAngle={4}
                    dataKey="value"
                    label={({ name, percent }) =>
                      `${name} ${(percent * 100).toFixed(0)}%`
                    }
                  >
                    {sentimentData.map((entry) => (
                      <Cell
                        key={entry.name}
                        fill={
                          SENTIMENT_COLORS[
                            entry.name.toLowerCase() as keyof typeof SENTIMENT_COLORS
                          ]
                        }
                      />
                    ))}
                  </Pie>
                  <Tooltip />
                </PieChart>
              </ResponsiveContainer>
            </div>

            {/* Category Scores Radar Chart */}
            <div className="card">
              <h3 className="mb-4 text-lg font-semibold text-surface-900">
                Category Scores
              </h3>
              <ResponsiveContainer width="100%" height={300}>
                <RadarChart cx="50%" cy="50%" outerRadius="80%" data={radarData}>
                  <PolarGrid stroke="#e2e8f0" />
                  <PolarAngleAxis
                    dataKey="category"
                    tick={{ fontSize: 11 }}
                  />
                  <PolarRadiusAxis tick={{ fontSize: 10 }} />
                  <Radar
                    name="Score"
                    dataKey="score"
                    stroke="#3b82f6"
                    fill="#3b82f6"
                    fillOpacity={0.3}
                  />
                  <Tooltip />
                </RadarChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* Advisor Performance Table */}
          <div className="card overflow-hidden p-0">
            <div className="border-b border-surface-200 px-6 py-4">
              <h3 className="text-lg font-semibold text-surface-900">
                Advisor Performance
              </h3>
            </div>
            {data.advisor_performance.length === 0 ? (
              <div className="px-6 py-10 text-center text-sm text-surface-500">
                No advisor performance data available.
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-left text-sm">
                  <thead className="border-b border-surface-200 bg-surface-50 text-xs uppercase text-surface-500">
                    <tr>
                      <th className="px-6 py-3 font-medium">Advisor</th>
                      <th className="px-6 py-3 font-medium">Total Calls</th>
                      <th className="px-6 py-3 font-medium">Avg Score</th>
                      <th className="px-6 py-3 font-medium">Avg Duration</th>
                      <th className="px-6 py-3 font-medium">
                        Positive Sentiment
                      </th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-surface-100">
                    {data.advisor_performance.map((advisor) => (
                      <tr
                        key={advisor.advisor_name}
                        className="hover:bg-surface-50"
                      >
                        <td className="whitespace-nowrap px-6 py-4 font-medium text-surface-900">
                          {advisor.advisor_name}
                        </td>
                        <td className="px-6 py-4 text-surface-600">
                          {advisor.total_calls}
                        </td>
                        <td className="px-6 py-4">
                          <ScoreBadge score={advisor.average_score} size="sm" />
                        </td>
                        <td className="px-6 py-4 text-surface-600">
                          {Math.floor(advisor.average_duration / 60)}m{" "}
                          {Math.round(advisor.average_duration % 60)}s
                        </td>
                        <td className="px-6 py-4 text-surface-600">
                          {Math.round(advisor.sentiment_positive_pct)}%
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </>
      )}
    </div>
  );
}
