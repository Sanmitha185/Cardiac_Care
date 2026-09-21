import React from 'react';
import { HeartPulse, PhoneCall, ShieldCheck } from 'lucide-react';

export const Footer: React.FC = () => {
  return (
    <footer className="bg-slate-900 text-slate-400 text-xs border-t border-slate-800 no-print">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-8 mb-10">
          
          {/* Brand Col */}
          <div className="md:col-span-1 space-y-3">
            <div className="flex items-center space-x-2.5 text-white">
              <div className="w-8 h-8 rounded-lg bg-brand-700 flex items-center justify-center">
                <HeartPulse className="w-5 h-5 text-white" />
              </div>
              <span className="text-base font-black tracking-tight">CARDIAC CARE</span>
            </div>
            <p className="text-slate-300 font-medium text-xs">
              AI-Assisted Cardiac Assessment
            </p>
            <p className="text-slate-400 leading-relaxed text-[11px]">
              A calm, guided way to organize your cardiac health information before speaking with a healthcare professional.
            </p>
          </div>

          {/* Cardiac Assessment */}
          <div>
            <h4 className="text-slate-200 font-bold uppercase tracking-wider mb-3 text-[11px]">
              Cardiac Assessment
            </h4>
            <ul className="space-y-2 text-slate-400 text-[11px]">
              <li>Initial Symptom Evaluation</li>
              <li>Clear symptom description</li>
              <li>Everyday health questions</li>
              <li>Medical history and context</li>
              <li>Easy-to-read summary</li>
            </ul>
          </div>

          {/* Patient Care */}
          <div>
            <h4 className="text-slate-200 font-bold uppercase tracking-wider mb-3 text-[11px]">
              Patient Care & Safety
            </h4>
            <ul className="space-y-2 text-slate-400 text-[11px]">
              <li>Guided conversations</li>
              <li>Immediate Acuity Escalation</li>
              <li>Clear health information</li>
              <li>Structured care summary</li>
              <li>Private assessment session</li>
            </ul>
          </div>

          {/* Emergency Assistance in India */}
          <div className="bg-slate-800/80 border border-slate-700/80 rounded-xl p-4">
            <h4 className="text-red-400 font-bold uppercase tracking-wider mb-2 text-[11px] flex items-center space-x-1.5">
              <ShieldCheck className="w-4 h-4 text-red-400" />
              <span>Emergency Assistance</span>
            </h4>
            <p className="text-slate-300 mb-3 text-[11px] leading-relaxed">
              If you or someone nearby is experiencing severe or rapidly worsening symptoms (such as crushing chest pain, radiating arm pain, or fainting):
            </p>
            <div className="space-y-2">
              <div className="text-xs font-semibold text-white">
                Emergency support:
              </div>
              <a
                href="tel:112"
                className="inline-flex items-center space-x-2 bg-red-600 hover:bg-red-700 text-white px-4 py-2.5 rounded-lg font-bold text-xs shadow-md transition-all w-full justify-center"
              >
                <PhoneCall className="w-4 h-4" />
                <span>Call 112 Immediately</span>
              </a>
            </div>
          </div>
        </div>

        {/* Bottom Legal & Clinical Bar */}
        <div className="pt-8 border-t border-slate-800 flex flex-col sm:flex-row items-center justify-between gap-4 text-slate-500 text-[11px]">
          <p>© 2026 Cardiac Care. All rights reserved.</p>
          <p className="text-center sm:text-right max-w-xl">
            AI-assisted clinical assessment. This service does not replace evaluation by a qualified healthcare professional. In case of acute cardiac distress, please seek immediate emergency care.
          </p>
        </div>
      </div>
    </footer>
  );
};
