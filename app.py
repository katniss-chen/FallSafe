
import streamlit as st

st.set_page_config(
    page_title="FallSafe",
    page_icon="🏥",
    layout="wide"
)

st.title("🏥 FallSafe")
st.subheader("Clinical Fall Prevention & Nursing Workflow")

st.warning(
    "Educational prototype using fictional patient data. "
    "Not for clinical decision-making."
)

st.sidebar.title("Navigation")

page = st.sidebar.radio(
    "Select a page",
    [
        "Patient Assessment",
        "Fall Risk Alerts",
        "Prevention Checklist",
        "Nursing Handoff",
        "Quality Dashboard"
    ]
)

patients = {
    "P001": {"age": 78, "unit": "Geriatrics"},
    "P002": {"age": 45, "unit": "Medical-Surgical"},
    "P003": {"age": 69, "unit": "Orthopedics"}
}

if page == "Patient Assessment":

    st.header("Patient Fall Risk Assessment")

    patient_id = st.selectbox(
        "Select Patient",
        list(patients.keys())
    )

    patient = patients[patient_id]

    col1, col2 = st.columns(2)

    with col1:
        st.metric("Patient Age", patient["age"])

    with col2:
        st.metric("Hospital Unit", patient["unit"])

    st.subheader("Fall Risk Factors")

    previous_fall = st.checkbox("History of falls")
    dizziness = st.checkbox("Dizziness or orthostatic symptoms")
    mobility = st.checkbox("Impaired mobility")
    medication = st.checkbox("Medication-related fall risk")

    if st.button("Submit Assessment"):

        risk_count = sum([
            previous_fall,
            dizziness,
            mobility,
            medication
        ])

        if risk_count >= 2:
            st.error("HIGH FALL RISK - Prevention review required")
        elif risk_count == 1:
            st.warning("Fall risk factor identified - Review required")
        else:
            st.info("No selected risk factors - Continue full assessment")

        st.caption(
            "Demonstration rules only. "
            "Not a validated fall risk assessment."
        )

elif page == "Fall Risk Alerts":
    st.header("Fall Risk Alerts")
    st.info("Clinical decision support features coming soon.")

elif page == "Prevention Checklist":
    st.header("Prevention Checklist")
    st.info("Electronic nursing checklist coming soon.")

elif page == "Nursing Handoff":
    st.header("Nursing Handoff")
    st.info("Shared nursing task tracking coming soon.")

elif page == "Quality Dashboard":
    st.header("Quality Dashboard")
    st.info("Patient safety analytics coming soon.")
