export type ObservationSource = 
  | 'PATIENT_REPORTED'
  | 'MANUAL'
  | 'DEVICE'
  | 'LAB'
  | 'DATABASE'
  | 'CALCULATED'
  | 'VALIDATED_RULE'
  | 'AI_INTERPRETATION'
  | 'NOT_REPORTED';

export interface Patient {
  id?: string;
  uhid: string;
  full_name: string;
  age: number;
  gender: string;
  blood_group?: string;
  contact_number?: string;
  emergency_contact_name?: string;
  emergency_contact_number?: string;
  created_at?: string;
}

export interface HealthMetrics {
  id?: string;
  patient_id?: string;
  weight_kg?: number;
  height_cm?: number;
  blood_pressure_status: string;
  resting_heart_rate_status: string;
  blood_glucose_status?: string;
  past_ecg_history?: string;
  recorded_at?: string;
  created_at?: string;
}

export interface ClinicalObservation {
  id: string;
  patient_id: string;
  assessment_id?: string;
  type: string;
  value: unknown;
  unit: string;
  source: ObservationSource;
  timestamp: number;
  quality: string;
}

export interface DynamicSymptom {
  presence?: string;
  rating_1_to_10?: number | null;
  duration?: string;
  radiation?: string;
  notes?: string;
}

export type ReportValue = string | number | boolean | null;

export interface DifferentialCondition {
  condition: string;
  category: 'CARDIAC' | 'PULMONARY' | 'GASTROINTESTINAL' | 'MUSCULOSKELETAL' | 'OTHER';
  why_considered: string;
  supporting_findings: string[];
  missing_information: string[];
  status: string; // "Not confirmed"
}

export interface ValidatedRiskScore {
  score_name: string;
  version: string;
  is_available: boolean;
  score_value?: number | null;
  max_score?: number;
  interpretation?: string;
  inputs_used?: Record<string, unknown>;
  missing_inputs?: string[];
  source_citation: string;
  calculated_at: number;
}

export interface PatientFriendlySummary {
  what_we_heard: string;
  important_symptoms: string[];
  why_evaluation_needed: string;
  what_to_do_next: string;
  emergency_guidance?: string[] | null;
}

export interface ReportData {
  // Core Acuity & Triage
  triage_category_level: string; // e.g. 'Category A (EMERGENCY)', 'Category B (URGENT)', 'Category C (ROUTINE)'
  urgency_recommendation?: string;
  triage_routing_recommendation?: string;

  // Leading Concern & Differential
  leading_concern?: {
    possible_condition: string;
    why_considered: string;
    status: string;
  };
  possible_conditions?: DifferentialCondition[];
  critical_red_flags?: Record<string, string>;
  critical_red_flags_identified?: Record<string, string>;

  // Summaries & Sparse Evidence
  doctor_clinical_summary_text?: string;
  patient_friendly_summary?: PatientFriendlySummary;
  reported_symptoms?: string[];
  reported_history?: string[];
  what_would_change_assessment?: string[];
  prognosis_risk_statement?: string;

  // Quantitative Metrics (Deterministic)
  clinical_completeness_pct?: number;
  calculated_risk_score_100?: number;
  confidence_percentage?: number;
  validated_risk_scores?: ValidatedRiskScore[];

  // Data Provenance & Limitations
  data_provenance?: Record<string, string>;
  limitations?: string[];

  // Legacy compatibility fields
  chest_pain_current?: string;
  pain_duration?: string;
  dynamic_symptoms_and_ratings?: Record<string, DynamicSymptom | ReportValue>;
  dynamic_risk_factors?: Record<string, string | number | boolean>;
  primary_suspected_pattern?: string;
  secondary_suspected_pattern?: string;

  [key: string]: unknown;
}

export interface ChatMessage {
  role: 'user' | 'assistant' | 'system';
  content: string;
  timestamp?: string;
}

export interface ChatResponse {
  status: 'SUCCESS' | 'ERROR';
  action?: 'ASK_QUESTION' | 'GENERATE_REPORT';
  message_to_patient?: string;
  ai_response?: string;
  is_report: boolean;
  is_emergency?: boolean;
  safety_status?: string;
  completeness?: number;
  questions_asked?: number;
  report_data?: ReportData;
  error?: string;
}

export interface Assessment {
  id: string;
  patient_id: string;
  metrics_id: string;
  full_chat_transcript: ChatMessage[];
  is_complete: boolean;
  patients?: Patient;
  patient_health_metrics?: HealthMetrics;
  created_at?: string;
  report_data?: ReportData;
  integrity?: {
    valid: boolean;
    errors: string[];
  };
  [key: string]: unknown;
}

export interface AdminDiagnostics {
  provider: string;
  endpoint: string;
  api_configured: boolean;
  masked_key?: string;
  primary_configured_model: string;
  primary_active_model: string;
  secondary_active_model: string;
  guardrail_model: string;
  fallback_active: boolean;
  fallback_reason?: string | null;
  catalog_count: number;
  last_latency_ms: number;
  last_error?: string | null;
  timestamp: number;
  supabase_connected: boolean;
}
