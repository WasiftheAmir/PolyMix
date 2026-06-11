import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="PolyMix",
    page_icon="🧪",
    layout="centered",
)

# ── Styling (Optimized for Zero-Scroll with Guidance text) ────────────────────
st.markdown("""
<style>
    html, body, [data-testid="stAppViewContainer"] {
        background-color: #ffffff;
        color: #1a1a1a;
        font-family: 'Segoe UI', sans-serif;
    }
    [data-testid="stHeader"] { background: transparent; }
    [data-testid="stSidebar"] { display: none; }
    [data-testid="block-container"] {
        padding-top: 1.2rem !important;
        padding-bottom: 1rem !important;
    }

    .pm-title {
        font-size: 1.8rem;
        font-weight: 800;
        letter-spacing: -0.5px;
        margin-bottom: 0;
    }
    .pm-subtitle {
        font-size: 0.85rem;
        color: #999;
        margin-top: 1px;
        margin-bottom: 12px;
    }

    .pm-card {
        background: #fafafa;
        border: 1px solid #ebebeb;
        border-radius: 12px;
        padding: 12px 16px;
        margin-bottom: 10px;
    }
    .pm-card-title {
        font-size: 0.72rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 1.2px;
        color: #e8336d;
        margin-bottom: 2px;
    }
    .pm-card-guidance {
        font-size: 0.78rem;
        color: #666;
        margin-bottom: 10px;
        line-height: 1.3;
    }
    .pm-card-example {
        color: #999;
        font-style: italic;
    }

    .pm-warn {
        background: #fff5f0;
        border: 1px solid #f5c0a0;
        border-radius: 8px;
        padding: 8px 12px;
        color: #c05000;
        font-size: 0.85rem;
    }

    .summary-strip {
        background: #e8336d;
        border-radius: 8px;
        padding: 8px 16px;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }
    .summary-strip-label { font-size: 0.75rem; color: rgba(255,255,255,0.8); }
    .summary-strip-val { font-size: 1.05rem; font-weight: 800; color: #fff; }

    .pm-success {
        background: #f0fdf4;
        border: 1px solid #86efac;
        border-radius: 8px;
        padding: 10px 14px;
        color: #166534;
        font-weight: 600;
        font-size: 0.9rem;
        text-align: center;
    }

    [data-testid="stTextInput"] input,
    [data-testid="stNumberInput"] input {
        background: #ffffff !important;
        border: 1px solid #ddd !important;
        color: #1a1a1a !important;
        border-radius: 8px !important;
    }
    [data-testid="stTextInput"] input:focus,
    [data-testid="stNumberInput"] input:focus {
        border-color: #e8336d !important;
        box-shadow: 0 0 0 2px rgba(232,51,109,0.12) !important;
    }

    .stButton > button {
        background: #e8336d !important;
        color: #ffffff !important;
        font-weight: 700 !important;
        border: none !important;
        border-radius: 8px !important;
        padding: 8px 20px !important;
        font-size: 0.9rem !important;
        width: 100%;
        height: 50px !important
        line-height: 50px !important
        transition: opacity 0.15s;
    }
    .stButton > button:hover { opacity: 0.88 !important; }
    .stButton > button:disabled { opacity: 0.4 !important; }

    [data-testid="stRadio"] label { color: #1a1a1a !important; font-size: 0.85rem; }
    [data-testid="stRadio"] p { color: #1a1a1a !important; }
    [data-testid="stWidgetLabel"] p { color: #1a1a1a !important; }
    label[data-testid="stWidgetLabel"] { color: #1a1a1a !important; }
    [data-testid="stMarkdownContainer"] p { color: #1a1a1a !important; }

    [data-testid="stSelectbox"] > div > div {
        background-color: #ffffff !important;
        border: 1px solid #ddd !important;
        color: #1a1a1a !important;
        border-radius: 8px !important;
    }
    [data-testid="stSelectbox"] svg { fill: #1a1a1a !important; }
    [data-testid="stSelectbox"] span { color: #1a1a1a !important; }

    [data-baseweb="popover"] ul { background-color: #ffffff !important; }
    [data-baseweb="popover"] li { background-color: #ffffff !important; color: #1a1a1a !important; }
    [data-baseweb="popover"] li:hover { background-color: #fce7ef !important; }

    [data-testid="stNumberInput"] button {
        background: #f0f0f0 !important;
        color: #1a1a1a !important;
        border: 1px solid #ddd !important;
    }

    [data-testid="block-container"] { background-color: #ffffff !important; }
    section[data-testid="stMain"] { background-color: #ffffff !important; }

    [data-testid="stDataFrame"] {
        border: 1px solid #ebebeb !important;
        border-radius: 8px !important;
        overflow: hidden;
    }

    #MainMenu, footer { visibility: hidden; }
</style>
""", unsafe_allow_html=True)

# ── Constants ─────────────────────────────────────────────────────────────────
SPREADSHEET_ID = "19vkOIuehijJoUqx0rr_Z24OMqHGsBVVHkF--2xdBkDM"
DATA_SHEET = "Sheet1"
LOG_SHEET = "Batch Log"

INGREDIENT_COLS = [
    "PPHP", "PPCP", "Chips %", "Compound %",
    "LDP", "ABS", "PC", "GPPS", "TPR", "RCP",
    "Dessicant", "Perfume MB", "Additive", "Filler", "MB"
]

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive.readonly",
]

# ── Google Sheets helpers ─────────────────────────────────────────────────────
@st.cache_resource(show_spinner=False)
def get_gc():
    creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=SCOPES)
    return gspread.authorize(creds)

@st.cache_data(ttl=120, show_spinner=False)
def load_data():
    gc = get_gc()
    sh = gc.open_by_key(SPREADSHEET_ID)
    ws = sh.worksheet(DATA_SHEET)
    records = ws.get_all_records()
    df = pd.DataFrame(records)
    for col in INGREDIENT_COLS:
        if col in df.columns:
            df[col] = df[col].astype(str).str.replace('%', '', regex=False).str.strip()
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0) / 100.0
    df["Accessories Code"] = df["Accessories Code"].astype(str).str.strip()
    df["Accessories Name"] = df["Accessories Name"].astype(str).str.strip()
    return df

def ensure_log_sheet():
    gc = get_gc()
    sh = gc.open_by_key(SPREADSHEET_ID)
    try:
        ws = sh.worksheet(LOG_SHEET)
    except gspread.exceptions.WorksheetNotFound:
        ws = sh.add_worksheet(title=LOG_SHEET, rows=1000, cols=30)
        headers = [
            "Timestamp", "Part Name", "Accessories Code",
            "Accessories Name", "Base Color", "Batch Size (kg)"
        ] + INGREDIENT_COLS
        ws.append_row(headers, value_input_option="USER_ENTERED")
    return ws

def log_batch(row_data: dict, batch_kg: float, ingredient_kgs: dict):
    ws = ensure_log_sheet()
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_row = [
        now,
        row_data.get("Name", ""),
        row_data.get("Accessories Code", ""),
        row_data.get("Accessories Name", ""),
        row_data.get("Base Color", ""),
        round(batch_kg, 3),
    ]
    for col in INGREDIENT_COLS:
        log_row.append(round(ingredient_kgs.get(col, 0), 3) if ingredient_kgs.get(col, 0) > 0 else "")
    ws.append_row(log_row, value_input_option="USER_ENTERED")

def has_recipe(row) -> bool:
    return any(row.get(c, 0) > 0 for c in INGREDIENT_COLS)

# ── Session state ─────────────────────────────────────────────────────────────
for key, default in [
    ("selected_row", None),
    ("batch_confirmed", False),
]:
    if key not in st.session_state:
        st.session_state[key] = default

# ── Header ────────────────────────────────────────────────────────────────────
st.markdown(
    '<div class="pm-title">'
    '<span style="color:#e8336d;">Poly</span>'
    '<span style="color:#1a1a1a;">Mix</span>'
    '</div>',
    unsafe_allow_html=True
)
st.markdown('<div class="pm-subtitle">ACI Premio Plastics · Batch Recipe Calculator</div>', unsafe_allow_html=True)

# ── Load data ─────────────────────────────────────────────────────────────────
with st.spinner("Loading masterfile..."):
    try:
        df = load_data()
    except Exception as e:
        st.error(f"Could not load WIP Masterfile: {e}")
        st.stop()

# ── STEP 1 & 2: Search & Configuration (Combined) ────────────────────────────
st.markdown(
    '<div class="pm-card">'
    '<div class="pm-card-title">Setup Batch</div>'
    '<div class="pm-card-guidance">Search the component masterfile by text or code, then assign your total batch target weight. <span class="pm-card-example">(e.g., Gold WD Frame 5D or 3108000537)</span></div>',
    unsafe_allow_html=True
)

col1, col2 = st.columns([1, 1])

with col1:
    search_term = st.text_input(
        "Search",
        placeholder="Search Name or Code...",
        label_visibility="collapsed",
        key="search_input"
    )
    search_mode = st.radio(
        "Search by",
        ["Name", "Code"],
        horizontal=True,
        label_visibility="collapsed"
    )

final_row = None
batch_kg = 50.0

if search_term.strip():
    term = search_term.strip().lower()
    if search_mode == "Name":
        results = df[df["Accessories Name"].str.lower().str.contains(term, na=False)].drop_duplicates(
            subset=["Accessories Code", "Accessories Name"]
        )
    else:
        results = df[df["Accessories Code"].str.lower().str.contains(term, na=False)].drop_duplicates(
            subset=["Accessories Code", "Accessories Name"]
        )

    if not results.empty:
        options = {}
        for _, r in results.iterrows():
            label = f"{r['Accessories Name']} · {r['Accessories Code']} · {r['Base Color']}"
            options[label] = r.to_dict()

        with col2:
            selected_label = st.selectbox(
                "Select accessory",
                list(options.keys()),
                label_visibility="collapsed"
            )
            final_row = options[selected_label]
            st.session_state.selected_row = final_row
            
            if has_recipe(final_row):
                batch_kg = st.number_input(
                    "Total amount (kg)",
                    min_value=0.1,
                    max_value=10000.0,
                    value=50.0,
                    step=0.5,
                    format="%.1f",
                )
            else:
                st.markdown('<div class="pm-warn">⚠ No recipe data available for this selection.</div>', unsafe_allow_html=True)
    else:
        with col2:
            st.markdown('<div class="pm-warn">⚠ No parts found. Try a different search term.</div>', unsafe_allow_html=True)
            st.session_state.selected_row = None
else:
    st.session_state.selected_row = None

st.markdown('</div>', unsafe_allow_html=True)

# ── STEP 3 & 4: Transposed Recipe Breakdown & Confirmation (Combined) ────────
if st.session_state.selected_row and has_recipe(st.session_state.selected_row):
    row = st.session_state.selected_row

    st.markdown(
        '<div class="pm-card">'
        '<div class="pm-card-title">Recipe Breakdown & Logging</div>'
        '<div class="pm-card-guidance">Weigh ingredients precisely as shown below. Verify totals before recording the run. <span class="pm-card-example">(e.g., Ensure Total Weight matches target batch size)</span></div>',
        unsafe_allow_html=True
    )

    # Building Transposed Structure
    columns = ["Metric"]
    pct_row = ["%"]
    kg_row = ["Amount (kg)"]
    ingredient_kgs = {}

    for col in INGREDIENT_COLS:
        pct = row.get(col, 0)
        if isinstance(pct, str):
            pct = 0
        if pct > 0:
            kg = round(pct * batch_kg, 3)
            ingredient_kgs[col] = kg
            columns.append(col.replace(" %", ""))
            pct_row.append(f"{pct*100:.1f}%")
            kg_row.append(f"{kg:.3f}")

    total_pct = sum(row.get(c, 0) for c in INGREDIENT_COLS if isinstance(row.get(c, 0), float) and row.get(c, 0) > 0)
    total_kg = sum(ingredient_kgs.values())

    transposed_df = pd.DataFrame([pct_row, kg_row], columns=columns)
    
    st.dataframe(
        transposed_df,
        use_container_width=True,
        hide_index=True,
    )

    if abs(total_pct - 1.0) > 0.02:
        st.markdown(f'<div class="pm-warn" style="margin-top:6px; margin-bottom:6px;">⚠ Recipe total is {total_pct*100:.1f}% — does not add up to 100%.</div>', unsafe_allow_html=True)

    # Action Row: Summary and Logging side by side
    bot_col1, bot_col2 = st.columns([1, 1])
    
    with bot_col1:
        st.markdown(f"""
        <div class="summary-strip" style="margin-top:0px;">
            <div>
                <div class="summary-strip-label">Total Pct</div>
                <div class="summary-strip-val" style="font-size:1.05rem;">{total_pct*100:.1f}%</div>
            </div>
            <div style="text-align:right;">
                <div class="summary-strip-label">Total Weight</div>
                <div class="summary-strip-val" style="font-size:1.05rem;">{total_kg:.3f} kg</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    with bot_col2:
        if not st.session_state.batch_confirmed:
            if st.button("✓ Confirm & Log Batch"):
                try:
                    log_batch(row, batch_kg, ingredient_kgs)
                    st.session_state.batch_confirmed = True
                    st.rerun()
                except Exception as e:
                    st.error(f"Failed to log batch: {e}")
        else:
            ts = datetime.now().strftime("%H:%M")
            st.markdown(f'<div class="pm-success" style="padding: 8px 12px;">✓ Batch logged successfully · {ts}</div>', unsafe_allow_html=True)
            if st.button("Start New Batch"):
                st.session_state.batch_confirmed = False
                st.rerun()

    st.markdown('</div>', unsafe_allow_html=True)
