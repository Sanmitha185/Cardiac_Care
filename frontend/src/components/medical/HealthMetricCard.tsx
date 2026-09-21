import React from 'react';
import { Activity, Heart, Scale, Ruler, Droplets, FileText } from 'lucide-react';

interface HealthMetricCardProps {
  label: string;
  value: string | number;
  unit?: string;
  status?: 'normal' | 'warning' | 'critical' | 'neutral';
  iconType: 'heart_rate' | 'blood_pressure' | 'weight' | 'height' | 'glucose' | 'ecg';
  subtitle?: string;
}

export const HealthMetricCard: React.FC<HealthMetricCardProps> = ({
  label,
  value,
  unit,
  status = 'normal',
  iconType,
  subtitle
}) => {
  const getIcon = () => {
    switch (iconType) {
      case 'heart_rate':
        return <Heart className="w-5 h-5 text-rose-500" />;
      case 'blood_pressure':
        return <Activity className="w-5 h-5 text-brand-600" />;
      case 'weight':
        return <Scale className="w-5 h-5 text-clinical-teal" />;
      case 'height':
        return <Ruler className="w-5 h-5 text-clinical-sky" />;
      case 'glucose':
        return <Droplets className="w-5 h-5 text-amber-500" />;
      case 'ecg':
        return <FileText className="w-5 h-5 text-indigo-500" />;
      default:
        return <Activity className="w-5 h-5 text-brand-500" />;
    }
  };

  const getStatusBadge = () => {
    switch (status) {
      case 'critical':
        return <span className="text-xs px-2 py-0.5 rounded-full font-medium bg-red-100 text-red-700">Urgent</span>;
      case 'warning':
        return <span className="text-xs px-2 py-0.5 rounded-full font-medium bg-amber-100 text-amber-800">Elevated</span>;
      case 'normal':
        return <span className="text-xs px-2 py-0.5 rounded-full font-medium bg-emerald-100 text-emerald-800">Normal</span>;
      default:
        return null;
    }
  };

  return (
    <div className="bg-white rounded-xl p-4 border border-slate-200/80 shadow-sm hover:shadow-md transition-all flex flex-col justify-between">
      <div className="flex items-center justify-between mb-2">
        <span className="text-xs font-semibold uppercase tracking-wider text-slate-500">{label}</span>
        <div className="p-2 bg-slate-50 rounded-lg border border-slate-100">
          {getIcon()}
        </div>
      </div>

      <div className="flex items-baseline space-x-1.5 my-1">
        <span className="text-2xl font-bold tracking-tight text-slate-900">{value}</span>
        {unit && <span className="text-xs font-medium text-slate-500">{unit}</span>}
      </div>

      <div className="flex items-center justify-between mt-2 pt-2 border-t border-slate-100 text-xs text-slate-500">
        <span>{subtitle || 'Clinical record'}</span>
        {getStatusBadge()}
      </div>
    </div>
  );
};
