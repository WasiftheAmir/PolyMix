import streamlit as st
import pandas as pd
import gspread
import re
import humanize
import json
from streamlit_javascript import st_javascript
from google.oauth2.service_account import Credentials
from rapidfuzz import process
from datetime import datetime, timezone, timedelta
# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="PolyMix",
    page_icon="🧪",
    layout="centered",
)

# ── Dark mode must be read BEFORE CSS is rendered ────────────────────────────
# ── LocalStorage Initialization ──────────────────────────────────────────────
js_data = st_javascript("JSON.stringify({dark_mode: localStorage.getItem('pm_dark_mode') || 'false', search: localStorage.getItem('pm_search') || '', batch_kg: localStorage.getItem('pm_batch_kg') || ''})")

if js_data and js_data != 0:
    if not st.session_state.get("storage_synced", False):
        try:
            data = json.loads(js_data)
            is_dark = data.get("dark_mode") == "true"
            st.session_state.dark_mode = is_dark
            st.session_state.dark_mode_checkbox = is_dark
            if data.get("search"): st.session_state.search_input = data.get("search")
            if data.get("batch_kg"): st.session_state.batch_kg = float(data.get("batch_kg"))
        except Exception:
            pass
        st.session_state.storage_synced = True

if "dark_mode" not in st.session_state:
    st.session_state.dark_mode = False

st.session_state.setdefault("batch_kg", 50.0)

_dark = st.session_state.dark_mode

# ── Color Palette ─────────────────────────────────────────────────────────────
THEME = {
    "brand_hue": "335",
    "brand_saturation": "85%",
    "text_hue": "360",
    "text_saturation": "35%",
    "warn_bg":       "#fff1f2",
    "warn_border":   "#fecdd3",
    "warn_text":     "#9f1239",
    "success_bg":    "#f0fdf4",
    "success_border":"#bbf7d0",
    "success_text":  "#166534",
}

bg_app        = "#0d0d0d" if _dark else "#ffffff"
bg_card       = "#1a1a1a" if _dark else "#ffffff"
bg_neutral    = "#2a2a2a" if _dark else "#f0f0f0"
text_lightness = "90%"    if _dark else "11%"
border_l      = "20%"     if _dark else "90%"
border_input_l= "25%"     if _dark else "85%"

# ── Styling ───────────────────────────────────────────────────────────────────
st.markdown(f"""
<style>
    :root {{
        --accent:          hsl({THEME["brand_hue"]}, {THEME["brand_saturation"]}, 45%);
        --accent-disabled: hsl({THEME["brand_hue"]}, {THEME["brand_saturation"]}, {"65%" if _dark else "85%"});
        --accent-light:    hsl({THEME["brand_hue"]}, {THEME["brand_saturation"]}, {"20%" if _dark else "94%"});
        --accent-glow:     hsla({THEME["brand_hue"]}, {THEME["brand_saturation"]}, 45%, 0.15);
        --border:          hsl({THEME["brand_hue"]}, 40%, {border_l});
        --border-input:    hsl({THEME["brand_hue"]}, 50%, {border_input_l});
        --bg-primary:      {bg_app};
        --bg-card:         {bg_card};
        --bg-neutral:      {bg_neutral};
        --text-main:       hsl({THEME["text_hue"]}, {THEME["text_saturation"]}, {text_lightness});
        --text-guidance:   hsl({THEME["text_hue"]}, {THEME["text_saturation"]}, {"65%" if _dark else "45%"});
        --text-muted:      hsl({THEME["text_hue"]}, 15%, {"50%" if _dark else "60%"});
        --warn-bg:         {THEME["warn_bg"]};
        --warn-border:     {THEME["warn_border"]};
        --warn-text:       {THEME["warn_text"]};
        --success-bg:      {THEME["success_bg"]};
        --success-border:  {THEME["success_border"]};
        --success-text:    {THEME["success_text"]};
        --accent-hover-opacity: 0.85;
    }}

    html, body, [data-testid="stAppViewContainer"] {{
        background-color: var(--bg-primary);
        color: var(--text-main);
        font-family: 'Segoe UI', sans-serif;
    }}
    [data-testid="stHeader"] {{ background: transparent; pointer-events: none; }}
    [data-testid="stSidebar"] {{ display: none; }}
    [data-testid="block-container"] {{
        padding-top: 1.2rem !important;
        padding-bottom: 1rem !important;
        background-color: var(--bg-primary) !important;
    }}
    section[data-testid="stMain"] {{ background-color: var(--bg-primary) !important; }}

    .pm-title {{
        font-size: 3.2rem;
        font-weight: 800;
        letter-spacing: -0.5px;
        margin-bottom: 0;
        line-height: 1;
    }}
    .pm-subtitle {{
        font-size: 0.85rem;
        color: var(--text-muted);
        margin-top: 1px;
        margin-bottom: 12px;
    }}
    .pm-card {{
        background: var(--bg-card);
        border: 1px solid var(--border);
        border-radius: 12px;
        padding: 12px 16px;
        margin-bottom: 10px;
    }}
    .pm-card-title {{
        font-size: 0.72rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 1.2px;
        color: var(--accent);
        margin-bottom: 2px;
    }}
    .pm-card-guidance {{
        font-size: 0.78rem;
        color: var(--text-guidance);
        margin-bottom: 10px;
        line-height: 1.3;
    }}
    .pm-card-example {{ color: var(--text-muted); font-style: italic; }}

    .pm-warn {{
        background: var(--warn-bg);
        border: 1px solid var(--warn-border);
        border-radius: 8px;
        padding: 8px 12px;
        color: var(--warn-text);
        font-size: 0.85rem;
        font-weight: 600;
        margin-bottom: 10px;
    }}
    .pm-success {{
        background: var(--success-bg);
        border: 1px solid var(--success-border);
        border-radius: 8px;
        padding: 0px 14px;
        color: var(--success-text);
        font-weight: 600;
        font-size: 0.9rem;
        display: flex;
        align-items: center;
        justify-content: center;
        height: 50px;
        width: 100%;
        box-sizing: border-box;
    }}
    .summary-strip {{
        background: var(--accent);
        border-radius: 8px;
        padding: 0px 16px;
        display: flex;
        justify-content: space-between;
        align-items: center;
        height: 50px;
        width: 100%;
        box-sizing: border-box;
    }}
    .summary-strip-label {{ font-size: 0.72rem; color: rgba(255,255,255,0.85); line-height: 1.1; }}
    .summary-strip-val   {{ font-size: 1.05rem; font-weight: 800; color: #fff; line-height: 1.2; }}


    [data-testid="stTextInput"] input,
    [data-testid="stNumberInput"] input {{
        background: var(--bg-card) !important;
        border: 1px solid var(--border-input) !important;
        color: var(--text-main) !important;
        border-radius: 8px !important;
    }}
    [data-testid="stTextInput"] input:focus,
    [data-testid="stNumberInput"] input:focus {{
        border-color: var(--accent) !important;
        box-shadow: 0 0 0 2px var(--accent-glow) !important;
    }}

    .stButton > button {{
        background: var(--accent) !important;
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
    }}
    .stButton > button p {{
        color: #ffffff !important;
        font-size: 1.25rem !important;
        font-weight: bold !important;
    }}
    .stButton > button:hover {{ opacity: var(--accent-hover-opacity) !important; }}
    .stButton > button:disabled,
    .stButton > button[disabled] {{
        background: var(--accent-disabled) !important;
        color: #ffffff !important;
        opacity: 1 !important;
        cursor: not-allowed !important;
    }}
    .stButton > button:disabled p,
    .stButton > button[disabled] p {{ color: #ffffff !important; }}

    [data-testid="stRadio"] label    {{ color: var(--text-main) !important; font-size: 0.85rem; }}
    [data-testid="stRadio"] p        {{ color: var(--text-main) !important; }}
    [data-testid="stWidgetLabel"] p  {{ color: var(--text-main) !important; }}
    label[data-testid="stWidgetLabel"] {{ color: var(--text-main) !important; }}
    [data-testid="stMarkdownContainer"] p {{ color: var(--text-main) !important; }}

    [data-testid="stSelectbox"] > div > div {{
        background-color: var(--bg-card) !important;
        border: 1px solid var(--border-input) !important;
        color: var(--text-main) !important;
        border-radius: 8px !important;
    }}
    [data-testid="stSelectbox"] svg  {{ fill: var(--text-main) !important; }}
    [data-testid="stSelectbox"] span {{ color: var(--text-main) !important; }}

    [data-baseweb="popover"] ul {{ background-color: var(--bg-card) !important; }}
    [data-baseweb="popover"] li {{
        background-color: var(--bg-card) !important;
        color: var(--text-main) !important;
    }}
    [data-baseweb="popover"] li:hover {{ background-color: var(--accent-light) !important; }}

    [data-testid="stNumberInput"] button {{
        background: var(--bg-neutral) !important;
        color: var(--text-main) !important;
        border: 1px solid var(--border-input) !important;
    }}

    [data-testid="stDataFrame"] {{
        border: 1px solid var(--border) !important;
        border-radius: 8px !important;
        overflow: hidden;
    }}

    #MainMenu, footer {{ visibility: hidden; }}

    @media (max-width: 768px) {{
        .pm-title {{ font-size: 2.2rem !important; }}
        [data-testid="block-container"] {{
            padding-left: 0.5rem !important;
            padding-right: 0.5rem !important;
        }}
        [data-testid="column"] {{
            width: 100% !important;
            flex: 1 1 100% !important;
            margin-bottom: 10px !important;
        }}
        .stButton > button {{ height: 45px !important; line-height: 45px !important; }}
        .stButton > button p {{ font-size: 1.1rem !important; }}
        .summary-strip {{ height: 45px !important; margin-bottom: 10px !important; }}
    }}
</style>
""", unsafe_allow_html=True)

# ── Constants ─────────────────────────────────────────────────────────────────
SPREADSHEET_ID = "19vkOIuehijJoUqx0rr_Z24OMqHGsBVVHkF--2xdBkDM"
DATA_SHEET     = "Sheet1"
BD_TZ          = timezone(timedelta(hours=6))

FACTORY_OPTIONS = {
    "Narayanganj (NG)": "Batch Log — NG",
    "N Poly":           "Batch Log — NPoly",
}

INGREDIENT_COLS = [
    "PPHP", "PPCP", "Chips %", "Compound %",
    "LDP", "ABS", "PC", "GPPS", "TPR", "RCP",
    "Dessicant", "Perfume MB", "Additive", "Filler", "MB"
]

LOG_HEADERS = [
    "Timestamp", "Factory", "Part Name", "Accessories Code",
    "Accessories Name", "Base Color", "Batch Size (kg)"
] + INGREDIENT_COLS

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
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

@st.cache_data(ttl=120, show_spinner=False)
def get_vocabulary_pool(df):
    vocab = set()
    for name in df["Accessories Name"].dropna():
        clean_name = re.sub(r'[^\w\s]', ' ', str(name).lower())
        for word in clean_name.split():
            if word:
                vocab.add(word)
    return list(vocab)

def ensure_log_sheet(log_sheet_name):
    gc = get_gc()
    sh = gc.open_by_key(SPREADSHEET_ID)
    try:
        ws = sh.worksheet(log_sheet_name)
    except gspread.exceptions.WorksheetNotFound:
        ws = sh.add_worksheet(title=log_sheet_name, rows=1000, cols=35)
        ws.append_row(LOG_HEADERS, value_input_option="USER_ENTERED")
    return ws

def log_batch(row_data, batch_kg, ingredient_kgs, factory_label, log_sheet_name):
    ws  = ensure_log_sheet(log_sheet_name)
    now = datetime.now(BD_TZ).strftime("%Y-%m-%d %H:%M:%S")
    log_row = [
        now, factory_label,
        row_data.get("Name", ""),
        row_data.get("Accessories Code", ""),
        row_data.get("Accessories Name", ""),
        row_data.get("Base Color", ""),
        round(batch_kg, 3),
    ]
    for col in INGREDIENT_COLS:
        log_row.append(round(ingredient_kgs.get(col, 0), 3) if ingredient_kgs.get(col, 0) > 0 else "")
    ws.append_row(log_row, value_input_option="USER_ENTERED")

@st.cache_data(ttl=30, show_spinner=False)
def load_recent_logs(log_sheet_name: str):
    gc = get_gc()
    sh = gc.open_by_key(SPREADSHEET_ID)
    try:
        ws      = sh.worksheet(log_sheet_name)
        records = ws.get_all_records()
        if not records:
            return pd.DataFrame()
        return pd.DataFrame(records).iloc[::-1].head(10).reset_index(drop=True)
    except Exception:
        return pd.DataFrame()

def delete_log_row(log_sheet_name, timestamp, accessories_code, batch_size):
    gc        = get_gc()
    sh        = gc.open_by_key(SPREADSHEET_ID)
    ws        = sh.worksheet(log_sheet_name)
    all_rows  = ws.get_all_values()
    if not all_rows:
        return False
    headers = all_rows[0]
    try:
        ts_col   = headers.index("Timestamp")
        code_col = headers.index("Accessories Code")
        kg_col   = headers.index("Batch Size (kg)")
    except ValueError:
        return False
    for i, row in enumerate(all_rows[1:], start=2):
        if (len(row) > max(ts_col, code_col, kg_col) and
            row[ts_col].strip()      == str(timestamp).strip() and
            row[code_col].strip()    == str(accessories_code).strip() and
            str(row[kg_col]).strip() == str(batch_size).strip()):
            ws.delete_rows(i)
            return True
    return False

def has_recipe(row):
    return any(row.get(c, 0) > 0 for c in INGREDIENT_COLS)

# ── Session state ─────────────────────────────────────────────────────────────
for key, default in [
    ("selected_row",      None),
    ("batch_confirmed",   False),
    ("active_cols",       []),
    ("current_part_code", None),
    ("pct_values",        {}),
    ("factory",           "Narayanganj (NG)"),
    ("pending_delete",    None),
    ("dark_mode",         False),
]:
    if key not in st.session_state:
        st.session_state[key] = default

# ── Header ────────────────────────────────────────────────────────────────────
# Title rendered full-width; toggle fixed to viewport top-right.
st.markdown(
    '<div class="pm-title">'
    '<span style="color:var(--accent);">Poly</span>'
    '<span style="color:var(--text-main);">Mix</span>'
    '</div>',
    unsafe_allow_html=True
)

st.markdown(f"""
<style>
/* Fix toggle to the top-left of the viewport — avoids Streamlit's deploy button */
div[data-testid="stCheckbox"] {{
    position: fixed;
    top: 1.2rem;
    left: 1.5rem;
    z-index: 99999999;
    margin: 0 !important;
    padding: 0 !important;
    pointer-events: auto !important;
}}
div[data-testid="stCheckbox"] label {{
    display: flex;
    align-items: center;
    cursor: pointer;
    margin: 0;
    padding: 0;
}}
/* Toggle track */
div[data-testid="stCheckbox"] label span:first-child {{
    display: inline-block;
    width: 51px;
    height: 31px;
    border-radius: 999px;
    background: {"#e8336d" if _dark else "#e5e7eb"};
    position: relative;
    transition: background 0.25s ease;
    flex-shrink: 0;
}}
div[data-testid="stCheckbox"] input[type="checkbox"] {{
    display: none;
}}
/* Knob */
div[data-testid="stCheckbox"] label span:first-child::after {{
    content: '';
    position: absolute;
    top: 3px;
    left: {"23px" if _dark else "3px"};
    width: 25px;
    height: 25px;
    border-radius: 50%;
    background: white;
    box-shadow: 0 2px 4px rgba(0,0,0,0.25);
    transition: left 0.25s ease;
}}
/* Hide label text */
div[data-testid="stCheckbox"] label p {{
    display: none !important;
}}
</style>
""", unsafe_allow_html=True)

def toggle_dark():
    st.session_state.dark_mode = st.session_state.dark_mode_checkbox

st.checkbox(
    "dark",
    key="dark_mode_checkbox",
    label_visibility="collapsed",
    on_change=toggle_dark
)


st.markdown(
    '<div class="pm-subtitle">ACI Premio Plastics · Batch Recipe Calculator · '
    '<span style="opacity:0.45;">developed by Wasif Amir</span></div>',
    unsafe_allow_html=True
)

# ── Factory selector ──────────────────────────────────────────────────────────
loc_col1, loc_col2 = st.columns([3, 1])
with loc_col1:
    selected_factory = st.radio(
        "Factory", list(FACTORY_OPTIONS.keys()),
        horizontal=True, label_visibility="collapsed", key="factory_radio"
    )
with loc_col2:
    st.markdown(
        f'<div style="font-size:0.78rem;color:var(--text-muted);padding-top:8px;">'
        f'Logging to: <strong style="color:var(--accent);">{FACTORY_OPTIONS[selected_factory]}</strong></div>',
        unsafe_allow_html=True
    )

if selected_factory != st.session_state.factory:
    st.session_state.factory        = selected_factory
    st.session_state.batch_confirmed = False
    st.session_state.pending_delete  = None
    load_recent_logs.clear()

st.markdown("<hr style='margin:8px 0 14px;border-color:var(--border);'>", unsafe_allow_html=True)
ACTIVE_LOG_SHEET = FACTORY_OPTIONS[selected_factory]

# ── Load masterfile ───────────────────────────────────────────────────────────
with st.spinner("Loading masterfile..."):
    try:
        df = load_data()
    except Exception as e:
        st.error(f"Could not load WIP Masterfile: {e}")
        st.stop()

# ── SETUP BATCH ───────────────────────────────────────────────────────────────
st.markdown(
    '<div class="pm-card">'
    '<div class="pm-card-title">Setup Batch</div>'
    '<div class="pm-card-guidance">'
    'Type one or more keywords to search accessories — all words must match (any order). '
    'Switch to Code to search by part number. '
    '<span class="pm-card-example">(e.g. "drawer white" matches "White Wardrobe Drawer")</span>'
    '</div>',
    unsafe_allow_html=True
)

col1, col2 = st.columns([1, 1])
with col1:
    search_term = st.text_input(
        "Search", placeholder="e.g. drawer white  or  3108000537",
        label_visibility="collapsed", key="search_input"
    )
    search_mode = st.radio(
        "Search by", ["Name", "Code"],
        horizontal=True, label_visibility="collapsed"
    )

batch_kg = st.session_state.batch_kg

if search_term.strip():
    if search_mode == "Name":
        vocab_pool = get_vocabulary_pool(df)
        
        # Split into tokens, filter empty strings from extra spaces
        raw_tokens = [t for t in search_term.strip().lower().split() if t]

        corrected_tokens = []
        for token in raw_tokens:
            if token in vocab_pool:
                corrected_tokens.append(token)
            else:
                match = process.extractOne(token, vocab_pool, score_cutoff=75)
                if match:
                    corrected_tokens.append(match[0])
                else:
                    corrected_tokens.append(token)

        # AND filter: every token must appear somewhere in Accessories Name
        mask = pd.Series([True] * len(df), index=df.index)
        for token in corrected_tokens:
            mask &= df["Accessories Name"].str.lower().str.contains(token, na=False)

        results = df[mask].drop_duplicates(subset=["Accessories Code", "Accessories Name"])

        if not results.empty:
            options = {
                f"{r['Accessories Name']} · {r['Accessories Code']} · {r['Base Color']}": r.to_dict()
                for _, r in results.iterrows()
            }
            with col2:
                selected_label = st.selectbox(
                    "Part", list(options.keys()), label_visibility="collapsed",
                    key="name_result_selectbox"
                )
                final_row = options[selected_label]
                st.session_state.selected_row = final_row
                if has_recipe(final_row):
                    batch_kg = st.number_input(
                        "Total amount (kg)", min_value=0.1, max_value=10000.0,
                        step=0.5, format="%.1f", key="batch_kg"
                    )
                else:
                    st.markdown('<div class="pm-warn">⚠ No recipe data for this part.</div>', unsafe_allow_html=True)
        else:
            with col2:
                st.markdown('<div class="pm-warn">⚠ No parts found. Try different keywords.</div>', unsafe_allow_html=True)
            st.session_state.selected_row      = None
            st.session_state.current_part_code = None

    else:  # Code search
        term = search_term.strip().lower()
        results = df[df["Accessories Code"].str.lower().str.contains(term, na=False)].drop_duplicates(
            subset=["Accessories Code", "Accessories Name"])

        if not results.empty:
            options = {
                f"{r['Accessories Name']} · {r['Accessories Code']} · {r['Base Color']}": r.to_dict()
                for _, r in results.iterrows()
            }
            with col2:
                selected_label = st.selectbox(
                    "Part", list(options.keys()), label_visibility="collapsed",
                    key="code_result_selectbox"
                )
                final_row = options[selected_label]
                st.session_state.selected_row = final_row
                if has_recipe(final_row):
                    batch_kg = st.number_input(
                        "Total amount (kg)", min_value=0.1, max_value=10000.0,
                        step=0.5, format="%.1f", key="batch_kg"
                    )
                else:
                    st.markdown('<div class="pm-warn">⚠ No recipe data for this part.</div>', unsafe_allow_html=True)
        else:
            with col2:
                st.markdown('<div class="pm-warn">⚠ No parts found. Try a different code.</div>', unsafe_allow_html=True)
            st.session_state.selected_row      = None
            st.session_state.current_part_code = None
else:
    st.session_state.selected_row      = None
    st.session_state.current_part_code = None

st.markdown('</div>', unsafe_allow_html=True)


# ── RECIPE BREAKDOWN & LOGGING ────────────────────────────────────────────────
if st.session_state.selected_row and has_recipe(st.session_state.selected_row):
    row = st.session_state.selected_row

    st.markdown(
        '<div class="pm-card">'
        '<div class="pm-card-title">Recipe Breakdown & Logging</div>'
        '<div class="pm-card-guidance">Adjust percentages if needed. Total must equal 100% before confirming. '
        '<span class="pm-card-example">(Changes log to the Batch Log but never alter the masterfile)</span></div>',
        unsafe_allow_html=True
    )

    part_code = row.get("Accessories Code", "unknown")
    if st.session_state.current_part_code != part_code:
        st.session_state.current_part_code = part_code
        st.session_state.batch_confirmed   = False
        st.session_state.active_cols       = [
            col for col in INGREDIENT_COLS
            if not isinstance(row.get(col, 0), str) and row.get(col, 0) > 0
        ]
        st.session_state.pct_values = {
            col: round(row.get(col, 0) * 100, 2) if not isinstance(row.get(col, 0), str) else 0.0
            for col in st.session_state.active_cols
        }

    active_cols = st.session_state.active_cols
    for col in active_cols:
        if col not in st.session_state.pct_values:
            st.session_state.pct_values[col] = 0.0
    pct_values = st.session_state.pct_values

    # Build table
    display_data = {
        col.replace(" %", ""): [pct_values[col], round((pct_values[col] / 100.0) * batch_kg, 3)]
        for col in active_cols
    }
    combined_df = pd.DataFrame(display_data, index=["%", "kg"])

    layout_mode = st.radio(
        "Mode", ["Standard (Horizontal)", "Mobile (Vertical Transposed)"],
        horizontal=True, label_visibility="collapsed"
    )
    is_vertical = (layout_mode == "Mobile (Vertical Transposed)")

    if is_vertical:
        combined_df   = combined_df.T
        column_config = {
            "%":  st.column_config.NumberColumn("%",  min_value=0, step=0.1, format="%.2f"),
            "kg": st.column_config.NumberColumn("kg", disabled=True, format="%.3f"),
        }
    else:
        column_config = {
            c: st.column_config.NumberColumn(c, min_value=0, step=0.1, format="%.3f")
            for c in combined_df.columns
        }

    editor_key = f"recipe_editor_{part_code}_{hash((tuple(sorted(pct_values.items())), batch_kg, tuple(active_cols), is_vertical))}"
    edited_df  = st.data_editor(combined_df, use_container_width=True, column_config=column_config, key=editor_key)

    new_pct_values = {}
    changed = False
    for col in active_cols:
        display_name = col.replace(" %", "")
        new_val = float(edited_df.loc[display_name, "%"] if is_vertical else edited_df.loc["%", display_name])
        new_pct_values[col] = new_val
        if abs(new_val - pct_values[col]) > 1e-9:
            changed = True
    if changed:
        st.session_state.pct_values = new_pct_values
        st.rerun()

    ingredient_kgs     = {col: round(pct_values[col] / 100.0 * batch_kg, 3) for col in active_cols}
    edited_pcts_decimal = {col: pct_values[col] / 100.0 for col in active_cols}
    total_pct   = sum(edited_pcts_decimal.values())
    total_kg    = sum(ingredient_kgs.values())
    pct_deviation = (total_pct - 1.0) * 100

    # Add ingredient
    remaining_cols = [c for c in INGREDIENT_COLS if c not in active_cols]
    if remaining_cols:
        add_c1, add_c2 = st.columns([3, 1])
        with add_c1:
            new_ingredient = st.selectbox(
                "Add", [c.replace(" %", "") for c in remaining_cols],
                label_visibility="collapsed", key=f"add_ing_{part_code}"
            )
        with add_c2:
            if st.button("+ Add", use_container_width=True, key=f"add_ing_btn_{part_code}"):
                matching = next(c for c in remaining_cols if c.replace(" %", "") == new_ingredient)
                st.session_state.active_cols.append(matching)
                st.rerun()

    if abs(pct_deviation) > 0.01:
        sign = "+" if pct_deviation > 0 else ""
        st.markdown(
            f'<div class="pm-warn">⚠ Recipe total is {total_pct*100:.1f}% — {sign}{pct_deviation:.1f}% '
            f'{"over" if pct_deviation > 0 else "under"} target.</div>',
            unsafe_allow_html=True
        )

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
        </div>""", unsafe_allow_html=True)

    with bot_col2:
        if not st.session_state.batch_confirmed:
            if st.button("Confirm & Log Batch", key="action_log_trigger",
                         use_container_width=True, disabled=abs(pct_deviation) > 0.01):
                try:
                    with st.spinner("Logging batch..."):
                        log_batch(row, batch_kg, ingredient_kgs, selected_factory, ACTIVE_LOG_SHEET)
                    st.session_state.batch_confirmed = True
                    load_recent_logs.clear()
                    st.toast("✓ Batch logged successfully", icon="✅")
                    st_javascript("localStorage.removeItem('pm_search'); localStorage.removeItem('pm_batch_kg');")
                    st.rerun()
                except Exception as e:
                    st.error(f"Failed to log batch: {e}")
        else:
            if st.button("Start New Batch", use_container_width=True):
                st.session_state.batch_confirmed = False
                st.rerun()

    if st.session_state.batch_confirmed:
        ts = datetime.now(BD_TZ).strftime("%H:%M")
        st.markdown(
            f'<div class="pm-success" style="margin-top:10px;">✓ Batch logged successfully · {ts}</div>',
            unsafe_allow_html=True
        )

    st.markdown('</div>', unsafe_allow_html=True)

# ── RECENT LOGS ───────────────────────────────────────────────────────────────
st.markdown(
    f'<div class="pm-card">'
    f'<div class="pm-card-title">Recent Logs — {selected_factory} (Last 10)</div>'
    f'<div class="pm-card-guidance">Check the box next to a row to delete it if a batch was logged in error.</div>',
    unsafe_allow_html=True
)

recent_logs_df = load_recent_logs(ACTIVE_LOG_SHEET)

if not recent_logs_df.empty:
    if "Timestamp" in recent_logs_df.columns:
        now = datetime.now(BD_TZ)
        def calc_time_ago(ts_str):
            try:
                ts = datetime.strptime(str(ts_str).strip(), "%Y-%m-%d %H:%M:%S").replace(tzinfo=BD_TZ)
                return humanize.naturaltime(now - ts)
            except Exception:
                return ""
        
        # Insert "Time Ago" right after "Timestamp"
        ts_idx = recent_logs_df.columns.get_loc("Timestamp")
        recent_logs_df.insert(ts_idx + 1, "Time Ago", recent_logs_df["Timestamp"].apply(calc_time_ago))

    cols_to_show = [c for c in recent_logs_df.columns
                    if not recent_logs_df[c].astype(str).str.strip().eq('').all()]
    display_df = recent_logs_df[cols_to_show].copy()
    display_df.insert(0, "🗑 Select", False)

    edited_logs = st.data_editor(
        display_df, use_container_width=True, hide_index=True,
        column_config={"🗑 Select": st.column_config.CheckboxColumn("🗑", width="small")},
        disabled=[c for c in display_df.columns if c != "🗑 Select"],
        key="logs_editor"
    )

    selected_rows = recent_logs_df[(edited_logs["🗑 Select"] == True).values]
    if not selected_rows.empty and st.session_state.pending_delete is None:
        r = selected_rows.iloc[0]
        st.markdown(
            f'<div class="pm-warn">⚠ Delete batch logged at <strong>{r.get("Timestamp","")}</strong> — '
            f'<strong>{r.get("Accessories Name","")}</strong>, '
            f'<strong>{r.get("Batch Size (kg)","")} kg</strong>? This cannot be undone.</div>',
            unsafe_allow_html=True
        )
        dc1, dc2 = st.columns([1, 1])
        with dc1:
            if st.button("✕ Confirm Delete", use_container_width=True, key="confirm_delete_btn"):
                st.session_state.pending_delete = {
                    "timestamp":        str(r.get("Timestamp", "")),
                    "accessories_code": str(r.get("Accessories Code", "")),
                    "batch_size":       str(r.get("Batch Size (kg)", "")),
                }
                st.rerun()
        with dc2:
            if st.button("Cancel", use_container_width=True, key="cancel_delete_btn"):
                st.rerun()

    if st.session_state.pending_delete:
        pd_data = st.session_state.pending_delete
        with st.spinner("Deleting log entry..."):
            success = delete_log_row(
                ACTIVE_LOG_SHEET,
                pd_data["timestamp"],
                pd_data["accessories_code"],
                pd_data["batch_size"],
            )
        st.session_state.pending_delete = None
        load_recent_logs.clear()
        st.toast("✓ Entry deleted" if success else "⚠ Row not found", icon="🗑️" if success else "⚠️")
        st.rerun()

else:
    st.caption(f"No batch entries found in {selected_factory} log yet.")

st.markdown('</div>', unsafe_allow_html=True)

# ── Safe State Persistence ───────────────────────────────────────────────────
if st.session_state.get("storage_synced", False):
    st_javascript(f"localStorage.setItem('pm_dark_mode', '{str(st.session_state.dark_mode).lower()}');")
    search_val = str(st.session_state.get('search_input', '')).replace("'", "\\'")
    st_javascript(f"localStorage.setItem('pm_search', '{search_val}');")
    st_javascript(f"localStorage.setItem('pm_batch_kg', '{st.session_state.get('batch_kg', '')}');")
