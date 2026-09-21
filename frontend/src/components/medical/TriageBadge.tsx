import React from 'react';
import { AlertTriangle, ShieldCheck, Clock } from 'lucide-react';

interface TriageBadgeProps {
  category: string;
  size?: 'sm' | 'md' | 'lg';
  showIcon?: boolean;
}

export const TriageBadge: React.FC<TriageBadgeProps> = ({
  category = 'Category C',
  size = 'md',
  showIcon = true,
}) => {
  const catUpper = (category || '').toUpperCase();
  const isEmergency = catUpper.includes('CATEGORY A') || catUpper.includes('EMERGENCY');
  const isUrgent = catUpper.includes('CATEGORY B') || catUpper.includes('URGENT');

  let style = {
    bg: 'bg-emerald-50 text-emerald-800 border-emerald-300/80',
    dot: 'bg-emerald-500',
    title: 'Category C — Routine',
    icon: <ShieldCheck className="w-4 h-4 text-emerald-600" />
  };

  if (isEmergency) {
    style = {
      bg: 'bg-red-50 text-red-900 border-red-300 shadow-sm',
      dot: 'bg-red-600 animate-ping',
      title: 'Category A — EMERGENCY',
      icon: <AlertTriangle className="w-4 h-4 text-red-600" />
    };
  } else if (isUrgent) {
    style = {
      bg: 'bg-amber-50 text-amber-900 border-amber-300',
      dot: 'bg-amber-500',
      title: 'Category B — Urgent Attention',
      icon: <Clock className="w-4 h-4 text-amber-600" />
    };
  }

  const sizeClasses = {
    sm: 'text-xs px-2.5 py-1',
    md: 'text-sm px-3.5 py-1.5',
    lg: 'text-base px-5 py-2.5 font-bold',
  };

  return (
    <div className={`inline-flex items-center space-x-2 rounded-full border font-semibold tracking-wide ${style.bg} ${sizeClasses[size]}`}>
      {isEmergency && (
        <span className="relative flex h-2 w-2">
          <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-red-400 opacity-75"></span>
          <span className="relative inline-flex rounded-full h-2 w-2 bg-red-600"></span>
        </span>
      )}
      {!isEmergency && showIcon && style.icon}
      <span>{category}</span>
    </div>
  );
};
