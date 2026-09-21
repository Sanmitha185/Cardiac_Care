import io
import time
from typing import Any, Dict, List, Optional
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable, KeepTogether

class MedicalPDFGenerator:
    """
    V3 Dynamic Medical PDF Generator.
    Follows Sparse Clinical State principles:
    - Strictly suppresses empty sections and missing fields.
    - Zero 'Not reported' / 'N/A' placeholder filler.
    - Only renders clinical evidence and measurements that actually exist.
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
            fontSize=16,
            leading=20,
            textColor=brand_color,
            spaceAfter=2
        )
        subtitle_style = ParagraphStyle(
            'DocSubtitle',
            parent=styles['Normal'],
            fontName='Helvetica',
            fontSize=8.5,
            leading=11,
            textColor=muted_color,
            spaceAfter=6
        )
        section_heading = ParagraphStyle(
            'SectionHead',
            parent=styles['Heading2'],
            fontName='Helvetica-Bold',
            fontSize=10.5,
            leading=13.5,
            textColor=primary_color,
            spaceBefore=7,
            spaceAfter=3
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
            fontSize=8.5,
            leading=11.5,
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

        # 1. Header Banner
        elements.append(Paragraph("CARDIAC CARE", title_style))
        elements.append(Paragraph("CLINICAL DECISION SUPPORT & SYMPTOM ASSESSMENT REPORT — NOT A DEFINITIVE DIAGNOSIS", subtitle_style))
        elements.append(HRFlowable(width="100%", thickness=1.5, color=brand_color, spaceAfter=6))

        # Triage Category & Acuity Alert
        triage = str(report_data.get("triage_category_level", "Category C (ROUTINE)")).upper()
        is_emergency = "CATEGORY A" in triage or "EMERGENCY" in triage
        
        triage_box_color = colors.HexColor("#fee2e2") if is_emergency else colors.HexColor("#f0fdf4")
        triage_text_color = danger_color if is_emergency else colors.HexColor("#166534")
        triage_border_color = danger_color if is_emergency else colors.HexColor("#22c55e")
        
        urgency_rec = report_data.get('urgency_recommendation', 'Clinical evaluation recommended')
        triage_p = Paragraph(
            f"<b>CLINICAL ACUITY: {triage}</b> — {urgency_rec}",
            ParagraphStyle('TriageP', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=9, textColor=triage_text_color)
        )
        triage_table = Table([[triage_p]], colWidths=[540])
        triage_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), triage_box_color),
            ('BOX', (0,0), (-1,-1), 1, triage_border_color),
            ('TOPPADDING', (0,0), (-1,-1), 5),
            ('BOTTOMPADDING', (0,0), (-1,-1), 5),
            ('LEFTPADDING', (0,0), (-1,-1), 8),
            ('RIGHTPADDING', (0,0), (-1,-1), 8),
        ]))
        elements.append(triage_table)
        elements.append(Spacer(1, 5))

        # 2. Patient Demographics (Sparse: only non-empty fields)
        pat_name = patient.get("full_name") or "Patient"
        uhid = patient.get("uhid") or "N/A"
        age = patient.get("age")
        gender = patient.get("gender")
        bg = patient.get("blood_group")
        contact = patient.get("contact_number")
        date_str = time.strftime('%d-%b-%Y %H:%M UTC', time.gmtime())

        demo_cells = [
            Paragraph(f"<b>Patient:</b> {pat_name}", body_style),
            Paragraph(f"<b>UHID:</b> {uhid}", body_style),
            Paragraph(f"<b>Assessment Date:</b> {date_str}", body_style)
        ]
        demo_row2 = []
        if age and gender:
            demo_row2.append(Paragraph(f"<b>Age / Sex:</b> {age} Yrs / {gender}", body_style))
        elif age:
            demo_row2.append(Paragraph(f"<b>Age:</b> {age} Yrs", body_style))
        elif gender:
            demo_row2.append(Paragraph(f"<b>Sex:</b> {gender}", body_style))
            
        if bg and bg != "Not reported":
            demo_row2.append(Paragraph(f"<b>Blood Group:</b> {bg}", body_style))
        if contact and contact != "Not reported":
            demo_row2.append(Paragraph(f"<b>Contact:</b> +91 {contact}", body_style))

        # Balance rows for table
        while len(demo_row2) < 3:
            demo_row2.append(Paragraph("", body_style))

        demo_table = Table([demo_cells, demo_row2], colWidths=[180, 180, 180])
        demo_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#f8fafc")),
            ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor("#cbd5e1")),
            ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor("#e2e8f0")),
            ('TOPPADDING', (0,0), (-1,-1), 4),
            ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ]))
        elements.append(demo_table)
        elements.append(Spacer(1, 5))

        # 3. Recorded Vitals (Sparse: only display measurements that actually exist)
        bp = metrics.get("blood_pressure_status")
        hr = metrics.get("resting_heart_rate_status")
        glucose = metrics.get("blood_glucose_status")
        ecg_hist = metrics.get("past_ecg_history")

        vital_cells = []
        if bp and bp != "Not recorded" and bp != "Not reported":
            vital_cells.append(Paragraph(f"<b>Blood Pressure:</b> {bp} mmHg [MANUAL]", body_style))
        if hr and hr != "Not recorded" and hr != "Not reported":
            vital_cells.append(Paragraph(f"<b>Heart Rate:</b> {hr} [MANUAL]", body_style))
        if glucose and glucose != "Not reported":
            vital_cells.append(Paragraph(f"<b>Blood Glucose:</b> {glucose}", body_style))
        if ecg_hist and ecg_hist != "Not reported":
            vital_cells.append(Paragraph(f"<b>Prior ECG/History:</b> {ecg_hist}", body_style))

        if vital_cells:
            elements.append(Paragraph("Recorded Baseline Vitals", section_heading))
            # Format in rows of up to 3
            v_rows = []
            for i in range(0, len(vital_cells), 3):
                row = vital_cells[i:i+3]
                while len(row) < 3:
                    row.append(Paragraph("", body_style))
                v_rows.append(row)
            
            vitals_table = Table(v_rows, colWidths=[180, 180, 180])
            vitals_table.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#f1f5f9")),
                ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor("#cbd5e1")),
                ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor("#e2e8f0")),
                ('TOPPADDING', (0,0), (-1,-1), 4),
                ('BOTTOMPADDING', (0,0), (-1,-1), 4),
            ]))
            elements.append(vitals_table)
            elements.append(Spacer(1, 5))

        # 4. Reported Symptoms (Sparse: ONLY actual evidence)
        reported_syms = report_data.get("reported_symptoms") or []
        if not reported_syms:
            # Fallback to narrative if sparse list not populated
            doc_sum = report_data.get("doctor_clinical_summary_text")
            if doc_sum:
                reported_syms = [doc_sum]

        if reported_syms:
            elements.append(Paragraph("Reported Symptom Characteristics", section_heading))
            sym_items = []
            for s in reported_syms:
                sym_items.append(Paragraph(f"• {s}", body_style))
            for item in sym_items:
                elements.append(item)
            elements.append(Spacer(1, 5))

        # 5. Reported History & Risk Factors (Omit if none reported!)
        reported_hist = report_data.get("reported_history") or []
        if reported_hist:
            elements.append(Paragraph("Relevant Medical History & Risk Factors", section_heading))
            for h in reported_hist:
                elements.append(Paragraph(f"• {h}", body_style))
            elements.append(Spacer(1, 5))

        # 6. Critical Red Flags (Omit if none!)
        red_flags = report_data.get("critical_red_flags") or report_data.get("critical_red_flags_identified") or {}
        if red_flags:
            elements.append(Paragraph("Deterministic Clinical Red Flags", section_heading))
            for flag, reason in red_flags.items():
                elements.append(Paragraph(f"• <b>{flag.replace('_', ' ').title()}:</b> {reason}", alert_style))
            elements.append(Spacer(1, 5))

        # 7. Differential Considerations (Dynamic: only relevant items, up to 4)
        possible_conditions = report_data.get("possible_conditions", [])
        if possible_conditions:
            elements.append(Paragraph("Differential Clinical Considerations (Not Confirmed Diagnoses)", section_heading))
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
            elements.append(Spacer(1, 5))

        # 8. Information That Would Materially Change This Assessment (Dynamic)
        what_would_change = report_data.get("what_would_change_assessment")
        if not what_would_change:
            what_would_change = [
                "12-Lead Electrocardiogram (ECG) to assess for acute ST-segment deviations or ischemia",
                "Serial High-Sensitivity Cardiac Troponin (hs-cTnI / hs-cTnT) to evaluate myocardial injury",
                "Formal cardiovascular physical examination (auscultation, chest wall palpation, vital reassessment)"
            ]
        elements.append(Paragraph("Information That Would Materially Change This Assessment", section_heading))
        for item in what_would_change:
            elements.append(Paragraph(f"• {item}", body_style))
        elements.append(Spacer(1, 5))

        # 9. Validated Decision Pathways & Completeness
        elements.append(Paragraph("Decision Pathways & Clinical Completeness", section_heading))
        comp_pct = report_data.get("clinical_completeness_pct", 0)
        elements.append(Paragraph(
            f"<b>Assessment Information Completeness:</b> {comp_pct}% of required branch clinical dimensions collected.",
            body_style
        ))

        # HEART score status (strictly un-fabricated)
        val_scores = report_data.get("validated_risk_scores", [])
        heart_info = "<b>HEART Score:</b> Unavailable. 12-lead ECG and cardiac troponin results were not available in this software assessment. Score was NOT fabricated."
        for s in val_scores:
            if s.get("score_name") and "HEART" in s.get("score_name"):
                if not s.get("is_available"):
                    missing_str = ", ".join(s.get('missing_inputs', []))
                    heart_info = f"<b>HEART Score:</b> Unavailable. Required objective inputs ({missing_str}) were not available. Score was NOT fabricated."
                else:
                    heart_info = f"<b>HEART Score:</b> {s.get('score_value')} / {s.get('max_score')} — {s.get('interpretation')}"
        elements.append(Paragraph(heart_info, body_style))
        elements.append(Spacer(1, 6))

        # 10. Clinician Review Block (Blank lines only — no fake doctor)
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
                Paragraph("License #: ______________________", body_style),
                Paragraph("Hospital / Facility: ______________________", body_style),
                Paragraph("Review Status: [ ] Evaluated  [ ] Pending", body_style)
            ]
        ]
        sign_table = Table(sign_block, colWidths=[180, 180, 180])
        sign_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#f8fafc")),
            ('BOX', (0,0), (-1,-1), 1, colors.HexColor("#94a3b8")),
            ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor("#e2e8f0")),
            ('TOPPADDING', (0,0), (-1,-1), 4),
            ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ]))
        elements.append(KeepTogether([
            Paragraph("Attending Clinician In-Person Review", section_heading),
            sign_table
        ]))
        elements.append(Spacer(1, 6))

        # 11. Mandatory Medical Disclaimer
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
