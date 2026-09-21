import React from 'react';
import { CheckCircle2, Circle } from 'lucide-react';

interface ClinicalTimelineProps {
  currentPhaseIndex: number; // 0 to 4
  questionsAsked?: number;
  completeness?: number;
  isEmergency?: boolean;
}

export const ClinicalTimeline: React.FC<ClinicalTimelineProps> = ({
  currentPhaseIndex = 0,
  questionsAsked = 0,
  completeness = 0,
}) => {
  const phases = [
    { title: '1. Symptoms & Onset', desc: 'Chief complaint & timing' },
    { title: '2. Quality & Severity', desc: 'Sensation & 0–10 rating' },
    { title: '3. Radiation & Associated Signs', desc: 'Spread, dyspnea, sweating' },
    { title: '4. History & Risk Factors', desc: 'Medical history, medications' },
    { title: '5. Synthesis & Decision Support', desc: 'Clinical evaluation' },
  ];

  return (
    <div className="bg-white rounded-2xl p-5 border border-slate-200/90 shadow-xs">
      <div className="flex items-center justify-between mb-3 pb-3 border-b border-slate-100">
        <div>
          <h4 className="text-xs font-bold uppercase tracking-wider text-slate-800">
            Adaptive Clinical Interview
          </h4>
          <span className="text-[11px] text-slate-500">
            {questionsAsked > 0 ? `${questionsAsked} question${questionsAsked > 1 ? 's' : ''} asked` : 'Inquiry initiated'}
          </span>
        </div>
        <span className="text-xs font-semibold text-brand-700 bg-brand-50 px-2.5 py-1 rounded-md border border-brand-100">
          Phase {Math.min(currentPhaseIndex + 1, 5)} of 5
        </span>
      </div>

      {completeness > 0 && (
        <div className="mb-4">
          <div className="flex justify-between text-[11px] text-slate-500 mb-1">
            <span>Information Completeness</span>
            <span className="font-semibold text-slate-700">{completeness}%</span>
          </div>
          <div className="w-full bg-slate-100 rounded-full h-1.5 overflow-hidden">
            <div 
              className="bg-brand-600 h-1.5 rounded-full transition-all duration-300"
              style={{ width: `${Math.min(completeness, 100)}%` }}
            />
          </div>
        </div>
      )}

      <div className="space-y-3.5">
        {phases.map((phase, idx) => {
          const isDone = idx < currentPhaseIndex;
          const isCurrent = idx === currentPhaseIndex;

          let icon = <Circle className="w-4 h-4 text-slate-300" />;
          let titleColor = 'text-slate-400';

          if (isDone) {
            icon = <CheckCircle2 className="w-4 h-4 text-emerald-600" />;
            titleColor = 'text-slate-700 font-medium';
          } else if (isCurrent) {
            icon = (
              <div className="w-4 h-4 rounded-full border-2 border-brand-700 flex items-center justify-center">
                <div className="w-1.5 h-1.5 bg-brand-700 rounded-full" />
              </div>
            );
            titleColor = 'text-brand-950 font-bold';
          }

          return (
            <div key={idx} className="flex items-start space-x-3">
              <div className="mt-0.5 flex-shrink-0">{icon}</div>
              <div className="flex-1 min-w-0">
                <div className={`text-xs ${titleColor}`}>
                  {phase.title}
                </div>
                <div className="text-[11px] text-slate-500">
                  {phase.desc}
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
