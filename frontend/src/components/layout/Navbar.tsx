import React from 'react';
import { HeartPulse, Shield, Activity, Beaker } from 'lucide-react';

interface NavbarProps {
  currentView: string;
  onNavigate: (view: string) => void;
  isAssessmentActive?: boolean;
  hasReport?: boolean;
  onOpenDemoMode?: () => void;
}

export const Navbar: React.FC<NavbarProps> = ({
  currentView,
  onNavigate,
  isAssessmentActive = false,
  hasReport = false,
  onOpenDemoMode,
}) => {
  const handleNavClick = (view: string) => {
    if (isAssessmentActive && view !== currentView) {
      const confirmLeave = window.confirm(
        'An assessment session is currently in progress. Leaving this page may interrupt your consultation. Do you wish to proceed?'
      );
      if (!confirmLeave) return;
    }
    onNavigate(view);
  };

  return (
    <header className="sticky top-0 z-40 bg-white/95 backdrop-blur-md border-b border-slate-200/80 transition-all no-print">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Brand Logo & Clinical Title */}
          <div 
            onClick={() => handleNavClick('landing')}
            className="flex items-center space-x-3 cursor-pointer group"
          >
            <div className="w-10 h-10 rounded-xl bg-brand-700 text-white flex items-center justify-center shadow-md shadow-brand-700/20 group-hover:bg-brand-800 transition-all">
              <HeartPulse className="w-6 h-6 text-white" />
            </div>
            <div>
              <div className="flex items-center space-x-2">
                <span className="text-lg font-black tracking-tight text-slate-900">
                  CARDIAC CARE
                </span>
                <span className="text-[10px] px-2 py-0.5 bg-brand-50 text-brand-800 rounded-full font-bold border border-brand-200">
                  AI-ASSISTED
                </span>
              </div>
              <p className="text-[10px] text-slate-500 font-semibold tracking-wider uppercase">
                AI-Assisted Cardiac Assessment
              </p>
            </div>
          </div>

          {/* Desktop Navigation Links */}
          <nav className="hidden md:flex items-center space-x-1">
            <button
              onClick={() => handleNavClick('landing')}
              className={`px-3.5 py-2 rounded-lg text-sm font-medium transition-all ${
                currentView === 'landing'
                  ? 'bg-brand-50 text-brand-700 font-semibold'
                  : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100'
              }`}
            >
              Overview
            </button>
            <button
              onClick={() => handleNavClick('onboarding')}
              className={`px-3.5 py-2 rounded-lg text-sm font-medium transition-all ${
                currentView === 'onboarding'
                  ? 'bg-brand-50 text-brand-700 font-semibold'
                  : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100'
              }`}
            >
              Patient
            </button>
            {isAssessmentActive && (
              <button
                onClick={() => handleNavClick('assessment')}
                className={`px-3.5 py-2 rounded-lg text-sm font-medium transition-all flex items-center space-x-1.5 ${
                  currentView === 'assessment'
                    ? 'bg-brand-50 text-brand-700 font-semibold'
                    : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100'
                }`}
              >
                <Activity className="w-4 h-4 text-brand-600 animate-pulse" />
                <span>Assessment</span>
              </button>
            )}
            {hasReport && (
              <button
                onClick={() => handleNavClick('report')}
                className={`px-3.5 py-2 rounded-lg text-sm font-medium transition-all ${
                  currentView === 'report'
                    ? 'bg-brand-50 text-brand-700 font-semibold'
                    : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100'
                }`}
              >
                Clinical Summary
              </button>
            )}
          </nav>

          {/* Right Status & Action Area */}
          <div className="flex items-center space-x-3">
            {/* Discrete Demo Mode button for Evaluators */}
            {onOpenDemoMode && (
              <button
                onClick={onOpenDemoMode}
                title="Open Demonstration Mode"
                className="hidden sm:inline-flex items-center space-x-1.5 py-1.5 px-3 rounded-lg border border-slate-200 hover:bg-slate-100 text-slate-600 text-xs font-medium transition-all"
              >
                <Beaker className="w-3.5 h-3.5 text-slate-500" />
                <span>Demo Mode</span>
              </button>
            )}

            <button
              onClick={() => handleNavClick('onboarding')}
              className="inline-flex items-center space-x-2 py-2 px-4 bg-brand-700 hover:bg-brand-800 active:bg-brand-900 text-white text-xs sm:text-sm font-semibold rounded-xl shadow-sm transition-all"
            >
              <Shield className="w-4 h-4" />
              <span>Start Assessment</span>
            </button>
          </div>
        </div>
      </div>
    </header>
  );
};
