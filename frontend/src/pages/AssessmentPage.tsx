import React, { useState, useEffect, useRef } from 'react';
import { 
  Send, 
  Stethoscope, 
  Activity, 
  AlertOctagon, 
  HeartPulse
} from 'lucide-react';
import type { Patient, HealthMetrics, ChatMessage, ReportData } from '../types/api';
import { apiService } from '../services/api';
import { AIMessage } from '../components/medical/AIMessage';
import { PatientMessage } from '../components/medical/PatientMessage';
import { LoadingAssessment } from '../components/medical/LoadingAssessment';
import { ClinicalTimeline } from '../components/medical/ClinicalTimeline';

interface AssessmentPageProps {
  assessmentId: string;
  patient: Patient;
  metrics: HealthMetrics;
  initialTranscript?: ChatMessage[];
  onAssessmentCompleted: (reportData: ReportData, transcript: ChatMessage[]) => void;
  onEmergencyDetected: (reportData: ReportData) => void;
}

function formatIndianTime(date = new Date()): string {
  return date.toLocaleTimeString('en-IN', {
    timeZone: 'Asia/Kolkata',
    hour: '2-digit',
    minute: '2-digit',
  });
}

export const AssessmentPage: React.FC<AssessmentPageProps> = ({
  assessmentId,
  patient,
  metrics,
  initialTranscript = [],
  onAssessmentCompleted,
  onEmergencyDetected,
}) => {
  // Dr. Cardia initial warm greeting
  const initialGreeting: ChatMessage = {
    role: 'assistant',
    content: "Hello. I'm here to help understand what you're experiencing. Please describe what you're feeling right now, in your own words.",
    timestamp: formatIndianTime()
  };

  const [messages, setMessages] = useState<ChatMessage[]>(() => (
    initialTranscript.length > 0 ? [initialGreeting, ...initialTranscript] : [initialGreeting]
  ));
  const [inputText, setInputText] = useState<string>('');
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [lastFailedMessage, setLastFailedMessage] = useState<string | null>(null);
  const [turnCount, setTurnCount] = useState<number>(Math.floor(initialTranscript.length / 2));
  const [questionsAsked, setQuestionsAsked] = useState<number>(Math.floor(initialTranscript.length / 2));
  const [completeness, setCompleteness] = useState<number>(0);
  const [currentPhaseIndex, setCurrentPhaseIndex] = useState<number>(() => {
    const turns = Math.floor(initialTranscript.length / 2);
    return turns <= 0 ? 0 : Math.min(turns + 1, 4);
  });

  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isLoading]);

  useEffect(() => {
    inputRef.current?.focus();
  }, []);

  const handleReportTrigger = (reportData: ReportData, transcript: ChatMessage[]) => {
    const isCatA = 
      (reportData.triage_category_level || '').toUpperCase().includes('CATEGORY A') ||
      (reportData.triage_category_level || '').toUpperCase().includes('EMERGENCY');

    if (isCatA) {
      onEmergencyDetected(reportData);
    } else {
      onAssessmentCompleted(reportData, transcript);
    }
  };

  const handleSendMessage = async (customMessage?: string) => {
    const messageToSend = customMessage || inputText.trim();
    if (!messageToSend || isLoading) return;

    setInputText('');
    setError(null);
    setLastFailedMessage(null);

    const userMsg: ChatMessage = {
      role: 'user',
      content: messageToSend,
      timestamp: formatIndianTime()
    };

    const isRetry = Boolean(customMessage && lastFailedMessage === messageToSend);
    const newTranscript = isRetry ? messages : [...messages, userMsg];
    setMessages(newTranscript);
    setIsLoading(true);

    try {
      // Send the real patient message to the Flask AI engine
      const response = await apiService.sendAssessmentMessage(assessmentId, messageToSend);
      const responseMessage = response.message_to_patient || response.ai_response;
      if (!responseMessage) {
        throw new Error('Assessment service returned an incomplete response. Please try again.');
      }

      const aiMsg: ChatMessage = {
        role: 'assistant',
        content: responseMessage,
        timestamp: formatIndianTime()
      };

      const updatedTranscript = [...newTranscript, aiMsg];
      setMessages(updatedTranscript);

      const newTurns = turnCount + 1;
      setTurnCount(newTurns);
      if (response.questions_asked !== undefined) {
        setQuestionsAsked(response.questions_asked);
      } else {
        setQuestionsAsked(newTurns);
      }
      if (response.completeness !== undefined) {
        setCompleteness(response.completeness);
      }

      // Phase tracker progression
      const activeQuestions = response.questions_asked ?? newTurns;
      if (activeQuestions <= 1) setCurrentPhaseIndex(1); // Characteristics
      else if (activeQuestions === 2) setCurrentPhaseIndex(2); // Radiation & Associated
      else if (activeQuestions <= 4) setCurrentPhaseIndex(3); // History & Risks
      else setCurrentPhaseIndex(4); // Clinical Summary

      // Check if the AI determined report completion or emergency
      if (response.is_report && response.report_data) {
        handleReportTrigger(response.report_data, updatedTranscript);
      }
    } catch (err: unknown) {
      console.error('Assessment consultation error:', err);
      setLastFailedMessage(messageToSend);
      setError(err instanceof Error
        ? err.message
        : 'Assessment service temporarily unavailable. Please try again.');
    } finally {
      setIsLoading(false);
      setTimeout(() => inputRef.current?.focus(), 150);
    }
  };

  return (
    <div className="min-h-screen bg-slate-100/70 py-6 px-4 sm:px-6 lg:px-8">
      <div className="max-w-7xl mx-auto">
        
        {/* Assessment Hospital Header */}
        <div className="bg-white rounded-2xl p-4 sm:p-5 border border-slate-200/90 shadow-xs mb-6 flex flex-col sm:flex-row items-center justify-between gap-4">
          <div className="flex items-center space-x-3.5">
            <div className="w-10 h-10 rounded-xl bg-brand-700 text-white flex items-center justify-center font-bold shadow-md shadow-brand-700/20">
              <HeartPulse className="w-5 h-5 text-white" />
            </div>
            <div>
              <div className="flex items-center space-x-2">
                <h1 className="text-base sm:text-lg font-extrabold text-slate-900 tracking-tight">
                  Cardiac Assessment
                </h1>
                <span className="text-[10px] px-2 py-0.5 rounded-full font-mono font-bold bg-brand-50 text-brand-800 border border-brand-200">
                  {patient.uhid}
                </span>
              </div>
              <p className="text-xs text-slate-500">
                Patient: <strong className="text-slate-800">{patient.full_name}</strong> • Age {patient.age} • {patient.gender}
              </p>
            </div>
          </div>

          <div className="flex items-center space-x-3 text-xs">
            <div className="px-3 py-1.5 rounded-lg bg-emerald-50 border border-emerald-200 text-emerald-800 font-semibold flex items-center space-x-1.5">
              <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
              <span>Assessment in Progress</span>
            </div>
          </div>
        </div>

        {/* Two-Column Clinical Layout */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
          
          {/* LEFT: Consultation Area (8 cols) */}
          <div className="lg:col-span-8 flex flex-col bg-white rounded-2xl border border-slate-200/90 shadow-sm overflow-hidden" style={{ minHeight: '620px' }}>
            
            {/* Consultation Top Bar */}
            <div className="px-6 py-3.5 bg-slate-50 border-b border-slate-200 flex items-center justify-between text-xs text-slate-600">
              <div className="flex items-center space-x-2 font-semibold">
                <Stethoscope className="w-4 h-4 text-brand-700" />
                <span>Consultation with Dr. Cardia</span>
              </div>
                <span className="text-slate-400">AI-assisted care</span>
            </div>

            {/* Chat Messages Feed */}
            <div className="flex-1 p-6 overflow-y-auto space-y-4 max-h-[520px]">
              {messages.map((msg, idx) => {
                if (msg.role === 'assistant') {
                  const isLatest = idx === messages.length - 1;
                  return (
                    <AIMessage
                      key={idx}
                      content={msg.content}
                      timestamp={msg.timestamp}
                      isLatest={isLatest}
                    />
                  );
                } else if (msg.role === 'user') {
                  return (
                    <PatientMessage
                      key={idx}
                      content={msg.content}
                      timestamp={msg.timestamp}
                    />
                  );
                }
                return null;
              })}

              {/* Reviewing Response Loading Animation */}
              {isLoading && (
                <LoadingAssessment
                  statusText="Dr. Cardia is reviewing your response"
                  subText="Analyzing symptoms and risk indicators"
                />
              )}

              {/* Error Callout */}
              {error && (
                <div className="bg-red-50 border border-red-200 rounded-xl p-4 text-xs text-red-800 flex items-start space-x-2 my-2">
                  <AlertOctagon className="w-4 h-4 text-red-600 flex-shrink-0 mt-0.5" />
                  <div className="flex-1">
                    <strong>Connection notice:</strong> {error}
                    <button
                      onClick={() => lastFailedMessage && handleSendMessage(lastFailedMessage)}
                      disabled={!lastFailedMessage || isLoading}
                      className="block mt-1 font-bold text-red-700 underline"
                    >
                      Retry sending response
                    </button>
                  </div>
                </div>
              )}

              <div ref={messagesEndRef} />
            </div>

            {/* Response Input Area — Starts 100% EMPTY by default */}
            <div className="p-4 sm:p-5 bg-white border-t border-slate-200">
              <form
                onSubmit={(e) => {
                  e.preventDefault();
                  handleSendMessage();
                }}
                className="flex items-center space-x-3"
              >
                <div className="relative flex-1">
                  <input
                    ref={inputRef}
                    type="text"
                    value={inputText}
                    onChange={(e) => setInputText(e.target.value)}
                    disabled={isLoading}
                    placeholder={
                      turnCount === 0
                        ? "Describe what you're experiencing in your own words..."
                        : "Type your reply to Dr. Cardia..."
                    }
                    className="w-full px-4 py-3.5 rounded-xl border border-slate-300 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500/20 focus:border-brand-600 disabled:bg-slate-50 disabled:text-slate-400 placeholder:text-slate-400"
                  />
                </div>

                <button
                  type="submit"
                  disabled={!inputText.trim() || isLoading}
                  className="inline-flex items-center justify-center px-6 py-3.5 bg-brand-700 hover:bg-brand-800 active:bg-brand-900 disabled:bg-slate-300 text-white font-bold rounded-xl shadow-xs transition-all text-sm flex-shrink-0"
                >
                  <Send className="w-4 h-4 mr-1.5" />
                  <span>Send</span>
                </button>
              </form>
              <div className="flex items-center justify-between text-[11px] text-slate-400 mt-2 px-1">
                <span>Press Enter to send response</span>
                <span>Speak naturally in your own words</span>
              </div>
            </div>

          </div>

          {/* RIGHT: Clinical Context Panel (4 cols) */}
          <div className="lg:col-span-4 space-y-5">
            
            {/* Adaptive Clinical Timeline Tracker */}
            <ClinicalTimeline
              currentPhaseIndex={currentPhaseIndex}
              questionsAsked={questionsAsked}
              completeness={completeness}
            />

            {/* Baseline Health Vitals Card */}
            <div className="bg-white rounded-2xl p-5 border border-slate-200/90 shadow-xs">
              <h4 className="text-xs font-bold uppercase tracking-wider text-slate-700 mb-3 flex items-center space-x-2">
                <Activity className="w-4 h-4 text-brand-700" />
                <span>Recorded Baseline Vitals</span>
              </h4>

              <div className="grid grid-cols-2 gap-3 text-xs">
                <div className="bg-slate-50 p-3 rounded-xl border border-slate-100">
                  <span className="text-slate-400 block text-[10px] uppercase font-bold">Blood Pressure</span>
                  <span className="text-slate-900 font-mono font-bold text-sm">{metrics.blood_pressure_status}</span>
                </div>
                <div className="bg-slate-50 p-3 rounded-xl border border-slate-100">
                  <span className="text-slate-400 block text-[10px] uppercase font-bold">Heart Rate</span>
                  <span className="text-slate-900 font-mono font-bold text-sm">{metrics.resting_heart_rate_status}</span>
                </div>
                <div className="bg-slate-50 p-3 rounded-xl border border-slate-100">
                  <span className="text-slate-400 block text-[10px] uppercase font-bold">Blood Glucose</span>
                  <span className="text-slate-900 font-medium">{metrics.blood_glucose_status || 'Not reported'}</span>
                </div>
                <div className="bg-slate-50 p-3 rounded-xl border border-slate-100">
                  <span className="text-slate-400 block text-[10px] uppercase font-bold">Past Cardiac History</span>
                  <span className="text-slate-900 font-medium truncate">{metrics.past_ecg_history || 'Not reported'}</span>
                </div>
              </div>
            </div>

            {/* Emergency 112 Protocol Advisory */}
            <div className="bg-red-50/80 border border-red-200 rounded-2xl p-4 text-xs text-red-900 space-y-1.5">
              <div className="flex items-center space-x-1.5 font-bold text-red-800">
                <AlertOctagon className="w-4 h-4 text-red-600" />
                <span>Emergency Guidance (India)</span>
              </div>
              <p className="text-[11px] text-red-800/90 leading-relaxed">
                If your pain is crushing, spreading to your jaw/left arm, or accompanied by sweating or breathlessness, call <strong>112</strong> immediately.
              </p>
            </div>

          </div>

        </div>

      </div>
    </div>
  );
};
