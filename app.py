import streamlit as st
import pandas as pd
from parser import parse_report

st.set_page_config(page_title="Echo Extractor — Paste & Parse", layout="wide")
st.title("🫀 Echo Extractor — Paste & Parse")

# Session-DF initialisieren
if "df" not in st.session_state:
    st.session_state.df = pd.DataFrame()

with st.sidebar:
    st.header("⚙️ Optionen")
    overwrite = st.checkbox("Vorhandene Zellen überschreiben", value=False)
    st.caption("Wenn aus: nur leere Zellen werden befüllt.")

st.subheader("1) Arztbrief/Freitext hier einfügen")
text = st.text_area(
    "Text hier einfügen (mehrere Dokumente sind ok)",
    height=300,
    placeholder="Füge hier den Arztbrief / Echo-/Stress-Echo-/Follow-up-Text ein …",
)

col_a, col_b = st.columns([1,1])
with col_a:
    if st.button("🔎 Analysieren & einfügen", use_container_width=True):
        if not text.strip():
            st.warning("Bitte zuerst Text einfügen.")
        else:
            parsed = parse_report(text)

            # in bestehende Tabelle einfügen (Upsert)
            key = f"{parsed.get('surname','')}|{parsed.get('first name','')}|{parsed.get('DOB','')}"
            if key.strip("|") == "":
                # Fallback-Key, falls Name/DOB nicht erkannt
                key = f"row_{len(st.session_state.df)+1}"
            if key in st.session_state.df.index:
                for col, val in parsed.items():
                    if overwrite or pd.isna(st.session_state.df.loc[key, col]) or st.session_state.df.loc[key, col] == "":
                        st.session_state.df.loc[key, col] = val
            else:
                row = pd.DataFrame([parsed])
                row.index = [key]
                st.session_state.df = pd.concat([st.session_state.df, row], axis=0)
            st.success("✅ Eingefügt")

with col_b:
    if st.button("🧹 Tabelle leeren", use_container_width=True):
        st.session_state.df = pd.DataFrame()
        st.info("Tabelle geleert.")

st.subheader("2) Ergebnis-Tabelle (editierbar)")
st.caption("Du kannst hier manuell korrigieren. Mit dem Download-Button exportierst du alles als CSV.")
st.dataframe(st.session_state.df, use_container_width=True)

st.download_button(
    "⬇️ Download CSV",
    st.session_state.df.to_csv(index=False).encode("utf-8"),
    file_name="echo_dataset.csv",
    mime="text/csv"
)

st.divider()
st.caption("Tipp: Du kannst beliebig viele Texte hintereinander einfügen und jeweils auf **Analysieren & einfügen** klicken.")