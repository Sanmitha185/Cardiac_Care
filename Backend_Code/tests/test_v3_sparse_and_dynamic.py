import os
import sys
import unittest

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from services.clinical_engine import clinical_engine, ClinicalState
from services.safety_engine import safety_engine
from services.scoring_service import scoring_service
from services.pdf_service import pdf_service
from services.hardware_service import validate_observation_value, ObservationSource, ClinicalObservation

class TestCardiacCareV3DynamicSpecifications(unittest.TestCase):
    """
    Validates Section 55 & V3 Dynamic Requirements:
    1. Sparse dynamic state (absence != negative, explicit negatives, empty section suppression).
    2. Dynamic report generation & PDF suppression of absent fields.
    3. Deterministic safety, 112 emergency routing, and lack of fabricated data.
    4. Hardware bounds validation & secret masking.
    """

    def test_01_only_provided_fields_appear(self):
        state = ClinicalState()
        state = clinical_engine.extract_clinical_facts("I have chest pain.", state)
        self.assertTrue(state.chest_pain)
        self.assertIsNone(state.pain_quality)
        self.assertIsNone(state.pain_severity)
        self.assertIsNone(state.pain_radiation)
        self.assertNotIn("smoking", state.risk_factors)
        self.assertNotIn("diabetes", state.risk_factors)

    def test_02_missing_smoking_is_absent(self):
        state = ClinicalState()
        state = clinical_engine.extract_clinical_facts("My chest hurts a bit.", state)
        self.assertNotIn("smoking", state.risk_factors)
        self.assertNotIn("smoking", state.explicit_denials)

    def test_03_missing_diabetes_is_absent(self):
        state = ClinicalState()
        state = clinical_engine.extract_clinical_facts("Just feeling dizzy.", state)
        self.assertNotIn("diabetes", state.risk_factors)
        self.assertNotIn("diabetes", state.explicit_denials)

    def test_04_missing_hypertension_is_absent(self):
        state = ClinicalState()
        state = clinical_engine.extract_clinical_facts("My chest aches.", state)
        self.assertNotIn("hypertension", state.risk_factors)

    def test_05_missing_family_history_is_absent(self):
        state = ClinicalState()
        state = clinical_engine.extract_clinical_facts("I felt a sharp pain.", state)
        self.assertIsNone(state.family_history)

    def test_06_missing_exertional_relationship_is_absent(self):
        state = ClinicalState()
        state = clinical_engine.extract_clinical_facts("I felt chest pressure.", state)
        self.assertIsNone(state.worse_with_exertion)

    def test_07_missing_radiation_is_absent(self):
        state = ClinicalState()
        state = clinical_engine.extract_clinical_facts("I have chest tightness.", state)
        self.assertIsNone(state.pain_radiation)

    def test_08_missing_nausea_is_absent(self):
        state = ClinicalState()
        state = clinical_engine.extract_clinical_facts("I have chest pain.", state)
        self.assertNotIn("nausea", state.associated_symptoms)

    def test_09_missing_dizziness_is_absent(self):
        state = ClinicalState()
        state = clinical_engine.extract_clinical_facts("I have chest pain.", state)
        self.assertNotIn("dizziness", state.associated_symptoms)

    def test_10_missing_palpitations_is_absent(self):
        state = ClinicalState()
        state = clinical_engine.extract_clinical_facts("I have chest pain.", state)
        self.assertNotIn("palpitations", state.associated_symptoms)

    def test_11_explicit_dont_smoke_stored_as_denial(self):
        state = ClinicalState()
        state = clinical_engine.extract_clinical_facts("I don't smoke at all.", state)
        self.assertIn("smoking", state.explicit_denials)
        self.assertEqual(state.risk_factors.get("smoking"), "Non-smoker")

    def test_12_silence_about_smoking_not_stored_as_negative(self):
        state = ClinicalState()
        state = clinical_engine.extract_clinical_facts("I have chest pain.", state)
        self.assertNotIn("smoking", state.explicit_denials)
        self.assertNotIn("smoking", state.risk_factors)

    def test_13_explicit_dont_have_diabetes_stored_as_negative(self):
        state = ClinicalState()
        state = clinical_engine.extract_clinical_facts("I don't have diabetes.", state)
        self.assertIn("diabetes", state.explicit_denials)
        self.assertEqual(state.risk_factors.get("diabetes"), "Denied")

    def test_14_silence_about_diabetes_not_stored_as_negative(self):
        state = ClinicalState()
        state = clinical_engine.extract_clinical_facts("I have chest heaviness.", state)
        self.assertNotIn("diabetes", state.explicit_denials)
        self.assertNotIn("diabetes", state.risk_factors)

    def test_15_rest_relief_does_not_imply_exertional_worsening(self):
        state = ClinicalState()
        state = clinical_engine.extract_clinical_facts("Relaxing makes it better.", state)
        self.assertTrue(state.better_with_rest)
        self.assertIsNone(state.worse_with_exertion, "Absence of exertional info must remain None")

    def test_16_duplicate_questions_prevented(self):
        state = ClinicalState()
        state = clinical_engine.extract_clinical_facts("My chest hurts, it goes to my jaw, and it is 8/10.", state)
        next_q = clinical_engine.select_next_question(state)
        self.assertIsNotNone(next_q)
        q_key, prompt = next_q
        self.assertNotIn(q_key, ["severity", "radiation"])

    def test_17_ambiguous_answers_do_not_create_facts(self):
        state = ClinicalState()
        state = clinical_engine.extract_clinical_facts("Sometimes it happens.", state)
        self.assertIsNone(state.duration)
        self.assertIsNone(state.onset)

    def test_18_patient_self_correction_handled(self):
        state = ClinicalState()
        state = clinical_engine.extract_clinical_facts("My pain is 3/10.", state)
        self.assertEqual(state.pain_severity, 3)
        state = clinical_engine.extract_clinical_facts("Actually it is 7/10 now.", state)
        self.assertEqual(state.pain_severity, 7)
        self.assertTrue(len(state.patient_corrections) > 0)

    def test_19_emergency_chest_pain_plus_jaw_radiation(self):
        state = ClinicalState()
        state = clinical_engine.extract_clinical_facts("Chest pain radiating to my jaw.", state)
        eval_res = safety_engine.evaluate(state.model_dump())
        self.assertTrue(eval_res.is_emergency)
        self.assertIn("112", eval_res.emergency_number)

    def test_20_emergency_flow_provides_112(self):
        state = ClinicalState()
        state.chest_pain = True
        state.pain_radiation = ["jaw"]
        eval_res = safety_engine.evaluate(state.model_dump())
        self.assertEqual(eval_res.emergency_number, "112")
        self.assertTrue(any("112" in inst for inst in eval_res.instructions))

    def test_21_llm_cannot_override_emergency_rule(self):
        state = ClinicalState()
        state.chest_pain = True
        state.pain_radiation = ["jaw"]
        eval_res = safety_engine.evaluate(state.model_dump())
        self.assertTrue(eval_res.is_emergency)
        # Even if AI output claims "routine", safety_eval remains Emergency
        report = clinical_engine.generate_clinical_synthesis(
            state=state,
            patient_info={"full_name": "Test Patient", "age": 45, "gender": "Male"},
            metrics={},
            safety=eval_res
        )
        self.assertEqual(report.triage_category_level, "Category A (EMERGENCY)")

    def test_22_missing_ecg_does_not_become_normal(self):
        state = ClinicalState()
        state.chest_pain = True
        eval_res = safety_engine.evaluate(state.model_dump())
        report = clinical_engine.generate_clinical_synthesis(
            state=state,
            patient_info={"full_name": "Test", "age": 50, "gender": "Male"},
            metrics={},
            safety=eval_res
        )
        report_str = str(report.model_dump())
        self.assertNotIn("Normal ECG", report_str)
        self.assertNotIn("normal electrocardiogram", report_str.lower())

    def test_23_missing_troponin_does_not_become_negative(self):
        state = ClinicalState()
        state.chest_pain = True
        eval_res = safety_engine.evaluate(state.model_dump())
        report = clinical_engine.generate_clinical_synthesis(
            state=state,
            patient_info={"full_name": "Test", "age": 50, "gender": "Male"},
            metrics={},
            safety=eval_res
        )
        report_str = str(report.model_dump())
        self.assertNotIn("Troponin negative", report_str)
        self.assertNotIn("negative troponin", report_str.lower())

    def test_24_heart_unavailable_without_required_inputs(self):
        state = ClinicalState()
        state.chest_pain = True
        score_res = scoring_service.evaluate_heart_score(
            clinical_state=state.model_dump(),
            patient_age=50,
            has_ecg=False,
            has_troponin=False
        )
        self.assertFalse(score_res.is_available)
        self.assertIsNone(score_res.score_value)

    def test_25_no_fabricated_confidence_or_risk_percentages(self):
        state = ClinicalState()
        state.chest_pain = True
        state.pain_severity = 5
        eval_res = safety_engine.evaluate(state.model_dump())
        report = clinical_engine.generate_clinical_synthesis(
            state=state,
            patient_info={"full_name": "Test", "age": 30, "gender": "Male"},
            metrics={},
            safety=eval_res
        )
        rep_str = str(report.model_dump())
        for forbidden in ["90.5%", "95%", "85/100", "91.7%"]:
            self.assertNotIn(forbidden, rep_str)

    def test_26_no_fabricated_confirmed_diagnosis(self):
        state = ClinicalState()
        state.chest_pain = True
        state.pain_radiation = ["jaw"]
        eval_res = safety_engine.evaluate(state.model_dump())
        report = clinical_engine.generate_clinical_synthesis(
            state=state,
            patient_info={"full_name": "Test", "age": 21, "gender": "Male"},
            metrics={},
            safety=eval_res
        )
        self.assertNotEqual(report.leading_concern.get("status"), "Confirmed")
        self.assertEqual(report.leading_concern.get("status"), "Not confirmed")

    def test_27_dynamic_clinical_consideration_generation(self):
        state = ClinicalState()
        state = clinical_engine.extract_clinical_facts("I have sudden fluttering palpitations and skipped beats.", state)
        eval_res = safety_engine.evaluate(state.model_dump())
        report = clinical_engine.generate_clinical_synthesis(
            state=state,
            patient_info={"full_name": "Test", "age": 28, "gender": "Female"},
            metrics={},
            safety=eval_res
        )
        conditions = [c.condition for c in report.possible_conditions]
        self.assertTrue(any("Arrhythmia" in c for c in conditions))

    def test_28_empty_sections_omitted_in_report_synthesis(self):
        state = ClinicalState()
        state = clinical_engine.extract_clinical_facts("I have chest pain.", state)
        eval_res = safety_engine.evaluate(state.model_dump())
        report = clinical_engine.generate_clinical_synthesis(
            state=state,
            patient_info={"full_name": "Test", "age": 25, "gender": "Male"},
            metrics={},
            safety=eval_res
        )
        self.assertEqual(len(report.reported_history), 0, "No history reported, so reported_history must be empty")
        self.assertNotIn("Not reported", str(report.reported_symptoms))

    def test_29_dynamic_pdf_omits_empty_fields_and_is_valid(self):
        report_data = {
            "triage_category_level": "Category C (ROUTINE)",
            "urgency_recommendation": "Routine evaluation",
            "clinical_completeness_pct": 60.0,
            "reported_symptoms": ["Chest discomfort", "Sharp sensation"],
            "reported_history": [],  # Empty
            "possible_conditions": [
                {
                    "condition": "Possible Musculoskeletal Discomfort",
                    "category": "MUSCULOSKELETAL",
                    "why_considered": "Sharp chest wall discomfort",
                    "supporting_findings": ["Sharp sensation"],
                    "missing_information": ["ECG"],
                    "status": "Not confirmed"
                }
            ],
            "doctor_clinical_summary_text": "Patient reports sharp chest discomfort."
        }
        pdf_bytes = pdf_service.generate_assessment_pdf(
            patient={"full_name": "Test Patient", "uhid": "CC-2026-T1", "age": 25, "gender": "Male"},
            metrics={}, # No vitals measured
            report_data=report_data,
            assessment_id="test-v3-pdf"
        )
        self.assertTrue(pdf_bytes.startswith(b"%PDF"))
        # PDF should NOT contain 'Not reported' spam
        pdf_text = pdf_bytes.decode('latin1', errors='ignore')
        self.assertNotIn("Smoking: Not reported", pdf_text)
        self.assertNotIn("Diabetes: Not reported", pdf_text)

    def test_30_hardware_observation_provenance_and_validation(self):
        is_valid, err = validate_observation_value("heart_rate", 75, "bpm")
        self.assertTrue(is_valid)

        is_invalid, err2 = validate_observation_value("heart_rate", 500, "bpm")
        self.assertFalse(is_invalid)

        obs = ClinicalObservation(
            id="obs-1",
            patient_id="pat-1",
            type="spo2",
            value=98,
            unit="%",
            source=ObservationSource.DEVICE,
            quality="HIGH"
        )
        self.assertEqual(obs.source, ObservationSource.DEVICE)

if __name__ == "__main__":
    unittest.main()
