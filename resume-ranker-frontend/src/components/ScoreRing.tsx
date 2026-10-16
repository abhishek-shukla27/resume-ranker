type Props = {
  value: number | string;
  max?: number;
  label: string;
  suffix?: string;
};

export function ScoreRing({ value, max = 100, label, suffix = "" }: Props) {
  const numeric = typeof value === "number" ? value : parseFloat(String(value));
  const safe = Number.isFinite(numeric) ? Math.max(0, Math.min(numeric, max)) : 0;
  const pct = max > 0 ? safe / max : 0;

  const size = 132;
  const stroke = 12;
  const radius = (size - stroke) / 2;
  const circumference = 2 * Math.PI * radius;
  const dash = circumference * pct;

  const hue = Math.round(120 * pct);
  const color = `hsl(${hue} 85% 55%)`;

  return (
    <div className="flex flex-col items-center gap-3">
      <div className="relative" style={{ width: size, height: size }}>
        <svg width={size} height={size} className="-rotate-90">
          <circle
            cx={size / 2}
            cy={size / 2}
            r={radius}
            fill="none"
            stroke="rgba(255,255,255,0.10)"
            strokeWidth={stroke}
          />
          <circle
            cx={size / 2}
            cy={size / 2}
            r={radius}
            fill="none"
            stroke={color}
            strokeWidth={stroke}
            strokeLinecap="round"
            strokeDasharray={`${dash} ${circumference - dash}`}
            style={{ transition: "stroke-dasharray 0.6s ease" }}
          />
        </svg>
        <div className="absolute inset-0 flex flex-col items-center justify-center">
          <span className="text-3xl font-bold text-white">
            {Number.isFinite(numeric) ? numeric : value}
            {suffix}
          </span>
          <span className="text-xs text-slate-400">/ {max}</span>
        </div>
      </div>
      <span className="text-sm font-medium text-slate-300">{label}</span>
    </div>
  );
}
