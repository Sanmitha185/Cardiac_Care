import re
import json
import logging
from typing import Any, Dict, List, Optional, Tuple
from pydantic import BaseModel, Field

from .nvidia_service import nvidia_service
from .safety_engine import safety_engine, SafetyEvaluation
from .scoring_service import scoring_service
from .rag_service import rag_service
from .hardware_service import ObservationSource

logger = logging.getLogger(__name__)

class ClinicalState(BaseModel):
    chief_complaint: Optional[str] = None
    chest_pain: Optional[bool] = None
    onset: Optional[str] = None
    duration: Optional[str] = None
    current: Optional[bool] = None
    pain_location: Optional[str] = None
    pain_quality: Optional[str] = None
    pain_severity: Optional[int] = None # 0 to 10
    pain_radiation: Optional[List[str]] = None
    worse_with_exertion: Optional[bool] = None
    better_with_rest: Optional[bool] = None
    associated_symptoms: Dict[str, bool] = Field(default_factory=dict)
    cardiac_history: Optional[str] = None
    risk_factors: Dict[str, str] = Field(default_factory=dict)
    medications: Optional[str] = None
    family_history: Optional[str] = None
    explicit_denials: List[str] = Field(default_factory=list)
    patient_corrections: List[Dict[str, Any]] = Field(default_factory=list)
    conflicts: List[str] = Field(default_factory=list)
    asked_question_keys: List[str] = Field(default_factory=list)
    question_count: int = 0
    current_branch: str = "GENERAL"

class DifferentialCondition(BaseModel):
    condition: str
    category: str # 'CARDIAC', 'PULMONARY', 'GASTROINTESTINAL', 'MUSCULOSKELETAL', 'OTHER'
    why_considered: str
    supporting_findings: List[str]
    missing_information: List[str]
    status: str = "Not confirmed"

class StructuredClinicalReport(BaseModel):
    triage_category_level: str
    urgency_recommendation: str
    leading_concern: Dict[str, Any]
    possible_conditions: List[DifferentialCondition]
    critical_red_flags: Dict[str, str]
    doctor_clinical_summary_text: str
    patient_friendly_summary: Dict[str, Any]
    reported_symptoms: List[str] = Field(default_factory=list)
    reported_history: List[str] = Field(default_factory=list)
    what_would_change_assessment: List[str] = Field(default_factory=list)
    clinical_completeness_pct: float
    validated_risk_scores: List[Dict[str, Any]]
    limitations: List[str]
    data_provenance: Dict[str, str]

class ClinicalEngine:
    """
    V3 Sparse Dynamic Cardiac Clinical Interview Engine with State Machine,
    Semantic Duplicate Suppression, Evidence-Based Extraction, and Dynamic Reporting.
    """

    MINIMUM_QUESTIONS = 5
    MAXIMUM_QUESTIONS = 10

    QUESTION_REGISTRY = {
        "severity": {
            "key": "pain_severity",
            "prompt": "On a scale from 0 to 10, with 0 being no pain and 10 being the most severe pain imaginable, how severe is your discomfort right now?",
            "check": lambda s: s.pain_severity is not None
        },
        "quality": {
            "key": "pain_quality",
            "prompt": "How would you describe the sensation — for example, does it feel like pressure, tightness, heaviness, squeezing, burning, sharp, stabbing, or aching?",
            "check": lambda s: s.pain_quality is not None
        },
        "radiation": {
            "key": "pain_radiation",
            "prompt": "Does the discomfort move or spread anywhere else, such as to your jaw, left arm, right arm, neck, or through to your back?",
            "check": lambda s: s.pain_radiation is not None
        },
        "onset_duration": {
            "key": "onset",
            "prompt": "When did this discomfort begin, and did it start suddenly or build up gradually over time?",
            "check": lambda s: (s.onset is not None or s.duration is not None)
        },
        "provocation": {
            "key": "worse_with_exertion",
            "prompt": "Does the discomfort become noticeably worse when you walk, climb stairs, or exert yourself physically?",
            "check": lambda s: s.worse_with_exertion is not None
        },
        "associated_symptoms": {
            "key": "associated_symptoms",
            "prompt": "Along with this discomfort, are you experiencing any shortness of breath, unusual sweating, nausea, or dizziness?",
            "check": lambda s: len(s.associated_symptoms) >= 1
        },
        "cardiac_history": {
            "key": "cardiac_history",
            "prompt": "Have you ever been diagnosed with any heart conditions, such as a prior heart attack, stents, high blood pressure, diabetes, or high cholesterol?",
            "check": lambda s: (s.cardiac_history is not None or "cardiac_history" in s.explicit_denials)
        },
        "medications": {
            "key": "medications",
            "prompt": "Are you currently taking any prescription medications, aspirin, or heart medications regularly?",
            "check": lambda s: (s.medications is not None or "medications" in s.explicit_denials)
        },
        "family_history": {
            "key": "family_history",
            "prompt": "Is there any history of early heart disease or unexpected sudden cardiac events in your immediate family?",
            "check": lambda s: (s.family_history is not None or "family_history" in s.explicit_denials)
        },
        "palpitations_detail": {
            "key": "palpitations_detail",
            "prompt": "Are your heart palpitations fast, irregular like fluttering, or do they feel like skipped beats? Have you felt faint during them?",
            "check": lambda s: "palpitations_detail" in s.asked_question_keys
        },
        "dyspnea_detail": {
            "key": "dyspnea_detail",
            "prompt": "Does the breathlessness happen while resting, or only when lying flat on your back or walking?",
            "check": lambda s: "dyspnea_detail" in s.asked_question_keys
        }
    }

    @classmethod
    def extract_clinical_facts(cls, user_text: str, current_state: ClinicalState) -> ClinicalState:
        """
        Sparse Evidence-Based Extraction:
        - Stores facts ONLY when supported by actual evidence.
        - Preserves explicit denials (e.g., 'I don't smoke').
        - Never defaults unmentioned attributes to false/null.
        - Supports patient self-correction and detects conflicting statements.
        """
        text = user_text.lower().strip()
        new_state = current_state.model_copy(deep=True)

        # 0. Check for patient self-correction
        correction_match = re.search(r"(?:actually|no wait|i meant|correction|changed to)\s*([0-9]|10)\b", text)
        if correction_match:
            new_val = int(correction_match.group(1))
            old_val = new_state.pain_severity
            new_state.pain_severity = new_val
            new_state.patient_corrections.append({
                "field": "pain_severity",
                "old_value": old_val,
                "new_value": new_val,
                "raw_text": user_text
            })
            return new_state

        # 1. Chief Complaint & Chest Pain
        if any(w in text for w in [
            "chest pain", "heart pain", "chest hurt", "hurts in my chest",
            "pressure in chest", "chest discomfort", "pain in chest", "heavy chest"
        ]):
            new_state.chest_pain = True
            new_state.chief_complaint = "Chest pain"
            new_state.current_branch = "CHEST_PAIN"
        elif any(w in text for w in ["palpitation", "racing heart", "fluttering", "heart skips"]):
            new_state.chief_complaint = "Palpitations"
            new_state.associated_symptoms["palpitations"] = True
            new_state.current_branch = "PALPITATIONS"
        elif any(w in text for w in ["short of breath", "breathless", "can't breathe", "hard to breathe"]):
            new_state.chief_complaint = "Shortness of breath"
            new_state.associated_symptoms["shortness_of_breath"] = True
            new_state.current_branch = "DYSPNEA"
        elif any(w in text for w in ["fainted", "blacked out", "passed out", "syncope"]):
            new_state.chief_complaint = "Syncope"
            new_state.associated_symptoms["syncope"] = True
            new_state.current_branch = "SYNCOPE"

        # 2. Pain Quality (sparse: only set if patient used quality descriptors)
        qualities = {
            "pressure": ["pressure", "heavy pressure", "weight", "elephant", "pressing"],
            "tightness": ["tight", "band", "tightness", "constriction"],
            "squeezing": ["squeezing", "vise", "clenched"],
            "crushing": ["crushing", "exploding"],
            "burning": ["burning", "on fire", "heartburn", "acid"],
            "sharp": ["sharp", "knife", "stabbing", "needle"],
            "tearing": ["tearing", "ripping"],
            "dull": ["dull", "ache", "aching"]
        }
        for q_label, markers in qualities.items():
            if any(m in text for m in markers):
                new_state.pain_quality = q_label
                break

        # 3. Pain Severity (0-10 numerical scale)
        sev_match = re.search(r"\b([0-9]|10)\s*(?:out of 10|/10|\b)", text)
        if sev_match:
            try:
                val = int(sev_match.group(1))
                if 0 <= val <= 10:
                    if new_state.pain_severity is not None and new_state.pain_severity != val:
                        new_state.patient_corrections.append({
                            "field": "pain_severity",
                            "previous": new_state.pain_severity,
                            "updated": val,
                            "utterance": text
                        })
                    new_state.pain_severity = val
            except ValueError:
                pass

        # 4. Radiation & Explicit Denial
        radiation_targets = []
        if any(w in text for w in ["jaw", "teeth", "chin"]):
            radiation_targets.append("jaw")
        if any(w in text for w in ["left arm", "arm", "fingers", "shoulder", "left shoulder"]):
            radiation_targets.append("left arm")
        if any(w in text for w in ["neck", "throat"]):
            radiation_targets.append("neck")
        if any(w in text for w in ["back", "shoulder blade", "between shoulder blades"]):
            radiation_targets.append("back")

        if radiation_targets:
            new_state.pain_radiation = radiation_targets
        elif any(w in text for w in ["doesn't spread", "no radiation", "only in my chest", "stays in the center", "nowhere else"]):
            new_state.pain_radiation = []
            if "radiation" not in new_state.explicit_denials:
                new_state.explicit_denials.append("radiation")

        # 5. Provocation vs Relief
        if any(w in text for w in ["worse when i walk", "worse with exertion", "worse with activity", "walking makes it worse", "exercise makes it worse"]):
            new_state.worse_with_exertion = True
        elif any(w in text for w in ["not worse with exertion", "exertion does not affect", "doesn't change with walking"]):
            new_state.worse_with_exertion = False

        if any(w in text for w in ["relaxing makes it better", "rest helps", "better with rest", "lying down helps", "sitting helps"]):
            new_state.better_with_rest = True
            # NOTE: We do NOT set worse_with_exertion = True here!

        # 6. Associated symptoms (only add keys that were mentioned)
        if any(w in text for w in ["sweat", "sweating", "cold sweat", "diaphoresis"]):
            new_state.associated_symptoms["sweating"] = True
        if any(w in text for w in ["breathless", "short of breath", "can't breathe", "hard to breathe"]):
            new_state.associated_symptoms["shortness_of_breath"] = True
        if any(w in text for w in ["nausea", "nauseous", "vomit", "sick to my stomach"]):
            new_state.associated_symptoms["nausea"] = True
        if any(w in text for w in ["dizzy", "lightheaded"]):
            new_state.associated_symptoms["dizziness"] = True
        if any(w in text for w in ["passed out", "blacked out", "fainted"]):
            new_state.associated_symptoms["syncope"] = True

        # 7. Medical History & Conflict Detection
        if any(w in text for w in ["no medical history", "nothing like that", "no prior health issues", "healthy"]):
            new_state.cardiac_history = "No reported history"
            if "cardiac_history" not in new_state.explicit_denials:
                new_state.explicit_denials.append("cardiac_history")
        else:
            hist_items = []
            if any(w in text for w in ["hypertension", "high blood pressure"]):
                hist_items.append("Hypertension")
            if any(w in text for w in ["diabetes", "high sugar", "insulin"]):
                hist_items.append("Type 2 Diabetes")
                # Check conflict if patient previously stated no medical history
                if new_state.cardiac_history == "No reported history":
                    new_state.conflicts.append("Patient previously stated no medical history, but subsequently reported diabetes.")
            if any(w in text for w in ["stent", "bypass", "heart attack", "cabg"]):
                hist_items.append("Coronary Artery Disease")
            if hist_items:
                new_state.cardiac_history = ", ".join(hist_items)

        # 8. Smoking (Strict: Check denials first before positive mention)
        if any(w in text for w in ["don't smoke", "dont smoke", "do not smoke", "never smoked", "non-smoker", "nonsmoker", "quit smoking"]):
            new_state.risk_factors["smoking"] = "Non-smoker"
            if "smoking" not in new_state.explicit_denials:
                new_state.explicit_denials.append("smoking")
        elif any(w in text for w in ["smoke", "smoker", "cigarettes", "pack per day"]):
            new_state.risk_factors["smoking"] = "Reported smoker"

        # 9. Diabetes explicit denial
        if any(w in text for w in ["don't have diabetes", "dont have diabetes", "no diabetes", "sugar is normal"]):
            new_state.risk_factors["diabetes"] = "Denied"
            if "diabetes" not in new_state.explicit_denials:
                new_state.explicit_denials.append("diabetes")

        # 10. Family History
        if any(w in text for w in ["family history", "father died of heart attack", "mother had bypass", "brother heart"]):
            new_state.family_history = "Positive family cardiac history"
        elif any(w in text for w in ["no family history", "no heart issues in family", "family is fine"]):
            new_state.family_history = "No reported history"
            if "family_history" not in new_state.explicit_denials:
                new_state.explicit_denials.append("family_history")
        elif text.strip() in ["no", "none", "nope", "not at all"] and ("family_history" in new_state.asked_question_keys or not new_state.family_history):
            new_state.family_history = "No reported history"
            if "family_history" not in new_state.explicit_denials:
                new_state.explicit_denials.append("family_history")

        return new_state

    @classmethod
    def select_next_question(cls, state: ClinicalState) -> Optional[Tuple[str, str]]:
        """
        Dynamically selects next clinically important question based on active branch.
        Suppresses duplicates and skips questions for already-collected facts.
        """
        if state.current_branch == "CHEST_PAIN" or state.chest_pain:
            priority_order = [
                "severity",
                "quality",
                "radiation",
                "onset_duration",
                "provocation",
                "associated_symptoms",
                "cardiac_history",
                "medications",
                "family_history"
            ]
        elif state.current_branch == "PALPITATIONS":
            priority_order = [
                "palpitations_detail",
                "associated_symptoms",
                "cardiac_history",
                "medications",
                "family_history"
            ]
        elif state.current_branch == "DYSPNEA":
            priority_order = [
                "dyspnea_detail",
                "provocation",
                "associated_symptoms",
                "cardiac_history",
                "medications"
            ]
        else:
            priority_order = [
                "severity",
                "onset_duration",
                "associated_symptoms",
                "cardiac_history",
                "medications"
            ]

        for q_id in priority_order:
            q_def = cls.QUESTION_REGISTRY.get(q_id)
            if not q_def:
                continue

            if q_id in state.asked_question_keys:
                continue

            if q_def["check"](state):
                continue

            return q_id, q_def["prompt"]

        return None

    @classmethod
    def generate_clinical_synthesis(
        cls,
        state: ClinicalState,
        patient_info: Dict[str, Any],
        metrics: Dict[str, Any],
        safety: SafetyEvaluation
    ) -> StructuredClinicalReport:
        """
        Synthesizes a sparse, evidence-grounded report.
        Strictly omits empty sections, placeholders, and fabricated numbers.
        """
        completeness = scoring_service.calculate_completeness(state.model_dump())
        age = patient_info.get("age")

        # Evaluate HEART score with strict requirement checking
        heart_score = scoring_service.evaluate_heart_score(
            clinical_state=state.model_dump(),
            patient_age=age,
            has_ecg=False,
            has_troponin=False
        )

        possible_conditions: List[DifferentialCondition] = []
        data_provenance: Dict[str, str] = {}

        # 1. Evaluate ACS consideration
        radiation_list = state.pain_radiation or []
        has_ischemic_radiation = any(loc in str(r).lower() for r in radiation_list for loc in ["jaw", "arm", "left arm", "neck"])
        has_pressure = state.pain_quality in ["pressure", "tightness", "squeezing", "crushing", "heavy"]

        if state.chest_pain and (has_ischemic_radiation or has_pressure or safety.is_emergency):
            supporting = ["Reported chest discomfort"]
            if has_ischemic_radiation:
                supporting.append(f"Radiation to {', '.join(radiation_list)}")
            if state.pain_severity:
                supporting.append(f"Reported severity {state.pain_severity}/10")
            if state.worse_with_exertion is True:
                supporting.append("Confirmed exertional worsening")

            possible_conditions.append(DifferentialCondition(
                condition="Possible Acute Coronary Syndrome (ACS)",
                category="CARDIAC",
                why_considered="Reported symptom pattern features characteristics and/or radiation consistent with myocardial ischemia.",
                supporting_findings=supporting,
                missing_information=["12-lead ECG", "Serum Troponin biomarkers", "In-person physician cardiovascular exam"],
                status="Not confirmed"
            ))

        # 2. Evaluate Musculoskeletal consideration
        if state.pain_quality in ["sharp", "stabbing"] and not has_ischemic_radiation:
            possible_conditions.append(DifferentialCondition(
                condition="Musculoskeletal Chest Wall Discomfort (e.g. Costochondritis)",
                category="MUSCULOSKELETAL",
                why_considered="Sharp, localized discomfort in the absence of ischemic radiation patterns.",
                supporting_findings=["Sharp/stabbing pain quality", "No reported radiation to jaw or left arm"],
                missing_information=["Chest wall palpation exam", "ECG to definitively rule out ischemia"],
                status="Not confirmed"
            ))

        # 3. Evaluate Gastrointestinal consideration
        if state.pain_quality == "burning" or "indigestion" in str(state.onset or "").lower():
            possible_conditions.append(DifferentialCondition(
                condition="Gastroesophageal Reflux (GERD) / Esophageal Discomfort",
                category="GASTROINTESTINAL",
                why_considered="Burning retrosternal discomfort.",
                supporting_findings=["Burning pain quality"],
                missing_information=["Trial of antacid therapy", "Cardiac ischemic exclusion"],
                status="Not confirmed"
            ))

        # 4. Evaluate Arrhythmia consideration
        if state.associated_symptoms.get("palpitations") or state.current_branch == "PALPITATIONS":
            possible_conditions.append(DifferentialCondition(
                condition="Symptomatic Cardiac Arrhythmia / Ectopy",
                category="CARDIAC",
                why_considered="Patient reports prominent palpitations or awareness of abnormal heart rhythm.",
                supporting_findings=["Reported palpitations"],
                missing_information=["ECG rhythm strip", "Holter monitor or cardiac event telemetry"],
                status="Not confirmed"
            ))

        if not possible_conditions:
            possible_conditions.append(DifferentialCondition(
                condition="Non-Specific Chest Discomfort",
                category="OTHER",
                why_considered="Symptoms reported do not demonstrate classical ischemic, pleuritic, or musculoskeletal patterns.",
                supporting_findings=["Clinical history documented"],
                missing_information=["Physical examination", "Diagnostic baseline ECG"],
                status="Not confirmed"
            ))

        leading_condition = possible_conditions[0].condition
        leading_why = possible_conditions[0].why_considered

        # Build Sparse List of Reported Symptoms (ONLY actual evidence)
        reported_symptoms: List[str] = []
        if state.chest_pain:
            reported_symptoms.append("Chest discomfort")
        if state.pain_quality:
            reported_symptoms.append(f"{state.pain_quality.title()} sensation")
        if state.pain_severity is not None:
            reported_symptoms.append(f"Severity: {state.pain_severity}/10")
        if state.pain_radiation:
            reported_symptoms.append(f"Radiation to {', '.join(state.pain_radiation)}")
        elif "radiation" in state.explicit_denials:
            reported_symptoms.append("No radiation to jaw, arms, or back (explicitly reported)")
        if state.better_with_rest:
            reported_symptoms.append("Improves with rest")
        if state.worse_with_exertion is True:
            reported_symptoms.append("Worsens with physical exertion")
        elif state.worse_with_exertion is False:
            reported_symptoms.append("Not related to physical exertion")
        for sym_name, sym_val in state.associated_symptoms.items():
            if sym_val:
                reported_symptoms.append(sym_name.replace("_", " ").title())

        # Build Sparse List of Reported History / Risk Factors
        reported_history: List[str] = []
        if state.cardiac_history and state.cardiac_history != "No reported history":
            reported_history.append(f"Known history: {state.cardiac_history}")
        elif "cardiac_history" in state.explicit_denials:
            reported_history.append("No prior cardiac history (explicitly reported)")
        if "smoking" in state.risk_factors:
            reported_history.append(state.risk_factors["smoking"])
        if "diabetes" in state.risk_factors:
            reported_history.append(f"Diabetes: {state.risk_factors['diabetes']}")
        if state.family_history and state.family_history != "No reported history":
            reported_history.append(f"Family history: {state.family_history}")

        # Dynamic "What would change the assessment"
        what_would_change: List[str] = []
        if state.current_branch == "CHEST_PAIN" or state.chest_pain:
            what_would_change = [
                "12-Lead Electrocardiogram (ECG) to assess ST-segment deviations or acute ischemia",
                "Serial High-Sensitivity Cardiac Troponin (hs-cTnI / hs-cTnT) to evaluate myocardial necrosis",
                "Formal cardiovascular physical examination (auscultation, chest wall palpation, vitals reassessment)"
            ]
        elif state.current_branch == "PALPITATIONS":
            what_would_change = [
                "12-Lead ECG rhythm strip during symptoms",
                "Continuous ambulatory Holter monitoring or cardiac event telemetry",
                "Serum electrolytes (potassium, magnesium) and thyroid stimulating hormone (TSH)"
            ]
        elif state.current_branch == "DYSPNEA":
            what_would_change = [
                "Chest radiography (CXR) to evaluate pulmonary congestion or parenchymal disease",
                "Transthoracic Echocardiogram (TTE) for ventricular function and valvular assessment",
                "Serum B-type Natriuretic Peptide (BNP / NT-proBNP) to differentiate cardiac from pulmonary causes"
            ]
        else:
            what_would_change = [
                "In-person physician cardiovascular evaluation and diagnostic baseline ECG",
                "Targeted laboratory investigations based on physical examination findings"
            ]

        # Data Provenance mapping
        if metrics.get("blood_pressure_status"):
            data_provenance["blood_pressure"] = ObservationSource.MANUAL.value
        if metrics.get("resting_heart_rate_status"):
            data_provenance["resting_heart_rate"] = ObservationSource.MANUAL.value
        data_provenance["symptoms"] = ObservationSource.PATIENT_REPORTED.value
        data_provenance["completeness_score"] = ObservationSource.CALCULATED.value
        data_provenance["safety_triage"] = ObservationSource.VALIDATED_RULE.value
        data_provenance["differential_patterns"] = ObservationSource.AI_INTERPRETATION.value

        limitations = [
            "This application provides AI-assisted clinical decision support and does NOT establish a definitive medical diagnosis.",
            "12-Lead Electrocardiogram (ECG) was not available in this software assessment.",
            "Cardiac biomarkers (High-Sensitivity Troponin) were not available.",
            "In-person physical examination was not performed."
        ]

        # Concise Doctor Summary
        doc_summary = (
            f"Patient {patient_info.get('full_name', 'Patient')} ({patient_info.get('age', 'Unknown')}yo {patient_info.get('gender', '')}) "
            f"completed an AI-assisted cardiac symptom assessment. Presentation: {', '.join(reported_symptoms) if reported_symptoms else 'cardiac symptoms'}. "
            f"Triage determined: {safety.triage_category}. Leading consideration: {leading_condition} (Not confirmed). "
            f"Branch completeness: {completeness.completeness_percentage}%. {safety.reason}."
        )

        # Sparse Patient-friendly summary
        heard_desc = f"You reported {'discomfort in your chest' if state.chest_pain else 'symptoms'}"
        if state.pain_quality:
            heard_desc += f" described as {state.pain_quality}"
        if state.pain_severity is not None:
            heard_desc += f", with a severity of {state.pain_severity}/10"
        if state.pain_radiation:
            heard_desc += f", spreading to your {', '.join(state.pain_radiation)}"
        elif "radiation" in state.explicit_denials:
            heard_desc += ", staying in the chest without spreading"

        patient_summary = {
            "what_we_heard": heard_desc + ".",
            "important_symptoms": reported_symptoms,
            "why_evaluation_needed": (
                "Symptoms in the chest area can arise from the heart, muscles, lungs, or digestive system. "
                "Because serious cardiac conditions require early professional care, in-person evaluation by a healthcare provider is advised."
            ),
            "what_to_do_next": safety.action_recommendation,
            "emergency_guidance": safety.instructions if safety.is_emergency else None
        }

        return StructuredClinicalReport(
            triage_category_level=safety.triage_category,
            urgency_recommendation=safety.action_recommendation,
            leading_concern={
                "possible_condition": leading_condition,
                "why_considered": leading_why,
                "status": "Not confirmed"
            },
            possible_conditions=possible_conditions[:4],
            critical_red_flags=safety.red_flags,
            doctor_clinical_summary_text=doc_summary,
            patient_friendly_summary=patient_summary,
            reported_symptoms=reported_symptoms,
            reported_history=reported_history,
            what_would_change_assessment=what_would_change,
            clinical_completeness_pct=completeness.completeness_percentage,
            validated_risk_scores=[heart_score.model_dump()],
            limitations=limitations,
            data_provenance=data_provenance
        )

clinical_engine = ClinicalEngine()
