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

# Centralized Core Color Variables for quick presentation adjustments
THEME = {
    # 1. Choose your mode: True for Light (Pure White), False for Dark (Pure Black)
    "light_mode": True,          
    
    # 2. Choose your main brand hue (0-360) and saturation (0%-100%)
    "brand_hue": "335",          # 200 is Sky Blue, 140 is Emerald, 25 is Orange, etc.
    "brand_saturation": "85%",   
    
    # 3. Choose your text base hue and saturation
    "text_hue": "360",           # Midnight/dark blue base
    "text_saturation": "35%",
    
    # 4. Static functional colors (will stay constant)
    "warn_bg": "#fff1f2",
    "warn_border": "#fecdd3",
    "warn_text": "#9f1239",
    "success_bg": "#f0fdf4",
    "success_border": "#bbf7d0",
    "success_text": "#166534",
}

# Mathematically handle the hard white vs hard black rules
bg_app = "#ffffff" if THEME["light_mode"] else "#000000"
bg_card = "#ffffff" if THEME["light_mode"] else "#121212" 
bg_neutral = "#f0f0f0" if THEME["light_mode"] else "#2a2a2a"
text_lightness = "11%" if THEME["light_mode"] else "90%"  

# ── Styling (Optimized for Responsive Desktop & Mobile layout) ────────────────────
st.markdown(f"""
<style>
    :root {{
        /* --- BRAND DERIVATIONS --- */
        --accent: hsl({THEME["brand_hue"]}, {THEME["brand_saturation"]}, 45%);
        --accent-disabled: hsl({THEME["brand_hue"]}, {THEME["brand_saturation"]}, 85%);
        --accent-light: hsl({THEME["brand_hue"]}, {THEME["brand_saturation"]}, 94%);
        --accent-glow: hsla({THEME["brand_hue"]}, {THEME["brand_saturation"]}, 45%, 0.12);
        --border: hsl({THEME["brand_hue"]}, 40%, 90%);
        --border-input: hsl({THEME["brand_hue"]}, 50%, 85%);
        
        /* --- FIXED BINARY BACKGROUNDS --- */
        --bg-primary: {bg_app}; 
        --bg-card: {bg_card};
        --bg-neutral: {bg_neutral};

        /* --- TEXT DERIVATIONS --- */
        --text-main: hsl({THEME["text_hue"]}, {THEME["text_saturation"]}, {text_lightness});      
        --text-guidance: hsl({THEME["text_hue"]}, {THEME["text_saturation"]}, 45%);  
        --text-muted: hsl({THEME["text_hue"]}, 15%, 60%);                             

        /* --- STATIC FUNCTIONAL COLORS --- */
        --warn-bg: {THEME["warn_bg"]};
        --warn-border: {THEME["warn_border"]};
        --warn-text: {THEME["warn_text"]};
        --success-bg: {THEME["success_bg"]};
        --success-border: {THEME["success_border"]};
        --success-text: {THEME["success_text"]};
        
        --accent-hover-opacity: 0.85;
    }}

    html, body, [data-testid="stAppViewContainer"] {{
        background-color: var(--bg-primary);
        color: var(--text-main);
        font-family: 'Segoe UI', sans-serif;
    }}
    [data-testid="stHeader"] {{ background: transparent; }}
    [data-testid="stSidebar"] {{ display: none; }}
    [data-testid="block-container"] {{
        padding-top: 1.2rem !important;
        padding-bottom: 1rem !important;
    }}

    .pm-title {{
        font-size: 3.2rem;
        font-weight: 800;
        letter-spacing: -0.5px;
        margin-bottom: 0;
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
    .pm-card-example {{
        color: var(--text-muted);
        font-style: italic;
    }}

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
    .summary-strip-val {{ font-size: 1.05rem; font-weight: 800; color: #fff; line-height: 1.2; }}

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
        color: var(--bg-card) !important; 
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
        color: var(--bg-card) !important;
        font-size: 1.25rem !important;
        font-weight: bold !important;
    }}
    .stButton > button:hover {{ opacity: var(--accent-hover-opacity) !important; }}
    .stButton > button:disabled,
    .stButton > button[disabled] {{
        background: var(--accent-disabled) !important;
        color: var(--bg-card) !important;
        opacity: 1 !important;
        cursor: not-allowed !important;
    }}
    .stButton > button:disabled p,
    .stButton > button[disabled] p {{
        color: var(--bg-card) !important;
    }}

    [data-testid="stRadio"] label {{ color: var(--text-main) !important; font-size: 0.85rem; }}
    [data-testid="stRadio"] p {{ color: var(--text-main) !important; }}
    [data-testid="stWidgetLabel"] p {{ color: var(--text-main) !important; }}
    label[data-testid="stWidgetLabel"] {{ color: var(--text-main) !important; }}
    [data-testid="stMarkdownContainer"] p {{ color: var(--text-main) !important; }}

    [data-testid="stSelectbox"] > div > div {{
        background-color: var(--bg-card) !important;
        border: 1px solid var(--border-input) !important;
        color: var(--text-main) !important;
        border-radius: 8px !important;
    }}
    [data-testid="stSelectbox"] svg {{ fill: var(--text-main) !important; }}
    [data-testid="stSelectbox"] span {{ color: var(--text-main) !important; }}

    [data-baseweb="popover"] ul {{ background-color: var(--bg-card) !important; }}
    [data-baseweb="popover"] li {{ background-color: var(--bg-card) !important; color: var(--text-main) !important; }}
    [data-baseweb="popover"] li:hover {{ background-color: var(--accent-light) !important; }}

    [data-testid="stNumberInput"] button {{
        background: var(--bg-neutral) !important;
        color: var(--text-main) !important;
        border: 1px solid var(--border-input) !important;
    }}

    [data-testid="block-container"] {{ background-color: var(--bg-primary) !important; }}
    section[data-testid="stMain"] {{ background-color: var(--bg-primary) !important; }}

    [data-testid="stDataFrame"] {{
        border: 1px solid var(--border) !important;
        border-radius: 8px !important;
        overflow: hidden;
    }}

    #MainMenu, footer {{ visibility: hidden; }}

    /* ─── MOBILE SPECIFIC INTERFACE OVERRIDES ─── */
    @media (max-width: 768px) {{
        .pm-title {{
            font-size: 2.2rem !important;
        }}
        [data-testid="block-container"] {{
            padding-left: 0.5rem !important;
            padding-right: 0.5rem !important;
        }}
        [data-testid="column"] {{
            width: 100% !important;
            flex: 1 1 100% !important;
            margin-bottom: 10px !important;
        }}
        .stButton > button {{
            height: 45px !important;
            line-height: 45px !important;
        }}
        .stButton > button p {{
            font-size: 1.1rem !important;
        }}
        .summary-strip {{
            height: 45px !important;
            margin-bottom: 10px !important;
        }}
    }}
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
    f'<div class="pm-title">'
    f'<span style="color:var(--accent);">Poly</span>'
    f'<span style="color:var(--text-main);">Mix</span>'
    f'</div>',
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
                st.markdown(f'<div class="pm-warn">⚠ No recipe data available for this selection.</div>', unsafe_allow_html=True)
    else:
        with col2:
            st.markdown(f'<div class="pm-warn">⚠ No parts found. Try a different search term.</div>', unsafe_allow_html=True)
            st.session_state.selected_row = None
            st.session_state.current_part_code = None
else:
    st.session_state.selected_row = None
    st.session_state.current_part_code = None

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

    # Reset active ingredient list, percentage values, and confirmation state
    # only when a different part is selected (not on every rerun)
    part_code = row.get("Accessories Code", "unknown")
    if st.session_state.current_part_code != part_code:
        st.session_state.current_part_code = part_code
        st.session_state.batch_confirmed = False
        st.session_state.active_cols = [
            col for col in INGREDIENT_COLS
            if not isinstance(row.get(col, 0), str) and row.get(col, 0) > 0
        ]
        st.session_state.pct_values = {
            col: round(row.get(col, 0) * 100, 2) if not isinstance(row.get(col, 0), str) else 0.0
            for col in st.session_state.active_cols
        }

    active_cols = st.session_state.active_cols

    # Ensure every active column has a tracked percentage
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

    # Adaptive mobile layout switch
    layout_mode = st.radio("Interface Mode", ["Standard (Horizontal)", "Mobile (Vertical Transposed)"], horizontal=True, label_visibility="collapsed")
    is_vertical = (layout_mode == "Mobile (Vertical Transposed)")

    if is_vertical:
        combined_df = combined_df.T
        column_config = {
            "%": st.column_config.NumberColumn("%", min_value=0, step=0.1, format="%.2f"),
            "kg": st.column_config.NumberColumn("kg", disabled=True, format="%.3f")
        }
    else:
        column_config = {
            c: st.column_config.NumberColumn(c, min_value=0, step=0.1, format="%.3f")
            for c in combined_df.columns
        }

    state_signature = (tuple(sorted(pct_values.items())), batch_kg, tuple(active_cols), is_vertical)
    editor_key = f"recipe_editor_{part_code}_{hash(state_signature)}"

    edited_df = st.data_editor(
        combined_df,
        use_container_width=True,
        column_config=column_config,
        key=editor_key
    )

    # Pull edited % values adaptively based on selected layout direction
    new_pct_values = {}
    changed = False
    for col in active_cols:
        display_name = col.replace(" %", "")
        if is_vertical:
            new_val = float(edited_df.loc[display_name, "%"])
        else:
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

    # Action Row: Summary and Logging side by side (CSS stacks these automatically on mobile)
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
            is_locked = abs(pct_deviation) > 0.01
            if st.button(
                "Confirm & Log Batch",
                key="action_log_trigger",
                use_container_width=True,
                disabled=is_locked
            ):
                try:
                    with st.spinner("Logging batch..."):
                        log_batch(row, batch_kg, ingredient_kgs)
                    st.session_state.batch_confirmed = True
                    st.toast("✓ Batch logged successfully", icon="✅")
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
