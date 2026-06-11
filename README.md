# PolyMix — Batch Recipe Calculator

Internal tool for factory-floor recipe mixing.

## What it does
- Search WIP parts by **Accessories Name** or **Accessories Code**
- Enter a batch size in kg
- Get exact ingredient weights (3 decimal places) for every component
- Confirm the batch to log it to the **Batch Log** sheet on the same WIP_MASTERFILE Google Sheet

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
