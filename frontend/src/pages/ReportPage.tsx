import React, { useState } from 'react';
import { jsPDF } from 'jspdf';
import { 
  Printer, 
  Download, 
  RotateCcw, 
  HeartPulse, 
  Activity, 
  FileText, 
  User, 
  AlertOctagon,
  Stethoscope,
  PhoneCall,
  AlertCircle,
  ClipboardList
} from 'lucide-react';
import type { Patient, HealthMetrics, ReportData, ChatMessage, DifferentialCondition } from '../types/api';
import { TriageBadge } from '../components/medical/TriageBadge';
import { RiskScoreGauge } from '../components/medical/RiskScoreGauge';
import { MedicalDisclaimer } from '../components/medical/MedicalDisclaimer';

interface ReportPageProps {
  reportData: ReportData;
  patient: Patient;
  metrics: HealthMetrics;
  transcript: ChatMessage[];
  assessmentId: string;
  onStartNewAssessment: () => void;
}

export const ReportPage: React.FC<ReportPageProps> = ({
  reportData,
  patient,
  metrics,
  transcript,
  assessmentId,
  onStartNewAssessment,
}) => {
  const [activeTab, setActiveTab] = useState<'patient' | 'doctor'>('patient');

  const indianDateStr = new Date().toLocaleString('en-IN', {
    timeZone: 'Asia/Kolkata',
    day: '2-digit',
    month: 'short',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  });

  const isEmergency = 
    (reportData.triage_category_level || '').toUpperCase().includes('CATEGORY A') ||
    (reportData.triage_category_level || '').toUpperCase().includes('EMERGENCY');

  const completeness = reportData.clinical_completeness_pct ?? 
    (typeof reportData.calculated_risk_score_100 === 'number' ? reportData.calculated_risk_score_100 : 0);

  const differentialList: DifferentialCondition[] = reportData.possible_conditions || [
    {
      condition: reportData.primary_suspected_pattern || "Possible Acute Coronary Syndrome",
      category: "CARDIAC",
      why_considered: "Reported symptoms feature characteristics consistent with cardiac concern.",
      supporting_findings: ["Reported chest discomfort"],
      missing_information: ["12-lead ECG", "Serum troponin biomarker", "In-person physician examination"],
      status: "Not confirmed"
    }
  ];

  const reportedSymptoms = reportData.reported_symptoms || 
    (reportData.patient_friendly_summary?.important_symptoms) || [];

  const reportedHistory = reportData.reported_history || [];

  const whatWouldChange = reportData.what_would_change_assessment || [
    "12-Lead Electrocardiogram (ECG) to assess acute ST-segment changes or ischemia",
    "Serial High-Sensitivity Cardiac Troponin (cTnI / cTnT) to evaluate myocardial necrosis",
    "Formal cardiovascular physical examination (auscultation, chest wall palpation, vital reassessment)"
  ];

  const handlePrint = () => {
    window.print();
  };

  const handleDownloadPdf = () => {
    const doc = new jsPDF({ format: 'a4', unit: 'mm' });
    const pageWidth = doc.internal.pageSize.getWidth();
    const pageHeight = doc.internal.pageSize.getHeight();
    const margin = 16;
    const contentWidth = pageWidth - margin * 2;
    let cursorY = margin;

    const ensureSpace = (needed: number) => {
      if (cursorY + needed > pageHeight - margin - 10) {
        doc.addPage();
        cursorY = margin;
      }
    };

    const addText = (text: string, size = 9, bold = false, color = '#1e293b') => {
      doc.setFont('helvetica', bold ? 'bold' : 'normal');
      doc.setFontSize(size);
      doc.setTextColor(color);
      const lines = doc.splitTextToSize(text || '', contentWidth) as string[];
      ensureSpace(lines.length * (size * 0.42) + 2);
      doc.text(lines, margin, cursorY);
      cursorY += lines.length * (size * 0.42) + 2;
    };

    const addSectionHeader = (title: string) => {
      ensureSpace(14);
      cursorY += 4;
      doc.setDrawColor('#cbd5e1');
      doc.setLineWidth(0.3);
      doc.line(margin, cursorY, pageWidth - margin, cursorY);
      cursorY += 6;
      addText(title, 11, true, '#0f172a');
    };

    // Header
    addText('CARDIAC CARE', 18, true, '#0f172a');
    addText('Clinical Decision-Support & Cardiac Assessment Summary', 10, false, '#0284c7');
    addText(`Assessment ID: ${assessmentId}  |  UHID: ${patient.uhid}  |  Date (IST): ${indianDateStr}`, 8, false, '#64748b');

    // Triage & Acuity
    cursorY += 2;
    addSectionHeader('1. Clinical Acuity & Triage Determination');
    addText(`Triage Category: ${reportData.triage_category_level}`, 10, true, isEmergency ? '#b91c1c' : '#0f172a');
    addText(`Recommended Routing: ${reportData.triage_routing_recommendation || reportData.urgency_recommendation || 'Clinical Evaluation'}`, 9, false);
    addText(`Assessment Information Completeness: ${completeness}% of core branch dimensions documented`, 9, false, '#475569');

    // Patient Demographics (Sparse: only non-empty)
    addSectionHeader('2. Patient Demographics & Baseline Vitals');
    let demoLine = `Name: ${patient.full_name}  |  Age: ${patient.age} Yrs  |  Sex: ${patient.gender}`;
    if (patient.blood_group && patient.blood_group !== 'Not reported') {
      demoLine += `  |  Blood Group: ${patient.blood_group}`;
    }
    addText(demoLine);

    if (metrics.blood_pressure_status && metrics.blood_pressure_status !== 'Not reported') {
      addText(`Blood Pressure: ${metrics.blood_pressure_status} mmHg [Source: MANUAL]`);
    }
    if (metrics.resting_heart_rate_status && metrics.resting_heart_rate_status !== 'Not reported') {
      addText(`Resting Heart Rate: ${metrics.resting_heart_rate_status} [Source: MANUAL]`);
    }
    if (metrics.blood_glucose_status && metrics.blood_glucose_status !== 'Not reported') {
      addText(`Blood Glucose: ${metrics.blood_glucose_status}`);
    }
    if (metrics.past_ecg_history && metrics.past_ecg_history !== 'Not reported') {
      addText(`Previous Cardiac History: ${metrics.past_ecg_history}`);
    }

    // Reported Symptoms (Sparse)
    if (reportedSymptoms.length > 0) {
      addSectionHeader('3. Reported Symptom Characteristics');
      reportedSymptoms.forEach(s => {
        addText(`• ${s}`, 9, false);
      });
    }

    // Medical History / Risk Factors (Sparse: omit if empty)
    if (reportedHistory.length > 0) {
      addSectionHeader('4. Medical History & Risk Factors');
      reportedHistory.forEach(h => {
        addText(`• ${h}`, 9, false);
      });
    }

    // Critical Red Flags (Omit if none)
    const redFlags = reportData.critical_red_flags || reportData.critical_red_flags_identified || {};
    if (Object.keys(redFlags).length > 0) {
      addSectionHeader('5. Deterministic Clinical Red Flags');
      Object.entries(redFlags).forEach(([flag, reason]) => {
        addText(`- ${flag.replace(/_/g, ' ')}: ${String(reason)}`, 9, true, '#b91c1c');
      });
    }

    // Differential Considerations
    addSectionHeader('6. Differential Clinical Considerations (Not Confirmed Diagnoses)');
    differentialList.forEach((item, idx) => {
      ensureSpace(18);
      addText(`${idx + 1}. ${item.condition} [Status: ${item.status}]`, 10, true, '#0f172a');
      addText(`   Why considered: ${item.why_considered}`, 8, false, '#334155');
      addText(`   Supporting evidence: ${item.supporting_findings.join(', ')}`, 8, false, '#334155');
      addText(`   Missing information: ${item.missing_information.join(', ')}`, 8, false, '#64748b');
      cursorY += 1;
    });

    // Validated Risk Pathways
    addSectionHeader('7. Validated Clinical Decision Pathways');
    addText('HEART Score for Suspected ACS: UNAVAILABLE', 9, true, '#475569');
    addText('Reason: Validated calculation strictly requires a 12-lead ECG and serum cardiac troponin biomarkers, which were not available in this software assessment. Score was not fabricated.', 8, false, '#64748b');

    // What would change assessment
    addSectionHeader('8. Information That Would Materially Change This Assessment');
    whatWouldChange.forEach(item => {
      addText(`• ${item}`, 8, false);
    });

    // Clinician Sign-off Block (BLANK - not prefilled)
    ensureSpace(28);
    addSectionHeader('9. Attending Clinician Review & Sign-off');
    addText('Clinician Name: _________________________________________', 9, false);
    cursorY += 2;
    addText('Clinician Signature: ______________________________________', 9, false);
    cursorY += 2;
    addText('Date & Time: ____________________________________________', 9, false);

    // Disclaimer
    ensureSpace(16);
    cursorY += 4;
    doc.setDrawColor('#cbd5e1');
    doc.line(margin, cursorY, pageWidth - margin, cursorY);
    cursorY += 4;
    addText('LEGAL & MEDICAL DISCLAIMER: This document is an AI-assisted clinical decision-support summary based solely on patient-reported information. It does NOT constitute a confirmed medical diagnosis and does NOT replace immediate evaluation by a qualified healthcare professional. For emergency symptoms in India, call 112.', 7.5, false, '#64748b');

    // Page numbering
    const totalPages = doc.getNumberOfPages();
    for (let p = 1; p <= totalPages; p++) {
      doc.setPage(p);
      doc.setFontSize(7.5);
      doc.setTextColor('#94a3b8');
      doc.text(`Cardiac Care | UHID: ${patient.uhid} | Page ${p} of ${totalPages}`, margin, pageHeight - 6);
    }

    doc.save(`CardiacCare_Report_${patient.uhid}_${assessmentId.slice(0, 8)}.pdf`);
  };

  const handleDownloadRecord = () => {
    const exportData = {
      application: "Cardiac Care — Clinical Decision Support",
      assessment_id: assessmentId,
      date_ist: indianDateStr,
      patient,
      metrics,
      report_data: reportData,
      transcript
    };
    const blob = new Blob([JSON.stringify(exportData, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `CardiacCare_Structured_${patient.uhid}_${Date.now()}.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  const patientSummary = reportData.patient_friendly_summary;

  return (
    <div className="min-h-screen bg-slate-100/70 py-8 px-4 sm:px-6 lg:px-8">
      <div className="max-w-5xl mx-auto space-y-6">
        
        {/* Top Actions & Tab Navigation */}
        <div className="bg-white rounded-2xl p-4 sm:p-5 border border-slate-200/90 shadow-xs flex flex-col sm:flex-row items-center justify-between gap-4 no-print">
          {/* Tab Switcher */}
          <div className="flex items-center space-x-2 bg-slate-100 p-1 rounded-xl">
            <button
              onClick={() => setActiveTab('patient')}
              className={`px-4 py-2 rounded-lg text-xs sm:text-sm font-bold transition-all flex items-center space-x-1.5 ${
                activeTab === 'patient'
                  ? 'bg-white text-brand-800 shadow-xs'
                  : 'text-slate-600 hover:text-slate-900'
              }`}
            >
              <User className="w-4 h-4" />
              <span>Patient Summary</span>
            </button>

            <button
              onClick={() => setActiveTab('doctor')}
              className={`px-4 py-2 rounded-lg text-xs sm:text-sm font-bold transition-all flex items-center space-x-1.5 ${
                activeTab === 'doctor'
                  ? 'bg-white text-brand-800 shadow-xs'
                  : 'text-slate-600 hover:text-slate-900'
              }`}
            >
              <Stethoscope className="w-4 h-4" />
              <span>Doctor Decision Support</span>
            </button>
          </div>

          {/* Action Buttons */}
          <div className="flex items-center space-x-2.5">
            <button
              onClick={handlePrint}
              className="inline-flex items-center space-x-1.5 py-2 px-3.5 bg-white hover:bg-slate-50 text-slate-700 font-semibold rounded-xl border border-slate-300 text-xs shadow-2xs transition-all"
            >
              <Printer className="w-3.5 h-3.5 text-slate-600" />
              <span>Print</span>
            </button>

            <button
              onClick={handleDownloadRecord}
              className="inline-flex items-center space-x-1.5 py-2 px-3.5 bg-white hover:bg-slate-50 text-slate-700 font-semibold rounded-xl border border-slate-300 text-xs shadow-2xs transition-all"
            >
              <Download className="w-3.5 h-3.5 text-slate-600" />
              <span>JSON</span>
            </button>

            <button
              onClick={handleDownloadPdf}
              className="inline-flex items-center space-x-1.5 py-2 px-4 bg-brand-700 hover:bg-brand-800 text-white font-bold rounded-xl text-xs shadow-sm transition-all"
            >
              <Download className="w-3.5 h-3.5" />
              <span>Download PDF</span>
            </button>

            <button
              onClick={onStartNewAssessment}
              className="inline-flex items-center space-x-1.5 py-2 px-4 bg-slate-800 hover:bg-slate-900 text-white font-semibold rounded-xl text-xs shadow-sm transition-all"
            >
              <RotateCcw className="w-3.5 h-3.5" />
              <span>New</span>
            </button>
          </div>
        </div>

        {/* =================================================================== */}
        {/* TAB 1: PATIENT SUMMARY VIEW */}
        {/* =================================================================== */}
        {activeTab === 'patient' && (
          <div className="bg-white rounded-2xl border border-slate-200/90 shadow-sm p-6 sm:p-10 space-y-8">
            {/* Header */}
            <div className="border-b border-slate-100 pb-6 flex items-start justify-between">
              <div>
                <span className="text-xs font-bold text-brand-700 uppercase tracking-wider block mb-1">
                  Cardiac Care Summary
                </span>
                <h1 className="text-2xl sm:text-3xl font-extrabold text-slate-900">
                  Your Assessment Overview
                </h1>
                <p className="text-xs text-slate-500 mt-1">
                  Prepared for: <strong className="text-slate-800">{patient.full_name}</strong> (UHID: {patient.uhid})
                </p>
              </div>

              <TriageBadge category={reportData.triage_category_level || 'Category C'} size="md" />
            </div>

            {/* Emergency Notice if Applicable */}
            {isEmergency && (
              <div className="bg-red-50 border-2 border-red-600/80 rounded-2xl p-6 text-red-900 space-y-3">
                <div className="flex items-center space-x-2 text-red-700 font-bold text-base">
                  <AlertOctagon className="w-5 h-5" />
                  <span>URGENT MEDICAL ATTENTION RECOMMENDED</span>
                </div>
                <p className="text-sm text-red-800 leading-relaxed">
                  Your symptoms feature patterns that can occur with serious heart conditions. Please do not drive yourself. 
                  Call emergency services immediately.
                </p>
                <div className="pt-2">
                  <a
                    href="tel:112"
                    className="inline-flex items-center space-x-2 px-6 py-3 bg-red-600 hover:bg-red-700 text-white font-bold rounded-xl text-sm shadow-md"
                  >
                    <PhoneCall className="w-4 h-4" />
                    <span>Call Emergency: 112 (India)</span>
                  </a>
                </div>
              </div>
            )}

            {/* What We Heard */}
            <div className="space-y-3">
              <h3 className="text-sm font-bold uppercase tracking-wider text-slate-900 flex items-center space-x-2">
                <ClipboardList className="w-4 h-4 text-brand-700" />
                <span>What You Reported</span>
              </h3>
              <p className="text-sm text-slate-700 bg-slate-50 p-4 rounded-xl border border-slate-200/80 leading-relaxed">
                {patientSummary?.what_we_heard || "You reported experiencing cardiac-related symptoms."}
              </p>
            </div>

            {/* Key Symptoms - Render ONLY if symptoms actually reported */}
            {reportedSymptoms.length > 0 && (
              <div className="space-y-3">
                <h3 className="text-sm font-bold uppercase tracking-wider text-slate-900">
                  Reported Symptoms
                </h3>
                <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-3">
                  {reportedSymptoms.map((sym, idx) => (
                    <div key={idx} className="bg-slate-50 p-3.5 rounded-xl border border-slate-200 text-xs text-slate-800 font-medium">
                      • {sym}
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Why Medical Evaluation is Needed */}
            <div className="space-y-3">
              <h3 className="text-sm font-bold uppercase tracking-wider text-slate-900">
                Why Medical Evaluation May Be Needed
              </h3>
              <p className="text-sm text-slate-700 bg-brand-50/50 p-4 rounded-xl border border-brand-100 leading-relaxed">
                {patientSummary?.why_evaluation_needed || (
                  "Symptoms in the chest area can arise from the heart, muscles, lungs, or digestive system. Because serious cardiac conditions require early professional care, in-person evaluation by a healthcare provider is advised."
                )}
              </p>
            </div>

            {/* What To Do Next */}
            <div className="space-y-3">
              <h3 className="text-sm font-bold uppercase tracking-wider text-slate-900">
                Recommended Next Step
              </h3>
              <div className="p-4 bg-slate-900 text-white rounded-xl text-sm font-medium">
                {patientSummary?.what_to_do_next || reportData.urgency_recommendation || "Consult a doctor for an in-person evaluation."}
              </div>
            </div>

            {/* Medical Disclaimer */}
            <MedicalDisclaimer variant="card" />
          </div>
        )}

        {/* =================================================================== */}
        {/* TAB 2: DOCTOR / CLINICAL DECISION SUPPORT VIEW */}
        {/* =================================================================== */}
        {activeTab === 'doctor' && (
          <div className="bg-white rounded-2xl border border-slate-200/90 shadow-sm p-6 sm:p-10 space-y-8">
            {/* Doctor Header */}
            <div className="border-b border-slate-200 pb-6 flex flex-col sm:flex-row justify-between items-start gap-4">
              <div className="flex items-start space-x-3.5">
                <div className="w-12 h-12 rounded-xl bg-slate-900 text-white flex items-center justify-center font-bold">
                  <HeartPulse className="w-7 h-7" />
                </div>
                <div>
                  <span className="text-xs font-bold text-brand-700 uppercase tracking-wider block">
                    Clinical Decision Support Document
                  </span>
                  <h1 className="text-2xl sm:text-3xl font-black text-slate-900 tracking-tight">
                    CARDIAC CARE
                  </h1>
                  <p className="text-xs text-slate-500 mt-0.5">
                    Objective symptom stratification, data provenance & differential considerations
                  </p>
                </div>
              </div>

              <div className="text-left sm:text-right space-y-1">
                <div className="text-xs text-slate-600">Date (IST): <strong className="text-slate-900">{indianDateStr}</strong></div>
                <div className="text-xs text-slate-600 font-mono">UHID: <strong className="text-brand-900">{patient.uhid}</strong></div>
                <div className="text-[11px] text-slate-400 font-mono">Assessment ID: {assessmentId}</div>
                <div className="pt-1.5">
                  <TriageBadge category={reportData.triage_category_level || 'Category C'} size="md" />
                </div>
              </div>
            </div>

            {/* Patient Demographics & Baseline Vitals (Sparse conditional rendering) */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6 bg-slate-50 rounded-2xl p-5 border border-slate-200/80">
              <div>
                <h3 className="text-xs font-bold uppercase tracking-wider text-slate-600 mb-3 flex items-center space-x-1.5">
                  <User className="w-4 h-4 text-brand-700" />
                  <span>Patient Demographics</span>
                </h3>
                <div className="grid grid-cols-2 gap-y-2 text-xs">
                  <span className="text-slate-500">Full Name:</span>
                  <span className="font-bold text-slate-900">{patient.full_name}</span>
                  <span className="text-slate-500">UHID:</span>
                  <span className="font-mono font-bold text-brand-900">{patient.uhid}</span>
                  <span className="text-slate-500">Age / Sex:</span>
                  <span className="font-semibold text-slate-900">{patient.age} Yrs / {patient.gender}</span>
                  {patient.blood_group && patient.blood_group !== 'Not reported' && (
                    <>
                      <span className="text-slate-500">Blood Group:</span>
                      <span className="font-semibold text-slate-900">{patient.blood_group}</span>
                    </>
                  )}
                  {patient.contact_number && patient.contact_number !== 'Not reported' && (
                    <>
                      <span className="text-slate-500">Contact:</span>
                      <span className="text-slate-800">+91 {patient.contact_number}</span>
                    </>
                  )}
                </div>
              </div>

              <div>
                <h3 className="text-xs font-bold uppercase tracking-wider text-slate-600 mb-3 flex items-center space-x-1.5">
                  <Activity className="w-4 h-4 text-brand-700" />
                  <span>Recorded Baseline Vitals</span>
                </h3>
                <div className="grid grid-cols-2 gap-y-2 text-xs">
                  {metrics.blood_pressure_status && metrics.blood_pressure_status !== 'Not reported' && (
                    <>
                      <span className="text-slate-500">Blood Pressure:</span>
                      <span className="font-mono font-bold text-slate-900">
                        {metrics.blood_pressure_status} <span className="text-[10px] font-normal text-slate-400">[MANUAL]</span>
                      </span>
                    </>
                  )}
                  {metrics.resting_heart_rate_status && metrics.resting_heart_rate_status !== 'Not reported' && (
                    <>
                      <span className="text-slate-500">Resting Heart Rate:</span>
                      <span className="font-mono font-bold text-slate-900">
                        {metrics.resting_heart_rate_status} <span className="text-[10px] font-normal text-slate-400">[MANUAL]</span>
                      </span>
                    </>
                  )}
                  {metrics.blood_glucose_status && metrics.blood_glucose_status !== 'Not reported' && (
                    <>
                      <span className="text-slate-500">Blood Glucose:</span>
                      <span className="font-semibold text-slate-900">{metrics.blood_glucose_status}</span>
                    </>
                  )}
                  {metrics.past_ecg_history && metrics.past_ecg_history !== 'Not reported' && (
                    <>
                      <span className="text-slate-500">Past ECG History:</span>
                      <span className="text-slate-800">{metrics.past_ecg_history}</span>
                    </>
                  )}
                </div>
              </div>
            </div>

            {/* Information Completeness & Triage Routing */}
            <div className="grid grid-cols-1 md:grid-cols-12 gap-6 items-center bg-white rounded-2xl p-6 border border-slate-200">
              <div className="md:col-span-4 flex flex-col items-center justify-center p-4 border-b md:border-b-0 md:border-r border-slate-100">
                <RiskScoreGauge score={completeness} size={150} />
                <div className="text-center mt-2">
                  <span className="text-xs font-bold uppercase text-slate-700 tracking-wider">
                    Information Completeness
                  </span>
                  <p className="text-[10px] text-slate-400">
                    Deterministic branch assessment completeness
                  </p>
                </div>
              </div>

              <div className="md:col-span-8 space-y-4">
                <div>
                  <span className="text-xs font-bold uppercase tracking-wider text-slate-500 block mb-1">
                    Triage Routing Recommendation
                  </span>
                  <div className="text-xl font-bold tracking-tight text-slate-900 flex items-center space-x-2">
                    <Stethoscope className="w-5 h-5 text-brand-700" />
                    <span>{reportData.triage_routing_recommendation || reportData.urgency_recommendation || 'Clinical Evaluation'}</span>
                  </div>
                </div>

                <div className="bg-slate-50 rounded-xl p-4 border border-slate-100 text-xs text-slate-700 space-y-1">
                  <strong className="text-slate-900">Clinical Narrative Summary:</strong>
                  <p className="leading-relaxed">
                    {reportData.doctor_clinical_summary_text || 'Assessment information collected.'}
                  </p>
                </div>
              </div>
            </div>

            {/* Sparse Reported Symptoms */}
            {reportedSymptoms.length > 0 && (
              <div className="space-y-3">
                <h3 className="text-sm font-bold uppercase tracking-wider text-slate-900 flex items-center space-x-2">
                  <ClipboardList className="w-4 h-4 text-brand-700" />
                  <span>Reported Symptom Characteristics</span>
                </h3>
                <div className="bg-slate-50 border border-slate-200 rounded-xl p-4 text-xs space-y-1.5">
                  {reportedSymptoms.map((sym, idx) => (
                    <div key={idx} className="flex items-start space-x-2 text-slate-800">
                      <span className="font-bold">•</span>
                      <span>{sym}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Sparse Reported Medical History & Risk Factors (Omit if none) */}
            {reportedHistory.length > 0 && (
              <div className="space-y-3">
                <h3 className="text-sm font-bold uppercase tracking-wider text-slate-900 flex items-center space-x-2">
                  <Activity className="w-4 h-4 text-brand-700" />
                  <span>Medical History & Risk Factors</span>
                </h3>
                <div className="bg-slate-50 border border-slate-200 rounded-xl p-4 text-xs space-y-1.5">
                  {reportedHistory.map((hist, idx) => (
                    <div key={idx} className="flex items-start space-x-2 text-slate-800">
                      <span className="font-bold">•</span>
                      <span>{hist}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Deterministic Red Flags (Omit if none) */}
            {(reportData.critical_red_flags || reportData.critical_red_flags_identified) && (
              <div className="space-y-3">
                <h3 className="text-sm font-bold uppercase tracking-wider text-slate-900 flex items-center space-x-2">
                  <AlertOctagon className="w-4 h-4 text-red-600" />
                  <span>Clinical Safety & Red Flags</span>
                </h3>
                <div className="bg-red-50 border border-red-200 rounded-xl p-4 text-xs space-y-1.5">
                  {Object.entries(reportData.critical_red_flags || reportData.critical_red_flags_identified || {}).map(([flag, reason], idx) => (
                    <div key={idx} className="flex items-start space-x-2 text-red-900">
                      <span className="font-bold">•</span>
                      <span><strong>{flag.replace(/_/g, ' ')}:</strong> {String(reason)}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Differential Clinical Considerations */}
            <div className="space-y-4">
              <h3 className="text-sm font-bold uppercase tracking-wider text-slate-900 flex items-center space-x-2">
                <FileText className="w-4 h-4 text-brand-700" />
                <span>Differential Clinical Considerations (Not Confirmed Diagnoses)</span>
              </h3>

              <div className="space-y-3">
                {differentialList.map((item, idx) => (
                  <div key={idx} className="bg-slate-50 border border-slate-200/90 rounded-xl p-5 space-y-2.5">
                    <div className="flex items-center justify-between">
                      <div className="text-base font-bold text-slate-900">
                        {idx + 1}. {item.condition}
                      </div>
                      <span className="px-2.5 py-0.5 rounded-full text-[11px] font-bold bg-amber-100 text-amber-900 border border-amber-300">
                        Status: {item.status || "Not confirmed"}
                      </span>
                    </div>

                    <p className="text-xs text-slate-700">
                      <strong className="text-slate-900">Why considered: </strong>
                      {item.why_considered}
                    </p>

                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs pt-1">
                      <div className="bg-white p-3 rounded-lg border border-slate-200">
                        <strong className="text-emerald-700 block mb-1">Supporting Findings:</strong>
                        <ul className="list-disc list-inside space-y-0.5 text-slate-700">
                          {item.supporting_findings.map((f, fIdx) => (
                            <li key={fIdx}>{f}</li>
                          ))}
                        </ul>
                      </div>

                      <div className="bg-white p-3 rounded-lg border border-slate-200">
                        <strong className="text-amber-800 block mb-1">Missing Objective Information:</strong>
                        <ul className="list-disc list-inside space-y-0.5 text-slate-600">
                          {item.missing_information.map((m, mIdx) => (
                            <li key={mIdx}>{m}</li>
                          ))}
                        </ul>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Validated Decision Pathways (HEART Score) */}
            <div className="space-y-3">
              <h3 className="text-sm font-bold uppercase tracking-wider text-slate-900 flex items-center space-x-2">
                <AlertCircle className="w-4 h-4 text-brand-700" />
                <span>Validated Clinical Decision Pathways</span>
              </h3>

              <div className="bg-slate-50 rounded-xl p-4 border border-slate-200 text-xs space-y-2">
                <div className="flex items-center justify-between">
                  <span className="font-bold text-slate-900">HEART Score for Suspected ACS</span>
                  <span className="px-2 py-0.5 rounded-md text-[10px] font-mono font-bold bg-slate-200 text-slate-700">
                    UNAVAILABLE
                  </span>
                </div>
                <p className="text-slate-600 leading-relaxed">
                  <strong>Reason:</strong> The validated HEART score calculation requires a 12-lead ECG and serum cardiac troponin biomarkers. In this software-based assessment, these objective inputs were not available. In strict accordance with clinical validation protocol, a score was <strong>NOT fabricated</strong>.
                </p>
                <div className="text-[10px] text-slate-400 font-mono">
                  Six AJ, Backus BE, Kelder JC. Chest pain in the emergency department: value of the HEART score. Neth Heart J. 2008.
                </div>
              </div>
            </div>

            {/* Dynamic: What Would Materially Change Assessment */}
            <div className="space-y-3">
              <h3 className="text-sm font-bold uppercase tracking-wider text-slate-900">
                Information That Would Materially Change This Assessment
              </h3>
              <div className="bg-slate-50 border border-slate-200 rounded-xl p-4 text-xs space-y-1.5 text-slate-700">
                {whatWouldChange.map((item, idx) => (
                  <div key={idx} className="flex items-start space-x-2">
                    <span className="font-bold text-brand-700">•</span>
                    <span>{item}</span>
                  </div>
                ))}
              </div>
            </div>

            {/* Attending Clinician Review Block (Blank lines only — no fake doctor) */}
            <div className="border border-slate-300 rounded-xl p-5 bg-slate-50 space-y-4">
              <h4 className="text-xs font-bold uppercase tracking-wider text-slate-700">
                Attending Clinician In-Person Review & Sign-Off
              </h4>
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 text-xs text-slate-600">
                <div>
                  <span className="block text-[11px] text-slate-400 mb-1">Clinician Name</span>
                  <div className="border-b border-slate-400 pb-1 font-mono text-slate-400">___________________________</div>
                </div>
                <div>
                  <span className="block text-[11px] text-slate-400 mb-1">Clinician Signature</span>
                  <div className="border-b border-slate-400 pb-1 font-mono text-slate-400">___________________________</div>
                </div>
                <div>
                  <span className="block text-[11px] text-slate-400 mb-1">Date & Time</span>
                  <div className="border-b border-slate-400 pb-1 font-mono text-slate-400">______/______/202___  ____:____</div>
                </div>
              </div>
              <p className="text-[11px] text-slate-500 italic">
                Status: Pending in-person physician clinical correlation.
              </p>
            </div>

            {/* Limitations & Disclaimer */}
            <MedicalDisclaimer variant="card" />
          </div>
        )}

      </div>
    </div>
  );
};
