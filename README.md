# PolyMix — Batch Recipe Calculator

Internal tool for factory-floor recipe mixing.

## What it does
- **Smart Search**: Multi-keyword, order-independent fuzzy search with built-in typo tolerance (via RapidFuzz) for part names, alongside exact-match Part Code search.
- **Factory Tracking**: Seamlessly switch context between different factory locations (e.g., Narayanganj and N Poly), tracking batches to separate dedicated sheets.
- **Recipe Calculator**: Input a target batch weight (kg) to instantly calculate exact ingredient weights (to 3 decimal places).
- **Interactive Recipe Editing**: Adjust ingredient percentages on the fly, add missing ingredients to a recipe, and monitor total percentage deviations before committing the batch. Features responsive horizontal and vertical (mobile-friendly) table layouts.
- **Recent Logs & Deletions**: View the 10 most recent batch logs for the selected factory and selectively delete erroneous entries directly from the web interface.
- **UI & Accessibility**: Built-in custom dark/light mode toggle to suit factory-floor environments.
- **Automatic Logging**: Confirmed batches are instantly pushed to the respective factory's Batch Log tab in the connected Google Sheet.

---

## Setup

### 1. Google Service Account
You need the same service account used for PolyColor, or create a new one:
1. Go to Google Cloud Console → IAM & Admin → Service Accounts
2. Create a key (JSON format) and download it
3. Share **WIP_MASTERFILE** with the service account email (Editor access)

### 2. Streamlit Secrets
Create `.streamlit/secrets.toml` locally (or paste into Streamlit Cloud → Settings → Secrets):

```toml
gcp_service_account = """
{ ...your full service account JSON here as a single string... }
"""
```

### 3. Run locally
```bash
pip install -r requirements.txt
streamlit run app.py
```

### 4. Deploy on Streamlit Community Cloud
1. Push to GitHub
2. Connect repo on share.streamlit.io
3. Add the `gcp_service_account` secret under Settings → Secrets

---

## Batch Log sheet
On first confirm, the app auto-creates a **Batch Log** sheet in WIP_MASTERFILE with columns:
`Timestamp | Part Name | Accessories Code | Accessories Name | Base Color | Batch Size (kg) | PPHP | PPCP | Chips % | Compound % | LDP | ABS | PC | GPPS | TPR | RCP | Dessicant | Perfume MB | Additive | Filler | MB`

---

## Notes
- Parts with `0.0%` total in the Masterfile are flagged as having no recipe — update the sheet to add them
- Data is cached for 2 minutes; changes to the Masterfile reflect within that window
