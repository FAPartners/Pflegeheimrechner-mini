# Import necessary libraries
import streamlit as st
from decimal import Decimal, getcontext, ROUND_HALF_UP
import io

# Set precision for Decimal calculations
getcontext().prec = 10

# --- Formatting Helper ---
def format_chf(value):
    """Formats a Decimal value as CHF string without decimal places."""
    if isinstance(value, (int, float)):
        value = Decimal(str(value))
    elif not isinstance(value, Decimal):
        return "N/A"
    if not value.is_finite():
        return "Unbegrenzt"
    return f"{value.quantize(Decimal('1'), rounding=ROUND_HALF_UP):,.0f}".replace(",", "'")

# --- Simplified Calculation Functions ---
# (calculate_simple_ebitda and calculate_simple_max_investment remain unchanged)
def calculate_simple_ebitda(
    anzahl_plaetze,
    belegung_prozent,
    avg_ertrag_tag,
    avg_kosten_tag
    ):
    """Calculates a simplified EBITDA based on average daily rates."""
    plaetze_d = Decimal(str(anzahl_plaetze))
    belegung_d = Decimal(str(belegung_prozent)) / 100
    ertrag_tag_d = Decimal(str(avg_ertrag_tag))
    kosten_tag_d = Decimal(str(avg_kosten_tag))
    tage_jahr = Decimal('365')

    belegte_plaetze = plaetze_d * belegung_d

    jahresertrag = belegte_plaetze * ertrag_tag_d * tage_jahr
    jahreskosten = belegte_plaetze * kosten_tag_d * tage_jahr # Vereinfachte Kostenannahme

    ebitda = jahresertrag - jahreskosten

    return ebitda, jahresertrag

def calculate_simple_max_investment(
    ebitda,
    available_funds,
    interest_rate, # Zinssatz als Dezimal (z.B. 0.05 für 5%) - WIRD JETZT FIX ÜBERGEBEN
    depreciation_rate # Abschreibungssatz als Dezimal
    ):
    """Calculates simplified maximum investment scope."""
    ebitda_d = Decimal(str(ebitda))
    funds_d = Decimal(str(available_funds))
    zinssatz_d = Decimal(str(interest_rate)) # Nimmt den übergebenen (fixen) Wert
    abschreibungssatz_d = Decimal(str(depreciation_rate))

    denominator = zinssatz_d + abschreibungssatz_d
    if denominator == 0:
        max_verschuldung = Decimal('Infinity')
    else:
         max_verschuldung = (ebitda_d - funds_d * abschreibungssatz_d) / denominator

    max_verschuldung = max(Decimal('0'), max_verschuldung)
    investition = funds_d + max_verschuldung

    return investition

# --- Streamlit App Layout ---

st.set_page_config(layout="centered")
st.title("Schnell-Check: Investitionsrechner Pflegeheim")
st.write("Erhalten Sie eine erste, **vereinfachte** Indikation für Ihren möglichen Investitionsrahmen.")

# --- Input Sections (Hauptbereich statt Sidebar) ---
st.subheader("Ihre Eckdaten:")

col1, col2 = st.columns(2)

# <<< NEU: Layout der Inputs angepasst >>>
with col1:
    in_anzahl_pflegeplaetze = st.number_input(
        "Anzahl geplanter Pflegeplätze",
        min_value=10, max_value=500, value=80, step=1,
        key="mini_plaetze"
    )
    in_avg_ertrag_tag = st.number_input(
        "Ø Ertrag pro Pflegebett und Tag (CHF)",
        min_value=10.0, max_value=1000.0, value=250.0, step=5.0,
        key="mini_ertrag",
        help="Kombinierter Durchschnitt aus Pflegetaxen, Pensionstaxen und Betreuungstaxen pro Tag pro Bett."
    )
    # Eigenmittel jetzt hier in Spalte 1:
    in_available_funds = st.number_input(
        "Verfügbare Eigenmittel (CHF)", # Label gekürzt
        min_value=0, max_value=100_000_000, value=5_000_000, step=100_000, format="%d",
        key="mini_funds",
        help="Eigenkapital, das Sie in das Projekt einbringen können/wollen."
    )

with col2:
    in_belegung_prozent = st.slider(
        "Erwartete Auslastung (%)",
        min_value=70, max_value=100, value=96, step=1,
        key="mini_belegung"
    )
    in_avg_kosten_tag = st.number_input(
        "Ø Kosten pro Pflegebett und Tag (CHF)",
        min_value=50.0, max_value=800.0, value=200.0, step=5.0,
        key="mini_kosten",
        help="Durchschnittliche operative Kosten (Personal & Sachkosten) pro Tag pro Bett."
    )
    in_abschreibungssatz = st.number_input(
        "Jhrl. Abschreibungssatz (%)",
        min_value=0.5, max_value=10.0, value=3.0, step=0.1,
        key="mini_abschreibung",
        help="Durchschnittlicher jährlicher Abschreibungssatz auf die Investition."
    )

# <<< NEU: Divider entfernt, da Eigenmittel jetzt in den Spalten sind >>>
# st.divider()


# --- Calculation and Display ---
st.subheader("Erste Indikation:")

# Führe Berechnungen durch
ebitda_result, ertrag_result = calculate_simple_ebitda(
    in_anzahl_pflegeplaetze,
    in_belegung_prozent,
    in_avg_ertrag_tag,
    in_avg_kosten_tag
)

# Konvertiere Prozentsätze für die Funktion
zinssatz_decimal = Decimal('0.05') # Fixer kalk. Zinssatz von 5%
abschreibungssatz_decimal = Decimal(str(in_abschreibungssatz)) / 100

investition_result = calculate_simple_max_investment(
    ebitda_result,
    in_available_funds,
    zinssatz_decimal,
    abschreibungssatz_decimal
)

# Zeige Ergebnisse an
res_col1, res_col2 = st.columns(2)

with res_col1:
    st.metric(
        label="Geschätztes jährliches EBITDA",
        value=f"CHF {format_chf(ebitda_result)}"
    )

with res_col2:
    st.metric(
        label="Maximaler Investitionsrahmen (geschätzt)",
        value=f"CHF {format_chf(investition_result)}",
        help=f"Basiert auf Ihrem EBITDA, {format_chf(in_available_funds)} CHF Eigenmitteln, einem fixen kalk. Zinssatz von 5% und {in_abschreibungssatz}% Abschreibung."
    )

# --- Call to Action ---
# (Restlicher Code bleibt unverändert)
st.info(
    """
    **Hinweis:** Dies ist eine **stark vereinfachte** Schnellschätzung.

    Faktoren wie detaillierte Kostenstrukturen (fix/variabel, Personalkosten/Sachkosten), Pflegestufenmix,
    Tarifdetails, Skalierungseffekte, Finanzierung über Zeit (Planung/Bau),
    Liquiditätspuffer und Erträge aus Zusatzleistungen (z.B. Wohnen im Alter)
    werden hier **nicht** berücksichtigt. Die Berechnung des Investitionsrahmens erfolgt mit einem **fixen kalkulatorischen Zinssatz von 5%**.
    """
)

st.markdown("---")
st.subheader("Interessiert an einer detaillierten Analyse?")

st.markdown(
    """
    Unsere **persönliche Beratung** ermöglicht Ihnen:

    * Detaillierte Szenarienvergleiche (Ist-Situation vs. Neubauvarianten)
    * Berücksichtigung von fixen und variablen Kosten mit Skalierung
    * **Variable Zinssätze** für Sensitivitätsanalysen
    * Einbezug von "Wohnen im Alter" (WiA)
    * Abbildung von Planungs- und Bauphasen mit Finanzierungsbedarf
    * Detaillierte KPI-Analyse (Margen, Kostenquoten, Verschuldungsfaktor)

    **Kontaktieren Sie uns für eine unverbindliche Erstberatung!**
    """
)

st.link_button("Beratung anfragen", "https://www.finaccess.ch/kontakt")

    # Optional: Fügen Sie hier Links oder Buttons hinzu
    # z.B.: st.link_button("Mehr erfahren", "Ihre_Website.ch/vollversion")
    
st.markdown("---")

# Optional: Platzhalter für Kontaktdaten
st.markdown("**FINACCESS**")
st.markdown("Gubelstrasse 11, 6300 Zug")
st.markdown("Ansprechperson: André Hummel | E-Mail: andre.hummel@finaccess.ch")

