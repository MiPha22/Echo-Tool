import re

def parse_report(text: str) -> dict:
    # Grundgerüst: einfache Heuristiken/Regex; kann iterativ erweitert werden
    result = {}

    # --- Stammdaten ---
    # Name "Nachname, Vorname"
    m_name = re.search(r"([A-ZÄÖÜ][a-zäöüß-]+),\s*([A-ZÄÖÜ][a-zäöüß-]+)", text)
    if m_name:
        result["surname"] = m_name.group(1)
        result["first name"] = m_name.group(2)

    # DOB
    m_dob = re.search(r"geb\.?\s*(\d{2}\.\d{2}\.\d{4})", text, re.IGNORECASE)
    if m_dob:
        result["DOB"] = m_dob.group(1)

    # Aufnahmenummer
    m_aufn = re.search(r"AufnahmeNr\.?\s*:\s*(\d+)", text, re.IGNORECASE)
    if m_aufn:
        result["Aufnahmenr"] = m_aufn.group(1)

    # Größe / Gewicht
    m_height = re.search(r"Größ(?:e|\.)\s*(\d{2,3})\s*cm", text, re.IGNORECASE)
    if m_height:
        result["size"] = int(m_height.group(1))
    m_weight = re.search(r"Gewicht\s*(\d{2,3})\s*kg", text, re.IGNORECASE)
    if m_weight:
        result["weight"] = int(m_weight.group(1))

    # --- Echo (Beispiele) ---
    m_ef = re.search(r"EF\s*(\d{1,2})\s*%|EF\s*biplan\s*(\d{1,2})\s*%", text, re.IGNORECASE)
    if m_ef:
        result["LVEF"] = int([g for g in m_ef.groups() if g][0])

    # LVEDV / LVESV (ml)
    m_lvedv = re.search(r"LVEDV\s*(\d{1,3})\s*ml", text, re.IGNORECASE)
    if m_lvedv: result["LVEDV"] = int(m_lvedv.group(1))
    m_lvesv = re.search(r"LVESV\s*(\d{1,3})\s*ml", text, re.IGNORECASE)
    if m_lvesv: result["LVESV"] = int(m_lvesv.group(1))

    # TAPSE (mm)
    m_tapse = re.search(r"TAPSE\s*(\d{1,2})\s*mm", text, re.IGNORECASE)
    if m_tapse: result["TAPSE"] = int(m_tapse.group(1))

    # LAVI (ml/m²)
    m_lavi = re.search(r"LA(?:EDV|-?Index)?\s*(\d{1,3})\s*ml/m²|LAESVI\s*>?<?\s*(\d{1,3})\s*ml/m²", text, re.IGNORECASE)
    if m_lavi:
        val = [g for g in m_lavi.groups() if g][0]
        result["LAVI"] = int(val)

    # E/A, E/e'
    m_ea = re.search(r"E\s*/\s*A\s*(\d+(?:[\.,]\d+)?)|E/A\s*(\d+(?:[\.,]\d+)?)", text, re.IGNORECASE)
    if m_ea:
        result["E/A"] = (m_ea.group(1) or m_ea.group(2)).replace(",", ".")
    m_ee = re.search(r"E\s*/\s*e['′]?\s*<?>?\s*(\d+(?:[\.,]\d+)?)", text, re.IGNORECASE)
    if m_ee:
        result["E/e'"] = m_ee.group(1).replace(",", ".")

    # TR Vmax Flag
    m_trv = re.search(r"TR\s*Vmax\s*(\d+(?:[\.,]\d+)?)\s*m/s|TRVmax\s*(\d+(?:[\.,]\d+)?)\s*m/s", text, re.IGNORECASE)
    if m_trv:
        v = float((m_trv.group(1) or m_trv.group(2)).replace(",", "."))
        result["TR Vmax\n0= <2,8\n1= >2,8"] = 1 if v >= 2.8 else 0

    # AS: Pmean / KÖF / Grad
    m_as_pmean = re.search(r"P\s*mean\s*:?\s*(\d{1,2})\s*mm\s*Hg|Pmean\s*(\d{1,2})", text, re.IGNORECASE)
    if m_as_pmean:
        result["AS\nPmean"] = int([g for g in m_as_pmean.groups() if g][0])
    m_as_koef = re.search(r"KÖF\s*:?\s*(\d+(?:[\.,]\d+)?)\s*cm²", text, re.IGNORECASE)
    if m_as_koef:
        result["AS\nKÖF"] = m_as_koef.group(1).replace(",", ".")
    m_as_grad = re.search(r"AS\s*(I{1,3}|IV|\d)", text, re.IGNORECASE)
    if m_as_grad:
        roman = m_as_grad.group(1).upper()
        mapping = {"I":"1","II":"2","III":"3","IV":"4"}
        result["AS\n0-3"] = mapping.get(roman, roman)

    # AI/MR/TR Grad
    def extract_grade(label):
        m = re.search(label + r"\s*(I{1,3}|IV|\d)(?:[°\s]*)", text, re.IGNORECASE)
        if m:
            roman = m.group(1).upper()
            mapping = {"I":"1","II":"2","III":"3","IV":"4"}
            return mapping.get(roman, roman)
        return None

    ai = extract_grade("AI")
    if ai: result["AI\n0-3"] = ai
    mr = extract_grade("MI|MR")
    if mr: result["MR\n0-3"] = mr
    tr = extract_grade("TI|TR")
    if tr: result["TR\n0-5"] = tr

    # Rhythmus
    if re.search(r"\bSR\b|Sinusrhythmus", text, re.IGNORECASE):
        result["rhythm\nSR=0\nAF=1\nHSM=2"] = 0
    elif re.search(r"\bVHF|Vorhofflimmern|AF\b", text, re.IGNORECASE):
        result["rhythm\nSR=0\nAF=1\nHSM=2"] = 1

    # NYHA (inkl. I-II / II-III etc.)
    m_nyha = re.search(r"NYHA\s*(I{1,4}(?:\s*[-/–]\s*I{1,4})?)", text, re.IGNORECASE)
    if m_nyha:
        token = m_nyha.group(1).upper().replace(" ", "")
        mapping = {"I":"1","II":"2","III":"3","IV":"4","I-II":"1.5","II-III":"2.5","III-IV":"3.5"}
        result["NYHA"] = mapping.get(token, token)

    # Stress-Echo
    if re.search(r"Stressechokardiograph", text, re.IGNORECASE):
        result["dynamic=0\ndobut=1"] = 1 if re.search(r"Dobutamin", text, re.IGNORECASE) else 0
        # Max HF
        m_hf = re.search(r"max\.?\s*HF\s*(\d{2,3})/?min|Bei Abbruch\s*(\d{2,3})/min", text, re.IGNORECASE)
        if m_hf:
            result["Heart rate max"] = int([g for g in m_hf.groups() if g][0])
        # Zielfrequenz erreicht?
        if re.search(r"Zielfrequenz\s*(?:erreicht|erreichen)", text, re.IGNORECASE):
            result["Heart rate aim reached?\nNo=0\nyes=1"] = 1

    # Rauchen
    if re.search(r"Ex-\s*(Nikotin|Raucher)|Ex-Nikotinabusus", text, re.IGNORECASE):
        result["smoking\nnever=0\nformer=1\ncurrent=2\n"] = 1
    elif re.search(r"Nikotinabusus|Raucher", text, re.IGNORECASE):
        result["smoking\nnever=0\nformer=1\ncurrent=2\n"] = 2
    elif re.search(r"Nichtraucher", text, re.IGNORECASE):
        result["smoking\nnever=0\nformer=1\ncurrent=2\n"] = 0

    return result
