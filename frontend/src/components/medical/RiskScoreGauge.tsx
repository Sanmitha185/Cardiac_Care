import React from 'react';

interface RiskScoreGaugeProps {
  score: number; // 0 - 100
  size?: number;
  strokeWidth?: number;
  showLabel?: boolean;
}

export const RiskScoreGauge: React.FC<RiskScoreGaugeProps> = ({
  score = 0,
  size = 180,
  strokeWidth = 14,
  showLabel = true,
}) => {
  // Clamp score between 0 and 100
  const validScore = Math.min(100, Math.max(0, Math.round(score)));
  
  // Radius and circumference
  const radius = (size - strokeWidth) / 2;
  const circumference = 2 * Math.PI * radius;
  // Use a 270-degree arc for an open gauge effect
  const arcLength = circumference * 0.75;
  const strokeDashoffset = arcLength - (validScore / 100) * arcLength;

  // Color selection based on clinical risk thresholds
  const getColor = () => {
    if (validScore >= 70) return { stroke: '#dc2626', text: 'text-red-600', label: 'High Risk / Immediate', bg: 'bg-red-50' };
    if (validScore >= 40) return { stroke: '#d97706', text: 'text-amber-600', label: 'Moderate Risk', bg: 'bg-amber-50' };
    return { stroke: '#16a34a', text: 'text-emerald-600', label: 'Low Risk / Routine', bg: 'bg-emerald-50' };
  };

  const theme = getColor();

  return (
    <div className="flex flex-col items-center justify-center">
      <div className="relative flex items-center justify-center" style={{ width: size, height: size }}>
        <svg
          width={size}
          height={size}
          className="transform -rotate-135"
        >
          {/* Background Track */}
          <circle
            cx={size / 2}
            cy={size / 2}
            r={radius}
            fill="none"
            stroke="#e2e8f0"
            strokeWidth={strokeWidth}
            strokeDasharray={`${arcLength} ${circumference}`}
            strokeLinecap="round"
          />
          {/* Active Risk Score Arc */}
          <circle
            cx={size / 2}
            cy={size / 2}
            r={radius}
            fill="none"
            stroke={theme.stroke}
            strokeWidth={strokeWidth}
            strokeDasharray={`${arcLength} ${circumference}`}
            strokeDashoffset={strokeDashoffset}
            strokeLinecap="round"
            style={{
              transition: 'stroke-dashoffset 1.2s cubic-bezier(0.4, 0, 0.2, 1)',
            }}
          />
        </svg>

        {/* Center score readout */}
        <div className="absolute inset-0 flex flex-col items-center justify-center text-center">
          <span className="text-4xl font-extrabold text-slate-900 tracking-tight">
            {validScore}
          </span>
          <span className="text-xs font-semibold text-slate-500 uppercase tracking-widest mt-0.5">
            Out of 100
          </span>
        </div>
      </div>

      {showLabel && (
        <div className={`mt-2 px-3 py-1 rounded-full text-xs font-semibold border ${theme.bg} ${theme.text} border-current/20`}>
          {theme.label}
        </div>
      )}
    </div>
  );
};
