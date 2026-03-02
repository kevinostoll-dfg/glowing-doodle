interface ScoreBadgeProps {
  score: number;
  size?: "sm" | "md" | "lg";
}

export default function ScoreBadge({ score, size = "md" }: ScoreBadgeProps) {
  const rounded = Math.round(score);

  let colorClasses: string;
  if (rounded > 80) {
    colorClasses = "bg-green-100 text-green-800 ring-green-600/20";
  } else if (rounded >= 60) {
    colorClasses = "bg-yellow-100 text-yellow-800 ring-yellow-600/20";
  } else {
    colorClasses = "bg-red-100 text-red-800 ring-red-600/20";
  }

  const sizeClasses = {
    sm: "px-1.5 py-0.5 text-xs",
    md: "px-2 py-1 text-sm",
    lg: "px-3 py-1.5 text-base",
  }[size];

  return (
    <span
      className={`inline-flex items-center rounded-full font-medium ring-1 ring-inset ${colorClasses} ${sizeClasses}`}
    >
      {rounded}
    </span>
  );
}
