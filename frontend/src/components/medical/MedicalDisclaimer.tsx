import React from 'react';
import { AlertCircle, PhoneCall } from 'lucide-react';

interface MedicalDisclaimerProps {
  className?: string;
  variant?: 'banner' | 'card' | 'minimal';
}

export const MedicalDisclaimer: React.FC<MedicalDisclaimerProps> = ({
  className = '',
  variant = 'card',
}) => {
  if (variant === 'banner') {
    return (
      <div className={`bg-brand-50 border-b border-brand-100 py-2.5 px-4 text-xs text-brand-950 flex flex-wrap items-center justify-center gap-2 ${className}`}>
        <div className="flex items-center space-x-1.5 font-medium text-center">
          <AlertCircle className="w-4 h-4 text-brand-700 flex-shrink-0" />
          <span>
            <strong>Clinical Notice:</strong> This AI-assisted assessment supports preliminary clinical evaluation and does not replace examination by a qualified physician.
          </span>
        </div>
        <span className="hidden sm:inline text-brand-300">•</span>
        <a
          href="tel:112"
          className="inline-flex items-center space-x-1 text-red-700 hover:text-red-800 font-bold underline"
        >
          <PhoneCall className="w-3.5 h-3.5" />
          <span>Emergency: 112</span>
        </a>
      </div>
    );
  }

  if (variant === 'minimal') {
    return (
      <p className={`text-xs text-slate-500 leading-relaxed ${className}`}>
        This AI-assisted assessment is intended to support preliminary clinical assessment and decision support. It does not establish a definitive medical diagnosis and does not replace evaluation by a qualified healthcare professional.
      </p>
    );
  }

  return (
    <div className={`bg-slate-50 border border-slate-200 rounded-xl p-4 flex items-start space-x-3 text-xs text-slate-700 leading-relaxed ${className}`}>
      <AlertCircle className="w-5 h-5 text-brand-700 flex-shrink-0 mt-0.5" />
      <div>
        <span className="font-bold text-slate-900 block mb-0.5">
          Medical Safety & Clinical Guidance
        </span>
        This AI-assisted assessment is designed to support preliminary clinical assessment and does not replace evaluation by a qualified healthcare professional. If you are experiencing severe or rapidly worsening chest pain, difficulty breathing, fainting or other serious symptoms, seek emergency medical attention immediately by calling <strong>112</strong>.
      </div>
    </div>
  );
};
