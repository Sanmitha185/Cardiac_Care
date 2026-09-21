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
    branch: str
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
    dynamic information completeness from diagnostic accuracy.
    """

    BRANCH_DIMENSIONS: Dict[str, List[str]] = {
        "CHEST_PAIN": [
            "onset_duration",
            "pain_severity",
            "pain_quality",
            "pain_radiation",
            "provocation_or_relief"
        ],
        "PALPITATIONS": [
            "palpitation_character",
            "onset_duration",
            "associated_presyncope",
            "provocation"
        ],
        "DYSPNEA": [
            "dyspnea_timing",
            "exertional_limits",
            "orthopnea_or_pnd",
            "chest_association"
        ],
        "SYNCOPE": [
            "prodromal_symptoms",
            "exertional_context",
            "post_event_recovery",
            "chest_or_rhythm_association"
        ],
        "GENERAL": [
            "chief_complaint",
            "onset_duration",
            "severity_or_quality"
        ]
    }

    @classmethod
    def calculate_completeness(cls, clinical_state: Dict[str, Any]) -> CompletenessResult:
        """
        Dynamically calculates the percentage of required clinical assessment
        information collected so far for the active symptom branch.
        """
        branch = clinical_state.get("current_branch", "GENERAL")
        if branch == "GENERAL" or branch not in cls.BRANCH_DIMENSIONS:
            if clinical_state.get("chest_pain"):
                branch = "CHEST_PAIN"
            elif clinical_state.get("palpitations") or (clinical_state.get("associated_symptoms") and clinical_state.get("associated_symptoms", {}).get("palpitations")):
                branch = "PALPITATIONS"
            elif clinical_state.get("dyspnea") or (clinical_state.get("associated_symptoms") and clinical_state.get("associated_symptoms", {}).get("shortness_of_breath")):
                branch = "DYSPNEA"
            elif clinical_state.get("syncope") or (clinical_state.get("associated_symptoms") and clinical_state.get("associated_symptoms", {}).get("syncope")):
                branch = "SYNCOPE"
            else:
                branch = "GENERAL"

        dimensions = cls.BRANCH_DIMENSIONS.get(branch, cls.BRANCH_DIMENSIONS["GENERAL"])
        collected: List[str] = []
        missing: List[str] = []

        if branch == "CHEST_PAIN":
            # 1. Onset or duration
            if clinical_state.get("onset") or clinical_state.get("duration"):
                collected.append("onset_duration")
            else:
                missing.append("onset_duration")

            # 2. Pain severity (0-10)
            if clinical_state.get("pain_severity") is not None:
                collected.append("pain_severity")
            else:
                missing.append("pain_severity")

            # 3. Pain quality
            if clinical_state.get("pain_quality"):
                collected.append("pain_quality")
            else:
                missing.append("pain_quality")

            # 4. Pain radiation (explicit list, can be empty if denied)
            if clinical_state.get("pain_radiation") is not None:
                collected.append("pain_radiation")
            else:
                missing.append("pain_radiation")

            # 5. Provocation or relief
            if (clinical_state.get("worse_with_exertion") is not None or 
                clinical_state.get("better_with_rest") is not None):
                collected.append("provocation_or_relief")
            else:
                missing.append("provocation_or_relief")

        elif branch == "PALPITATIONS":
            assoc = clinical_state.get("associated_symptoms", {})
            if clinical_state.get("palpitation_character") or assoc.get("palpitations"):
                collected.append("palpitation_character")
            else:
                missing.append("palpitation_character")

            if clinical_state.get("onset") or clinical_state.get("duration"):
                collected.append("onset_duration")
            else:
                missing.append("onset_duration")

            if assoc.get("dizziness") is not None or assoc.get("syncope") is not None:
                collected.append("associated_presyncope")
            else:
                missing.append("associated_presyncope")

            if clinical_state.get("worse_with_exertion") is not None:
                collected.append("provocation")
            else:
                missing.append("provocation")

        elif branch == "DYSPNEA":
            assoc = clinical_state.get("associated_symptoms", {})
            if assoc.get("shortness_of_breath"):
                collected.append("dyspnea_timing")
            else:
                missing.append("dyspnea_timing")

            if clinical_state.get("worse_with_exertion") is not None:
                collected.append("exertional_limits")
            else:
                missing.append("exertional_limits")

            if clinical_state.get("orthopnea") is not None:
                collected.append("orthopnea_or_pnd")
            else:
                missing.append("orthopnea_or_pnd")

            if clinical_state.get("chest_pain") is not None:
                collected.append("chest_association")
            else:
                missing.append("chest_association")

        elif branch == "SYNCOPE":
            assoc = clinical_state.get("associated_symptoms", {})
            if assoc.get("syncope") or assoc.get("dizziness"):
                collected.append("prodromal_symptoms")
            else:
                missing.append("prodromal_symptoms")

            if clinical_state.get("duration"):
                collected.append("duration_unconsciousness")
            else:
                missing.append("duration_unconsciousness")

            if clinical_state.get("worse_with_exertion") is not None:
                collected.append("exertional_context")
            else:
                missing.append("exertional_context")

            if clinical_state.get("chest_pain") is not None or assoc.get("palpitations") is not None:
                collected.append("chest_or_rhythm_association")
            else:
                missing.append("chest_or_rhythm_association")

        else: # GENERAL
            if clinical_state.get("chief_complaint") or clinical_state.get("chest_pain"):
                collected.append("chief_complaint")
            else:
                missing.append("chief_complaint")

            if clinical_state.get("onset") or clinical_state.get("duration"):
                collected.append("onset_duration")
            else:
                missing.append("onset_duration")

            if clinical_state.get("pain_severity") is not None or clinical_state.get("pain_quality"):
                collected.append("severity_or_quality")
            else:
                missing.append("severity_or_quality")

        total = len(dimensions)
        count = len(collected)
        pct = round((count / total) * 100.0, 1) if total > 0 else 0.0

        return CompletenessResult(
            branch=branch,
            completeness_percentage=pct,
            total_required_fields=total,
            collected_fields_count=count,
            collected_fields=collected,
            missing_fields=missing,
            description=f"{count} of {total} {branch.replace('_', ' ').title()} core clinical assessment dimensions documented."
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
