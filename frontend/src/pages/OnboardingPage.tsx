import React, { useState } from 'react';
import { 
  User, 
  Activity, 
  ArrowRight, 
  ArrowLeft, 
  CheckCircle2, 
  AlertCircle, 
  ShieldAlert,
  Loader2
} from 'lucide-react';
import type { Patient, HealthMetrics } from '../types/api';
import { apiService } from '../services/api';

interface OnboardingPageProps {
  onAssessmentInitialized: (assessmentId: string, patient: Patient, metrics: HealthMetrics) => void;
  onCancel: () => void;
  demoPersona?: 'stemi' | 'routine' | null;
  onClearDemoPersona?: () => void;
}

export const OnboardingPage: React.FC<OnboardingPageProps> = ({
  onAssessmentInitialized,
  onCancel,
}) => {
  const [step, setStep] = useState<1 | 2>(1);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [createdPatient, setCreatedPatient] = useState<{ id: string; uhid: string } | null>(null);
  const [createdMetricsId, setCreatedMetricsId] = useState<string | null>(null);

  // Patient Form State — Starts 100% EMPTY by default
  const [fullName, setFullName] = useState<string>('');
  const [age, setAge] = useState<string>('');
  const [gender, setGender] = useState<string>('');
  const [bloodGroup, setBloodGroup] = useState<string>('');
  const [contactNumber, setContactNumber] = useState<string>('');
  const [emergencyName, setEmergencyName] = useState<string>('');
  const [emergencyNumber, setEmergencyNumber] = useState<string>('');

  // Metrics Form State — Starts 100% EMPTY by default
  const [systolic, setSystolic] = useState<string>('');
  const [diastolic, setDiastolic] = useState<string>('');
  const [heartRate, setHeartRate] = useState<string>('');
  const [weightKg, setWeightKg] = useState<string>('');
  const [heightCm, setHeightCm] = useState<string>('');
  const [bloodGlucose, setBloodGlucose] = useState<string>('');
  const [pastEcg, setPastEcg] = useState<string>('');

  // Validation Errors
  const [errors, setErrors] = useState<Record<string, string>>({});

  // Validation functions
  const validatePhone = (phone: string): boolean => {
    const cleaned = phone.replace(/[\s-]/g, '');
    return /^[6-9]\d{9}$/.test(cleaned);
  };

  const validateStep1 = (): boolean => {
    const newErrors: Record<string, string> = {};

    if (!fullName.trim()) {
      newErrors.fullName = 'Please enter your full name.';
    }

    const ageNum = parseInt(age, 10);
    if (!age.trim() || isNaN(ageNum) || ageNum < 1 || ageNum > 120) {
      newErrors.age = 'Please enter an age between 1 and 120 years.';
    }

    if (!gender) {
      newErrors.gender = 'Please select your biological sex.';
    }

    if (contactNumber.trim() && !validatePhone(contactNumber)) {
      newErrors.contactNumber = 'Please enter a valid 10-digit Indian mobile number (e.g. 98765 43210).';
    }

    if (emergencyNumber.trim() && !validatePhone(emergencyNumber)) {
      newErrors.emergencyNumber = 'Please enter a valid 10-digit Indian mobile number (e.g. 98765 43210).';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const validateStep2 = (): boolean => {
    const newErrors: Record<string, string> = {};

    const systolicValue = Number(systolic);
    const diastolicValue = Number(diastolic);
    const heartRateValue = Number(heartRate);

    if (!systolic.trim() || !Number.isInteger(systolicValue) || systolicValue < 70 || systolicValue > 250) {
      newErrors.systolic = 'Please enter a valid systolic blood pressure.';
    }

    if (!diastolic.trim() || !Number.isInteger(diastolicValue) || diastolicValue < 40 || diastolicValue > 150) {
      newErrors.diastolic = 'Please enter a valid diastolic blood pressure.';
    }

    if (!heartRate.trim() || !Number.isInteger(heartRateValue) || heartRateValue < 30 || heartRateValue > 220) {
      newErrors.heartRate = 'Please enter a resting heart rate between 30 and 220 bpm.';
    }

    if (weightKg && (Number(weightKg) < 2 || Number(weightKg) > 400)) {
      newErrors.weightKg = 'Please enter your weight in kilograms.';
    }

    if (heightCm && (Number(heightCm) < 40 || Number(heightCm) > 250)) {
      newErrors.heightCm = 'Please enter your height in centimetres.';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleNext = () => {
    if (validateStep1()) {
      setStep(2);
      window.scrollTo({ top: 0, behavior: 'smooth' });
    }
  };

  const handleSubmit = async () => {
    if (!validateStep2()) return;

    setIsLoading(true);
    setErrorMessage(null);

    const patientPayload: Omit<Patient, 'uhid'> = {
      full_name: fullName.trim(),
      age: parseInt(age, 10),
      gender,
      blood_group: bloodGroup || undefined,
      contact_number: contactNumber.trim() || undefined,
      emergency_contact_name: emergencyName.trim() || undefined,
      emergency_contact_number: emergencyNumber.trim() || undefined,
    };

    const metricsPayload: HealthMetrics = {
      blood_pressure_status: `${systolic.trim()}/${diastolic.trim()}`,
      resting_heart_rate_status: `${heartRate.trim()} bpm`,
      weight_kg: weightKg ? parseFloat(weightKg) : undefined,
      height_cm: heightCm ? parseInt(heightCm, 10) : undefined,
      blood_glucose_status: bloodGlucose.trim() || undefined,
      past_ecg_history: pastEcg.trim() || undefined,
    };

    try {
      let patientId: string;
      let finalUhid: string;
      if (createdPatient) {
        patientId = createdPatient.id;
        finalUhid = createdPatient.uhid;
      } else {
        // Flask assigns and persists the authoritative UHID.
        const patientRes = await apiService.createPatient(patientPayload);
        patientId = patientRes.patient_id;
        if (!patientRes.uhid) {
          throw new Error('The hospital system did not return a patient identifier. Please try again.');
        }
        finalUhid = patientRes.uhid;
        setCreatedPatient({ id: patientId, uhid: finalUhid });
      }

      // 2. Create Health Metrics in Backend
      const metricsWithPatient = {
        ...metricsPayload,
        patient_id: patientId
      };
      const metricsId = createdMetricsId || (await apiService.createMetrics(metricsWithPatient)).metrics_id;
      if (!createdMetricsId) setCreatedMetricsId(metricsId);

      // 3. Initialize Assessment in Backend
      const assessmentRes = await apiService.initAssessment(patientId, metricsId);
      const assessmentId = assessmentRes.assessment_id;

      // 4. Proceed to Clinical Assessment
      onAssessmentInitialized(
        assessmentId,
        { ...patientPayload, id: patientId, uhid: finalUhid },
        { ...metricsWithPatient, id: metricsId }
      );
    } catch (err: unknown) {
      console.error('Initialization error:', err);
      setErrorMessage('The assessment service is temporarily unavailable. Your entered information has been kept. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-50 py-10 px-4 sm:px-6 lg:px-8">
      <div className="max-w-3xl mx-auto">
        
        {/* Stepper Header */}
        <div className="bg-white rounded-2xl p-6 border border-slate-200/90 shadow-xs mb-8">
          <div className="flex items-center justify-between max-w-xl mx-auto">
            {/* Step 1 */}
            <div className="flex items-center space-x-2.5">
              <div className={`w-8 h-8 rounded-full flex items-center justify-center text-xs font-bold ${
                step === 1 ? 'bg-brand-700 text-white' : 'bg-emerald-600 text-white'
              }`}>
                {step > 1 ? <CheckCircle2 className="w-5 h-5" /> : '1'}
              </div>
              <div>
                <span className="text-xs font-bold text-slate-900 block">Patient Info</span>
                <span className="text-[10px] text-slate-500">Demographics</span>
              </div>
            </div>

            <div className={`flex-1 h-0.5 mx-4 ${step >= 2 ? 'bg-brand-700' : 'bg-slate-200'}`} />

            {/* Step 2 */}
            <div className="flex items-center space-x-2.5">
              <div className={`w-8 h-8 rounded-full flex items-center justify-center text-xs font-bold ${
                step === 2 ? 'bg-brand-700 text-white' : 'bg-slate-200 text-slate-600'
              }`}>
                2
              </div>
              <div>
                <span className="text-xs font-bold text-slate-900 block">Health Vitals</span>
                <span className="text-[10px] text-slate-500">Clinical Metrics</span>
              </div>
            </div>

            <div className="flex-1 h-0.5 mx-4 bg-slate-200" />

            {/* Step 3 */}
            <div className="flex items-center space-x-2.5 opacity-40">
              <div className="w-8 h-8 rounded-full bg-slate-200 text-slate-600 flex items-center justify-center text-xs font-bold">
                3
              </div>
              <div>
                <span className="text-xs font-bold text-slate-900 block">Dr. Cardia</span>
                <span className="text-[10px] text-slate-500">Consultation</span>
              </div>
            </div>
          </div>
        </div>

        {/* Error Alert */}
        {errorMessage && (
          <div className="mb-6 bg-red-50 border border-red-200 rounded-xl p-4 flex items-start space-x-3 text-red-800 text-sm">
            <ShieldAlert className="w-5 h-5 text-red-600 flex-shrink-0 mt-0.5" />
            <div className="flex-1">
              <strong className="font-semibold block mb-1">We couldn't save your information</strong>
              <span>{errorMessage}</span>
            </div>
          </div>
        )}

        {/* STEP 1: PATIENT INFORMATION */}
        {step === 1 && (
          <div className="bg-white rounded-2xl p-6 sm:p-8 border border-slate-200/90 shadow-xs space-y-6">
            <div className="border-b border-slate-100 pb-4">
              <div className="flex items-center space-x-2 text-brand-700 font-bold text-xs uppercase tracking-wider mb-1">
                <User className="w-4 h-4" />
                <span>Patient Registration</span>
              </div>
              <h2 className="text-2xl font-extrabold text-slate-900 tracking-tight">
                Patient Demographics & Identification
              </h2>
              <p className="text-sm text-slate-500 mt-1">
                Enter your details to create an authoritative hospital record for this assessment.
              </p>
            </div>

            {/* Form Fields */}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-5">
              
              {/* Full Name */}
              <div className="sm:col-span-2">
                <label htmlFor="full-name" className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1.5">
                  Full Name <span className="text-red-500">*</span>
                </label>
                <input
                  id="full-name"
                  type="text"
                  value={fullName}
                  onChange={(e) => {
                    setFullName(e.target.value);
                    if (errors.fullName) setErrors({ ...errors, fullName: '' });
                  }}
                  placeholder="Enter your full name"
                  className={`w-full px-4 py-3 rounded-xl border text-sm focus:outline-none focus:ring-2 transition-all ${
                    errors.fullName
                      ? 'border-red-300 focus:ring-red-200 bg-red-50/30'
                      : 'border-slate-300 focus:ring-brand-500/20 focus:border-brand-600'
                  }`}
                />
                {errors.fullName && (
                  <p className="text-xs text-red-600 mt-1 flex items-center space-x-1">
                    <AlertCircle className="w-3.5 h-3.5" />
                    <span>{errors.fullName}</span>
                  </p>
                )}
              </div>

              {/* Age */}
              <div>
                <label htmlFor="age" className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1.5">
                  Age (Years) <span className="text-red-500">*</span>
                </label>
                <input
                  id="age"
                  type="number"
                  min={1}
                  max={120}
                  value={age}
                  onChange={(e) => {
                    setAge(e.target.value);
                    if (errors.age) setErrors({ ...errors, age: '' });
                  }}
                  placeholder="Enter age"
                  className={`w-full px-4 py-3 rounded-xl border text-sm focus:outline-none focus:ring-2 transition-all ${
                    errors.age
                      ? 'border-red-300 focus:ring-red-200 bg-red-50/30'
                      : 'border-slate-300 focus:ring-brand-500/20 focus:border-brand-600'
                  }`}
                />
                {errors.age && (
                  <p className="text-xs text-red-600 mt-1 flex items-center space-x-1">
                    <AlertCircle className="w-3.5 h-3.5" />
                    <span>{errors.age}</span>
                  </p>
                )}
              </div>

              {/* Biological Sex / Gender */}
              <div>
                <label htmlFor="gender" className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1.5">
                  Biological Sex <span className="text-red-500">*</span>
                </label>
                <select
                  id="gender"
                  value={gender}
                  onChange={(e) => setGender(e.target.value)}
                  className={`w-full px-4 py-3 rounded-xl border text-sm focus:outline-none focus:ring-2 focus:ring-brand-500/20 focus:border-brand-600 bg-white text-slate-800 ${errors.gender ? 'border-red-300' : 'border-slate-300'}`}
                >
                  <option value="">Select biological sex</option>
                  <option value="Male">Male</option>
                  <option value="Female">Female</option>
                  <option value="Other">Other</option>
                  <option value="Prefer not to say">Prefer not to say</option>
                </select>
                {errors.gender && <p className="text-xs text-red-600 mt-1">{errors.gender}</p>}
              </div>

              {/* Blood Group */}
              <div>
                <label htmlFor="blood-group" className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1.5">
                  Blood Group
                </label>
                <select
                  id="blood-group"
                  value={bloodGroup}
                  onChange={(e) => setBloodGroup(e.target.value)}
                  className="w-full px-4 py-3 rounded-xl border border-slate-300 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500/20 focus:border-brand-600 bg-white text-slate-800"
                >
                  <option value="">Select blood group</option>
                  <option value="O+">O+</option>
                  <option value="O-">O-</option>
                  <option value="A+">A+</option>
                  <option value="A-">A-</option>
                  <option value="B+">B+</option>
                  <option value="B-">B-</option>
                  <option value="AB+">AB+</option>
                  <option value="AB-">AB-</option>
                  <option value="Unknown / Not known">Unknown / Not known</option>
                </select>
              </div>

              {/* Patient Contact Number (Indian format) */}
              <div>
                <label htmlFor="contact-number" className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1.5">
                  Patient Contact Number
                </label>
                <div className="relative">
                  <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-slate-400 text-xs font-medium">
                    +91
                  </div>
                  <input
                    id="contact-number"
                    type="tel"
                    maxLength={10}
                    value={contactNumber}
                    onChange={(e) => {
                      const val = e.target.value.replace(/\D/g, '');
                      setContactNumber(val);
                      if (errors.contactNumber) setErrors({ ...errors, contactNumber: '' });
                    }}
                    placeholder="98765 43210"
                    className={`w-full pl-12 pr-4 py-3 rounded-xl border text-sm focus:outline-none focus:ring-2 transition-all ${
                      errors.contactNumber
                        ? 'border-red-300 focus:ring-red-200 bg-red-50/30'
                        : 'border-slate-300 focus:ring-brand-500/20 focus:border-brand-600'
                    }`}
                  />
                </div>
                {errors.contactNumber && (
                  <p className="text-xs text-red-600 mt-1 flex items-center space-x-1">
                    <AlertCircle className="w-3.5 h-3.5" />
                    <span>{errors.contactNumber}</span>
                  </p>
                )}
              </div>

              {/* Emergency Contact Name */}
              <div>
                <label htmlFor="emergency-name" className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1.5">
                  Emergency Contact Name
                </label>
                <input
                  id="emergency-name"
                  type="text"
                  value={emergencyName}
                  onChange={(e) => setEmergencyName(e.target.value)}
                  placeholder="Enter emergency contact name"
                  className="w-full px-4 py-3 rounded-xl border border-slate-300 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500/20 focus:border-brand-600"
                />
              </div>

              {/* Emergency Contact Number (Indian format) */}
              <div>
                <label htmlFor="emergency-number" className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1.5">
                  Emergency Contact Number
                </label>
                <div className="relative">
                  <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-slate-400 text-xs font-medium">
                    +91
                  </div>
                  <input
                    id="emergency-number"
                    type="tel"
                    maxLength={10}
                    value={emergencyNumber}
                    onChange={(e) => {
                      const val = e.target.value.replace(/\D/g, '');
                      setEmergencyNumber(val);
                      if (errors.emergencyNumber) setErrors({ ...errors, emergencyNumber: '' });
                    }}
                    placeholder="98765 43210"
                    className={`w-full pl-12 pr-4 py-3 rounded-xl border text-sm focus:outline-none focus:ring-2 transition-all ${
                      errors.emergencyNumber
                        ? 'border-red-300 focus:ring-red-200 bg-red-50/30'
                        : 'border-slate-300 focus:ring-brand-500/20 focus:border-brand-600'
                    }`}
                  />
                </div>
                {errors.emergencyNumber && (
                  <p className="text-xs text-red-600 mt-1 flex items-center space-x-1">
                    <AlertCircle className="w-3.5 h-3.5" />
                    <span>{errors.emergencyNumber}</span>
                  </p>
                )}
              </div>
            </div>

            {/* Navigation Buttons */}
            <div className="flex items-center justify-between pt-6 border-t border-slate-100">
              <button
                type="button"
                onClick={onCancel}
                className="px-6 py-3 text-slate-600 hover:text-slate-900 font-semibold text-sm transition-all"
              >
                Back to Overview
              </button>

              <button
                type="button"
                onClick={handleNext}
                className="inline-flex items-center space-x-2 px-8 py-3.5 bg-brand-700 hover:bg-brand-800 text-white font-bold rounded-xl shadow-md transition-all text-sm"
              >
                    <span>Continue to Health Information</span>
                <ArrowRight className="w-4 h-4" />
              </button>
            </div>
          </div>
        )}

        {/* STEP 2: HEALTH VITALS */}
        {step === 2 && (
          <div className="bg-white rounded-2xl p-6 sm:p-8 border border-slate-200/90 shadow-xs space-y-6">
            <div className="border-b border-slate-100 pb-4">
              <div className="flex items-center space-x-2 text-brand-700 font-bold text-xs uppercase tracking-wider mb-1">
                <Activity className="w-4 h-4" />
                <span>Clinical Vitals & Background</span>
              </div>
              <h2 className="text-2xl font-extrabold text-slate-900 tracking-tight">
                Baseline Health Information
              </h2>
              <p className="text-sm text-slate-500 mt-1">
                Provide your current health measurements and known cardiac history. If you do not know a value, choose the option that says so.
              </p>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-5">
              {/* Blood Pressure */}
              <div className="sm:col-span-2 rounded-xl border border-slate-200 bg-slate-50 p-4">
                <label htmlFor="heart-rate" className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1.5">
                  Blood Pressure <span className="text-red-500">*</span>
                </label>
                <p className="text-xs text-slate-500 mb-3">Blood pressure is recorded as two numbers.</p>
                <div className="grid grid-cols-[1fr_auto_1fr] items-end gap-3 max-w-lg">
                  <div>
                    <label htmlFor="systolic" className="block text-xs font-semibold text-slate-700 mb-1">Systolic</label>
                    <div className="flex items-center gap-2">
                      <input
                        id="systolic"
                        type="number"
                        inputMode="numeric"
                        min={70}
                        max={250}
                        value={systolic}
                        onChange={(e) => { setSystolic(e.target.value); if (errors.systolic) setErrors({ ...errors, systolic: '' }); }}
                        placeholder="Enter systolic"
                        className={`w-full px-3 py-3 rounded-xl border text-sm font-mono focus:outline-none focus:ring-2 focus:ring-brand-500/20 focus:border-brand-600 ${errors.systolic ? 'border-red-300 bg-red-50/30' : 'border-slate-300'}`}
                      />
                      <span className="text-xs text-slate-500">mmHg</span>
                    </div>
                  </div>
                  <span className="pb-3 text-xl font-semibold text-slate-400">/</span>
                  <div>
                    <label htmlFor="diastolic" className="block text-xs font-semibold text-slate-700 mb-1">Diastolic</label>
                    <div className="flex items-center gap-2">
                      <input
                        id="diastolic"
                        type="number"
                        inputMode="numeric"
                        min={40}
                        max={150}
                        value={diastolic}
                        onChange={(e) => { setDiastolic(e.target.value); if (errors.diastolic) setErrors({ ...errors, diastolic: '' }); }}
                        placeholder="Enter diastolic"
                        className={`w-full px-3 py-3 rounded-xl border text-sm font-mono focus:outline-none focus:ring-2 focus:ring-brand-500/20 focus:border-brand-600 ${errors.diastolic ? 'border-red-300 bg-red-50/30' : 'border-slate-300'}`}
                      />
                      <span className="text-xs text-slate-500">mmHg</span>
                    </div>
                  </div>
                </div>
                {(errors.systolic || errors.diastolic) && <p className="text-xs text-red-600 mt-2">{errors.systolic || errors.diastolic}</p>}
              </div>

              {/* Resting Heart Rate */}
              <div>
                <label htmlFor="weight" className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1.5">
                  Resting Heart Rate <span className="text-red-500">*</span>
                </label>
                <input
                  id="heart-rate"
                  type="number"
                  inputMode="numeric"
                  min={30}
                  max={220}
                  value={heartRate}
                  onChange={(e) => {
                    setHeartRate(e.target.value);
                    if (errors.heartRate) setErrors({ ...errors, heartRate: '' });
                  }}
                  placeholder="Enter heart rate"
                  className={`w-full px-4 py-3 rounded-xl border text-sm font-mono focus:outline-none focus:ring-2 transition-all ${
                    errors.heartRate
                      ? 'border-red-300 focus:ring-red-200 bg-red-50/30'
                      : 'border-slate-300 focus:ring-brand-500/20 focus:border-brand-600'
                  }`}
                />
                <span className="text-[11px] text-slate-400">Heart rate while resting, in beats per minute (bpm)</span>
                {errors.heartRate && (
                  <p className="text-xs text-red-600 mt-1 flex items-center space-x-1">
                    <AlertCircle className="w-3.5 h-3.5" />
                    <span>{errors.heartRate}</span>
                  </p>
                )}
              </div>

              {/* Weight */}
              <div>
                <label htmlFor="height" className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1.5">
                  Weight (kg)
                </label>
                <input
                  id="weight"
                  type="number"
                  step="0.1"
                  value={weightKg}
                  onChange={(e) => setWeightKg(e.target.value)}
                  min={2}
                  max={400}
                  inputMode="decimal"
                  placeholder="e.g. 65"
                  className={`w-full px-4 py-3 rounded-xl border text-sm focus:outline-none focus:ring-2 focus:ring-brand-500/20 focus:border-brand-600 ${errors.weightKg ? 'border-red-300' : 'border-slate-300'}`}
                />
                <span className="text-[11px] text-slate-400">kg</span>
                {errors.weightKg && <p className="text-xs text-red-600 mt-1">{errors.weightKg}</p>}
              </div>

              {/* Height */}
              <div>
                <label htmlFor="blood-glucose" className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1.5">
                  Height (cm)
                </label>
                <input
                  id="height"
                  type="number"
                  min={40}
                  max={250}
                  inputMode="numeric"
                  value={heightCm}
                  onChange={(e) => setHeightCm(e.target.value)}
                  placeholder="e.g. 170"
                  className={`w-full px-4 py-3 rounded-xl border text-sm focus:outline-none focus:ring-2 focus:ring-brand-500/20 focus:border-brand-600 ${errors.heightCm ? 'border-red-300' : 'border-slate-300'}`}
                />
                <span className="text-[11px] text-slate-400">cm</span>
                {errors.heightCm && <p className="text-xs text-red-600 mt-1">{errors.heightCm}</p>}
              </div>

              {/* Blood Glucose Status */}
              <div>
                <label htmlFor="past-ecg" className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1.5">
                  Blood Glucose Status
                </label>
                <select
                  id="blood-glucose"
                  value={bloodGlucose}
                  onChange={(e) => setBloodGlucose(e.target.value)}
                  className="w-full px-4 py-3 rounded-xl border border-slate-300 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500/20 focus:border-brand-600 bg-white"
                >
                  <option value="">Select glucose status</option>
                  <option value="Normal">Normal</option>
                  <option value="High">High</option>
                  <option value="Low">Low</option>
                  <option value="Diabetic / Known Diabetes">Diabetic / Known Diabetes</option>
                  <option value="Not known">Not known</option>
                  <option value="Not measured">Not measured</option>
                </select>
              </div>

              {/* Past ECG / Cardiac History */}
              <div>
                <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1.5">
                  Past ECG / Cardiac History
                </label>
                <select
                  id="past-ecg"
                  value={pastEcg}
                  onChange={(e) => setPastEcg(e.target.value)}
                  className="w-full px-4 py-3 rounded-xl border border-slate-300 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500/20 focus:border-brand-600 bg-white"
                >
                  <option value="">Select history</option>
                  <option value="No known cardiac history">No known cardiac history</option>
                  <option value="Normal">Normal</option>
                  <option value="Abnormal">Abnormal</option>
                  <option value="Previous abnormal ECG">Previous abnormal ECG</option>
                  <option value="Previous cardiac condition">Previous cardiac condition</option>
                  <option value="Not known">Not known</option>
                  <option value="Not available">Not available</option>
                </select>
              </div>
            </div>

            <div className="rounded-xl border border-brand-100 bg-brand-50/60 p-4">
              <h3 className="text-sm font-bold text-brand-950">Review Your Health Information</h3>
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mt-3 text-xs">
                <div><span className="block text-slate-500">Blood Pressure</span><strong className="text-slate-900">{systolic || '—'} / {diastolic || '—'} mmHg</strong></div>
                <div><span className="block text-slate-500">Heart Rate</span><strong className="text-slate-900">{heartRate || '—'} bpm</strong></div>
                <div><span className="block text-slate-500">Weight</span><strong className="text-slate-900">{weightKg || 'Not reported'}{weightKg ? ' kg' : ''}</strong></div>
                <div><span className="block text-slate-500">Height</span><strong className="text-slate-900">{heightCm || 'Not reported'}{heightCm ? ' cm' : ''}</strong></div>
                <div><span className="block text-slate-500">Blood Glucose</span><strong className="text-slate-900">{bloodGlucose || 'Not reported'}</strong></div>
                <div><span className="block text-slate-500">Previous ECG</span><strong className="text-slate-900">{pastEcg || 'Not reported'}</strong></div>
              </div>
            </div>

            {/* Navigation Buttons */}
            <div className="flex items-center justify-between pt-6 border-t border-slate-100">
              <button
                type="button"
                onClick={() => setStep(1)}
                disabled={isLoading}
                className="inline-flex items-center space-x-1.5 px-6 py-3 text-slate-600 hover:text-slate-900 font-semibold text-sm transition-all"
              >
                <ArrowLeft className="w-4 h-4" />
                <span>Back to Demographics</span>
              </button>

              <button
                type="button"
                onClick={handleSubmit}
                disabled={isLoading}
                className="inline-flex items-center space-x-2 px-8 py-3.5 bg-brand-700 hover:bg-brand-800 active:bg-brand-900 disabled:bg-slate-300 text-white font-bold rounded-xl shadow-md transition-all text-sm"
              >
                {isLoading ? (
                  <>
                    <Loader2 className="w-4 h-4 animate-spin" />
                    <span>Saving your information...</span>
                  </>
                ) : (
                  <>
                    <span>{errorMessage ? 'Try Again' : 'Save & Continue'}</span>
                    <ArrowRight className="w-4 h-4" />
                  </>
                )}
              </button>
            </div>
          </div>
        )}

      </div>
    </div>
  );
};
