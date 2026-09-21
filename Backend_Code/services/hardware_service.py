from enum import Enum
from typing import Any, Dict, List, Optional
import time
import uuid
from pydantic import BaseModel, Field

class ObservationSource(str, Enum):
    PATIENT_REPORTED = "PATIENT_REPORTED"
    MANUAL = "MANUAL"
    DEVICE = "DEVICE"
    LAB = "LAB"
    DATABASE = "DATABASE"
    CALCULATED = "CALCULATED"
    VALIDATED_RULE = "VALIDATED_RULE"
    AI_INTERPRETATION = "AI_INTERPRETATION"
    NOT_REPORTED = "NOT_REPORTED"

class ClinicalObservation(BaseModel):
    """
    Standardized Clinical Observation structure.
    Allows seamlessly blending patient-reported, manually entered,
    and future electronic hardware-measured physiological data.
    """
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    patient_id: str
    assessment_id: Optional[str] = None
    type: str # e.g. 'heart_rate', 'blood_pressure_systolic', 'spo2', 'ecg'
    value: Any
    unit: str # e.g. 'bpm', 'mmHg', '%', 'Celsius'
    source: ObservationSource = ObservationSource.MANUAL
    timestamp: float = Field(default_factory=time.time)
    quality: str = "HIGH" # 'HIGH', 'FAIR', 'NOISY', 'UNVALIDATED'

class DeviceIngestPayload(BaseModel):
    patient_id: str
    assessment_id: str
    device_id: str
    observations: List[Dict[str, Any]]

# Physiological boundary checks to prevent erroneous or corrupt sensor data
PHYSIOLOGICAL_LIMITS = {
    "heart_rate": {"min": 25, "max": 260, "unit": "bpm"},
    "blood_pressure_systolic": {"min": 50, "max": 280, "unit": "mmHg"},
    "blood_pressure_diastolic": {"min": 30, "max": 180, "unit": "mmHg"},
    "spo2": {"min": 50, "max": 100, "unit": "%"},
    "temperature": {"min": 30.0, "max": 44.0, "unit": "Celsius"},
    "respiratory_rate": {"min": 6, "max": 60, "unit": "breaths/min"},
    "glucose": {"min": 20, "max": 800, "unit": "mg/dL"}
}

def validate_observation_value(obs_type: str, value: Any, unit: str) -> tuple[bool, Optional[str]]:
    """Validates physiological limits and unit correctness."""
    if obs_type in PHYSIOLOGICAL_LIMITS:
        limits = PHYSIOLOGICAL_LIMITS[obs_type]
        try:
            num_val = float(value)
            if num_val < limits["min"] or num_val > limits["max"]:
                return False, f"Value {num_val} for {obs_type} is out of physiological bounds ({limits['min']}-{limits['max']} {limits['unit']})."
        except (ValueError, TypeError):
            return False, f"Value for {obs_type} must be numerical."
    return True, None

class HardwareService:
    """
    Manages observations and acts as an ingestion gateway for future
    cardiac electronics and telemetry hardware.
    """
    def __init__(self):
        # keyed by assessment_id -> list of ClinicalObservation
        self._observations_by_assessment: Dict[str, List[ClinicalObservation]] = {}

    def ingest_observations(
        self,
        patient_id: str,
        assessment_id: str,
        device_id: str,
        raw_observations: List[Dict[str, Any]]
    ) -> tuple[List[ClinicalObservation], List[str]]:
        validated_obs: List[ClinicalObservation] = []
        errors: List[str] = []

        for item in raw_observations:
            obs_type = item.get("type", "").strip().lower()
            val = item.get("value")
            unit = item.get("unit", "").strip()

            is_valid, err_msg = validate_observation_value(obs_type, val, unit)
            if not is_valid:
                errors.append(err_msg or f"Invalid observation: {item}")
                continue

            obs = ClinicalObservation(
                patient_id=patient_id,
                assessment_id=assessment_id,
                type=obs_type,
                value=val,
                unit=unit,
                source=ObservationSource.DEVICE,
                quality=item.get("quality", "HIGH")
            )
            validated_obs.append(obs)

        if assessment_id not in self._observations_by_assessment:
            self._observations_by_assessment[assessment_id] = []
        self._observations_by_assessment[assessment_id].extend(validated_obs)

        return validated_obs, errors

    def get_observations_for_assessment(self, assessment_id: str) -> List[ClinicalObservation]:
        return self._observations_by_assessment.get(assessment_id, [])

hardware_service = HardwareService()
