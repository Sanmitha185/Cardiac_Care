import React from 'react';

interface ECGPulseProps {
  className?: string;
  color?: string;
  speed?: 'slow' | 'normal' | 'fast';
  height?: number;
  interactive?: boolean;
}

export const ECGPulse: React.FC<ECGPulseProps> = ({
  className = '',
  color = '#0284c7',
  height = 40,
}) => {
  return (
    <div className={`relative overflow-hidden flex items-center ${className}`} style={{ height }}>
      {/* Background grid line */}
      <div className="absolute inset-x-0 h-px bg-slate-200 dark:bg-slate-700/50" />
      
      {/* SVG Cardiac Waveform: Isoelectric line -> P wave -> Q dip -> R spike -> S dip -> T wave */}
      <svg
        viewBox="0 0 500 100"
        preserveAspectRatio="none"
        className="w-full h-full stroke-current"
        style={{ color }}
      >
        <path
          d="M 0 50 
             L 80 50 
             Q 90 40, 100 50 
             L 130 50 
             L 140 60 
             L 155 10 
             L 170 85 
             L 185 50 
             L 210 50 
             Q 230 25, 250 50 
             L 330 50 
             Q 340 40, 350 50 
             L 380 50 
             L 390 60 
             L 405 10 
             L 420 85 
             L 435 50 
             L 460 50 
             Q 480 25, 500 50"
          fill="none"
          strokeWidth="2.5"
          strokeLinecap="round"
          strokeLinejoin="round"
          className="opacity-40"
        />

        {/* Animated scanning pulse overlay */}
        <path
          d="M 0 50 
             L 80 50 
             Q 90 40, 100 50 
             L 130 50 
             L 140 60 
             L 155 10 
             L 170 85 
             L 185 50 
             L 210 50 
             Q 230 25, 250 50 
             L 330 50 
             Q 340 40, 350 50 
             L 380 50 
             L 390 60 
             L 405 10 
             L 420 85 
             L 435 50 
             L 460 50 
             Q 480 25, 500 50"
          fill="none"
          strokeWidth="3"
          strokeLinecap="round"
          strokeLinejoin="round"
          strokeDasharray="120 380"
          className="animate-ecg-scan"
        />
      </svg>
    </div>
  );
};
