import re

def _grade_from_roman_or_digit(token: str, max_scale=5):
    if not token:
        return None
    token = token.strip().upper().replace("°","")
    roman_map = {"I":"1","II":"2","III":"3","IV":"4","V":"5"}
    if token in roman_map:
        return roman_map[token]
    m = re.match(r"^\d$", token)
    if m:
        return token
    return None

def parse_report(text: str) -> dict:
    # Robust parser with guards to avoid AttributeError when patterns are absent.
    result = {}
    if not text or not isinstance(text, str):
        return result

    # --- Stammdaten ---
    m_name = re.search(r"([A-ZÄÖÜ][a-zäöüß-]+),\s*([A-ZÄÖÜ][a-zäöüß-]+)", text)
    if m_name:
        result["surname"] = m_name.group(1)
        result["first name"] = m_name.group(2)

    m_dob = re.search(r"geb\.?\s*(\d{2}\.\d{2}\.\d{4})", text, re.IGNORECASE)
    if m_dob:
        result["DOB"] = m_dob.group(1)

    m_aufn = re.search(r"AufnahmeNr\.?\s*:\s*(\d+)", text, re.IGNORECASE)
    if m_aufn:
        result["Aufnahmenr"] = m_aufn.group(1)

    # Größe / Gewicht
    m_height = re.search(r"Größ(?:e|\.)\s*(\d{2,3})\s*cm", text, re.IGNORECASE)
    if m_height:
        try: result["size"] = int(m_height.group(1))
        except: pass
    m_weight = re.search(r"Gewicht\s*(\d{2,3})\s*kg", text, re.IGNORECASE)
    if m_weight:
        try: result["weight"] = int(m_weight.group(1))
        except: pass

    # --- Echo core ---
    m_ef = re.search(r"(?:EF\s*biplan\s*(\d{1,2})\s*%|EF\s*(\d{1,2})\s*%)", text, re.IGNORECASE)
    if m_ef:
        val = next((g for g in m_ef.groups() if g), None)
        if val: result["LVEF"] = int(val)

    m_lvedv = re.search(r"LVEDV\s*(\d{1,3})\s*ml", text, re.IGNORECASE)
    if m_lvedv:
        try: result["LVEDV"] = int(m_lvedv.group(1))
        except: pass
    m_lvesv = re.search(r"LVESV\s*(\d{1,3})\s*ml", text, re.IGNORECASE)
    if m_lvesv:
        try: result["LVESV"] = int(m_lvesv.group(1))
        except: pass

    m_tapse = re.search(r"TAPSE\s*(\d{1,2})\s*mm", text, re.IGNORECASE)
    if m_tapse:
        try: result["TAPSE"] = int(m_tapse.group(1))
        except: pass

    # LAVI (ml/m²)
    m_lavi = re.search(r"(?:LA(?:EDV|-?Index)?\s*(\d{1,3})\s*ml/m²|LAESVI\s*<?>?\s*(\d{1,3})\s*ml/m²)", text, re.IGNORECASE)
    if m_lavi:
        val = next((g for g in m_lavi.groups() if g), None)
        if val:
            try: result["LAVI"] = int(val)
            except: pass

    # E/A, E/e'
    m_ea = re.search(r"(?:E\s*/\s*A|E/A)\s*(\d+(?:[.,]\d+)?)", text, re.IGNORECASE)
    if m_ea:
        result["E/A"] = m_ea.group(1).replace(",", ".")
    m_ee = re.search(r"E\s*/\s*e['′]?\s*<??>?\s*(\d+(?:[.,]\d+)?)", text, re.IGNORECASE)
    if m_ee:
        result["E/e'"] = m_ee.group(1).replace(",", ".")

    # TR Vmax -> Flag
    m_trv = re.search(r"(?:TR\s*Vmax|TRVmax)\s*(\d+(?:[.,]\d+)?)\s*m/s", text, re.IGNORECASE)
    if m_trv:
        try:
            v = float(m_trv.group(1).replace(",", "."))
            result["TR Vmax\n0= <2,8\n1= >2,8"] = 1 if v >= 2.8 else 0
        except: pass

    # AS: Pmean / KÖF / Grad
    m_as_pmean = re.search(r"(?:P\s*mean\s*:?\s*(\d{1,2})\s*mm\s*Hg|Pmean\s*(\d{1,2}))", text, re.IGNORECASE)
    if m_as_pmean:
        val = next((g for g in m_as_pmean.groups() if g), None)
        if val:
            try: result["AS\nPmean"] = int(val)
            except: pass
    m_as_koef = re.search(r"KÖF\s*:? \s*(\d+(?:[.,]\d+)?)\s*cm²", text, re.IGNORECASE | re.VERBOSE)
    if m_as_koef:
        result["AS\nKÖF"] = m_as_koef.group(1).replace(",", ".")

    # safe extract_grade with guard
    def extract_grade(pattern, max_scale=5):
        m = re.search(r"(?:{})\s*(I{1,3}|IV|V|\d)".format(pattern), text, re.IGNORECASE)
        if not m:
            return None
        token = m.group(1)
        return _grade_from_roman_or_digit(token, max_scale=max_scale)

    ai = extract_grade(r"\bAI\b", max_scale=3)
    if ai is not None: result["AI\n0-3"] = ai
    mr = extract_grade(r"\bMI\b|\bMR\b", max_scale=3)
    if mr is not None: result["MR\n0-3"] = mr
    tr = extract_grade(r"\bTI\b|\bTR\b", max_scale=5)
    if tr is not None: result["TR\n0-5"] = tr

    # Rhythmus
    if re.search(r"\bSR\b|Sinusrhythmus", text, re.IGNORECASE):
        result["rhythm\nSR=0\nAF=1\nHSM=2"] = 0
    elif re.search(r"\bVHF\b|Vorhofflimmern|\bAF\b", text, re.IGNORECASE):
        result["rhythm\nSR=0\nAF=1\nHSM=2"] = 1

    # NYHA inkl. Spannweiten
    m_nyha = re.search(r"NYHA\s*(I{1,4}(?:\s*[-/–]\s*I{1,4})?)", text, re.IGNORECASE)
    if m_nyha:
        token = m_nyha.group(1).upper().replace(" ", "")
        mapping = {"I":"1","II":"2","III":"3","IV":"4","I-II":"1.5","II-III":"2.5","III-IV":"3.5"}
        result["NYHA"] = mapping.get(token, token)

    # Stress-Echo
    if re.search(r"Stressechokardiograph", text, re.IGNORECASE):
        result["dynamic=0\ndobut=1"] = 1 if re.search(r"Dobutamin", text, re.IGNORECASE) else 0
        m_hf = re.search(r"(?:max\.?\s*HF|Bei Abbruch)\s*(\d{2,3})/?min", text, re.IGNORECASE)
        if m_hf:
            try: result["Heart rate max"] = int(m_hf.group(1))
            except: pass
        if re.search(r"Zielfrequenz\s*(?:erreicht|erreichen)", text, re.IGNORECASE):
            result["Heart rate aim reached?\nNo=0\nyes=1"] = 1

    # Raucherstatus
    if re.search(r"Ex-\s*(Nikotin|Raucher)|Ex-Nikotinabusus", text, re.IGNORECASE):
        result["smoking\nnever=0\nformer=1\ncurrent=2\n"] = 1
    elif re.search(r"Nikotinabusus|Raucher", text, re.IGNORECASE):
        result["smoking\nnever=0\nformer=1\ncurrent=2\n"] = 2
    elif re.search(r"Nichtraucher", text, re.IGNORECASE):
        result["smoking\nnever=0\nformer=1\ncurrent=2\n"] = 0

    return result