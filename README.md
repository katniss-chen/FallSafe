# FallSafe AI 2.0 — Research and Nursing Workflow Prototype

An educational Streamlit demo combining a **fictional inpatient fall-prevention workflow** with a **separate CDC NHIS 2023 research model**.

## Run

```bash
pip install -r requirements.txt
streamlit run app.py
```

For Streamlit Community Cloud, set the entrypoint to `app.py` at the repository root.

## Modules

- Patient Assessment — illustrative four-factor rule, **not a validated clinical risk scale**.
- Fall Risk Alerts — demo workflow alerts.
- Prevention Checklist — records prevention task status.
- Nursing Handoff — task ownership, acknowledgement, escalation simulation, and gap summary.
- Quality Dashboard — fictional workflow metrics and clearly labeled synthetic fall incidence.
- AI Research (NHIS 2023) — independent research classifier for **self-reported falls in the prior 12 months**.

## Research model

The `models/` folder includes two pre-trained scikit-learn pipelines and a JSON evaluation report. The `scripts/` folder contains the training script. To reproduce training, obtain `adult23.csv` from CDC NHIS 2023, place it beside `scripts/train_fallsafe_baseline.py`, and run that script. The training script writes artifacts into `scripts/`; move the output model and report files to `models/` to update the web app. Do **not** commit the original CDC CSV.

**Important:** The original held-out test metrics use a 0.5 decision threshold and have very low recall. The evaluation is unweighted and ignores NHIS survey design. This is not an externally validated, prospective, or inpatient model. Model outputs must not trigger clinical interventions. Survey field labels and response codes should be checked against the official NHIS codebook.

## Safety and limitations

- Fictional patients only; no patient health information should be entered.
- In-memory browser-session records, not a real database or EHR.
- No authentication, real notifications, or clinical decision support validation.
- Prevention gap detection is a transparent rule-based check of **pending tasks**, not an AI prediction.
- Bed rails, bed alarms and signage depend on clinical assessment and local policy.
- Load `.joblib` files only from trusted sources; deserialization can execute code.

Source: [CDC NHIS 2023 documentation](https://www.cdc.gov/nchs/nhis/documentation/2023-nhis.html).
