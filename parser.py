# parser.py
import re
from datetime import datetime

# ---------- Helpers ----------
DEC = r"\d+(?:[.,]\d+)?"

def num(s):
    if s is None: return None
    return float(s.replace(",", "."))
def to_int(s):
    try: return int(float(str(s).replace(",", ".")))
    except: return None
def bsa_mosteller(height_cm, weight_kg):
    if not height_cm or not weight_kg: return None
    try:
        return round(((height_cm * weight_kg) / 3600.0) ** 0.5, 2)
    except: return None
def first(txt, *groups):
    for g in groups:
        if g: return g
    return None
def find_date_near_keyword(text, kw_regex):
    m = re.search(rf"{kw_regex}[^0-9]{{0,40}}(\d{{2}}\.\d{{2}}\.\d{{4}})", text, re.IGNORECASE|re.DOTALL)
    return m.group(1) if m else None
def find_any_date(text):
    m = re.search(r"(\d{2}\.\d{2}\.\d{4})", text)
    return m.group(1) if m else None

# Roman/arabisch (I–V oder 1–5)
def _grade_from_roman_or_digit(token: str, max_scale=5):
    if not token: return None
    token = token.strip().upper().replace("°","")
    roman_map = {"I":"1","II":"2","III":"3","IV":"4","V":"5"}
    if token in roman_map:
        return roman_map[token]
    if re.match(r"^\d$", token):  # 0..9
        return token
    return None

def _extract_grade(text, pattern, max_scale=5):
    # … „Grad II“, „II°“, römisch/arabisch, MR/MI, TR/TI etc.
    regex = rf"(?:{pattern})\s*(?:Grad\s*)?(I{{1,3}}|IV|V|\d)"
    m = re.search(regex, text, re.IGNORECASE)
    if not m: return None
    return _grade_from_roman_or_digit(m.group(1), max_scale=max_scale)

# ---------- Row template (ALL columns) ----------
def init_row():
    cols = [
        "surname","first name","DOB","Aufnahmenr",
        "Date \nStressecho; positiv-> mark green",
        "kind of FU\n1=in house\n2=tel/Tod\n3=to be done",
        "Follow-Up\ndeceased=0\nHKU/CT only=1\nTTE/clinical only=2\nboth=3",
        "Indikation\nStressecho\n0=khk\n1=AS\n2=AV-Klappen\n3=HFpEF",
        "sex\n0=male\n1=female","size","weight","KOF","CVRF",
        "hyperten\nno=0\nyes=1","diabetes\nno=0\nyes=1","dyslipid\nno=0\nyes=1",
        "Heart failure diagnosis?","AF\nno=0\nparox=1\npers=2\nperm=3",
        "PM\nno=0\n1-C-PM=1\n2-C-PM=2\nCRT=3\nICD=4",
        "chronic lung\n disease\nno=0\nyes=1",
        "previous known ICM\nno=0\n1-GE=1; 2-GE=2; 3-GE=3",
        "prior MI\nno=0\nyes=1","prior PCI\nno=0\nyes=1","prior CABG\nno=0\nyes=1",
        "valve intervention/ surgery\nno=0\nyes=1","valve history freetext","NYHA",
        "smoking\nnever=0\nformer=1\ncurrent=2\n","Medication",
        "APT\nno=0\nASS=1\nP2y=2\nDAPT=3","OAK","RAASi","ARNI","Betablocker","MRA","SGLT2","Diuretics","Statin",
        "labs\nbaseline","GFR","LDL-C","Hb","NTproBNP",
        "labs latest\nfollow-up","date","GFR","LDL-C","Hb","NTproBNP",
        "rest echo\nbaseline","date","rhythm\nSR=0\nAF=1\nHSM=2","LVEF","LVEDV","LVESV","TAPSE","LAVI",
        "MR\n0-3","TR\n0-5","E/A","E/e'","e' reduced\nno=0\nyes=1",
        "TR Vmax\n0= <2,8\n1= >2,8","AS\n0-3","AS\nPmean","AS\nKÖF","AI\n0-3",
        "wall motion\nrest ","anterior\nnormal=0\nhypokin=1\nakin=2\ndyskin=3",
        "antero- \nlateral\nnormal=0\nhypokin=1\nakin=2\ndyskin=3",
        "antero-\nseptal\nnormal=0\nhypokin=1\nakin=2\ndyskin=3",
        "inferior\nnormal=0\nhypokin=1\nakin=2\ndyskin=3",
        "infero-\nlateral\nnormal=0\nhypokin=1\nakin=2\ndyskin=3",
        "infero-\nseptal\nnormal=0\nhypokin=1\nakin=2\ndyskin=3",
        "global hypokinesie\nno=0\nyes=1","number of segments with ischemia",
        "stress echo\nbaseline","date","dynamic=0\ndobut=1","dobutamin max dose ug/kgKG",
        "Heart rate max","Heart rate aim reached?\nNo=0\nyes=1",
        "RR sys rest","RR dia rest","RR sys max","RR dia max","Watt","MET",
        "dyspnoe\nno=0\nyes=1","AP\nno=0\nyes=1","muscular \nfatigue\nno=0\nyes=1",
        "ended prema-turely\nno=0; dyspnoe=1; AP=2; muscular=3; other=4",
        "insufficient image quality\nno=0\nyes=1","Freetext ",
        "LA-reservoir \nstrain BL","LA conduit-\nstrain","LA booster \npump","LV-strain \n(GLS)",
        "MR 0-3","TR 0-5","LVOT SV\nrest","LVOT SVI rest\nRechner","LVOT SVI \nrest",
        "LVOT SV\nmax","LVOT SVI max\nRechner","SVI max",
        "AS Pmean max\n(mmHg)","AS KÖF min\n(cm2)",
        "wall motion\nstress ","anterior\nnormal=0\nhypokin=1\nakin=2\ndyskin=3",
        "antero- \nlateral\nnormal=0\nhypokin=1\nakin=2\ndyskin=3",
        "antero-\nseptal\nnormal=0\nhypokin=1\nakin=2\ndyskin=3",
        "inferior\nnormal=0\nhypokin=1\nakin=2\ndyskin=3",
        "infero-\nlateral\nnormal=0\nhypokin=1\nakin=2\ndyskin=3",
        "infero-\nseptal\nnormal=0\nhypokin=1\nakin=2\ndyskin=3",
        "number of segments with ischemia",
        "first CT after \nbaseline echo","date of CT",
        "stenosis >50%\nLAD\nno=0\nyes=1","stenosis >50%\nLCX\nno=0\nyes=1",
        "stenosis >50%\nLM\nno=0\nyes=1","stenosis >50%\nRCA\nno=0\nyes=1",
        "wall motion abnormality in baseline SE aligns\nno=0\nyes=1",
        "first MRT after baseline SE","date of MRT","perfusion deficit LAD","perfusion deficit LCX","perfusion deficit RCA","deficit aligns with SE",
        "first cath after \nbaseline echo","date of cath",
        "stenosis >50%\nLAD\nno=0\nyes=1","stenosis >/=50%\nLCX\nno=0\nyes=1","stenosis >50%\nLM\nno=0\nyes=1","stenosis >50%\nRCA\nno=0\nyes=1",
        "wall motion abnormality in baseline SE aligns\nno=0\nyes=1",
        "revasc\nno=0\nyes=1","Bypass\nno=0\nyes=1","revasc/ surgery freetext",
        "PCI\nLAD\nno=0\nyes=1 ","PCI\nLCX\nno=0\nyes=1 ","PCI\nLM\nno=0\nyes=1 ","PCI\nRCA\nno=0\nyes=1 ",
        "AS\nONLY (discharge=   hospitalization for TAVI)","TAVI\nno=0\nyes=date ","Aortenkl- surgery\nno=0\nyes=date",
        "Pmean discharge","KÖF discharge","AS 0-3 discharge","AR 0-3 discharge",
        "latest\nfollow-up","date of \nlatest FU","alive=0\ndeceased= date","cause of death",
        "heart failure hospitalisation\nnumber since baseline","date of first\n HF hospitalisation after baseline",
        "myocardial infarction after baseline\nno=0\nyes=1","coronary intervention since initial cath\nno=0\nyes=1",
        "CABG since initial cath\nno=0\nyes=1","freetext intervention/ surgery",
        "heart Failure diagnosis\nno=0\nyes=1 ","date of HF diagnosis if new since baseline ",
        "AF\nno=0\nparox=1\npers=2\nperm=3","NYHA class",
        "echo\nlatest follow up","date of latest follow up echo","rhythm\nSR=0\nAF=1\nHSM=2, others=3",
        "LVEF","LVEDV","LVESV","TAPSE","LAVI","MR\n0-3","TR\n0-5",
        "AV-valve intervention new, freetext ","E/A","E/e'","e' reduced\nno=0\nyes=1",
        "TR Vmax","AS\n0-3","AS\nPmean","AS\nKÖF (nicht indiziert)","AI\n0-3"
    ]
    return {c: "" for c in cols}

# ---------- Main parser ----------
def parse_report(text: str) -> dict:
    row = init_row()
    if not text or not isinstance(text, str):
        return row

    # --- Personen/Meta ---
    m_name = re.search(r"([A-ZÄÖÜ][a-zäöüß-]+),\s*([A-ZÄÖÜ][a-zäöüß-]+)", text)
    if m_name:
        row["surname"] = m_name.group(1)
        row["first name"] = m_name.group(2)

    m_dob = re.search(r"geb\.?\s*(\d{2}\.\d{2}\.\d{4})", text, re.IGNORECASE)
    if m_dob: row["DOB"] = m_dob.group(1)

    m_aufn = re.search(r"AufnahmeNr\.?\s*:\s*(\d+)", text, re.IGNORECASE)
    if m_aufn: row["Aufnahmenr"] = m_aufn.group(1)

    # Sex aus „Patientin/Patient“
    if re.search(r"\bPatientin\b", text, re.IGNORECASE):
        row["sex\n0=male\n1=female"] = 1
    elif re.search(r"\bPatient\b", text, re.IGNORECASE):
        row["sex\n0=male\n1=female"] = 0

    # Größe / Gewicht / KOF
    m_height = re.search(r"Größ(?:e|\.)\s*(\d{2,3})\s*cm", text, re.IGNORECASE)
    if m_height: row["size"] = to_int(m_height.group(1))
    m_weight = re.search(r"Gewicht\s*(\d{2,3})\s*kg", text, re.IGNORECASE)
    if m_weight: row["weight"] = to_int(m_weight.group(1))
    if row["size"] and row["weight"]:
        row["KOF"] = bsa_mosteller(row["size"], row["weight"])

    # CVRFs
    row["hyperten\nno=0\nyes=1"] = 1 if re.search(r"Hyperton", text, re.IGNORECASE) else 0
    row["diabetes\nno=0\nyes=1"] = 1 if re.search(r"Diabetes|HbA1c", text, re.IGNORECASE) else 0
    row["dyslipid\nno=0\nyes=1"] = 1 if re.search(r"Hyperlipid|LDL|Statin", text, re.IGNORECASE) else 0
    row["chronic lung\n disease\nno=0\nyes=1"] = 1 if re.search(r"COPD|Asthma", text, re.IGNORECASE) else 0

    # HF Diagnose
    row["Heart failure diagnosis?"] = 1 if re.search(r"Herzinsuffizienz|HFmrEF|HFrEF|HFpEF", text, re.IGNORECASE) else 0

    # AF
    if re.search(r"permanent(?:es)? Vorhofflimmern|perm\.*\s*VHF", text, re.IGNORECASE):
        row["AF\nno=0\nparox=1\npers=2\nperm=3"] = 3
    elif re.search(r"persistierend(?:es)? Vorhofflimmern|persist", text, re.IGNORECASE):
        row["AF\nno=0\nparox=1\npers=2\nperm=3"] = 2
    elif re.search(r"paroxysmal(?:es)? Vorhofflimmern|parox", text, re.IGNORECASE):
        row["AF\nno=0\nparox=1\npers=2\nperm=3"] = 1
    elif re.search(r"Vorhofflimmern|VHF|AF", text, re.IGNORECASE):
        row["AF\nno=0\nparox=1\npers=2\nperm=3"] = 1  # fallback

    # Devices
    if re.search(r"\bCRT(?:-D|D)?\b", text, re.IGNORECASE):
        row["PM\nno=0\n1-C-PM=1\n2-C-PM=2\nCRT=3\nICD=4"] = 3
    elif re.search(r"\bICD\b", text):
        row["PM…"] = 4
    elif re.search(r"2-?K(?:ammer)?-?Schrittmacher|Dual|DDD|DDIR", text, re.IGNORECASE):
        row["PM\nno=0\n1-C-PM=1\n2-C-PM=2\nCRT=3\nICD=4"] = 2
    elif re.search(r"1-?K(?:ammer)?-?Schrittmacher|VVI|AAI", text, re.IGNORECASE):
        row["PM\nno=0\n1-C-PM=1\n2-C-PM=2\nCRT=3\nICD=4"] = 1
    else:
        row["PM\nno=0\n1-C-PM=1\n2-C-PM=2\nCRT=3\nICD=4"] = 0

    # KHK/HKU Vorgeschichte
    if re.search(r"\b(\d)\s*-\s*G(?:efäßerkrankung|E)\b", text):
        row["previous known ICM\nno=0\n1-GE=1; 2-GE=2; 3-GE=3"] = to_int(re.search(r"\b(\d)\s*-\s*G", text).group(1))
    elif re.search(r"Eingefäßerkrankung|1-GE", text, re.IGNORECASE):
        row["previous known ICM…"] = 1
    elif re.search(r"2-?GE|Zwei-Gefäß", text, re.IGNORECASE):
        row["previous known ICM…"] = 2
    elif re.search(r"3-?GE|Drei-Gefäß", text, re.IGNORECASE):
        row["previous known ICM…"] = 3
    else:
        row["previous known ICM…"] = 0

    row["prior MI\nno=0\nyes=1"] = 1 if re.search(r"Myokardinfarkt|STEMI|NSTEMI", text, re.IGNORECASE) else 0
    row["prior PCI\nno=0\nyes=1"] = 1 if re.search(r"PCI|DES-Implantation|Stent", text, re.IGNORECASE) else 0
    row["prior CABG\nno=0\nyes=1"] = 1 if re.search(r"Bypass|ACVB|CABG", text, re.IGNORECASE) else 0

    # Klappen-OP/TAVI
    if re.search(r"\bTAVI\b|Transkatheter-Aortenklappenimplantation", text, re.IGNORECASE) or \
       re.search(r"Aortenklappenersatz|Mitralklappenrekonstruktion|TKR mittels Ring|MitraClip|Annuloplastie", text, re.IGNORECASE):
        row["valve intervention/ surgery\nno=0\nyes=1"] = 1
        # Freitext History (kurz)
        m_hist = re.search(r"(Z\.n\..{0,200}?(?:Valve|Ring|AKE|TKR|Mitra|TAVI).{0,120})", text, re.IGNORECASE|re.DOTALL)
        if m_hist: row["valve history freetext"] = re.sub(r"\s+", " ", m_hist.group(1)).strip()
    else:
        row["valve intervention/ surgery…"] = 0

    # NYHA (auch Spannen)
    m_nyha = re.search(r"NYHA\s*(I{1,4})(?:\s*(?:[-/–]|bis)\s*(I{1,4}))?", text, re.IGNORECASE)
    if m_nyha:
        a, b = m_nyha.group(1,2)
        mapping = {"I":"1","II":"2","III":"3","IV":"4"}
        row["NYHA"] = (str((float(mapping[a])+float(mapping[b]))/2) if b else mapping[a])

    # Rauchen
    if re.search(r"Ex-?\s*(Nikotin|Raucher)|Ex-Nikotinabusus|Former smoker", text, re.IGNORECASE):
        row["smoking\nnever=0\nformer=1\ncurrent=2\n"] = 1
    elif re.search(r"Nikotinabusus|Raucher\b", text, re.IGNORECASE):
        row["smoking…"] = 2
    elif re.search(r"Nichtraucher", text, re.IGNORECASE):
        row["smoking…"] = 0

    # Medikation (für APT/OAK/RAASi/… Marker)
    meds_block = []
    for line in text.splitlines():
        if re.search(r"Medikament|Medikation|ASS|Apixaban|Edoxaban|Phenprocoumon|Falithrom|Apixaban|Rivaroxaban|Warfarin|\
Simvastatin|Atorvastatin|Rosuvastatin|Pravastatin|Candesartan|Valsartan|Enalapril|Ramipril|Sacubitril|Carvedilol|Bisoprolol|Nebivolol|\
Spironolacton|Eplerenon|Dapagliflozin|Empagliflozin|Torasemid|Furosemid|HCT", line, re.IGNORECASE):
            meds_block.append(line.strip())
    row["Medication"] = " | ".join(meds_block)[:1000]

    has_ASS = bool(re.search(r"\bASS\b|Aspirin", text, re.IGNORECASE))
    has_P2Y = bool(re.search(r"Clopidogrel|Prasugrel|Ticagrelor", text, re.IGNORECASE))
    row["APT\nno=0\nASS=1\nP2y=2\nDAPT=3"] = 3 if (has_ASS and has_P2Y) else (1 if has_ASS else (2 if has_P2Y else 0))
    row["OAK"] = 1 if re.search(r"Apixaban|Rivaroxaban|Edoxaban|Dabigatran|Phenprocoumon|Falithrom|Warfarin", text, re.IGNORECASE) else 0
    row["RAASi"] = 1 if re.search(r"Ramipril|Enalapril|Lisinopril|Perindopril|Candesartan|Valsartan|Olmesartan|Losartan", text, re.IGNORECASE) else 0
    row["ARNI"] = 1 if re.search(r"Sacubitril|Entresto", text, re.IGNORECASE) else 0
    row["Betablocker"] = 1 if re.search(r"Bisoprolol|Nebivolol|Metoprolol|Carvedilol|Atenolol|Betablocker", text, re.IGNORECASE) else 0
    row["MRA"] = 1 if re.search(r"Spironolacton|Eplerenon", text, re.IGNORECASE) else 0
    row["SGLT2"] = 1 if re.search(r"Dapagliflozin|Empagliflozin|Ertugliflozin|SGLT2", text, re.IGNORECASE) else 0
    row["Diuretics"] = 1 if re.search(r"Torasemid|Furosemid|Hydrochlorothiazid|HCT|Diuret", text, re.IGNORECASE) else 0
    row["Statin"] = 1 if re.search(r"Simvastatin|Atorvastatin|Rosuvastatin|Pravastatin|Statin", text, re.IGNORECASE) else 0

    # ----- Labs (Baseline & Follow-up) -----
    def _grab_lab(pattern, key, dest_row):
        m = re.search(pattern, text, re.IGNORECASE)
        if m:
            dest_row[key] = str(num(m.group(1)))
    # baseline block marker (wenn ausdrücklich „Labor:“)
    if re.search(r"\bLabor\b[:\s]", text, re.IGNORECASE):
        row["labs\nbaseline"] = 1
    _grab_lab(r"GFR[\/ ]?\/?CKD.*?:\s*("+DEC+")", "GFR", row)
    _grab_lab(r"LDL[- ]?Cholesterin.*?:\s*("+DEC+")", "LDL-C", row)
    _grab_lab(r"\bHämoglobin\b.*?:\s*("+DEC+")", "Hb", row)
    _grab_lab(r"(?:NT-?pro-?BNP|N-?terminales pro BNP).*?:\s*("+DEC+")", "NTproBNP", row)

    # follow-up lab with date near the lab list
    m_follow_date = re.search(r"\b(\d{2}\.\d{2}\.\d{4})\b(?:(?!\n\n).){0,120}Kalium|LDL|GFR|NT-?pro", text, re.IGNORECASE|re.DOTALL)
    if m_follow_date:
        row["labs latest\nfollow-up"] = 1
        row["date"] = m_follow_date.group(1)
        _grab_lab(r"GFR[\/ ]?\/?CKD.*?:\s*("+DEC+")", "GFR", row)           # same text scope, ok
        _grab_lab(r"LDL[- ]?Cholesterin.*?:\s*("+DEC+")", "LDL-C", row)
        _grab_lab(r"\bHämoglobin\b.*?:\s*("+DEC+")", "Hb", row)
        _grab_lab(r"(?:NT-?pro-?BNP|N-?terminales pro BNP).*?:\s*("+DEC+")", "NTproBNP", row)

    # ----- Echo baseline (rest) -----
    base_date = find_date_near_keyword(text, r"Echokardiographie.*?vom") or find_any_date(text)
    if base_date: row["date"] = base_date

    # Rhythm
    if re.search(r"\bSR\b|Sinusrhythmus", text, re.IGNORECASE):
        row["rhythm\nSR=0\nAF=1\nHSM=2"] = 0
    elif re.search(r"\bVHF\b|Vorhofflimmern|\bAF\b", text, re.IGNORECASE):
        row["rhythm…"] = 1
    elif re.search(r"Schrittmacher|HSM|VVI|DDD|DDIR", text, re.IGNORECASE):
        row["rhythm…"] = 2

    # EF / Volumina / TAPSE / LAVI
    m_ef = re.search(r"EF(?:\s*biplan)?\s*(\d{1,2})\s*%", text, re.IGNORECASE)
    if m_ef: row["LVEF"] = to_int(m_ef.group(1))
    m_lvedv = re.search(r"LVEDV\s*("+DEC+")\s*ml", text, re.IGNORECASE)
    if m_lvedv: row["LVEDV"] = to_int(m_lvedv.group(1))
    m_lvesv = re.search(r"LVESV\s*("+DEC+")\s*ml", text, re.IGNORECASE)
    if m_lvesv: row["LVESV"] = to_int(m_lvesv.group(1))
    m_tapse = re.search(r"TAPSE\s*("+DEC+")\s*mm", text, re.IGNORECASE)
    if m_tapse: row["TAPSE"] = to_int(m_tapse.group(1))
    m_lavi = re.search(r"(?:LA(?:EDV|-?Index)?\s*("+DEC+")\s*ml/m²|LAESVI\s*<?>?\s*("+DEC+")\s*ml/m²)", text, re.IGNORECASE)
    if m_lavi:
        row["LAVI"] = to_int(first(*m_lavi.groups()))

    # Diastole
    m_ea = re.search(r"(?:E\s*/\s*A|E/A)\s*("+DEC+")", text, re.IGNORECASE)
    if m_ea: row["E/A"] = str(num(m_ea.group(1)))
    m_ee = re.search(r"E\s*/\s*e['′]?\s*<??>?\s*("+DEC+")", text, re.IGNORECASE)
    if m_ee:
        row["E/e'"] = str(num(m_ee.group(1)))
        row["e' reduced\nno=0\nyes=1"] = 1 if num(m_ee.group(1)) and num(m_ee.group(1))>=14 else 0

    # E/A
    m_ea = re.search(r"(?:E\s*/\s*A|E/A)\s*[:=]?\s*(\d+(?:[.,]\d+)?)", text, re.IGNORECASE)
    if not m_ea:
        # fallback: Muster "E/A\n 0,77"
        m_ea = re.search(r"E/A\s*\(?\s*(\d+(?:[.,]\d+)?)", text, re.IGNORECASE)
    if m_ea:
        result["E/A"] = m_ea.group(1).replace(",", ".")

    # E/e'
    m_ee = re.search(r"(?:E\s*/\s*e['′]?)\s*[:=]?\s*(\d+(?:[.,]\d+)?)", text, re.IGNORECASE)
    if not m_ee:
        # fallback: Muster "E/E‘ 9" (mit Sonderzeichen Apostroph)
        m_ee = re.search(r"E\s*/\s*E[‘']\s*(\d+(?:[.,]\d+)?)", text, re.IGNORECASE)
    if m_ee:
        result["E/e'"] = m_ee.group(1).replace(",", ".")


    # TR Vmax -> Flag
    m_trv = re.search(r"(?:TR\s*Vmax|TRVmax|TR\s*V\s*max)\s*("+DEC+")\s*m/s", text, re.IGNORECASE)
    if m_trv:
        row["TR Vmax\n0= <2,8\n1= >2,8"] = 1 if num(m_trv.group(1)) and num(m_trv.group(1))>=2.8 else 0

    # AS/AI/MR/TR Grades & Werte
    as_pmean = re.search(r"(?:P\s*mean\s*:?\s*(\d{1,2})\s*mm\s*Hg|Pmean\s*(\d{1,2}))", text, re.IGNORECASE)
    if as_pmean: row["AS\nPmean"] = to_int(first(*as_pmean.groups()))
    as_koef = re.search(r"(K[ÖO]F)\s*:?\s*("+DEC+")\s*cm²", text, re.IGNORECASE)
    if as_koef: row["AS\nKÖF"] = str(num(as_koef.group(2)))
    ai = _extract_grade(text, r"\bAI\b", max_scale=3)
    if ai: row["AI\n0-3"] = ai
    mr = _extract_grade(text, r"\bMI\b|\bMR\b", max_scale=3)
    if mr: row["MR\n0-3"] = mr
    tr = _extract_grade(text, r"\bTI\b|\bTR\b", max_scale=5)
    if tr: row["TR\n0-5"] = tr
    # vereinfachte AS Grad aus Pmean/KÖF falls nicht explizit
    if not row.get("AS\n0-3") and (row.get("AS\nPmean") or row.get("AS\nKÖF")):
        pmean = row.get("AS\nPmean")
        koef = float(row["AS\nKÖF"]) if row.get("AS\nKÖF") else None
        if pmean and pmean>=40 or (koef and koef<1.0): row["AS\n0-3"] = "3"
        elif pmean and pmean>=20 or (koef and koef<1.5): row["AS\n0-3"] = "2"
        else: row["AS\n0-3"] = "1"
    
    # ---- Negativformulierung: keine MI => MR = 0 (nur wenn noch nichts erkannt) ----
    if "MR\n0-3" not in result:
        if re.search(r"(?:keine|ohne)\s+(?:MI|Mitralinsuffizienz(?:en)?)", text, re.IGNORECASE):
        result["MR\n0-3"] = "0"
    if "AI\n0-3" not in result:
        if re.search(r"(?:keine|ohne)\s+(?:AI|Aorteninsuffizienz(?:en)?)", text, re.IGNORECASE):
            result["AI\n0-3"] = "0"

    if "TR\n0-5" not in result:
        if re.search(r"(?:keine|ohne)\s+(?:TI|Trikuspidalinsuffizienz(?:en)?)", text, re.IGNORECASE):
            result["TR\n0-5"] = "0"

    # ---- Negativformulierung: keine AS ----
    if "AS\n0-3" not in result:
        if re.search(r"(?:keine|ohne)\s+(?:AS|Aortenklappenstenose)", text, re.IGNORECASE):
            result["AS\n0-3"] = "0"


    # ---------- Wandbewegung (REST) ----------
    # Spaltennamen der Segmente exakt wie in deiner Tabelle
    seg_cols = {
        r"antero[- ]?septal": "antero-\nseptal\nnormal=0\nhypokin=1\nakin=2\ndyskin=3",
        r"antero[- ]?lateral": "antero- \nlateral\nnormal=0\nhypokin=1\nakin=2\ndyskin=3",
        r"\banterior\b":       "anterior\nnormal=0\nhypokin=1\nakin=2\ndyskin=3",
        r"infero[- ]?septal":  "infero-\nseptal\nnormal=0\nhypokin=1\nakin=2\ndyskin=3",
        r"infero[- ]?lateral": "infero-\nlateral\nnormal=0\nhypokin=1\nakin=2\ndyskin=3",
        r"\binferior\b":       "inferior\nnormal=0\nhypokin=1\nakin=2\ndyskin=3",
    }

    # alle Segmente default = "0", falls sie in der Tabelle stehen
    for col in seg_cols.values():
        result[col] = result.get(col, "0")

    # „keine/ohne regionalen Kinetik-/Wandbewegungsstörungen“ => alles 0
    no_regional = re.search(
        r"(?:keine|ohne)\s+regional(?:en|e)\s+(?:Kinetik|Wandbewegungs)stör",
        text, re.IGNORECASE
    )
    if no_regional:
        result["wall motion\nrest "] = 0
        result["global hypokinesie\nno=0\nyes=1"] = 0
        result["number of segments with ischemia"] = 0
    else:
        # Intensität: Hypo=1, Akin=2, Dyskin=3 (Standard falls unklar: 1)
        severity = None
        if re.search(r"\bDyskin", text, re.IGNORECASE):
            severity = "3"
        elif re.search(r"\bAkines", text, re.IGNORECASE):
            severity = "2"
        elif re.search(r"\bHypokines", text, re.IGNORECASE):
            severity = "1"

        matched_any = False
        if severity:
            for pat, col in seg_cols.items():
                if re.search(pat, text, re.IGNORECASE):
                    result[col] = severity
                    matched_any = True

        # Falls Kinetikstörung erwähnt, aber kein Segment genannt -> nur Flag setzen
        if severity:
            result["wall motion\nrest "] = 1
        elif re.search(r"Kinetikstör|Wandbewegungsstör", text, re.IGNORECASE):
            result["wall motion\nrest "] = 1

        # global hypokinesie Flag
        result["global hypokinesie\nno=0\nyes=1"] = 1 if re.search(r"globale\s+Hypokinesie", text, re.IGNORECASE) else 0

        # „number of segments with ischemia“ gehört eigentlich zum STRESS-Teil.
        # Für REST setzen wir nur, wenn ausdrücklich gefordert – sonst nicht anfassen.
        # Wenn du für REST sicher 0 willst, kommentier die nächste Zeile ein:
        # result["number of segments with ischemia"] = 0


    # ----- Stressecho baseline -----
    if re.search(r"Stressechokardiograph", text, re.IGNORECASE):
        row["stress echo\nbaseline"] = 1
        se_date = find_date_near_keyword(text, r"Stressechokardiographie.*?vom") or find_any_date(text)
        if se_date: row["date"] = se_date
        row["dynamic=0\ndobut=1"] = 1 if re.search(r"Dobutamin", text, re.IGNORECASE) else 0
        m_dose = re.search(r"(\d{1,2})\s*ug\/?kg(?:KG)?\/?min.*?(?:3\s*min|Min)", text, re.IGNORECASE|re.DOTALL)
        if m_dose: row["dobutamin max dose ug/kgKG"] = to_int(m_dose.group(1))
        # HF/BP
        m_hfmax = re.search(r"(?:Bei Abbruch\s*|Herzfrequenz.*?Bei Abbruch\s*)(\d{2,3})\/?min|max\.\s*HF.*?(\d{2,3})", text, re.IGNORECASE)
        row["Heart rate max"] = to_int(first(*(m_hfmax.groups() if m_hfmax else [])))
        row["Heart rate aim reached?\nNo=0\nyes=1"] = 1 if re.search(r"Zielfrequenz.*?erreicht", text, re.IGNORECASE) else 0
        # RR
        m_rr_rest = re.search(r"Ausgangs-?RR[: ]\s*(\d{2,3})\s*/\s*(\d{2,3})", text, re.IGNORECASE)
        if m_rr_rest:
            row["RR sys rest"], row["RR dia rest"] = to_int(m_rr_rest.group(1)), to_int(m_rr_rest.group(2))
        m_rr_max = re.search(r"RR.*?bis\s*(\d{2,3})\s*\(?(\d{2,3})?\)?\s*mm\s*Hg|RR-Verhalten.*?maximal\s*(\d{2,3})/(\d{2,3})", text, re.IGNORECASE|re.DOTALL)
        if m_rr_max:
            vals = [g for g in m_rr_max.groups() if g]
            if len(vals)>=2:
                row["RR sys max"], row["RR dia max"] = to_int(vals[0]), to_int(vals[1])
        # Symptome/Abbruch
        row["dyspnoe\nno=0\nyes=1"] = 1 if re.search(r"Dyspnoe", text, re.IGNORECASE) else 0
        row["AP\nno=0\nyes=1"] = 1 if re.search(r"Angina pectoris|AP", text, re.IGNORECASE) else 0
        row["muscular \nfatigue\nno=0\nyes=1"] = 1 if re.search(r"Ermüdung|Fatigue|Erschöpfung", text, re.IGNORECASE) else 0
        if re.search(r"Abbruchgrund.*AP", text, re.IGNORECASE): row["ended prema-turely\nno=0; dyspnoe=1; AP=2; muscular=3; other=4"] = 2
        elif re.search(r"Abbruchgrund.*Dyspnoe", text, re.IGNORECASE): row["ended prema-…"] = 1
        elif re.search(r"Abbruchgrund.*mus", text, re.IGNORECASE): row["ended prema-…"] = 3
        elif re.search(r"Abbruchgrund", text, re.IGNORECASE): row["ended prema-…"] = 4
        # WMA unter Stress
        if re.search(r"unter.*Dobutamin.*Hypokinesie|Ischämie", text, re.IGNORECASE):
            row["wall motion\nstress "] = 1
            if re.search(r"anteroseptal", text, re.IGNORECASE): row["antero-\nseptal\nnormal=0\nhypokin=1\nakin=2\ndyskin=3"] = "1"
            if re.search(r"anterior", text, re.IGNORECASE): row["anterior\nnormal=0\nhypokin=1\nakin=2\ndyskin=3"] = "1"
            if re.search(r"inferior", text, re.IGNORECASE): row["inferior\nnormal=0\nhypokin=1\nakin=2\ndyskin=3"] = "1"

    # ----- CT / MRT / Cath (erste nach Baseline) -----
    # CT
    if re.search(r"\bCT\b|CTA", text, re.IGNORECASE):
        row["first CT after \nbaseline echo"] = 1
        row["date of CT"] = find_date_near_keyword(text, r"CT.*?(?:vom|am)") or find_any_date(text)
        # Koronarstenosen aus CT (selten explizit), meist nur notiert wenn >50%
        for art, col in [("LAD","stenosis >50%\nLAD\nno=0\nyes=1"),
                         ("LCX","stenosis >50%\nLCX\nno=0\nyes=1"),
                         ("LM","stenosis >50%\nLM\nno=0\nyes=1"),
                         ("RCA","stenosis >50%\nRCA\nno=0\nyes=1")]:
            if re.search(fr"{art}.*?(?:> ?50|hochgradig|signifikant)", text, re.IGNORECASE):
                row[col] = 1
            else:
                row[col] = row.get(col,"") or 0

    # MRT
    if re.search(r"\bMRT\b|Cardio-?MRI|Stress-?MRT", text, re.IGNORECASE):
        row["first MRT after baseline SE"] = 1
        row["date of MRT"] = find_date_near_keyword(text, r"MRT.*?(?:vom|am)") or find_any_date(text)

    # Cath / HKU
    if re.search(r"HK-?Untersuchung|Koronarangiographie|Herzkatheter", text, re.IGNORECASE):
        row["first cath after \nbaseline echo"] = 1
        row["date of cath"] = find_date_near_keyword(text, r"(?:HK|Herzkatheter|Koronarangiographie).*(?:vom|am)") or find_any_date(text)
        # Gefäße
        lad = 1 if re.search(r"LAD.*?(> ?50|signifikant|Stenose)", text, re.IGNORECASE) else 0
        lcx = 1 if re.search(r"(LCX|RCX).*?(> ?50|signifikant|Stenose)", text, re.IGNORECASE) else 0
        lm  = 1 if re.search(r"\bLM\b.*?(> ?50|signifikant|Stenose)", text, re.IGNORECASE) else 0
        rca = 1 if re.search(r"\bRCA\b.*?(> ?50|signifikant|Stenose)", text, re.IGNORECASE) else 0
        row["stenosis >50%\nLAD\nno=0\nyes=1"] = lad
        row["stenosis >/=50%\nLCX\nno=0\nyes=1"] = lcx
        row["stenosis >50%\nLM\nno=0\nyes=1"] = lm
        row["stenosis >50%\nRCA\nno=0\nyes=1"] = rca
        row["revasc\nno=0\nyes=1"] = 1 if re.search(r"PCI|Stent|Bifurkationsstent|Rotablation|Bypass", text, re.IGNORECASE) else 0
        row["Bypass\nno=0\nyes=1"] = 1 if re.search(r"Bypass|CABG|ACVB", text, re.IGNORECASE) else 0
        # Einzel-PCI Felder
        row["PCI\nLAD\nno=0\nyes=1 "] = 1 if re.search(r"PCI.*LAD|Stent.*LAD", text, re.IGNORECASE) else 0
        row["PCI\nLCX\nno=0\nyes=1 "] = 1 if re.search(r"PCI.*(LCX|RCX)|Stent.*(LCX|RCX)", text, re.IGNORECASE) else 0
        row["PCI\nLM\nno=0\nyes=1 "] = 1 if re.search(r"PCI.*\bLM\b|Stent.*\bLM\b", text, re.IGNORECASE) else 0
        row["PCI\nRCA\nno=0\nyes=1 "] = 1 if re.search(r"PCI.*\bRCA\b|Stent.*\bRCA\b", text, re.IGNORECASE) else 0

    # Follow-up (letztes Echo/klinisch) – einfache Heuristik
    if re.search(r"Verlaufskontrolle|kardiologische Kontrolle|latest follow-up", text, re.IGNORECASE):
        row["latest\nfollow-up"] = 1
        row["date of \nlatest FU"] = find_any_date(text)

    # Latest follow-up Echo (wenn zweites Echo vorkommt)
    if re.search(r"Befund Echokardiographie vom\s*\d{2}\.\d{2}\.\d{4}", text, re.IGNORECASE):
        # nimm die letzte EF im Text als „latest“
        ef_all = list(re.finditer(r"EF(?:\s*biplan)?\s*(\d{1,2})\s*%", text, re.IGNORECASE))
        if ef_all:
            row["echo\nlatest follow up"] = 1
            row["LVEF"] = to_int(ef_all[-1].group(1))  # überschreibt ggf. baseline – bei Bedarf duplizieren in UI

    return row

