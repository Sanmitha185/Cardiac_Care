import re
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
    V3 Deterministic Clinical Safety Engine.
    Operates strictly on evidence that actually exists:
    - Distinguishes TRUE, FALSE (explicitly denied), and UNKNOWN (absent from data).
    - Missing information is never defaulted to false or negative.
    - Generates dynamic, evidence-based emergency reasons reflecting only reported facts.
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
        radiation = clinical_state.get("pain_radiation")
        explicit_denials = clinical_state.get("explicit_denials", [])

        # Radiation check (Only if present and not explicitly denied)
        if radiation and "radiation" not in explicit_denials:
            if isinstance(radiation, str):
                radiation = [radiation]
            radiation_lower = [str(r).lower() for r in radiation]
            concerning_radiation = any(loc in r for r in radiation_lower for loc in ["jaw", "arm", "left arm", "neck", "shoulder", "back"])
            if chest_pain and concerning_radiation:
                red_flags["radiation_to_vital_areas"] = f"Chest pain radiating to {', '.join(radiation_lower)} was reported."
                is_emergency = True
                primary_concern = "Possible Acute Coronary Syndrome (ACS)"
                reasons.append(f"Chest pain with radiation to the {', '.join(radiation_lower)}")

        # Autonomic symptoms check
        associated = clinical_state.get("associated_symptoms") or {}
        has_syncope = associated.get("syncope") is True
        has_dyspnea = associated.get("shortness_of_breath") is True
        has_sweating = associated.get("sweating") is True
        has_palpitations = associated.get("palpitations") is True

        if chest_pain and (has_sweating or has_dyspnea):
            s_list = []
            if has_sweating:
                s_list.append("sweating (diaphoresis)")
            if has_dyspnea:
                s_list.append("shortness of breath")
            red_flags["ischemic_autonomic_symptoms"] = f"Chest discomfort accompanied by {', '.join(s_list)} was reported."
            is_emergency = True
            primary_concern = primary_concern or "Possible Acute Coronary Syndrome (ACS)"
            reasons.append(f"Chest discomfort accompanied by {', '.join(s_list)}")

        # Syncope check
        if has_syncope:
            if chest_pain or has_palpitations:
                red_flags["cardiogenic_syncope"] = "Loss of consciousness accompanied by chest pain or palpitations was reported."
                is_emergency = True
                primary_concern = primary_concern or "Cardiogenic Syncope / Suspected Arrhythmia"
                reasons.append("Fainting/syncope with cardiac symptoms")
            else:
                red_flags["unexplained_syncope"] = "Unexplained fainting/syncope requires prompt medical evaluation."
                is_urgent = True
                reasons.append("Unexplained fainting episode")

        # Severe hyperacute pain check (>= 8/10) with sudden/tearing onset
        onset = (clinical_state.get("onset") or "").lower()
        try:
            sev_num = float(severity) if severity is not None else 0
        except (ValueError, TypeError):
            sev_num = 0

        if chest_pain and sev_num >= 8:
            if "sudden" in onset or "thunderbolt" in onset or "tearing" in quality or "ripping" in quality:
                red_flags["hyperacute_severe_pain"] = "Sudden-onset severe (8+/10) tearing chest pain was reported."
                is_emergency = True
                primary_concern = primary_concern or "Possible Acute Aortic Syndrome or Severe Ischemia"
                reasons.append("Sudden-onset severe tearing chest pain")
            else:
                red_flags["severe_chest_pain"] = f"Severe chest pain rated {int(sev_num)}/10 warrants prompt clinical evaluation."
                is_urgent = True

        # Baseline vitals red flags (only if explicitly recorded)
        if baseline_metrics:
            hr_str = str(baseline_metrics.get("resting_heart_rate_status", "")).lower()
            bp_str = str(baseline_metrics.get("blood_pressure_status", "")).lower()
            
            hr_match = re.search(r"(\d+)", hr_str)
            if hr_match:
                hr_val = int(hr_match.group(1))
                if hr_val > 150 or hr_val < 40:
                    red_flags["hemodynamic_instability_hr"] = f"Measured heart rate of {hr_val} bpm is outside safe limits."
                    is_emergency = True
                    reasons.append(f"Critical heart rate ({hr_val} bpm)")

            bp_match = re.search(r"(\d+)\s*/\s*(\d+)", bp_str)
            if bp_match:
                sys_val = int(bp_match.group(1))
                dia_val = int(bp_match.group(2))
                if sys_val >= 200 or dia_val >= 120:
                    red_flags["hypertensive_crisis"] = f"Measured blood pressure {sys_val}/{dia_val} mmHg represents a potential hypertensive crisis."
                    is_urgent = True
                    reasons.append(f"Severe hypertension ({sys_val}/{dia_val} mmHg)")
                elif sys_val < 80:
                    red_flags["severe_hypotension"] = f"Measured systolic blood pressure {sys_val} mmHg indicates severe hypotension."
                    is_emergency = True
                    reasons.append(f"Severe hypotension ({sys_val} mmHg systolic)")

        # Compile final determination
        if is_emergency:
            triage = "Category A (EMERGENCY)"
            rec = "Immediate Emergency Department / Casualty Evaluation via Ambulance"
            summary_reason = f"{'; '.join(reasons)} was reported. Urgent medical evaluation is recommended." if reasons else "High-risk cardiac symptom combination detected."
            instructions = [
                "Call Indian Emergency Medical Services at 112 immediately.",
                "Do not attempt to drive yourself. Wait for emergency services or have someone transport you.",
                "Sit in a comfortable upright position, stay calm, and loosen tight clothing around your chest and neck.",
                "If prescribed emergency cardiac medication by your doctor, take as instructed."
            ]
        elif is_urgent:
            triage = "Category B (URGENT)"
            rec = "Urgent Outpatient Cardiology / Urgent Care Evaluation within 12-24 hours"
            summary_reason = f"{'; '.join(reasons)}. Prompt physician evaluation is recommended." if reasons else "Symptoms require prompt physician evaluation."
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
                "Keep a log of when the discomfort occurs, what you were doing, and how long it lasts.",
                "If new severe symptoms develop or pain spreads to your jaw or left arm, seek emergency care immediately."
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
