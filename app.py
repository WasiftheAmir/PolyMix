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
        font-size: 3.2rem;
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
        background: #fef2f2;
        border: 1px solid #fca5a5;
        border-radius: 8px;
        padding: 8px 12px;
        color: #b91c1c;
        font-size: 0.85rem;
        font-weight: 600;
        margin-bottom: 10px;
    }

    .pm-success {
        background: #f0fdf4;
        border: 1px solid #86efac;
        border-radius: 8px;
        padding: 0px 14px;
        color: #166534;
        font-weight: 600;
        font-size: 0.9rem;
        display: flex;
        align-items: center;
        justify-content: center;
        height: 50px;
        width: 100%;
        box-sizing: border-box;
    }

    .summary-strip {
        background: #e8336d;
        border-radius: 8px;
        padding: 0px 16px;
        display: flex;
        justify-content: space-between;
        align-items: center;
        height: 50px;
        width: 100%;
        box-sizing: border-box;
    }
    .summary-strip-label { font-size: 0.72rem; color: rgba(255,255,255,0.85); line-height: 1.1; }
    .summary-strip-val { font-size: 1.05rem; font-weight: 800; color: #fff; line-height: 1.2; }

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
        border: none !important;
        border-radius: 8px !important;
        font-size: 3rem !important;
        font-weight: bold !important;
        width: 100% !important;
        height: 50px !important;
        line-height: 50px !important;
        padding: 0 !important; 
        transition: opacity 0.15s;
    }
    .stButton > button p {
        color: #ffffff !important;
        font-size: 1.25rem !important;
        font-weight: bold !important;
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

@st.cache_data(ttl=60, show_spinner=False)
def load_recent_logs():
    gc = get_gc()
    sh = gc.open_by_key(SPREADSHEET_ID)
    try:
        ws = sh.worksheet(LOG_SHEET)
        records = ws.get_all_records()
        if not records:
            return pd.DataFrame()
        df_log = pd.DataFrame(records)
        return df_log.iloc[::-1].head(10)
    except Exception:
        return pd.DataFrame()

def has_recipe(row) -> bool:
    return any(row.get(c, 0) > 0 for c in INGREDIENT_COLS)

# ── Session state ─────────────────────────────────────────────────────────────
for key, default in [
    ("selected_row", None),
    ("batch_confirmed", False),
    ("active_cols", []),
    ("current_part_code", None),
    ("pct_values", {}),
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
            st.session_state.batch_confirmed = False
            
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

# ── STEP 3 & 4: Editable Recipe Breakdown & Confirmation ──────────────────────
if st.session_state.selected_row and has_recipe(st.session_state.selected_row):
    row = st.session_state.selected_row

    st.markdown(
        '<div class="pm-card">'
        '<div class="pm-card-title">Recipe Breakdown & Logging</div>'
        '<div class="pm-card-guidance">Adjust ingredient percentages if needed (e.g., excess recycled chips, recipe tweaks). Verify totals equal 100% before confirming. <span class="pm-card-example">(Edited recipes log but do not change the masterfile)</span></div>',
        unsafe_allow_html=True
    )

    # Reset active ingredient list & percentage values when a different part is selected
    part_code = row.get("Accessories Code", "unknown")
    if st.session_state.current_part_code != part_code:
        st.session_state.current_part_code = part_code
        st.session_state.active_cols = [
            col for col in INGREDIENT_COLS
            if not isinstance(row.get(col, 0), str) and row.get(col, 0) > 0
        ]
        st.session_state.pct_values = {
            col: round(row.get(col, 0) * 100, 2) if not isinstance(row.get(col, 0), str) else 0.0
            for col in st.session_state.active_cols
        }

    active_cols = st.session_state.active_cols

    # Ensure every active column has a tracked percentage (e.g. newly added ingredients)
    for col in active_cols:
        if col not in st.session_state.pct_values:
            st.session_state.pct_values[col] = 0.0

    pct_values = st.session_state.pct_values

    # Build combined % / kg table — ingredients as columns, two rows (% and kg)
    display_data = {}
    for col in active_cols:
        display_name = col.replace(" %", "")
        pct_val = pct_values[col]
        kg_val = round((pct_val / 100.0) * batch_kg, 3)
        display_data[display_name] = [pct_val, kg_val]

    combined_df = pd.DataFrame(display_data, index=["%", "kg"])

    column_config = {
        c: st.column_config.NumberColumn(c, min_value=0, step=0.1, format="%.3f")
        for c in combined_df.columns
    }

    # Key includes a signature of current values so the widget refreshes
    # whenever percentages, batch size, or the active column set changes
    state_signature = (tuple(sorted(pct_values.items())), batch_kg, tuple(active_cols))
    editor_key = f"recipe_editor_{part_code}_{hash(state_signature)}"

    edited_df = st.data_editor(
        combined_df,
        use_container_width=True,
        column_config=column_config,
        key=editor_key
    )

    # Pull edited % values (the kg row is derived, so edits to it are ignored)
    new_pct_values = {}
    changed = False
    for col in active_cols:
        display_name = col.replace(" %", "")
        new_val = float(edited_df.loc["%", display_name])
        new_pct_values[col] = new_val
        if abs(new_val - pct_values[col]) > 1e-9:
            changed = True

    if changed:
        st.session_state.pct_values = new_pct_values
        st.rerun()

    # Calculate ingredient kg amounts from current percentages
    ingredient_kgs = {}
    edited_pcts_decimal = {}
    for col in active_cols:
        pct_val = pct_values[col] / 100.0
        edited_pcts_decimal[col] = pct_val
        ingredient_kgs[col] = round(pct_val * batch_kg, 3)

    # ── Add ingredient control ────────────────────────────────────────────────
    remaining_cols = [c for c in INGREDIENT_COLS if c not in active_cols]
    if remaining_cols:
        add_col1, add_col2 = st.columns([3, 1])
        with add_col1:
            new_ingredient = st.selectbox(
                "Add ingredient",
                [c.replace(" %", "") for c in remaining_cols],
                label_visibility="collapsed",
                key=f"add_ingredient_select_{part_code}"
            )
        with add_col2:
            if st.button("+ Add", use_container_width=True, key=f"add_ingredient_btn_{part_code}"):
                # Map display name back to actual column name
                matching_col = next(c for c in remaining_cols if c.replace(" %", "") == new_ingredient)
                st.session_state.active_cols.append(matching_col)
                st.rerun()

    # Calculate totals with edited percentages
    total_pct = sum(edited_pcts_decimal.values())
    total_kg = sum(ingredient_kgs.values())
    pct_deviation = (total_pct - 1.0) * 100

    # Warning if total doesn't equal 100%
    if abs(pct_deviation) > 0.01:
        if pct_deviation > 0:
            st.markdown(f'<div class="pm-warn">⚠ Recipe total is {total_pct*100:.1f}% — {pct_deviation:+.1f}% over target.</div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="pm-warn">⚠ Recipe total is {total_pct*100:.1f}% — {pct_deviation:.1f}% under target.</div>', unsafe_allow_html=True)

    # Action Row: Summary and Logging side by side
    bot_col1, bot_col2 = st.columns([1, 1])
    
    with bot_col1:
        st.markdown(f"""
        <div class="summary-strip">
            <div>
                <div class="summary-strip-label">Total Pct</div>
                <div class="summary-strip-val">{total_pct*100:.1f}%</div>
            </div>
            <div style="text-align:right;">
                <div class="summary-strip-label">Total Weight</div>
                <div class="summary-strip-val">{total_kg:.3f} kg</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    with bot_col2:
        if not st.session_state.batch_confirmed:
            if st.button("Confirm & Log Batch", key="action_log_trigger", use_container_width=True):
                try:
                    log_batch(row, batch_kg, ingredient_kgs)
                    st.session_state.batch_confirmed = True
                    st.rerun()
                except Exception as e:
                    st.error(f"Failed to log batch: {e}")
        else:
            ts = datetime.now().strftime("%H:%M")
            st.markdown(f'<div class="pm-success">✓ Batch logged successfully · {ts}</div>', unsafe_allow_html=True)
            if st.button("Start New Batch", use_container_width=True):
                st.session_state.batch_confirmed = False
                st.rerun()

    st.markdown('</div>', unsafe_allow_html=True)

# ── RECENT LOGS HISTORY ───────────────────────────────────────────────────────
st.markdown(
    '<div class="pm-card">'
    '<div class="pm-card-title">Recent Factory Logs (Last 10)</div>',
    unsafe_allow_html=True
)

recent_logs_df = load_recent_logs()

if not recent_logs_df.empty:
    columns_to_keep = [col for col in recent_logs_df.columns if not recent_logs_df[col].astype(str).str.strip().eq('').all()]
    st.dataframe(
        recent_logs_df[columns_to_keep],
        use_container_width=True,
        hide_index=True
    )
else:
    st.caption("No recent batch entries found in the log.")

st.markdown('</div>', unsafe_allow_html=True)
