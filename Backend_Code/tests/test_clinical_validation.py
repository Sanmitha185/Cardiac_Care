import os
import sys
import unittest

# Ensure parent directory is in sys.path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from services.clinical_engine import clinical_engine, ClinicalState
from services.safety_engine import safety_engine
from services.scoring_service import scoring_service
from services.hardware_service import hardware_service, ObservationSource, validate_observation_value

class TestCardiacCareClinicalValidation(unittest.TestCase):

    def test_01_normal_low_risk_case(self):
        """Phase 25: Normal/low-risk case with non-cardiac, non-radiating mild discomfort."""
        state = ClinicalState()
        state = clinical_engine.extract_clinical_facts("I had a mild ache in my chest after lifting a heavy box yesterday, rated 2 out of 10.", state)
        state = clinical_engine.extract_clinical_facts("It only lasted a few minutes and is completely gone now. No radiation.", state)
        
        evaluation = safety_engine.evaluate(state.model_dump())
        self.assertFalse(evaluation.is_emergency, "Normal/low-risk case should NOT trigger emergency escalation.")
        self.assertEqual(evaluation.triage_category, "Category C (ROUTINE)")

    def test_02_critical_chest_pain_with_jaw_radiation(self):
        """Phase 24: Critical case with chest pain and jaw radiation triggers emergency immediately."""
        state = ClinicalState()
        state = clinical_engine.extract_clinical_facts("I am having chest pain.", state)
        state = clinical_engine.extract_clinical_facts("It is sharp and rated 5 out of 10.", state)
        state = clinical_engine.extract_clinical_facts("The pain radiates to my jaw.", state)
        
        evaluation = safety_engine.evaluate(state.model_dump())
        self.assertTrue(evaluation.is_emergency, "Chest pain radiating to jaw MUST trigger emergency guidance.")
        self.assertEqual(evaluation.triage_category, "Category A (EMERGENCY)")
        self.assertIn("112", evaluation.emergency_number)
        self.assertIn("Possible Acute Coronary Syndrome (ACS)", evaluation.primary_concern)

    def test_03_no_fabrication_relaxing_vs_exertion(self):
        """Phase 24: 'relaxing makes it better' must NOT auto-convert to 'worse with exertion = true'."""
        state = ClinicalState()
        state = clinical_engine.extract_clinical_facts("I have chest discomfort. Relaxing makes it better.", state)
        
        self.assertTrue(state.better_with_rest, "better_with_rest should be true.")
        self.assertIsNone(state.worse_with_exertion, "worse_with_exertion MUST NOT be inferred from 'relaxing makes it better'.")

    def test_04_no_fabricated_history_or_smoking(self):
        """Phase 26 & 27: Patient saying 'nothing like that' should not invent smoking or diabetes."""
        state = ClinicalState()
        state = clinical_engine.extract_clinical_facts("I have no medical history, nothing like that.", state)
        
        self.assertEqual(state.cardiac_history, "No reported history")
        self.assertNotIn("smoking", state.risk_factors, "Smoking must NOT be inferred if not reported.")
        self.assertNotIn("diabetes", state.risk_factors, "Diabetes must NOT be inferred if not reported.")

    def test_05_no_duplicate_questions(self):
        """Phase 3: Verify semantic duplicate question suppression."""
        state = ClinicalState()
        # Patient explicitly gives severity and radiation in opening statement
        state = clinical_engine.extract_clinical_facts("My chest hurts, it shoots to my jaw, and severity is 8 out of 10.", state)
        
        # The next question should NOT ask for severity or radiation!
        next_q = clinical_engine.select_next_question(state)
        self.assertIsNotNone(next_q)
        q_key, prompt = next_q
        self.assertNotIn(q_key, ["severity", "radiation"], f"Should not ask for already provided fact '{q_key}'.")

    def test_06_pain_quality_vs_severity_separation(self):
        """Phase 3: Pain quality and numerical severity must remain independent."""
        state = ClinicalState()
        state = clinical_engine.extract_clinical_facts("It feels like heaviness and crushing pressure, severity is 7/10.", state)
        
        self.assertIn(state.pain_quality, ["pressure", "crushing"])
        self.assertEqual(state.pain_severity, 7)

    def test_07_palpitations_branching(self):
        """Phase 3: Palpitations activate rhythm branch."""
        state = ClinicalState()
        state = clinical_engine.extract_clinical_facts("My heart is racing and I feel sudden fluttering palpitations.", state)
        
        self.assertEqual(state.current_branch, "PALPITATIONS")
        self.assertTrue(state.associated_symptoms.get("palpitations"))

    def test_08_syncope_emergency_with_chest_pain(self):
        """Phase 5: Syncope + chest pain is a critical emergency red flag."""
        state = ClinicalState()
        state = clinical_engine.extract_clinical_facts("I had chest pain and then I fainted and blacked out for a few seconds.", state)
        
        evaluation = safety_engine.evaluate(state.model_dump())
        self.assertTrue(evaluation.is_emergency)
        self.assertIn("cardiogenic_syncope", evaluation.red_flags)

    def test_09_validated_score_unavailable_when_missing_inputs(self):
        """Phase 7: HEART score must NOT be fabricated when ECG and troponin are unavailable."""
        state = ClinicalState()
        state = clinical_engine.extract_clinical_facts("Chest pain for 2 hours.", state)
        
        score_result = scoring_service.evaluate_heart_score(
            clinical_state=state.model_dump(),
            patient_age=55,
            has_ecg=False,
            has_troponin=False
        )
        self.assertFalse(score_result.is_available, "HEART score must NOT be marked available without ECG and troponin.")
        self.assertIsNone(score_result.score_value)
        self.assertIn("12-Lead Electrocardiogram (ECG)", score_result.missing_inputs)
        self.assertTrue(any("Troponin" in item for item in score_result.missing_inputs))

    def test_10_deterministic_completeness_calculation(self):
        """V3: Completeness calculation must be dynamic by active branch and deterministic."""
        state = ClinicalState()
        state.chest_pain = True
        state.pain_severity = 6
        state.pain_quality = "pressure"
        state.pain_radiation = ["left arm"]
        state.onset = "1 hour ago"
        state.worse_with_exertion = True
        
        result = scoring_service.calculate_completeness(state.model_dump())
        self.assertEqual(result.branch, "CHEST_PAIN")
        self.assertEqual(result.total_required_fields, 5)
        self.assertEqual(result.collected_fields_count, 5)
        self.assertEqual(result.completeness_percentage, 100.0)

    def test_11_differential_conditions_limit_and_status(self):
        """Phase 6: Differential must not exceed 4 conditions and all must state 'Not confirmed'."""
        state = ClinicalState()
        state = clinical_engine.extract_clinical_facts("Chest tightness radiating to left arm with sweating.", state)
        eval_res = safety_engine.evaluate(state.model_dump())
        report = clinical_engine.generate_clinical_synthesis(
            state=state,
            patient_info={"full_name": "Test Patient", "age": 60, "gender": "Male"},
            metrics={"blood_pressure_status": "130/85", "resting_heart_rate_status": "78 bpm"},
            safety=eval_res
        )
        self.assertLessEqual(len(report.possible_conditions), 4)
        for cond in report.possible_conditions:
            self.assertEqual(cond.status, "Not confirmed")
            self.assertGreater(len(cond.missing_information), 0)

    def test_12_hardware_observation_physiologic_limits(self):
        """Phase 4 & 36: Physiologic bounds check for hardware observations."""
        valid_hr, _ = validate_observation_value("heart_rate", 72, "bpm")
        self.assertTrue(valid_hr)
        
        invalid_hr, err = validate_observation_value("heart_rate", 450, "bpm")
        self.assertFalse(invalid_hr)
        self.assertIn("out of physiological bounds", err)

        valid_spo2, _ = validate_observation_value("spo2", 98, "%")
        self.assertTrue(valid_spo2)

        invalid_spo2, _ = validate_observation_value("spo2", 120, "%")
        self.assertFalse(invalid_spo2)

    def test_13_diagnostics_masking_key_never_exposed(self):
        """Section 63: Admin diagnostics must NEVER expose complete API key or secrets."""
        from services.nvidia_service import nvidia_service
        diag = nvidia_service.get_diagnostics()
        self.assertIn("masked_key", diag)
        self.assertNotIn("api_key", diag)
        self.assertTrue(diag["masked_key"].startswith("********"))
        # Ensure full raw key is not anywhere in values
        for k, v in diag.items():
            if isinstance(v, str):
                self.assertFalse(v.startswith("nvapi-"), f"Exposed key found in field {k}")

    def test_14_ambiguous_symptom_requires_clarification(self):
        """Section 78: Ambiguous answers ('sometimes it happens') must NOT be guessed as constant."""
        state = ClinicalState()
        state = clinical_engine.extract_clinical_facts("Sometimes it happens.", state)
        # Should not guess constant duration or onset
        self.assertIsNone(state.onset, "System must not guess onset from ambiguous 'sometimes it happens'.")
        self.assertIsNone(state.duration, "System must not guess duration from ambiguous 'sometimes it happens'.")

    def test_15_no_fabricated_confidence_or_risk_percentage(self):
        """Section 30 & 84: Clinical synthesis must NEVER output arbitrary AI probabilities like 95% or 85/100."""
        state = ClinicalState()
        state.chest_pain = True
        state.pain_severity = 5
        state.pain_quality = "sharp"
        state.pain_radiation = ["jaw"]
        eval_res = safety_engine.evaluate(state.model_dump())
        
        report = clinical_engine.generate_clinical_synthesis(
            state=state,
            patient_info={"full_name": "Test Patient", "age": 21, "gender": "Male"},
            metrics={"blood_pressure_status": "120/80", "resting_heart_rate_status": "72 bpm"},
            safety=eval_res
        )
        report_dict = report.model_dump()
        report_str = str(report_dict)
        
        self.assertNotIn("95%", report_str)
        self.assertNotIn("85/100", report_str)
        self.assertNotIn("91.7%", report_str)
        self.assertNotIn("90.5%", report_str)

    def test_16_emergency_link_tel_112(self):
        """Section 26 & 101: Emergency evaluation must recommend immediate evaluation and 112 emergency phone contact."""
        state = ClinicalState()
        state.chest_pain = True
        state.pain_radiation = ["jaw"]
        eval_res = safety_engine.evaluate(state.model_dump())
        
        self.assertTrue(eval_res.is_emergency)
        self.assertEqual(eval_res.emergency_number, "112")
        self.assertIn("112", str(eval_res.instructions))
        self.assertTrue(any("Do not" in inst for inst in eval_res.instructions))

    def test_17_provenance_manual_device_lab_separation(self):
        """Section 55: Distinct provenance categories for patient reported, manual, and device facts."""
        from services.hardware_service import ClinicalObservation, ObservationSource
        obs = ClinicalObservation(
            id="obs-1",
            patient_id="pat-1",
            type="heart_rate",
            value=72,
            unit="bpm",
            source=ObservationSource.DEVICE,
            quality="GOOD"
        )
    def test_18_pdf_generation_valid_bytes_and_blank_signature(self):
        """Section 52, 53 & 54: PDF must be valid binary PDF with blank physician review block."""
        from services.pdf_service import pdf_service
        patient = {"full_name": "Rohan Sharma", "uhid": "CC-2026-9912", "age": 42, "gender": "Male", "blood_group": "B+"}
        metrics = {"blood_pressure_status": "125/82", "resting_heart_rate_status": "74 bpm"}
        report_data = {
            "triage_category_level": "Category C (ROUTINE)",
            "urgency_recommendation": "Non-urgent outpatient evaluation",
            "clinical_completeness_pct": 85.0,
            "possible_conditions": [
                {
                    "condition": "Possible Musculoskeletal Discomfort",
                    "category": "MUSCULOSKELETAL",
                    "supporting_findings": ["Focal chest wall ache after physical lifting"],
                    "missing_information": ["12-lead ECG", "Troponin"],
                    "status": "Not confirmed"
                }
            ],
            "doctor_clinical_summary_text": "Patient reports transient focal chest discomfort without radiating symptoms."
        }
        pdf_bytes = pdf_service.generate_assessment_pdf(
            patient=patient,
            metrics=metrics,
            report_data=report_data,
            assessment_id="test-assessment-uuid-1234"
        )
        self.assertIsInstance(pdf_bytes, bytes)
        self.assertTrue(pdf_bytes.startswith(b"%PDF"), "Generated file must be a valid PDF binary starting with %PDF")
        self.assertGreater(len(pdf_bytes), 1000)

    def test_19_exact_critical_case_section_76_and_116(self):
        """
        Section 76 & 116 Exact Flow Verification:
        Patient: 21-year-old
        Symptoms: "I am having chest pain" -> "sharp" -> "5" -> "yes till jaw it goes"
        Relief: "relaxing makes it better"
        History: "nothing like that" -> "no"
        """
        from services.pdf_service import pdf_service
        state = ClinicalState()
        
        # Step 1: Initial complaint
        state = clinical_engine.extract_clinical_facts("I am having chest pain", state)
        self.assertTrue(state.chest_pain)
        
        # Step 2: Quality
        state = clinical_engine.extract_clinical_facts("sharp", state)
        self.assertEqual(state.pain_quality, "sharp")
        
        # Step 3: Severity
        state = clinical_engine.extract_clinical_facts("5", state)
        self.assertEqual(state.pain_severity, 5)
        
        # Step 4: Radiation
        state = clinical_engine.extract_clinical_facts("yes till jaw it goes", state)
        self.assertIn("jaw", state.pain_radiation)
        
        # Step 5: Relief - relaxing makes it better
        state = clinical_engine.extract_clinical_facts("relaxing makes it better", state)
        self.assertTrue(state.better_with_rest)
        # MUST NOT infer worse_with_exertion
        self.assertIsNone(state.worse_with_exertion, "MUST NOT infer exertional worsening from relaxing makes it better")
        
        # Step 6: Medical history - nothing like that
        state = clinical_engine.extract_clinical_facts("nothing like that", state)
        self.assertEqual(state.cardiac_history, "No reported history")
        self.assertNotIn("smoking", state.risk_factors)
        self.assertNotIn("diabetes", state.risk_factors)
        
        # Step 7: Family history - no
        state = clinical_engine.extract_clinical_facts("no", state)
        self.assertEqual(state.family_history, "No reported history")

        # Step 8: Safety Engine Evaluation
        safety_eval = safety_engine.evaluate(state.model_dump())
        self.assertTrue(safety_eval.is_emergency, "Jaw radiation with chest pain must trigger emergency")
        self.assertEqual(safety_eval.emergency_number, "112")
        self.assertIn("112", str(safety_eval.instructions))
        self.assertIn("Possible Acute Coronary Syndrome", safety_eval.primary_concern)

        # Step 9: Clinical Synthesis
        report = clinical_engine.generate_clinical_synthesis(
            state=state,
            patient_info={"full_name": "Young Adult Patient", "age": 21, "gender": "Other"},
            metrics={"blood_pressure_status": "118/76", "resting_heart_rate_status": "76 bpm"},
            safety=safety_eval
        )
        report_dict = report.model_dump()
        
        # Must say possible, NOT confirmed ACS
        self.assertIn("Possible Acute Coronary Syndrome", report.leading_concern["possible_condition"])
        self.assertEqual(report.leading_concern["status"], "Not confirmed")
        
        # Must identify missing ECG and troponin
        missing_overall = []
        for c in report.possible_conditions:
            missing_overall.extend(c.missing_information)
        self.assertTrue(any("ECG" in m for m in missing_overall))
        self.assertTrue(any("troponin" in m.lower() for m in missing_overall))

        # Generate PDF
        pdf_bytes = pdf_service.generate_assessment_pdf(
            patient={"full_name": "Young Adult Patient", "uhid": "CC-2026-CRIT", "age": 21, "gender": "Other"},
            metrics={"blood_pressure_status": "118/76", "resting_heart_rate_status": "76 bpm"},
            report_data=report_dict,
            assessment_id="crit-case-21yo"
        )
        self.assertTrue(pdf_bytes.startswith(b"%PDF"))
        self.assertGreater(len(pdf_bytes), 1500)

if __name__ == "__main__":
    unittest.main()
