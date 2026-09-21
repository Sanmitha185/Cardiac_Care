from typing import Any, Dict, List
from pydantic import BaseModel

class KnowledgeItem(BaseModel):
    topic: str
    title: str
    source: str
    citation: str
    year: int
    content: str
    diagnostic_prerequisites: List[str]

# Curated Authoritative Cardiology Knowledge Base (AHA / ACC / ESC Guidelines)
CARDIAC_KNOWLEDGE_BASE: List[KnowledgeItem] = [
    KnowledgeItem(
        topic="acute_coronary_syndrome",
        title="2021 AHA/ACC/ASE/CHEST/SAEM/SCCT/SCMR Guideline for the Evaluation and Diagnosis of Chest Pain",
        source="American Heart Association / American College of Cardiology",
        citation="Gulati M, et al. Circulation. 2021;144(22):e368-e454.",
        year=2021,
        content=(
            "Chest discomfort (pressure, tightness, heaviness) radiating to the left arm, both arms, "
            "or jaw is strongly associated with acute myocardial ischemia. A normal resting examination "
            "does not rule out ACS. Early 12-lead ECG within 10 minutes of presentation and serial high-sensitivity "
            "cardiac troponin are mandatory diagnostic standards. History alone cannot confirm or exclude myocardial infarction."
        ),
        diagnostic_prerequisites=["12-lead ECG within 10 minutes", "Serial High-Sensitivity Troponin", "Physician Examination"]
    ),
    KnowledgeItem(
        topic="stable_angina",
        title="2019 ESC Guidelines for the Diagnosis and Management of Chronic Coronary Syndromes",
        source="European Society of Cardiology",
        citation="Knuuti J, et al. Eur Heart J. 2020;41(3):407-477.",
        year=2019,
        content=(
            "Typical stable angina meets three criteria: (1) substernal chest discomfort of characteristic quality and duration; "
            "(2) provoked by exertion or emotional stress; (3) relieved by rest and/or nitroglycerin within minutes. "
            "Atypical angina meets 2 of these criteria. Non-anginal chest pain meets 0 or 1 criterion."
        ),
        diagnostic_prerequisites=["Resting ECG", "Non-invasive functional imaging or CCTA", "Lipid and glycemic panel"]
    ),
    KnowledgeItem(
        topic="pericarditis",
        title="2015 ESC Guidelines for the Diagnosis and Management of Pericardial Diseases",
        source="European Society of Cardiology",
        citation="Adler Y, et al. Eur Heart J. 2015;36(42):2921-2964.",
        year=2015,
        content=(
            "Acute pericarditis is diagnosed with at least 2 of 4 criteria: (1) sharp, pleuritic chest pain improved by sitting up "
            "and leaning forward; (2) pericardial friction rub; (3) new widespread ST-elevation or PR depression on ECG; "
            "(4) new or worsening pericardial effusion. Biomarkers of inflammation (CRP, ESR) are typically elevated."
        ),
        diagnostic_prerequisites=["12-lead ECG", "Echocardiography", "Inflammatory markers (CRP)"]
    ),
    KnowledgeItem(
        topic="arrhythmia_palpitations",
        title="2020 ESC Guidelines for the Diagnosis and Management of Atrial Fibrillation",
        source="European Society of Cardiology",
        citation="Hindricks G, et al. Eur Heart J. 2021;42(5):373-498.",
        year=2020,
        content=(
            "Palpitations accompanied by presyncope, syncope, or chest discomfort require prompt electrocardiographic "
            "rhythm documentation. Atrial fibrillation or ventricular tachyarrhythmias can compromise cardiac output. "
            "Documentation of an irregular rhythm episode lasting >= 30 seconds on ECG or Holter monitor is required for definitive diagnosis."
        ),
        diagnostic_prerequisites=["12-lead ECG or Holter Monitor", "Serum Electrolytes (K+, Mg++)", "Echocardiography"]
    ),
    KnowledgeItem(
        topic="pulmonary_embolism",
        title="2019 ESC Guidelines for the Diagnosis and Management of Acute Pulmonary Embolism",
        source="European Society of Cardiology",
        citation="Konstantinides SV, et al. Eur Heart J. 2020;41(4):543-603.",
        year=2019,
        content=(
            "Acute pulmonary embolism typically presents with acute-onset dyspnea, pleuritic chest pain, cough, or syncope. "
            "Risk factors include recent surgery, immobilization, prior DVT/PE, malignancy, or hypercoagulable states. "
            "Pre-test probability scoring (Wells / Geneva) guides D-dimer testing or CT pulmonary angiography."
        ),
        diagnostic_prerequisites=["Clinical Wells Score", "High-sensitivity D-Dimer or CT Pulmonary Angiography"]
    ),
    KnowledgeItem(
        topic="musculoskeletal_chest_wall",
        title="Clinical Practice Guidelines: Evaluation of Non-Cardiac Chest Pain",
        source="American Academy of Family Physicians",
        citation="Cayley WE Jr. Am Fam Physician. 2005;72(10):2012-2020.",
        year=2005,
        content=(
            "Musculoskeletal chest pain (such as costochondritis) is characterized by localized tenderness reproduced by "
            "direct palpation of the costochondral junctions or chest wall musculature. It is typically exacerbated by deep "
            "breathing or trunk movement and lacks ischemic radiation or autonomic symptoms."
        ),
        diagnostic_prerequisites=["Physical examination with chest wall palpation", "Exclusion of acute coronary syndrome"]
    ),
    KnowledgeItem(
        topic="gastrointestinal_chest_pain",
        title="Evaluation and Management of Non-Cardiac Chest Pain: ACG Clinical Guideline",
        source="American College of Gastroenterology",
        citation="Fass R, et al. Am J Gastroenterol. 2021;116(12):2326-2342.",
        year=2021,
        content=(
            "Gastroesophageal reflux disease (GERD) and esophageal motility disorders are common non-cardiac causes of "
            "retrosternal burning or pressure. Pain may be provoked by meals, recumbency, or stress, and relieved by antacids. "
            "However, esophageal symptoms can mimic cardiac angina, necessitating cardiac exclusion before confirming a GI etiology."
        ),
        diagnostic_prerequisites=["Cardiac ischemic exclusion", "Trial of high-dose PPI or upper endoscopy"]
    )
]

class CardiacRAGService:
    """Retrieval-Augmented Generation service referencing curated cardiac clinical guidelines."""

    @staticmethod
    def retrieve(clinical_state: Dict[str, Any]) -> List[KnowledgeItem]:
        matched: List[KnowledgeItem] = []
        radiation = [str(r).lower() for r in (clinical_state.get("pain_radiation") or [])]
        quality = (clinical_state.get("pain_quality") or "").lower()
        associated = clinical_state.get("associated_symptoms") or {}
        chest_pain = clinical_state.get("chest_pain", False)

        # ACS / Ischemia match
        if chest_pain and (any(loc in r for r in radiation for loc in ["jaw", "arm", "left arm", "neck", "shoulder"]) or "pressure" in quality or "tight" in quality or "crush" in quality):
            matched.append(CARDIAC_KNOWLEDGE_BASE[0]) # ACS guideline

        # Exertional match -> Stable Angina
        if clinical_state.get("worse_with_exertion") is True:
            matched.append(CARDIAC_KNOWLEDGE_BASE[1])

        # Pleuritic / Sharp match -> Pericarditis
        if "sharp" in quality or "stabbing" in quality:
            matched.append(CARDIAC_KNOWLEDGE_BASE[2])

        # Palpitations / Syncope
        if associated.get("palpitations") or associated.get("syncope") or clinical_state.get("palpitations"):
            matched.append(CARDIAC_KNOWLEDGE_BASE[3])

        # Dyspnea
        if associated.get("shortness_of_breath") or clinical_state.get("shortness_of_breath"):
            matched.append(CARDIAC_KNOWLEDGE_BASE[4])

        # Burning / Relieved by rest / food
        if "burn" in quality or "indigestion" in quality:
            matched.append(CARDIAC_KNOWLEDGE_BASE[6])

        # Musculoskeletal consideration
        if "sharp" in quality and not any("jaw" in r or "arm" in r for r in radiation):
            matched.append(CARDIAC_KNOWLEDGE_BASE[5])

        # Default fallback: at least include ACS & Stable Angina foundational guidelines
        if not matched:
            matched = [CARDIAC_KNOWLEDGE_BASE[0], CARDIAC_KNOWLEDGE_BASE[1]]

        return matched[:3]

rag_service = CardiacRAGService()
