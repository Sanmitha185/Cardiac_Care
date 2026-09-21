from typing import Any, Dict, List, Optional
from pydantic import BaseModel

class SafetyEvaluation(BaseModel):
    is_emergency: bool
    triage_category: str # 'Category A (EMERGENCY)', 'Category B (URGENT)', 'Category C (ROUTINE)'
    red_flags: Dict[str, str]
    primary_concern: Optional[str] = None
    reason: str
    action_recommendation: str
    emergency_number: str = "112"
    instructions: List[str]

class SafetyEngine:
    """
    Deterministic clinical safety engine.
    Evaluates safety-critical symptom combinations independently of the LLM.
    Guarantees that emergency conditions interrupt unnecessary questioning.
    """

    @staticmethod
    def evaluate(clinical_state: Dict[str, Any], baseline_metrics: Optional[Dict[str, Any]] = None) -> SafetyEvaluation:
        red_flags: Dict[str, str] = {}
        is_emergency = False
        is_urgent = False
        primary_concern: Optional[str] = None
        reasons: List[str] = []

        # Extract structured findings
        chest_pain = clinical_state.get("chest_pain", False)
        severity = clinical_state.get("pain_severity")
        quality = (clinical_state.get("pain_quality") or "").lower()
        radiation = clinical_state.get("pain_radiation") or []
        if isinstance(radiation, str):
            radiation = [radiation]
        radiation_lower = [str(r).lower() for r in radiation]

        associated = clinical_state.get("associated_symptoms") or {}
        has_syncope = associated.get("syncope") is True or clinical_state.get("syncope") is True
        has_dyspnea = associated.get("shortness_of_breath") is True or clinical_state.get("shortness_of_breath") is True
        has_sweating = associated.get("sweating") is True or clinical_state.get("sweating") is True
        has_palpitations = associated.get("palpitations") is True or clinical_state.get("palpitations") is True
        has_dizziness = associated.get("dizziness") is True or clinical_state.get("dizziness") is True

        # Check Radiation Red Flags (Jaw, Left Arm, Neck, Back)
        concerning_radiation = any(loc in r for r in radiation_lower for loc in ["jaw", "arm", "left arm", "neck", "shoulder", "back"])
        if chest_pain and concerning_radiation:
            red_flags["radiation_to_vital_areas"] = f"Chest pain radiating to {', '.join(radiation_lower)} is a documented hallmark of myocardial ischemia."
            is_emergency = True
            primary_concern = "Possible Acute Coronary Syndrome (ACS)"
            reasons.append(f"Chest pain radiating to {', '.join(radiation_lower)}")

        # Check Chest Pain + Autonomic Symptoms (Sweating, Dyspnea, Nausea/Vomiting)
        if chest_pain and (has_sweating or has_dyspnea):
            red_flags["ischemic_autonomic_symptoms"] = "Chest discomfort combined with diaphoresis or acute shortness of breath warrants immediate emergency evaluation."
            is_emergency = True
            primary_concern = primary_concern or "Possible Acute Coronary Syndrome (ACS)"
            reasons.append("Chest pain accompanied by sweating or shortness of breath")

        # Check Syncope / Fainting Red Flags
        if has_syncope:
            if chest_pain or has_palpitations:
                red_flags["cardiogenic_syncope"] = "Transient loss of consciousness associated with chest pain or palpitations is a critical sign of acute arrhythmia or structural obstruction."
                is_emergency = True
                primary_concern = primary_concern or "Cardiogenic Syncope / Suspected Arrhythmia"
                reasons.append("Fainting associated with chest pain or palpitations")
            else:
                red_flags["unexplained_syncope"] = "Unexplained syncope requires prompt medical evaluation."
                is_urgent = True

        # Check High Pain Severity (>= 8/10) with Sudden Onset
        onset = (clinical_state.get("onset") or "").lower()
        try:
            sev_num = float(severity) if severity is not None else 0
        except (ValueError, TypeError):
            sev_num = 0

        if chest_pain and sev_num >= 8:
            if "sudden" in onset or "thunderbolt" in onset or "tearing" in quality or "ripping" in quality:
                red_flags["hyperacute_severe_pain"] = "Sudden-onset severe tearing/ripping chest pain is a critical red flag for acute aortic syndrome or major infarction."
                is_emergency = True
                primary_concern = primary_concern or "Possible Acute Aortic Syndrome or Severe Ischemia"
                reasons.append("Sudden-onset severe (8+/10) pain")
            else:
                red_flags["severe_chest_pain"] = f"Severe chest pain rated {sev_num}/10 warrants high clinical priority."
                is_urgent = True

        # Check Vital Sign Red Flags (if provided in baseline metrics)
        if baseline_metrics:
            hr_str = str(baseline_metrics.get("resting_heart_rate_status", "")).lower()
            bp_str = str(baseline_metrics.get("blood_pressure_status", "")).lower()
            
            # Simple extraction for severe tachycardia / bradycardia
            import re
            hr_match = re.search(r"(\d+)", hr_str)
            if hr_match:
                hr_val = int(hr_match.group(1))
                if hr_val > 150 or hr_val < 40:
                    red_flags["hemodynamic_instability_hr"] = f"Heart rate of {hr_val} bpm falls into a critical range."
                    is_emergency = True
                    reasons.append(f"Critical heart rate ({hr_val} bpm)")

            bp_match = re.search(r"(\d+)\s*/\s*(\d+)", bp_str)
            if bp_match:
                sys_val = int(bp_match.group(1))
                dia_val = int(bp_match.group(2))
                if sys_val >= 200 or dia_val >= 120:
                    red_flags["hypertensive_crisis"] = f"Blood pressure {sys_val}/{dia_val} mmHg represents a potential hypertensive crisis."
                    is_urgent = True
                elif sys_val < 80:
                    red_flags["severe_hypotension"] = f"Systolic blood pressure {sys_val} mmHg suggests possible cardiogenic shock."
                    is_emergency = True
                    reasons.append(f"Hypotension ({sys_val} mmHg systolic)")

        # Compile final determination
        if is_emergency:
            triage = "Category A (EMERGENCY)"
            rec = "Immediate Emergency Department / Casualty Evaluation via Ambulance"
            summary_reason = "; ".join(reasons) if reasons else "High-risk cardiac symptom combination detected."
            instructions = [
                "Call Indian Emergency Medical Services at 112 immediately.",
                "Do not attempt to drive yourself. Wait for emergency services or have someone transport you.",
                "Sit in a comfortable upright position, stay calm, and loosen tight clothing around your chest and neck.",
                "If prescribed emergency cardiac medication (such as sublingual nitroglycerin or aspirin) by your doctor, take as instructed."
            ]
        elif is_urgent:
            triage = "Category B (URGENT)"
            rec = "Urgent Outpatient Cardiology / Urgent Care Evaluation within 12-24 hours"
            summary_reason = "; ".join(reasons) if reasons else "Symptoms require prompt physician evaluation."
            instructions = [
                "Contact a cardiologist or urgent care clinic today for clinical evaluation.",
                "Avoid strenuous exertion, heavy lifting, or unaccustomed physical activity.",
                "If your symptoms intensify, spread, or you experience sweating or breathlessness, call 112 immediately."
            ]
        else:
            triage = "Category C (ROUTINE)"
            rec = "Routine Primary Care or Cardiology Outpatient Consultation"
            summary_reason = "No acute emergency red flags identified from the reported symptoms."
            instructions = [
                "Schedule a routine evaluation with your primary physician to discuss your symptoms.",
                "Keep a written log of any future episodes, noting the time, activity, and duration.",
                "Seek immediate emergency care if symptoms worsen, spread to jaw/arm, or cause breathlessness."
            ]

        return SafetyEvaluation(
            is_emergency=is_emergency,
            triage_category=triage,
            red_flags=red_flags,
            primary_concern=primary_concern,
            reason=summary_reason,
            action_recommendation=rec,
            emergency_number="112",
            instructions=instructions
        )

safety_engine = SafetyEngine()
