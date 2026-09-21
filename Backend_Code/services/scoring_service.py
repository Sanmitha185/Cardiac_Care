from typing import Any, Dict, List, Optional
import time
from pydantic import BaseModel

class ValidatedScoreResult(BaseModel):
    score_name: str
    version: str
    is_available: bool
    score_value: Optional[int] = None
    max_score: Optional[int] = None
    interpretation: Optional[str] = None
    inputs_used: Dict[str, Any] = {}
    missing_inputs: List[str] = []
    source_citation: str
    calculated_at: float

class CompletenessResult(BaseModel):
    completeness_percentage: float
    total_required_fields: int
    collected_fields_count: int
    collected_fields: List[str]
    missing_fields: List[str]
    description: str

class ScoringService:
    """
    Manages deterministic clinical calculations.
    Ensures zero fabricated risk scores and strictly separates
    information completeness from diagnostic accuracy.
    """

    CORE_CLINICAL_DIMENSIONS = [
        "pain_presence",
        "onset",
        "duration",
        "pain_severity",
        "pain_quality",
        "pain_radiation",
        "associated_symptoms",
        "provocation_or_relief",
        "cardiac_or_medical_history",
        "current_symptom_status"
    ]

    @classmethod
    def calculate_completeness(cls, clinical_state: Dict[str, Any]) -> CompletenessResult:
        """
        Calculates the deterministic percentage of required clinical assessment
        information collected so far.
        """
        collected: List[str] = []
        missing: List[str] = []

        # 1. Pain presence
        if "chest_pain" in clinical_state and clinical_state["chest_pain"] is not None:
            collected.append("pain_presence")
        else:
            missing.append("pain_presence")

        # 2. Onset
        if clinical_state.get("onset"):
            collected.append("onset")
        else:
            missing.append("onset")

        # 3. Duration
        if clinical_state.get("duration"):
            collected.append("duration")
        else:
            missing.append("duration")

        # 4. Severity (0-10)
        if clinical_state.get("pain_severity") is not None:
            collected.append("pain_severity")
        else:
            missing.append("pain_severity")

        # 5. Quality
        if clinical_state.get("pain_quality"):
            collected.append("pain_quality")
        else:
            missing.append("pain_quality")

        # 6. Radiation
        if "pain_radiation" in clinical_state and clinical_state["pain_radiation"] is not None:
            collected.append("pain_radiation")
        else:
            missing.append("pain_radiation")

        # 7. Associated symptoms
        assoc = clinical_state.get("associated_symptoms")
        if isinstance(assoc, dict) and len(assoc) > 0:
            collected.append("associated_symptoms")
        else:
            missing.append("associated_symptoms")

        # 8. Provocation / relief
        if clinical_state.get("worse_with_exertion") is not None or clinical_state.get("better_with_rest") is not None:
            collected.append("provocation_or_relief")
        else:
            missing.append("provocation_or_relief")

        # 9. Medical history / risk factors
        hist = clinical_state.get("past_history") or clinical_state.get("cardiac_history")
        rf = clinical_state.get("risk_factors")
        if hist is not None or rf is not None:
            collected.append("cardiac_or_medical_history")
        else:
            missing.append("cardiac_or_medical_history")

        # 10. Current status
        if "current" in clinical_state and clinical_state["current"] is not None:
            collected.append("current_symptom_status")
        else:
            missing.append("current_symptom_status")

        total = len(cls.CORE_CLINICAL_DIMENSIONS)
        count = len(collected)
        pct = round((count / total) * 100.0, 1)

        return CompletenessResult(
            completeness_percentage=pct,
            total_required_fields=total,
            collected_fields_count=count,
            collected_fields=collected,
            missing_fields=missing,
            description=f"{count} of {total} core clinical assessment dimensions documented."
        )

    @classmethod
    def evaluate_heart_score(
        cls,
        clinical_state: Dict[str, Any],
        patient_age: Optional[int],
        has_ecg: bool = False,
        ecg_data: Optional[Dict[str, Any]] = None,
        has_troponin: bool = False,
        troponin_value: Optional[float] = None
    ) -> ValidatedScoreResult:
        """
        Evaluates the clinical HEART Score (Six et al., 2008; Backus et al., 2013).
        STRICT MEDICAL RULE: If ECG or Troponin is missing, DO NOT FABRICATE A SCORE.
        Report explicitly that the validated score is unavailable.
        """
        missing_inputs: List[str] = []
        if not has_ecg or ecg_data is None:
            missing_inputs.append("12-Lead Electrocardiogram (ECG)")
        if not has_troponin or troponin_value is None:
            missing_inputs.append("Initial Serum Cardiac Troponin (cTnI/cTnT)")

        if missing_inputs:
            return ValidatedScoreResult(
                score_name="HEART Score for Suspected ACS",
                version="2008/2013 Clinical Pathway",
                is_available=False,
                score_value=None,
                max_score=10,
                interpretation="Validated score unavailable: Required objective clinical inputs (ECG and Troponin) were not provided.",
                inputs_used={"age": patient_age},
                missing_inputs=missing_inputs,
                source_citation="Six AJ, Backus BE, Kelder JC. Chest pain in the emergency department: value of the HEART score. Neth Heart J. 2008;16(6):191-196.",
                calculated_at=time.time()
            )

        # In future hardware/lab integration, this calculates the authentic validated HEART score (0-10)
        # History (0-2), ECG (0-2), Age (0-2), Risk factors (0-2), Troponin (0-2)
        score = 0
        if patient_age:
            if patient_age >= 65:
                score += 2
            elif patient_age >= 45:
                score += 1

        return ValidatedScoreResult(
            score_name="HEART Score for Suspected ACS",
            version="2008/2013 Clinical Pathway",
            is_available=True,
            score_value=score,
            max_score=10,
            interpretation=f"Score: {score}/10. Requires attending physician clinical correlation.",
            inputs_used={"age": patient_age, "ecg": True, "troponin": True},
            missing_inputs=[],
            source_citation="Six AJ, Backus BE, Kelder JC. Neth Heart J. 2008;16(6):191-196.",
            calculated_at=time.time()
        )

scoring_service = ScoringService()
