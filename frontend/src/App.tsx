import { useEffect, useState } from 'react';
import { Navbar } from './components/layout/Navbar';
import { Footer } from './components/layout/Footer';
import { LandingPage } from './pages/LandingPage';
import { OnboardingPage } from './pages/OnboardingPage';
import { AssessmentPage } from './pages/AssessmentPage';
import { ReportPage } from './pages/ReportPage';
import { EmergencyAlert } from './components/medical/EmergencyAlert';
import type { Patient, HealthMetrics, ReportData, ChatMessage } from './types/api';
import { apiService } from './services/api';

type ViewState = 'landing' | 'onboarding' | 'assessment' | 'emergency' | 'report';
const ACTIVE_ASSESSMENT_KEY = 'cardiac-care-active-assessment';

export function App() {
  const [currentView, setCurrentView] = useState<ViewState>('landing');
  const [assessmentId, setAssessmentId] = useState<string>('');
  const [patient, setPatient] = useState<Patient | null>(null);
  const [metrics, setMetrics] = useState<HealthMetrics | null>(null);
  const [reportData, setReportData] = useState<ReportData | null>(null);
  const [transcript, setTranscript] = useState<ChatMessage[]>([]);
  const [loadError, setLoadError] = useState<string | null>(null);

  useEffect(() => {
    const savedAssessmentId = sessionStorage.getItem(ACTIVE_ASSESSMENT_KEY);
    if (!savedAssessmentId) return;

    void apiService.getAssessment(savedAssessmentId).then(({ assessment }) => {
      if (!assessment.patients || !assessment.patient_health_metrics) return;

      setAssessmentId(assessment.id);
      setPatient(assessment.patients);
      setMetrics(assessment.patient_health_metrics);
      setTranscript(assessment.full_chat_transcript || []);

      const assessmentRecord = assessment as unknown as Record<string, unknown>;
      if (assessment.integrity && !assessment.integrity.valid) {
        console.error('[REPORT DATA INTEGRITY]', assessment.integrity.errors);
        setLoadError('This assessment contains inconsistent information and cannot be shown until it is reviewed.');
        setCurrentView('report');
        return;
      }
      if (assessment.is_complete && typeof assessmentRecord.triage_category_level === 'string') {
        setReportData(assessmentRecord as unknown as ReportData);
        const triage = assessmentRecord.triage_category_level.toUpperCase();
        setCurrentView(triage.includes('CATEGORY A') || triage.includes('EMERGENCY') ? 'emergency' : 'report');
      } else {
        setCurrentView('assessment');
      }
    }).catch(() => {
      sessionStorage.removeItem(ACTIVE_ASSESSMENT_KEY);
    });
  }, []);

  // Handlers
  const handleStartOnboarding = () => {
    setCurrentView('onboarding');
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  const handleAssessmentInitialized = (
    newAssessmentId: string,
    newPatient: Patient,
    newMetrics: HealthMetrics
  ) => {
    setAssessmentId(newAssessmentId);
    setPatient(newPatient);
    setMetrics(newMetrics);
    sessionStorage.setItem(ACTIVE_ASSESSMENT_KEY, newAssessmentId);
    setCurrentView('assessment');
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  const handleAssessmentCompleted = (
    finalReport: ReportData,
    finalTranscript: ChatMessage[]
  ) => {
    setReportData(finalReport);
    setTranscript(finalTranscript);
    sessionStorage.setItem(ACTIVE_ASSESSMENT_KEY, assessmentId);
    setCurrentView('report');
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  const handleEmergencyDetected = (finalReport: ReportData) => {
    setReportData(finalReport);
    sessionStorage.setItem(ACTIVE_ASSESSMENT_KEY, assessmentId);
    setCurrentView('emergency');
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  const handleStartNewAssessment = () => {
    setAssessmentId('');
    setPatient(null);
    setMetrics(null);
    setReportData(null);
    setTranscript([]);
    sessionStorage.removeItem(ACTIVE_ASSESSMENT_KEY);
    setCurrentView('onboarding');
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  const isAssessmentActive = currentView === 'assessment' && Boolean(assessmentId);
  const hasReport = Boolean(reportData);

  return (
    <div className="flex flex-col min-h-screen bg-slate-50 text-slate-900 font-sans">
      {/* Hide standard navbar in full-screen emergency mode */}
      {currentView !== 'emergency' && (
        <Navbar
          currentView={currentView}
          onNavigate={(view) => setCurrentView(view as ViewState)}
          isAssessmentActive={isAssessmentActive}
          hasReport={hasReport}
        />
      )}

      {/* Main Content Area */}
      <main className="flex-1">
        {loadError && (
          <div className="max-w-3xl mx-auto px-4 py-16 text-center">
            <h1 className="text-2xl font-bold text-slate-900">Assessment unavailable</h1>
            <p className="mt-3 text-slate-600">{loadError}</p>
          </div>
        )}
        {currentView === 'landing' && (
          <LandingPage onStartAssessment={handleStartOnboarding} />
        )}

        {currentView === 'onboarding' && (
          <OnboardingPage
            onAssessmentInitialized={handleAssessmentInitialized}
            onCancel={() => setCurrentView('landing')}
          />
        )}

        {currentView === 'assessment' && patient && metrics && (
          <AssessmentPage
            assessmentId={assessmentId}
            patient={patient}
            metrics={metrics}
            initialTranscript={transcript}
            onAssessmentCompleted={handleAssessmentCompleted}
            onEmergencyDetected={handleEmergencyDetected}
          />
        )}

        {currentView === 'emergency' && reportData && (
          <EmergencyAlert
            reportData={reportData}
            onViewReport={() => setCurrentView('report')}
          />
        )}

        {currentView === 'report' && reportData && patient && metrics && (
          <ReportPage
            reportData={reportData}
            patient={patient}
            metrics={metrics}
            assessmentId={assessmentId}
            transcript={transcript}
            onStartNewAssessment={handleStartNewAssessment}
          />
        )}
      </main>

      {/* Hide standard footer in emergency mode */}
      {currentView !== 'emergency' && <Footer />}

    </div>
  );
}

export default App;
