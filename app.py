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

# ── Styling ───────────────────────────────────────────────────────────────────
st.markdown("""
<style>
    html, body, [data-testid="stAppViewContainer"] {
        background-color: #ffffff;
        color: #1a1a1a;
        font-family: 'Segoe UI', sans-serif;
    }
    [data-testid="stHeader"] { background: transparent; }
    [data-testid="stSidebar"] { display: none; }

    .pm-title {
        font-size: 2.2rem;
        font-weight: 800;
        letter-spacing: -0.5px;
        margin-bottom: 0;
    }
    .pm-subtitle {
        font-size: 0.9rem;
        color: #999;
        margin-top: 2px;
        margin-bottom: 28px;
    }

    .pm-card {
        background: #fafafa;
        border: 1px solid #ebebeb;
        border-radius: 12px;
        padding: 20px 24px;
        margin-bottom: 18px;
    }
    .pm-card-title {
        font-size: 0.75rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 1.2px;
        color: #e8336d;
        margin-bottom: 14px;
    }

    .pm-warn {
        background: #fff5f0;
        border: 1px solid #f5c0a0;
        border-radius: 8px;
        padding: 12px 16px;
        color: #c05000;
        font-size: 0.88rem;
    }

    .summary-strip {
        background: #e8336d;
        border-radius: 8px;
        padding: 14px 20px;
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-top: 6px;
    }
    .summary-strip-label { font-size: 0.8rem; color: rgba(255,255,255,0.8); }
    .summary-strip-val { font-size: 1.2rem; font-weight: 800; color: #fff; }

    .pm-success {
        background: #f0fdf4;
        border: 1px solid #86efac;
        border-radius: 8px;
        padding: 14px 18px;
        color: #166534;
        font-weight: 600;
        font-size: 0.95rem;
        text-align: center;
    }

    hr { border-color: #ebebeb; margin: 20px 0; }

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
        color: #fff !important;
        font-weight: 700 !important;
        border: none !important;
        border-radius: 8px !important;
        padding: 10px 24px !important;
        font-size: 0.95rem !important;
        width: 100%;
        transition: opacity 0.15s;
    }
    .stButton > button:hover { opacity: 0.88 !important; }
    .stButton > button:disabled { opacity: 0.4 !important; }

    /* Radio buttons — label text and option text */
    [data-testid="stRadio"] label { color: #1a1a1a !important; font-size: 0.88rem; }
    [data-testid="stRadio"] p { color: #1a1a1a !important; }

    /* All widget labels (number input, text input descriptions) */
    [data-testid="stWidgetLabel"] p { color: #1a1a1a !important; }
    label[data-testid="stWidgetLabel"] { color: #1a1a1a !important; }

    /* General paragraph and markdown text */
    [data-testid="stMarkdownContainer"] p { color: #1a1a1a !important; }

    /* Selectbox — white background, dark text */
    [data-testid="stSelectbox"] > div > div {
        background-color: #ffffff !important;
        border: 1px solid #ddd !important;
        color: #1a1a1a !important;
        border-radius: 8px !important;
    }
    [data-testid="stSelectbox"] svg { fill: #1a1a1a !important; }
    [data-testid="stSelectbox"] span { color: #1a1a1a !important; }

    /* Selectbox dropdown list */
    [data-baseweb="popover"] ul {
        background-color: #ffffff !important;
    }
    [data-baseweb="popover"] li {
        background-color: #ffffff !important;
        color: #1a1a1a !important;
    }
    [data-baseweb="popover"] li:hover {
        background-color: #fce7ef !important;
    }

    /* Number input +/- buttons */
    [data-testid="stNumberInput"] button {
        background: #f0f0f0 !important;
        color: #1a1a1a !important;
        border: 1px solid #ddd !important;
    }

    /* Main block background */
    [data-testid="block-container"] {
        background-color: #ffffff !important;
    }
    section[data-testid="stMain"] {
        background-color: #ffffff !important;
    }

    /* Style the dataframe to match */
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

# ── STEP 1: Search ────────────────────────────────────────────────────────────
st.markdown('<div class="pm-card"><div class="pm-card-title">Step 1 — Find Part</div>', unsafe_allow_html=True)
st.caption("Search by Accessories Name (e.g. 'Gold WD Frame 5D') or switch to Code and enter an accessories code (e.g. '3108000537'). Select the matching part from the results.")

col1, col2 = st.columns([2, 1])
with col1:
    search_term = st.text_input(
        "Search",
        placeholder="e.g. Gold WD Frame 5D  or  3108000537",
        label_visibility="collapsed",
        key="search_input"
    )
with col2:
    search_mode = st.radio(
        "Search by",
        ["Name", "Code"],
        horizontal=True,
        label_visibility="collapsed"
    )

st.markdown('</div>', unsafe_allow_html=True)

# ── Results ───────────────────────────────────────────────────────────────────
results = pd.DataFrame()
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
    st.markdown(f'<div style="font-size:0.8rem;color:#999;margin-bottom:8px;">{len(results)} result(s) found</div>', unsafe_allow_html=True)

    options = {}
    for _, r in results.iterrows():
        label = f"{r['Accessories Name']}  ·  {r['Accessories Code']}  ·  {r['Base Color']}"
        options[label] = r.to_dict()

    selected_label = st.selectbox(
        "Select accessory",
        list(options.keys()),
        label_visibility="collapsed"
    )
    selected_row = options[selected_label]

    parts_for_accessory = df[df["Accessories Code"] == str(selected_row["Accessories Code"])]

    if len(parts_for_accessory) > 1:
        st.markdown('<div style="font-size:0.8rem;color:#777;margin:10px 0 6px;">Multiple WIP parts use this accessory — select the specific part:</div>', unsafe_allow_html=True)
        part_options = {}
        for _, r in parts_for_accessory.iterrows():
            lbl = f"{r['Name']}  (Code {r['Code']})"
            part_options[lbl] = r.to_dict()
        selected_part_label = st.selectbox("Select part", list(part_options.keys()), label_visibility="collapsed")
        final_row = part_options[selected_part_label]
    else:
        final_row = parts_for_accessory.iloc[0].to_dict()

    st.session_state.selected_row = final_row
    st.session_state.batch_confirmed = False

elif search_term.strip():
    st.markdown('<div class="pm-warn">⚠ No parts found. Try a different search term.</div>', unsafe_allow_html=True)

# ── STEP 2: Batch size ────────────────────────────────────────────────────────
if st.session_state.selected_row:
    row = st.session_state.selected_row

    st.markdown("---")
    st.markdown('<div class="pm-card"><div class="pm-card-title">Step 2 — Batch Size</div>', unsafe_allow_html=True)
    st.caption("Enter the total weight of the mixture you want to prepare in kg. The ingredient amounts will be calculated automatically.")

    st.markdown(f"""
    <div style="margin-bottom:14px;">
        <div style="font-size:1.05rem;font-weight:700;color:#1a1a1a;">{row.get('Accessories Name','')}</div>
        <div style="font-size:0.82rem;color:#999;margin-top:3px;">
            Code: <span style="color:#555;">{row.get('Accessories Code','')}</span> &nbsp;·&nbsp;
            Color: <span style="color:#555;">{row.get('Base Color','')}</span> &nbsp;·&nbsp;
            WIP: <span style="color:#555;">{row.get('Name','')}</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    if not has_recipe(row):
        st.markdown('<div class="pm-warn">⚠ No recipe data available for this part. Please update the WIP Masterfile.</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
    else:
        batch_kg = st.number_input(
            "Total mixture amount (kg)",
            min_value=0.1,
            max_value=10000.0,
            value=50.0,
            step=0.5,
            format="%.1f",
        )
        st.markdown('</div>', unsafe_allow_html=True)

        # ── STEP 3: Ingredient breakdown ──────────────────────────────────────
        st.markdown("---")
        st.markdown('<div class="pm-card"><div class="pm-card-title">Step 3 — Ingredient Breakdown</div>', unsafe_allow_html=True)
        st.caption("Exact amounts for each ingredient based on the recipe percentages and your batch size. Add each ingredient to the mixer in the amounts shown.")

        ingredient_kgs = {}
        table_rows = []
        for col in INGREDIENT_COLS:
            pct = row.get(col, 0)
            if isinstance(pct, str):
                pct = 0
            if pct > 0:
                kg = round(pct * batch_kg, 3)
                ingredient_kgs[col] = kg
                display_name = col.replace(" %", "")
                table_rows.append({
                    "Ingredient": display_name,
                    "%": f"{pct*100:.1f}%",
                    "Amount (kg)": f"{kg:.3f}",
                })

        total_pct = sum(row.get(c, 0) for c in INGREDIENT_COLS if isinstance(row.get(c, 0), float) and row.get(c, 0) > 0)
        total_kg = sum(ingredient_kgs.values())

        table_df = pd.DataFrame(table_rows)
        st.dataframe(
            table_df,
            use_container_width=True,
            hide_index=True,
        )

        st.markdown(f"""
        <div class="summary-strip">
            <div>
                <div class="summary-strip-label">Total Percentage</div>
                <div class="summary-strip-val">{total_pct*100:.1f}%</div>
            </div>
            <div style="text-align:right;">
                <div class="summary-strip-label">Total Weight</div>
                <div class="summary-strip-val">{total_kg:.3f} kg</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        if abs(total_pct - 1.0) > 0.02:
            st.markdown(f'<div class="pm-warn" style="margin-top:10px;">⚠ Recipe total is {total_pct*100:.1f}% — does not add up to 100%. Check the Masterfile.</div>', unsafe_allow_html=True)

        st.markdown('</div>', unsafe_allow_html=True)

        # ── STEP 4: Confirm & Log ─────────────────────────────────────────────
        st.markdown("---")
        st.markdown('<div class="pm-card"><div class="pm-card-title">Step 4 — Confirm Batch</div>', unsafe_allow_html=True)
        st.caption("Once you have prepared the batch using the amounts above, press Confirm to log it to the Batch Log sheet with a timestamp.")

        if not st.session_state.batch_confirmed:
            if st.button("✓ Confirm & Log Batch"):
                try:
                    with st.spinner("Logging batch..."):
                        log_batch(row, batch_kg, ingredient_kgs)
                    st.session_state.batch_confirmed = True
                    st.rerun()
                except Exception as e:
                    st.error(f"Failed to log batch: {e}")
        else:
            ts = datetime.now().strftime("%d %b %Y, %H:%M")
            st.markdown(f'<div class="pm-success">✓ Batch logged successfully · {ts}</div>', unsafe_allow_html=True)
            if st.button("Start New Batch"):
                st.session_state.selected_row = None
                st.session_state.batch_confirmed = False
                st.rerun()

        st.markdown('</div>', unsafe_allow_html=True)
