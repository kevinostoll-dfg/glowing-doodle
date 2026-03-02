import { useState, useRef } from "react";
import { useParams, Link } from "react-router-dom";
import { useCall, useUpdateCall } from "@/hooks/useCalls";
import ScoreBadge from "@/components/ScoreBadge";
import type { TranscriptSegment, ScorecardCategory } from "@/types";

type TabKey = "overview" | "transcript" | "scorecard" | "recording";

function formatDuration(seconds: number): string {
  const mins = Math.floor(seconds / 60);
  const secs = seconds % 60;
  return `${mins}:${secs.toString().padStart(2, "0")}`;
}

function formatTimestamp(seconds: number): string {
  const mins = Math.floor(seconds / 60);
  const secs = Math.floor(seconds % 60);
  return `${mins}:${secs.toString().padStart(2, "0")}`;
}

function formatDate(dateStr: string): string {
  return new Date(dateStr).toLocaleDateString("en-US", {
    weekday: "long",
    month: "long",
    day: "numeric",
    year: "numeric",
    hour: "numeric",
    minute: "2-digit",
  });
}

function OverviewTab({ call }: { call: NonNullable<ReturnType<typeof useCall>["data"]> }) {
  return (
    <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
      {/* Call Metadata */}
      <div className="card">
        <h3 className="mb-4 text-lg font-semibold text-surface-900">
          Call Details
        </h3>
        <dl className="space-y-3 text-sm">
          <div className="flex justify-between">
            <dt className="text-surface-500">Direction</dt>
            <dd className="font-medium capitalize text-surface-900">
              {call.direction}
            </dd>
          </div>
          <div className="flex justify-between">
            <dt className="text-surface-500">Caller</dt>
            <dd className="font-medium text-surface-900">
              {call.caller_name || "Unknown"} ({call.caller_number})
            </dd>
          </div>
          <div className="flex justify-between">
            <dt className="text-surface-500">Started</dt>
            <dd className="font-medium text-surface-900">
              {formatDate(call.started_at)}
            </dd>
          </div>
          <div className="flex justify-between">
            <dt className="text-surface-500">Duration</dt>
            <dd className="font-medium text-surface-900">
              {formatDuration(call.duration_seconds)}
            </dd>
          </div>
          <div className="flex justify-between">
            <dt className="text-surface-500">Status</dt>
            <dd>
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
            </dd>
          </div>
          {call.participants.length > 0 && (
            <div className="flex justify-between">
              <dt className="text-surface-500">Participants</dt>
              <dd className="text-right font-medium text-surface-900">
                {call.participants.map((p) => p.name).join(", ")}
              </dd>
            </div>
          )}
          {call.tags.length > 0 && (
            <div className="flex justify-between">
              <dt className="text-surface-500">Tags</dt>
              <dd className="flex flex-wrap gap-1">
                {call.tags.map((tag) => (
                  <span
                    key={tag}
                    className="rounded-full bg-surface-100 px-2 py-0.5 text-xs text-surface-600"
                  >
                    {tag}
                  </span>
                ))}
              </dd>
            </div>
          )}
        </dl>
      </div>

      {/* Score Overview */}
      <div className="card">
        <h3 className="mb-4 text-lg font-semibold text-surface-900">
          Score Overview
        </h3>
        {call.metrics ? (
          <div className="space-y-4">
            <div className="flex items-center gap-4">
              <div className="text-4xl font-bold text-surface-900">
                {Math.round(call.metrics.overall_score)}
              </div>
              <ScoreBadge score={call.metrics.overall_score} size="lg" />
            </div>

            <div className="space-y-3">
              <div className="flex justify-between text-sm">
                <span className="text-surface-500">Sentiment</span>
                <span
                  className={`font-medium capitalize ${
                    call.metrics.sentiment === "positive"
                      ? "text-green-600"
                      : call.metrics.sentiment === "negative"
                      ? "text-red-600"
                      : "text-yellow-600"
                  }`}
                >
                  {call.metrics.sentiment}
                </span>
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-surface-500">Advisor Talk Ratio</span>
                <span className="font-medium text-surface-900">
                  {Math.round(call.metrics.talk_ratio.advisor * 100)}%
                </span>
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-surface-500">Customer Talk Ratio</span>
                <span className="font-medium text-surface-900">
                  {Math.round(call.metrics.talk_ratio.customer * 100)}%
                </span>
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-surface-500">Silence</span>
                <span className="font-medium text-surface-900">
                  {Math.round(call.metrics.silence_percentage * 100)}%
                </span>
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-surface-500">Interruptions</span>
                <span className="font-medium text-surface-900">
                  {call.metrics.interruptions}
                </span>
              </div>
            </div>

            {call.metrics.keywords.length > 0 && (
              <div>
                <div className="mb-2 text-sm text-surface-500">Keywords</div>
                <div className="flex flex-wrap gap-1">
                  {call.metrics.keywords.map((kw) => (
                    <span
                      key={kw}
                      className="rounded-full bg-brand-50 px-2 py-0.5 text-xs font-medium text-brand-700"
                    >
                      {kw}
                    </span>
                  ))}
                </div>
              </div>
            )}
          </div>
        ) : (
          <p className="text-sm text-surface-500">
            Score not yet available for this call.
          </p>
        )}
      </div>

      {/* Notes */}
      <div className="card lg:col-span-2">
        <NotesEditor callId={call.id} initialNotes={call.notes} />
      </div>
    </div>
  );
}

function NotesEditor({
  callId,
  initialNotes,
}: {
  callId: string;
  initialNotes: string;
}) {
  const [notes, setNotes] = useState(initialNotes);
  const [saved, setSaved] = useState(false);
  const updateCall = useUpdateCall(callId);

  const handleSave = () => {
    updateCall.mutate(
      { notes },
      {
        onSuccess: () => {
          setSaved(true);
          setTimeout(() => setSaved(false), 2000);
        },
      }
    );
  };

  return (
    <div>
      <div className="mb-2 flex items-center justify-between">
        <h3 className="text-lg font-semibold text-surface-900">Notes</h3>
        <div className="flex items-center gap-2">
          {saved && (
            <span className="text-sm text-green-600">Saved!</span>
          )}
          <button
            onClick={handleSave}
            disabled={updateCall.isPending}
            className="btn-primary text-xs"
          >
            {updateCall.isPending ? "Saving..." : "Save Notes"}
          </button>
        </div>
      </div>
      <textarea
        value={notes}
        onChange={(e) => setNotes(e.target.value)}
        placeholder="Add notes about this call..."
        rows={4}
        className="input resize-none"
      />
    </div>
  );
}

function TranscriptTab({
  transcript,
}: {
  transcript: TranscriptSegment[];
}) {
  if (transcript.length === 0) {
    return (
      <div className="card text-center text-sm text-surface-500">
        No transcript available for this call.
      </div>
    );
  }

  return (
    <div className="card space-y-4">
      <h3 className="text-lg font-semibold text-surface-900">Transcript</h3>
      <div className="space-y-3">
        {transcript.map((segment, idx) => (
          <div key={idx} className="flex gap-3">
            <div className="mt-0.5 shrink-0 text-xs text-surface-400">
              {formatTimestamp(segment.start_time)}
            </div>
            <div className="flex-1">
              <div
                className={`mb-0.5 text-xs font-medium ${
                  segment.role === "advisor"
                    ? "text-brand-600"
                    : "text-purple-600"
                }`}
              >
                {segment.speaker} ({segment.role})
              </div>
              <div
                className={`rounded-lg px-3 py-2 text-sm ${
                  segment.role === "advisor"
                    ? "bg-brand-50 text-surface-800"
                    : "bg-purple-50 text-surface-800"
                }`}
              >
                {segment.text}
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

function ScorecardTab({
  categories,
}: {
  categories: ScorecardCategory[];
}) {
  if (categories.length === 0) {
    return (
      <div className="card text-center text-sm text-surface-500">
        No scorecard data available.
      </div>
    );
  }

  return (
    <div className="card">
      <h3 className="mb-4 text-lg font-semibold text-surface-900">
        Scorecard
      </h3>
      <div className="space-y-5">
        {categories.map((cat) => {
          const pct =
            cat.max_score > 0 ? (cat.score / cat.max_score) * 100 : 0;
          let barColor: string;
          if (pct > 80) barColor = "bg-green-500";
          else if (pct >= 60) barColor = "bg-yellow-500";
          else barColor = "bg-red-500";

          return (
            <div key={cat.name}>
              <div className="mb-1 flex items-center justify-between">
                <span className="text-sm font-medium text-surface-900">
                  {cat.name}
                </span>
                <span className="text-sm text-surface-500">
                  {cat.score}/{cat.max_score} (weight: {cat.weight}x)
                </span>
              </div>
              <div className="h-2.5 w-full rounded-full bg-surface-200">
                <div
                  className={`h-2.5 rounded-full transition-all ${barColor}`}
                  style={{ width: `${Math.min(pct, 100)}%` }}
                />
              </div>
              {cat.comments && (
                <p className="mt-1 text-xs text-surface-500">{cat.comments}</p>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}

function RecordingTab({ recordingUrl }: { recordingUrl: string | null }) {
  const audioRef = useRef<HTMLAudioElement>(null);

  if (!recordingUrl) {
    return (
      <div className="card text-center text-sm text-surface-500">
        No recording available for this call.
      </div>
    );
  }

  return (
    <div className="card">
      <h3 className="mb-4 text-lg font-semibold text-surface-900">
        Recording
      </h3>
      <audio
        ref={audioRef}
        controls
        className="w-full"
        src={recordingUrl}
        preload="metadata"
      >
        Your browser does not support the audio element.
      </audio>
    </div>
  );
}

const tabs: { key: TabKey; label: string }[] = [
  { key: "overview", label: "Overview" },
  { key: "transcript", label: "Transcript" },
  { key: "scorecard", label: "Scorecard" },
  { key: "recording", label: "Recording" },
];

export default function CallDetail() {
  const { id } = useParams<{ id: string }>();
  const { data: call, isLoading, isError } = useCall(id);
  const [activeTab, setActiveTab] = useState<TabKey>("overview");

  if (isLoading) {
    return (
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
    );
  }

  if (isError || !call) {
    return (
      <div className="py-20 text-center text-red-500">
        Failed to load call details.{" "}
        <Link to="/calls" className="text-brand-600 hover:underline">
          Back to calls
        </Link>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Breadcrumb */}
      <div className="flex items-center gap-2 text-sm text-surface-500">
        <Link to="/calls" className="hover:text-brand-600">
          Calls
        </Link>
        <svg
          className="h-4 w-4"
          fill="none"
          viewBox="0 0 24 24"
          strokeWidth={1.5}
          stroke="currentColor"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            d="M8.25 4.5l7.5 7.5-7.5 7.5"
          />
        </svg>
        <span className="text-surface-900">
          {call.caller_name || call.caller_number}
        </span>
      </div>

      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-surface-900">
            {call.caller_name || "Unknown Caller"}
          </h1>
          <p className="text-sm text-surface-500">
            {formatDate(call.started_at)} &middot;{" "}
            {formatDuration(call.duration_seconds)} &middot;{" "}
            <span className="capitalize">{call.direction}</span>
          </p>
        </div>
        {call.metrics && (
          <ScoreBadge score={call.metrics.overall_score} size="lg" />
        )}
      </div>

      {/* Tabs */}
      <div className="border-b border-surface-200">
        <nav className="-mb-px flex gap-6">
          {tabs.map((tab) => (
            <button
              key={tab.key}
              onClick={() => setActiveTab(tab.key)}
              className={`border-b-2 pb-3 text-sm font-medium transition-colors ${
                activeTab === tab.key
                  ? "border-brand-600 text-brand-600"
                  : "border-transparent text-surface-500 hover:border-surface-300 hover:text-surface-700"
              }`}
            >
              {tab.label}
            </button>
          ))}
        </nav>
      </div>

      {/* Tab Content */}
      {activeTab === "overview" && <OverviewTab call={call} />}
      {activeTab === "transcript" && (
        <TranscriptTab transcript={call.transcript} />
      )}
      {activeTab === "scorecard" && (
        <ScorecardTab categories={call.metrics?.categories ?? []} />
      )}
      {activeTab === "recording" && (
        <RecordingTab recordingUrl={call.recording_url} />
      )}
    </div>
  );
}
