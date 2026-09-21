import React from 'react';
import { ShieldAlert, PhoneCall, ArrowRight, HeartPulse, AlertCircle } from 'lucide-react';
import type { ReportData } from '../../types/api';

interface EmergencyAlertProps {
  reportData: ReportData;
  onViewReport: () => void;
}

export const EmergencyAlert: React.FC<EmergencyAlertProps> = ({
  reportData,
  onViewReport
}) => {
  const primaryConcern = 
    reportData.leading_concern?.possible_condition ||
    reportData.primary_suspected_pattern ||
    "Possible Acute Coronary Syndrome";

  return (
    <div className="min-h-screen bg-slate-950 text-white flex flex-col justify-between p-6 sm:p-12 relative overflow-hidden">
      {/* Background ambient lighting */}
      <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_top,_var(--tw-gradient-stops))] from-red-950/50 via-slate-950 to-black -z-10" />

      {/* Hospital Clinical Header */}
      <div className="max-w-4xl mx-auto w-full flex items-center justify-between border-b border-slate-800 pb-6">
        <div className="flex items-center space-x-3">
          <div className="p-2.5 bg-red-600 text-white rounded-xl shadow-md">
            <HeartPulse className="w-6 h-6" />
          </div>
          <div>
            <span className="text-[10px] font-bold tracking-widest text-red-400 uppercase">
              Emergency Clinical Advisory
            </span>
            <h1 className="text-xl font-black tracking-tight text-white">
              CARDIAC CARE
            </h1>
          </div>
        </div>

        <div className="text-right">
          <span className="text-xs px-3 py-1 bg-red-950/90 border border-red-800 text-red-200 rounded-full font-bold">
            URGENT MEDICAL ATTENTION RECOMMENDED
          </span>
        </div>
      </div>

      {/* Main Alert Container */}
      <div className="max-w-3xl mx-auto w-full my-auto py-8">
        <div className="bg-slate-900/95 border-2 border-red-600/90 rounded-2xl p-6 sm:p-10 shadow-2xl backdrop-blur-md">
          
          <div className="flex items-center space-x-3.5 mb-6">
            <div className="p-2.5 bg-red-600/20 text-red-500 rounded-xl">
              <ShieldAlert className="w-8 h-8" />
            </div>
            <div>
              <h2 className="text-2xl sm:text-3xl font-extrabold text-white tracking-tight">
                POTENTIALLY SERIOUS CARDIAC SYMPTOMS
              </h2>
              <p className="text-xs text-red-400 font-semibold mt-0.5">
                URGENT MEDICAL ATTENTION RECOMMENDED
              </p>
            </div>
          </div>

          <div className="bg-red-950/40 border border-red-800/80 rounded-xl p-5 mb-6 space-y-2">
            <div className="flex items-center justify-between text-xs">
              <span className="font-bold text-red-300 uppercase tracking-wider">Possible Clinical Concern:</span>
              <span className="px-2.5 py-0.5 rounded-full bg-red-900/80 text-red-200 border border-red-700 text-[11px] font-bold">
                Status: Not confirmed
              </span>
            </div>
            <div className="text-lg font-bold text-white">
              {primaryConcern}
            </div>
            <p className="text-xs text-slate-300 leading-relaxed pt-1">
              <strong>Reason:</strong> Your reported symptoms include patterns that can occur with serious cardiac conditions, such as myocardial ischemia.
            </p>
          </div>

          {/* Prominent Medical Safety Principle Notice */}
          <div className="bg-slate-800/80 border border-slate-700 rounded-xl p-3.5 mb-6 text-xs text-slate-300 flex items-start space-x-2.5">
            <AlertCircle className="w-4 h-4 text-amber-400 flex-shrink-0 mt-0.5" />
            <div>
              <strong className="text-white">Important Notice: </strong>
              This is an AI-assisted preliminary assessment and does not establish a confirmed diagnosis. Immediate evaluation by a physician with a 12-lead ECG and cardiac blood tests is required.
            </div>
          </div>

          {/* Action Guidance */}
          <div className="space-y-3 mb-8">
            <h3 className="text-xs font-bold uppercase tracking-wider text-slate-400">
              Immediate Safety Steps:
            </h3>
            <ul className="space-y-2.5 text-sm text-slate-300">
              <li className="flex items-start space-x-2.5">
                <span className="text-red-400 font-bold">•</span>
                <span>Call Emergency Medical Services at <strong className="text-white">112</strong> immediately.</span>
              </li>
              <li className="flex items-start space-x-2.5">
                <span className="text-red-400 font-bold">•</span>
                <span>Do not drive yourself to the hospital. Have someone drive you or wait for an ambulance.</span>
              </li>
              <li className="flex items-start space-x-2.5">
                <span className="text-red-400 font-bold">•</span>
                <span>Sit in a comfortable upright position, stay calm, and loosen any tight clothing around your neck or chest.</span>
              </li>
            </ul>
          </div>

          {/* CTAs */}
          <div className="flex flex-col sm:flex-row gap-4 pt-4 border-t border-slate-800">
            <a
              href="tel:112"
              className="flex-1 inline-flex items-center justify-center space-x-2.5 py-4 px-6 bg-red-600 hover:bg-red-700 active:bg-red-800 text-white font-bold rounded-xl shadow-lg shadow-red-950 transition-all text-base text-center"
            >
              <PhoneCall className="w-5 h-5" />
              <span>Call 112 (Emergency)</span>
            </a>

            <button
              onClick={onViewReport}
              className="inline-flex items-center justify-center space-x-2 py-4 px-6 bg-slate-800 hover:bg-slate-700 text-slate-200 hover:text-white font-semibold rounded-xl border border-slate-700 transition-all text-base"
            >
              <span>View Clinical Summary</span>
              <ArrowRight className="w-5 h-5" />
            </button>
          </div>
        </div>
      </div>

      {/* Footer Notice */}
      <div className="max-w-4xl mx-auto w-full text-center text-xs text-slate-500 pt-4 border-t border-slate-800">
        Cardiac Care decision support protocol. Does not replace immediate hands-on clinical evaluation by medical professionals.
      </div>
    </div>
  );
};
