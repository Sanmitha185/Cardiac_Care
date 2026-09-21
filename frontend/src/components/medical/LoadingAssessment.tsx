import React from 'react';
import { Stethoscope } from 'lucide-react';
import { ECGPulse } from './ECGPulse';

interface LoadingAssessmentProps {
  statusText?: string;
  subText?: string;
}

export const LoadingAssessment: React.FC<LoadingAssessmentProps> = ({
  statusText = 'Dr. Cardia is reviewing your response',
  subText = 'Evaluating symptoms and cardiac indicators',
}) => {
  return (
    <div className="bg-white/95 backdrop-blur-sm border border-brand-100 rounded-2xl p-5 shadow-xs my-4 max-w-lg mx-auto">
      <div className="flex items-center space-x-3 mb-2">
        <div className="relative flex items-center justify-center w-8 h-8 rounded-full bg-brand-50 text-brand-700">
          <Stethoscope className="w-4 h-4 text-brand-700 animate-pulse" />
        </div>
        <div>
          <h4 className="text-sm font-bold text-slate-900 tracking-tight">
            {statusText}
          </h4>
          <p className="text-xs text-slate-500">
            {subText}
          </p>
        </div>
      </div>

      {/* Subtle ECG pulse line */}
      <div className="py-2">
        <ECGPulse height={32} color="#0354a1" />
      </div>

      <div className="flex items-center justify-between text-[11px] text-slate-400 px-1 pt-1 border-t border-slate-100">
        <span>Clinical Consultation</span>
        <span className="text-brand-700 font-medium">Please wait a moment...</span>
      </div>
    </div>
  );
};
