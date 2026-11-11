
import streamlit as st
from datetime import datetime

st.set_page_config(
    page_title="FallSafe",
    page_icon="🏥",
    layout="wide"
)

# -----------------------------------------
# Fictional patient data
# -----------------------------------------

PATIENTS = {
    "P001": {"age": 78, "unit": "Geriatrics"},
    "P002": {"age": 45, "unit": "Medical-Surgical"},
    "P003": {"age": 69, "unit": "Orthopedics"}
}

RISK_FACTORS = {
    "previous_fall": "History of falls",
    "dizziness": "Dizziness or orthostatic symptoms",
    "mobility": "Impaired mobility",
    "medication": "Medication-related fall risk"
}

PREVENTION_ITEMS = {
    "education": "Patient education completed",
    "bed_alarm": "Bed alarm activated",
    "signage": "Fall risk signage placed",
    "call_light": "Call light within reach",
    "bed_position": "Bed low and wheels locked",
    "bed_rails": "Bed rails appropriately positioned",
    "toileting": "Assisted toileting plan established"
}

STATUS_OPTIONS = [
    "Pending",
    "Completed",
    "Not indicated"
]


# -----------------------------------------
# Session data
# -----------------------------------------

if "records" not in st.session_state:
    st.session_state.records = {
        patient_id: {
            "assessment": None,
            "risk": "Not assessed",
            "assessment_time": None,
            "checklist": {
                item: "Pending"
                for item in PREVENTION_ITEMS
            },
            "checklist_time": None
        }
        for patient_id in PATIENTS
    }


def calculate_risk(assessment):
    """
    Educational demonstration only.
    Not a validated clinical scoring system.
    """
    count = sum(assessment.values())

    if count >= 2:
        return "High"
    elif count == 1:
        return "Review required"
    return "No selected factors"


def show_risk_alert(record):
    risk = record["risk"]

    if risk == "Not assessed":
        st.warning(
            "Assessment pending. Fall risk is unknown. "
            "Complete the assessment and follow interim "
            "safety precautions."
        )

    elif risk == "High":
        st.error(
            "HIGH FALL RISK - Prevention review required."
        )

    elif risk == "Review required":
        st.warning(
            "Fall risk factor identified. "
            "Further nursing review required."
        )

    else:
        st.info(
            "No selected risk factors. "
            "This does not establish low fall risk."
        )


# -----------------------------------------
# Header and navigation
# -----------------------------------------

st.title("🏥 FallSafe")
st.caption(
    "Clinical Fall Prevention & Nursing Workflow"
)

st.warning(
    "Educational prototype. Fictional patient data only. "
    "Not a validated clinical tool or real EHR."
)

page = st.sidebar.radio(
    "Navigation",
    [
        "Patient Assessment",
        "Fall Risk Alerts",
        "Prevention Checklist",
        "Nursing Handoff",
        "Quality Dashboard"
    ]
)

patient_id = st.sidebar.selectbox(
    "Select patient",
    list(PATIENTS.keys())
)

patient = PATIENTS[patient_id]
record = st.session_state.records[patient_id]

st.sidebar.divider()
st.sidebar.write(f"**Age:** {patient['age']}")
st.sidebar.write(f"**Unit:** {patient['unit']}")
st.sidebar.write(f"**Risk:** {record['risk']}")

st.divider()


# -----------------------------------------
# Page 1: Patient Assessment
# -----------------------------------------

if page == "Patient Assessment":

    st.header("Patient Fall Risk Assessment")

    col1, col2 = st.columns(2)
    col1.metric("Patient Age", patient["age"])
    col2.metric("Hospital Unit", patient["unit"])

    show_risk_alert(record)

    st.subheader("Fall Risk Factors")

    previous = record["assessment"] or {}

    with st.form(f"assessment_form_{patient_id}"):

        answers = {}

        for factor, label in RISK_FACTORS.items():
            answers[factor] = st.checkbox(
                label,
                value=previous.get(factor, False)
            )

        submitted = st.form_submit_button(
            "Save Assessment",
            type="primary"
        )

    if submitted:
        old_assessment = record["assessment"]

        record["assessment"] = answers.copy()
        record["risk"] = calculate_risk(answers)
        record["assessment_time"] = (
            datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        )

        if old_assessment != answers:
            record["checklist"] = {
                item: "Pending"
                for item in PREVENTION_ITEMS
            }
            record["checklist_time"] = None

        st.success("Assessment saved for this demo session.")
        show_risk_alert(record)

    if record["assessment_time"]:
        st.caption(
            "Last assessment: "
            + record["assessment_time"]
        )

    st.info(
        "This simplified four-factor rule is for "
        "demonstration only. A real hospital must use "
        "approved assessment criteria and nursing judgment."
    )


# -----------------------------------------
# Page 2: Clinical Alerts
# -----------------------------------------

elif page == "Fall Risk Alerts":

    st.header("Clinical Decision Support Alerts")

    st.subheader(f"Patient {patient_id}")
    show_risk_alert(record)

    if record["assessment"] is None:
        st.error(
            "Action required: Initial fall risk "
            "assessment has not been completed."
        )

    else:
        st.write("### Identified Risk Factors")

        factors = [
            label
            for factor, label in RISK_FACTORS.items()
            if record["assessment"].get(factor, False)
        ]

        if factors:
            for factor in factors:
                st.write(f"- {factor}")
        else:
            st.write("No selected factors documented.")

    st.divider()
    st.subheader("Prevention Task Status")

    checklist = record["checklist"]

    pending = sum(
        status == "Pending"
        for status in checklist.values()
    )

    completed = sum(
        status == "Completed"
        for status in checklist.values()
    )

    col1, col2 = st.columns(2)
    col1.metric("Completed", completed)
    col2.metric("Pending", pending)

    if pending > 0:
        st.warning(
            f"{pending} prevention tasks are still pending."
        )
    else:
        st.success(
            "All checklist items have been reviewed."
        )

    st.caption(
        "Checklist completion does not remove "
        "a patient's fall risk designation."
    )


# -----------------------------------------
# Page 3: Prevention Checklist
# -----------------------------------------

elif page == "Prevention Checklist":

    st.header("Electronic Fall Prevention Checklist")

    st.write(f"**Patient:** {patient_id}")
    show_risk_alert(record)

    if record["assessment"] is None:
        st.warning(
            "Fall risk assessment is incomplete. "
            "Do not interpret this as low risk."
        )

    st.write(
        "Confirm the appropriate bedside prevention "
        "measures. Select 'Not indicated' only when "
        "clinically appropriate."
    )

    with st.form(f"checklist_form_{patient_id}"):

        responses = {}

        for item, label in PREVENTION_ITEMS.items():

            responses[item] = st.selectbox(
                label,
                STATUS_OPTIONS,
                index=STATUS_OPTIONS.index(
                    record["checklist"][item]
                ),
                key=f"check_{patient_id}_{item}"
            )

        saved = st.form_submit_button(
            "Save Prevention Checklist",
            type="primary"
        )

    if saved:
        record["checklist"] = responses.copy()
        record["checklist_time"] = (
            datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        )
        st.success("Checklist saved for this demo session.")

    statuses = record["checklist"]

    completed = sum(
        value == "Completed"
        for value in statuses.values()
    )

    pending = sum(
        value == "Pending"
        for value in statuses.values()
    )

    not_indicated = sum(
        value == "Not indicated"
        for value in statuses.values()
    )

    col1, col2, col3 = st.columns(3)

    col1.metric("Completed", completed)
    col2.metric("Pending", pending)
    col3.metric("Not indicated", not_indicated)

    st.progress(
        (completed + not_indicated) /
        len(PREVENTION_ITEMS)
    )

    if pending > 0:
        st.warning(
            f"{pending} items remain pending. "
            "Follow up according to clinical urgency."
        )
    else:
        st.success("Checklist review documented.")

    st.info(
        "Documentation is not proof of bedside execution. "
        "Bed alarms and bed rails must be used according "
        "to patient assessment and hospital policy."
    )

    if record["checklist_time"]:
        st.caption(
            "Last checklist update: "
            + record["checklist_time"]
        )


# -----------------------------------------
# Pages to develop next
# -----------------------------------------

elif page == "Nursing Handoff":

    st.header("Nursing Handoff")
    st.info(
        "Next phase: Task assignment, shift handoff, "
        "acknowledgment, and escalation tracking."
    )

elif page == "Quality Dashboard":

    st.header("Quality Dashboard")
    st.info(
        "Next phase: Fall prevention compliance "
        "and patient safety analytics."
    )
