import React from 'react';
import { 
  HeartPulse, 
  ArrowRight, 
  ShieldCheck, 
  Clock, 
  Activity, 
  AlertTriangle, 
  Stethoscope, 
  Lock,
  PhoneCall
} from 'lucide-react';
import { ECGPulse } from '../components/medical/ECGPulse';
import { MedicalDisclaimer } from '../components/medical/MedicalDisclaimer';

interface LandingPageProps {
  onStartAssessment: () => void;
}

export const LandingPage: React.FC<LandingPageProps> = ({ onStartAssessment }) => {
  const scrollToHowItWorks = () => {
    const el = document.getElementById('how-it-works');
    if (el) {
      el.scrollIntoView({ behavior: 'smooth' });
    }
  };

  return (
    <div className="flex flex-col min-h-screen">
      {/* Top Clinical & Safety Disclaimer Banner */}
      <MedicalDisclaimer variant="banner" />

      {/* HERO SECTION */}
      <section className="relative overflow-hidden bg-gradient-to-b from-brand-50/60 via-slate-50 to-white pt-12 pb-20 lg:pt-20 lg:pb-28 clinical-grid">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-12 items-center">
            
            {/* Left Hero Content (7 cols) */}
            <div className="lg:col-span-7 space-y-6">
              {/* Small Label */}
              <div className="inline-flex items-center space-x-2 px-3.5 py-1.5 rounded-full bg-brand-100/90 border border-brand-200/90 text-brand-900 text-xs font-bold uppercase tracking-wider">
                <HeartPulse className="w-4 h-4 text-brand-700 animate-pulse" />
                <span>AI-Assisted Cardiac Care</span>
              </div>

              {/* Main Heading */}
              <h1 className="text-4xl sm:text-5xl lg:text-6xl font-extrabold text-slate-900 tracking-tight leading-[1.14]">
                Understand Your Heart.{' '}
                <span className="text-transparent bg-clip-text bg-gradient-to-r from-brand-700 via-brand-600 to-clinical-cyan">
                  Act When It Matters.
                </span>
              </h1>

              {/* Supporting Text */}
              <p className="text-lg sm:text-xl text-slate-600 max-w-2xl font-normal leading-relaxed">
                An intelligent cardiac assessment experience designed to structure symptoms, health information and risk indicators into a clear clinical assessment.
              </p>

              {/* Primary & Secondary Action CTAs */}
              <div className="flex flex-col sm:flex-row gap-4 pt-4">
                <button
                  onClick={onStartAssessment}
                  className="inline-flex items-center justify-center space-x-2 py-4 px-8 bg-brand-700 hover:bg-brand-800 active:bg-brand-900 text-white font-bold rounded-xl shadow-lg shadow-brand-700/25 transition-all text-base group"
                >
                  <span>Start Cardiac Assessment</span>
                  <ArrowRight className="w-5 h-5 group-hover:translate-x-1 transition-transform" />
                </button>

                <button
                  onClick={scrollToHowItWorks}
                  className="inline-flex items-center justify-center space-x-2 py-4 px-7 bg-white hover:bg-slate-50 text-slate-700 font-semibold rounded-xl border border-slate-300 shadow-xs transition-all text-base"
                >
                  <span>How It Works</span>
                </button>
              </div>

              {/* Emergency Hotline strip */}
              <div className="pt-2 flex items-center space-x-4 text-xs text-slate-500">
                <a href="tel:112" className="flex items-center space-x-1.5 text-red-700 hover:text-red-800 font-bold transition-colors">
                  <PhoneCall className="w-3.5 h-3.5" />
                  <span>Emergency: 112</span>
                </a>
                <span>•</span>
                <div className="flex items-center space-x-1">
                  <Lock className="w-3.5 h-3.5 text-slate-400" />
                  <span>Confidential Clinical Session</span>
                </div>
              </div>
            </div>

            {/* Right Hero Visual Card (5 cols) */}
            <div className="lg:col-span-5">
              <div className="relative mx-auto max-w-md">
                {/* Subtle medical ambient glow */}
                <div className="absolute -inset-2 bg-gradient-to-r from-brand-600/15 to-clinical-cyan/15 rounded-3xl blur-xl -z-10" />

                {/* Main Cardiology Monitor Card */}
                <div className="bg-white/95 backdrop-blur-md rounded-2xl border border-slate-200/90 shadow-xl p-6 relative overflow-hidden">
                  
                  {/* Top Monitor Bar */}
                  <div className="flex items-center justify-between border-b border-slate-100 pb-3 mb-4">
                    <div className="flex items-center space-x-2">
                      <div className="w-2.5 h-2.5 rounded-full bg-emerald-500 animate-pulse" />
                      <span className="text-xs font-bold text-slate-800 uppercase tracking-wider">
                        Cardiac Assessment
                      </span>
                    </div>
                    <span className="text-[11px] font-mono text-slate-500">
                      Ready to begin
                    </span>
                  </div>

                  {/* Anatomical Heart & ECG Telemetry Display */}
                  <div className="bg-slate-900 rounded-xl p-4 my-3 text-emerald-400 shadow-inner relative overflow-hidden">
                    <div className="flex items-center justify-between text-xs mb-1 font-mono text-emerald-400/80">
                      <span>Heart assessment</span>
                      <span className="flex items-center space-x-1 font-bold">
                        <Activity className="w-3.5 h-3.5 animate-pulse" />
                        <span>READY</span>
                      </span>
                    </div>
                    <ECGPulse height={64} color="#10b981" />
                    <div className="flex justify-between text-[10px] font-mono text-slate-400 mt-1">
                      <span>HEART</span>
                      <span>CARE</span>
                      <span>READY</span>
                    </div>
                  </div>

                  {/* Dr. Cardia Consultation Card Preview */}
                  <div className="space-y-3 mt-4">
                    <div className="bg-brand-50/90 border border-brand-100 rounded-xl p-3 text-xs leading-relaxed text-slate-900">
                      <div className="flex items-center space-x-1.5 text-brand-800 font-bold mb-1">
                        <Stethoscope className="w-3.5 h-3.5" />
                        <span>Meet Dr. Cardia</span>
                      </div>
                      Your AI-assisted cardiac assessment companion.
                    </div>

                  </div>

                  {/* Clinical Decision Support Status */}
                  <div className="mt-5 pt-3 border-t border-slate-100 flex items-center justify-between text-xs">
                    <span className="text-slate-500 font-medium">Assessment status:</span>
                    <span className="px-2.5 py-0.5 rounded-md bg-brand-50 text-brand-800 border border-brand-200 font-bold">
                      Ready to begin
                    </span>
                  </div>
                </div>
              </div>
            </div>

          </div>
        </div>
      </section>

      {/* HOW IT WORKS SECTION */}
      <section id="how-it-works" className="py-20 bg-white border-t border-slate-200/80">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center max-w-3xl mx-auto mb-16">
            <span className="text-xs font-bold uppercase tracking-wider text-brand-700 bg-brand-50 px-3.5 py-1 rounded-full border border-brand-200">
              Simple Assessment Steps
            </span>
            <h2 className="text-3xl sm:text-4xl font-extrabold text-slate-900 tracking-tight mt-3">
              How It Works
            </h2>
            <p className="text-base text-slate-600 mt-3 leading-relaxed">
              A phased clinical assessment methodology structured around patient-reported symptoms and cardiology triage protocols.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8">
            {/* Step 1 */}
            <div className="bg-slate-50 rounded-2xl p-6 border border-slate-200/90 hover:shadow-md transition-all relative">
              <div className="w-10 h-10 rounded-xl bg-brand-100 text-brand-800 font-extrabold flex items-center justify-center mb-4 text-base">
                01
              </div>
              <h3 className="text-lg font-bold text-slate-900 mb-2">
                Patient Information
              </h3>
              <p className="text-sm text-slate-600 leading-relaxed">
                Share your basic details and an emergency contact so your assessment can be prepared safely.
              </p>
            </div>

            {/* Step 2 */}
            <div className="bg-slate-50 rounded-2xl p-6 border border-slate-200/90 hover:shadow-md transition-all relative">
              <div className="w-10 h-10 rounded-xl bg-clinical-sky/20 text-clinical-sky font-extrabold flex items-center justify-center mb-4 text-base">
                02
              </div>
              <h3 className="text-lg font-bold text-slate-900 mb-2">
                Health & Vital Information
              </h3>
              <p className="text-sm text-slate-600 leading-relaxed">
                Record baseline blood pressure, resting heart rate, blood glucose status, and any past cardiac history to provide clinical context.
              </p>
            </div>

            {/* Step 3 */}
            <div className="bg-slate-50 rounded-2xl p-6 border border-slate-200/90 hover:shadow-md transition-all relative">
              <div className="w-10 h-10 rounded-xl bg-clinical-teal/20 text-clinical-teal font-extrabold flex items-center justify-center mb-4 text-base">
                03
              </div>
              <h3 className="text-lg font-bold text-slate-900 mb-2">
                AI-Assisted Cardiac Interview
              </h3>
              <p className="text-sm text-slate-600 leading-relaxed">
                Describe your symptoms in your own words. Dr. Cardia guides you through the details that help make your health information clear.
              </p>
            </div>

            {/* Step 4 */}
            <div className="bg-slate-50 rounded-2xl p-6 border border-slate-200/90 hover:shadow-md transition-all relative">
              <div className="w-10 h-10 rounded-xl bg-brand-700 text-white font-extrabold flex items-center justify-center mb-4 text-base">
                04
              </div>
              <h3 className="text-lg font-bold text-slate-900 mb-2">
                Clinical Assessment Summary
              </h3>
              <p className="text-sm text-slate-600 leading-relaxed">
                Receive a clear summary of the information you shared and the next steps suggested by the assessment.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* CLINICAL RIGOR & SAFETY SECTION */}
      <section className="py-20 bg-slate-50 border-t border-slate-200/80">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center max-w-3xl mx-auto mb-16">
            <span className="text-xs font-bold uppercase tracking-wider text-clinical-teal bg-teal-50 px-3.5 py-1 rounded-full border border-teal-200">
              Care That Is Easy To Follow
            </span>
            <h2 className="text-3xl sm:text-4xl font-extrabold text-slate-900 tracking-tight mt-3">
              A calmer way to prepare for care
            </h2>
            <p className="text-base text-slate-600 mt-3 leading-relaxed">
              Designed with calm, focused questions and comprehensive risk factor extraction.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            <div className="bg-white rounded-2xl p-6 border border-slate-200/90 shadow-xs">
              <div className="w-12 h-12 rounded-xl bg-brand-50 text-brand-700 flex items-center justify-center mb-4">
                <Clock className="w-6 h-6" />
              </div>
              <h3 className="text-lg font-bold text-slate-900 mb-2">
                Guided Questions
              </h3>
              <p className="text-sm text-slate-600 leading-relaxed">
                Dr. Cardia keeps the conversation focused with one clear, clinically relevant question at a time.
              </p>
            </div>

            <div className="bg-white rounded-2xl p-6 border border-slate-200/90 shadow-xs">
              <div className="w-12 h-12 rounded-xl bg-red-50 text-red-600 flex items-center justify-center mb-4">
                <AlertTriangle className="w-6 h-6" />
              </div>
              <h3 className="text-lg font-bold text-slate-900 mb-2">
                Urgent Symptoms
              </h3>
              <p className="text-sm text-slate-600 leading-relaxed">
                Helps bring urgent symptoms to attention quickly so you know when to seek immediate care.
              </p>
            </div>

            <div className="bg-white rounded-2xl p-6 border border-slate-200/90 shadow-xs">
              <div className="w-12 h-12 rounded-xl bg-emerald-50 text-emerald-600 flex items-center justify-center mb-4">
                <ShieldCheck className="w-6 h-6" />
              </div>
              <h3 className="text-lg font-bold text-slate-900 mb-2">
                Organized Health History
              </h3>
              <p className="text-sm text-slate-600 leading-relaxed">
                Keeps the details you share organized so they are easier to review with a healthcare professional.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* CTA BOTTOM BANNER */}
      <section className="bg-brand-900 text-white py-16 relative overflow-hidden">
        <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 text-center relative z-10">
          <h2 className="text-3xl sm:text-4xl font-extrabold tracking-tight mb-4">
            Begin Your Cardiac Assessment
          </h2>
          <p className="text-slate-300 max-w-2xl mx-auto mb-8 text-base">
            Take a guided 3 to 5 minute clinical assessment to structure your symptoms and receive an immediate decision support summary.
          </p>
          <button
            onClick={onStartAssessment}
            className="inline-flex items-center space-x-2 py-4 px-8 bg-white hover:bg-brand-50 text-brand-900 font-bold rounded-xl shadow-lg transition-all text-base"
          >
            <span>Start Assessment Now</span>
            <ArrowRight className="w-5 h-5" />
          </button>
        </div>
      </section>

      {/* Bottom Medical Safety Card */}
      <div className="max-w-5xl mx-auto px-4 py-8">
        <MedicalDisclaimer variant="card" />
      </div>
    </div>
  );
};
