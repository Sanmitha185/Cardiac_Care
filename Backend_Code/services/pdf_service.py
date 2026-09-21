import os
import io
import time
from typing import Any, Dict, Optional
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable, KeepTogether

class MedicalPDFGenerator:
    """
    Generates professional hospital-grade clinical decision-support PDFs
    incorporating structured clinical state, provenance, differential considerations,
    missing information, and physician review block.
    """

    @staticmethod
    def generate_assessment_pdf(
        patient: Dict[str, Any],
        metrics: Dict[str, Any],
        report_data: Dict[str, Any],
        assessment_id: str
    ) -> bytes:
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=letter,
            rightMargin=36,
            leftMargin=36,
            topMargin=36,
            bottomMargin=36
        )

        styles = getSampleStyleSheet()
        primary_color = colors.HexColor("#0f172a") # Slate 900
        brand_color = colors.HexColor("#0369a1")   # Sky 700
        danger_color = colors.HexColor("#b91c1c")  # Red 700
        muted_color = colors.HexColor("#475569")   # Slate 600

        title_style = ParagraphStyle(
            'DocTitle',
            parent=styles['Heading1'],
            fontName='Helvetica-Bold',
            fontSize=18,
            leading=22,
            textColor=brand_color,
            spaceAfter=2
        )
        subtitle_style = ParagraphStyle(
            'DocSubtitle',
            parent=styles['Normal'],
            fontName='Helvetica',
            fontSize=9,
            leading=12,
            textColor=muted_color,
            spaceAfter=8
        )
        section_heading = ParagraphStyle(
            'SectionHead',
            parent=styles['Heading2'],
            fontName='Helvetica-Bold',
            fontSize=11,
            leading=14,
            textColor=primary_color,
            spaceBefore=8,
            spaceAfter=4
        )
        body_style = ParagraphStyle(
            'Body',
            parent=styles['Normal'],
            fontName='Helvetica',
            fontSize=8.5,
            leading=11.5,
            textColor=colors.HexColor("#1e293b")
        )
        alert_style = ParagraphStyle(
            'AlertText',
            parent=styles['Normal'],
            fontName='Helvetica-Bold',
            fontSize=9,
            leading=12,
            textColor=danger_color
        )
        disclaimer_style = ParagraphStyle(
            'Disclaimer',
            parent=styles['Normal'],
            fontName='Helvetica-Oblique',
            fontSize=7.5,
            leading=10,
            textColor=muted_color
        )

        elements = []

        # 1. Header & Organization Banner
        elements.append(Paragraph("CARDIAC CARE V2", title_style))
        elements.append(Paragraph("CLINICAL DECISION SUPPORT & SYMPTOM ASSESSMENT REPORT — NOT A DEFINITIVE DIAGNOSIS", subtitle_style))
        elements.append(HRFlowable(width="100%", thickness=1.5, color=brand_color, spaceAfter=8))

        # Triage Category & Acuity Alert
        triage = str(report_data.get("triage_category_level", "Category C (ROUTINE)")).upper()
        is_emergency = "CATEGORY A" in triage or "EMERGENCY" in triage
        
        triage_box_color = colors.HexColor("#fee2e2") if is_emergency else colors.HexColor("#f0fdf4")
        triage_text_color = danger_color if is_emergency else colors.HexColor("#166534")
        triage_border_color = danger_color if is_emergency else colors.HexColor("#22c55e")
        
        triage_p = Paragraph(
            f"<b>CLINICAL ACUITY: {triage}</b> — {report_data.get('urgency_recommendation', 'Evaluation recommended')}",
            ParagraphStyle('TriageP', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=9.5, textColor=triage_text_color)
        )
        triage_table = Table([[triage_p]], colWidths=[540])
        triage_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), triage_box_color),
            ('BOX', (0,0), (-1,-1), 1, triage_border_color),
            ('TOPPADDING', (0,0), (-1,-1), 6),
            ('BOTTOMPADDING', (0,0), (-1,-1), 6),
            ('LEFTPADDING', (0,0), (-1,-1), 8),
            ('RIGHTPADDING', (0,0), (-1,-1), 8),
        ]))
        elements.append(triage_table)
        elements.append(Spacer(1, 6))

        # 2. Patient Demographics & Assessment Metadata Table
        pat_name = patient.get("full_name", "Not specified")
        uhid = patient.get("uhid", "N/A")
        age = str(patient.get("age", "N/A"))
        gender = patient.get("gender", "N/A")
        bg = patient.get("blood_group", "Not reported")
        date_str = time.strftime('%d-%b-%Y %H:%M:%S UTC', time.gmtime())

        demo_data = [
            [
                Paragraph(f"<b>Patient Name:</b> {pat_name}", body_style),
                Paragraph(f"<b>UHID:</b> {uhid}", body_style),
                Paragraph(f"<b>Age / Sex:</b> {age} / {gender}", body_style)
            ],
            [
                Paragraph(f"<b>Blood Group:</b> {bg}", body_style),
                Paragraph(f"<b>Assessment ID:</b> {assessment_id[:16]}...", body_style),
                Paragraph(f"<b>Date / Time:</b> {date_str}", body_style)
            ]
        ]
        demo_table = Table(demo_data, colWidths=[180, 180, 180])
        demo_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#f8fafc")),
            ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor("#cbd5e1")),
            ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor("#e2e8f0")),
            ('TOPPADDING', (0,0), (-1,-1), 4),
            ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ]))
        elements.append(demo_table)
        elements.append(Spacer(1, 6))

        # 3. Recorded Vitals & Baseline Physical Measurements
        elements.append(Paragraph("Recorded Baseline Vitals & Physiological Parameters", section_heading))
        bp = metrics.get("blood_pressure_status", "Not recorded")
        hr = metrics.get("resting_heart_rate_status", "Not recorded")
        glucose = metrics.get("blood_glucose_status", "Not reported")
        ecg_hist = metrics.get("past_ecg_history", "Not reported")

        vitals_data = [
            [
                Paragraph(f"<b>Blood Pressure:</b> {bp} (MANUAL)", body_style),
                Paragraph(f"<b>Heart Rate:</b> {hr} (MANUAL)", body_style),
                Paragraph(f"<b>Blood Glucose:</b> {glucose} (MANUAL)", body_style),
                Paragraph(f"<b>Known Cardiac History:</b> {ecg_hist}", body_style)
            ]
        ]
        vitals_table = Table(vitals_data, colWidths=[135, 135, 135, 135])
        vitals_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#f1f5f9")),
            ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor("#cbd5e1")),
            ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor("#e2e8f0")),
            ('TOPPADDING', (0,0), (-1,-1), 4),
            ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ]))
        elements.append(vitals_table)
        elements.append(Spacer(1, 6))

        # 4. Reported Symptoms & Characteristics
        elements.append(Paragraph("Symptom Presentation & Clinical Inquiry Findings", section_heading))
        lead_concern = report_data.get("leading_concern", {})
        why_c = lead_concern.get("why_considered", "Clinical evaluation conducted.")
        doctor_summary = report_data.get("doctor_clinical_summary_text", why_c)
        elements.append(Paragraph(doctor_summary, body_style))
        elements.append(Spacer(1, 6))

        # 5. Differential Considerations (Max 4, strictly 'Not confirmed')
        elements.append(Paragraph("Differential Considerations (AI-Assisted — Not Confirmed)", section_heading))
        possible_conditions = report_data.get("possible_conditions", [])
        
        diff_rows = [
            [
                Paragraph("<b>Consideration</b>", body_style),
                Paragraph("<b>Category</b>", body_style),
                Paragraph("<b>Supporting Evidence</b>", body_style),
                Paragraph("<b>Missing / Unconfirmed</b>", body_style),
                Paragraph("<b>Status</b>", body_style)
            ]
        ]
        for cond in possible_conditions[:4]:
            diff_rows.append([
                Paragraph(str(cond.get("condition", "N/A")), body_style),
                Paragraph(str(cond.get("category", "CARDIAC")), body_style),
                Paragraph("; ".join(cond.get("supporting_findings", ["Symptoms reported"])), body_style),
                Paragraph("; ".join(cond.get("missing_information", ["12-lead ECG", "Troponin"])), body_style),
                Paragraph("<b>Not confirmed</b>", alert_style if is_emergency else body_style)
            ])
        
        diff_table = Table(diff_rows, colWidths=[110, 65, 155, 130, 80])
        diff_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#e2e8f0")),
            ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor("#94a3b8")),
            ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor("#cbd5e1")),
            ('TOPPADDING', (0,0), (-1,-1), 3),
            ('BOTTOMPADDING', (0,0), (-1,-1), 3),
        ]))
        elements.append(diff_table)
        elements.append(Spacer(1, 6))

        # 6. Validated Scores & Completeness
        elements.append(Paragraph("Clinical Information Completeness & Validated Scoring", section_heading))
        comp_pct = report_data.get("clinical_completeness_pct", 0)
        completeness_msg = f"<b>Clinical Information Completeness:</b> {comp_pct}% of required primary assessment fields collected."
        elements.append(Paragraph(completeness_msg, body_style))

        # HEART score status
        val_scores = report_data.get("validated_risk_scores", [])
        heart_info = "<b>HEART Score:</b> Unavailable. Reason: 12-lead ECG and cardiac troponin lab results are not available in this software assessment. Score was NOT fabricated."
        for s in val_scores:
            if s.get("score_name") == "HEART":
                if not s.get("is_available"):
                    heart_info = f"<b>HEART Score:</b> Unavailable (v{s.get('version')}). Reason: {', '.join(s.get('missing_inputs', []))} not available. Score not fabricated."
                else:
                    heart_info = f"<b>HEART Score:</b> {s.get('score_value')} / {s.get('max_score')} — {s.get('interpretation')} (Source: {s.get('source_citation')})"
        elements.append(Paragraph(heart_info, body_style))
        elements.append(Spacer(1, 6))

        # 7. What Would Materially Change Assessment
        elements.append(Paragraph("Information that Could Materially Change this Assessment", section_heading))
        change_items = [
            "1. 12-Lead Electrocardiogram (ECG) to rule out ST-segment elevation (STEMI) or acute ischemia.",
            "2. Serial high-sensitivity cardiac troponin (hs-cTnI / hs-cTnT) testing to evaluate myocardial necrosis.",
            "3. Formal in-person physical cardiovascular examination including auscultation and chest wall palpation.",
            "4. Dynamic continuous rhythm monitoring and continuous SpO2/blood pressure reassessment."
        ]
        for item in change_items:
            elements.append(Paragraph(item, body_style))
        elements.append(Spacer(1, 8))

        # 8. Physician / Clinician Review Block (Blank lines only — no fake doctor)
        sign_block = [
            [
                Paragraph("<b>Clinician In-Person Review:</b>", body_style),
                Paragraph("<b>Attending Physician Signature:</b>", body_style),
                Paragraph("<b>Date & Time:</b>", body_style)
            ],
            [
                Paragraph("Name: ____________________________________", body_style),
                Paragraph("Signature: _______________________________", body_style),
                Paragraph("Date: ______ / ______ / 202___", body_style)
            ],
            [
                Paragraph("Medical License #: ______________________", body_style),
                Paragraph("Hospital / Facility: ______________________", body_style),
                Paragraph("Time: ______ : ______ (24h)", body_style)
            ]
        ]
        sign_table = Table(sign_block, colWidths=[180, 180, 180])
        sign_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#f8fafc")),
            ('BOX', (0,0), (-1,-1), 1, colors.HexColor("#94a3b8")),
            ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor("#e2e8f0")),
            ('TOPPADDING', (0,0), (-1,-1), 5),
            ('BOTTOMPADDING', (0,0), (-1,-1), 5),
        ]))
        elements.append(KeepTogether([
            Paragraph("Clinician In-Person Review Block", section_heading),
            sign_table
        ]))
        elements.append(Spacer(1, 6))

        # 9. Medical & Legal Disclaimer
        disclaimer_text = (
            "<b>MANDATORY MEDICAL ADVISORY:</b> This document is generated as AI-assisted clinical decision support "
            "based exclusively on patient-reported answers and manually entered vitals. It does NOT establish a definitive diagnosis "
            "and does NOT replace evaluation by a qualified healthcare professional. If this patient presents with emergency "
            "cardiac symptoms, initiate immediate emergency transfer (112 in India) without delay."
        )
        elements.append(Paragraph(disclaimer_text, disclaimer_style))

        doc.build(elements)
        pdf_bytes = buffer.getvalue()
        buffer.close()
        return pdf_bytes

pdf_service = MedicalPDFGenerator()
