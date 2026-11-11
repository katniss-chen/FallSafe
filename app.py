import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta

st.set_page_config(page_title='FallSafe', page_icon='🏥', layout='wide')
PATIENTS = {'P001': {'age': 78, 'unit': 'Geriatrics'}, 'P002': {'age': 45, 'unit': 'Medical-Surgical'}, 'P003': {'age': 69, 'unit': 'Orthopedics'}}
RISK_FACTORS = {'previous_fall': 'History of falls', 'dizziness': 'Dizziness or orthostatic symptoms', 'mobility': 'Impaired mobility', 'medication': 'Medication-related fall risk'}
PREVENTION_ITEMS = {'education': 'Patient education completed', 'bed_alarm': 'Bed alarm activated, if indicated', 'signage': 'Fall risk signage placed, if indicated', 'call_light': 'Call light within reach', 'bed_position': 'Bed low and wheels locked', 'bed_rails': 'Bed rails appropriately positioned', 'toileting': 'Assisted toileting plan established, if indicated'}
STATUS_OPTIONS = ['Pending', 'Completed', 'Not indicated']
OWNERS = ['Unassigned', 'Current shift nurse', 'Incoming shift nurse', 'Charge nurse']

def now():
    return datetime.now().astimezone().isoformat(timespec='seconds')

def new_task():
    return {'status': 'Pending', 'owner': 'Unassigned', 'acknowledged_at': None, 'completed_at': None, 'updated_at': None, 'not_indicated_reason': '', 'assigned_at': None, 'escalated_at': None}

def new_record():
    return {'assessment': None, 'risk': 'Not assessed', 'assessment_time': None, 'tasks': {key: new_task() for key in PREVENTION_ITEMS}, 'events': []}

if 'records' not in st.session_state:
    st.session_state.records = {pid: new_record() for pid in PATIENTS}

def event(record, action, item=None, details=''):
    record['events'].append({'time': now(), 'action': action, 'item': item or '-', 'details': details})

def risk_of(answers):
    count = sum(answers.values())
    return 'High' if count >= 2 else 'Review required' if count == 1 else 'No selected factors'

def risk_alert(record):
    risk = record['risk']
    if risk == 'Not assessed':
        st.warning('Assessment pending — fall risk unknown. Follow interim precautions.')
    elif risk == 'High':
        st.error('HIGH FALL RISK — Prevention review required.')
    elif risk == 'Review required':
        st.warning('Fall risk factor identified — further nursing review required.')
    else:
        st.info('No selected factors. This does not establish low fall risk.')

def task_counts(record):
    return {s: sum(t['status'] == s for t in record['tasks'].values()) for s in STATUS_OPTIONS}

def save_task(record, key, new_status, new_owner, reason=''):
    task = record['tasks'][key]
    old_status, old_owner = task['status'], task['owner']
    if new_owner != old_owner:
        task['owner'] = new_owner
        task['assigned_at'] = now() if new_owner != 'Unassigned' else None
        task['acknowledged_at'] = None
        task['escalated_at'] = None
        event(record, 'Task assigned', key, f'{old_owner} → {new_owner}')
    if new_status != old_status:
        task['status'] = new_status
        task['completed_at'] = now() if new_status == 'Completed' else None
        task['not_indicated_reason'] = reason if new_status == 'Not indicated' else ''
        if new_status != 'Pending':
            task['escalated_at'] = None
        if new_status == 'Pending':
            task['acknowledged_at'] = None
        event(record, 'Task status changed', key, f'{old_status} → {new_status}')
    elif new_status == 'Not indicated' and reason != task['not_indicated_reason']:
        task['not_indicated_reason'] = reason
        event(record, 'Not-indicated rationale updated', key, reason)
    task['updated_at'] = now()
    # Clear cached checklist widgets so cross-page updates are visible.
    if page != 'Prevention Checklist':
        st.session_state.pop(f'check_{patient_id}_{key}', None)
        st.session_state.pop(f'reason_{patient_id}_{key}', None)

st.title('🏥 FallSafe')
st.caption('Clinical Fall Prevention & Nursing Workflow | Portfolio Prototype')
st.warning('Educational simulation with fictional patients. Not a validated fall-risk tool, real EHR, or clinical alerting service.')
page = st.sidebar.radio('Navigation', ['Patient Assessment', 'Fall Risk Alerts', 'Prevention Checklist', 'Nursing Handoff', 'Quality Dashboard'])
patient_id = st.sidebar.selectbox('Select patient', list(PATIENTS))
patient = PATIENTS[patient_id]
record = st.session_state.records[patient_id]
st.sidebar.write(f"**Age:** {patient['age']} | **Unit:** {patient['unit']}")
st.sidebar.write(f"**Risk:** {record['risk']}")
st.divider()

if page == 'Patient Assessment':
    st.header('Patient Fall Risk Assessment')
    a, b = st.columns(2)
    a.metric('Patient Age', patient['age'])
    b.metric('Hospital Unit', patient['unit'])
    risk_alert(record)
    with st.form(f'assessment_{patient_id}'):
        previous = record['assessment'] or {}
        answers = {k: st.checkbox(label, value=previous.get(k, False)) for k, label in RISK_FACTORS.items()}
        submitted = st.form_submit_button('Save Assessment', type='primary')
    if submitted:
        changed = record['assessment'] != answers
        record['assessment'] = answers.copy()
        record['risk'] = risk_of(answers)
        record['assessment_time'] = now()
        event(record, 'Assessment saved', details=f"Risk: {record['risk']}")
        if changed:
            for key, task in record['tasks'].items():
                if task['status'] != 'Pending':
                    event(record, 'Task requires re-review', key, 'Assessment changed')
                task.update(new_task())
        st.success('Assessment saved for this browser session.')
        risk_alert(record)
    if record['assessment_time']:
        st.caption('Last assessment: ' + record['assessment_time'])
    st.info('Four-factor rule is for demonstration only, not a validated clinical scoring system.')

elif page == 'Fall Risk Alerts':
    st.header('Clinical Decision Support Alerts')
    risk_alert(record)
    if record['assessment'] is None:
        st.error('Action required: Initial fall risk assessment is incomplete.')
    else:
        st.subheader('Identified Risk Factors')
        factors = [label for k, label in RISK_FACTORS.items() if record['assessment'].get(k)]
        st.write(', '.join(factors) if factors else 'No selected factors documented.')
    counts = task_counts(record)
    a, b, c = st.columns(3)
    a.metric('Completed', counts['Completed'])
    b.metric('Pending', counts['Pending'])
    c.metric('Not indicated', counts['Not indicated'])
    if counts['Pending']:
        st.warning(f"{counts['Pending']} prevention tasks remain pending.")
    else:
        st.success('All prevention items reviewed; risk designation remains unchanged.')
    unowned = [PREVENTION_ITEMS[k] for k, t in record['tasks'].items() if t['status'] == 'Pending' and t['owner'] == 'Unassigned']
    if unowned:
        st.info(f'{len(unowned)} pending tasks have no assigned owner. Review Nursing Handoff.')

elif page == 'Prevention Checklist':
    st.header('Electronic Fall Prevention Checklist')
    risk_alert(record)
    if record['assessment'] is None:
        st.warning('Assessment incomplete. Do not interpret this as low risk.')
    st.caption('Save statuses here; Nursing Handoff reads the same tasks. Not indicated requires a reason.')
    with st.form(f'checklist_{patient_id}'):
        choices = {}
        reasons = {}
        for key, label in PREVENTION_ITEMS.items():
            task = record['tasks'][key]
            choices[key] = st.selectbox(label, STATUS_OPTIONS, index=STATUS_OPTIONS.index(task['status']), key=f'check_{patient_id}_{key}')
            reasons[key] = st.text_input('Reason if not indicated', value=task['not_indicated_reason'], key=f'reason_{patient_id}_{key}') if choices[key] == 'Not indicated' else ''
        saved = st.form_submit_button('Save Prevention Checklist', type='primary')
    if saved:
        missing = [PREVENTION_ITEMS[k] for k in PREVENTION_ITEMS if choices[k] == 'Not indicated' and not reasons[k].strip()]
        if missing:
            st.error('Provide a reason for each Not indicated item: ' + ', '.join(missing))
        else:
            for key in PREVENTION_ITEMS:
                task = record['tasks'][key]
                save_task(record, key, choices[key], task['owner'], reasons[key].strip())
            st.success('Checklist saved. Handoff and alerts now reflect these statuses.')
    counts = task_counts(record)
    a, b, c = st.columns(3)
    a.metric('Completed', counts['Completed'])
    b.metric('Pending', counts['Pending'])
    c.metric('Not indicated', counts['Not indicated'])
    st.progress((counts['Completed'] + counts['Not indicated']) / len(PREVENTION_ITEMS))
    st.info('A recorded checkbox is not proof of bedside execution. Bed alarms, signage, and rails depend on assessment and local policy.')

elif page == 'Nursing Handoff':
    st.header('Nursing Handoff & Task Accountability')
    risk_alert(record)
    counts = task_counts(record)
    a, b, c = st.columns(3)
    a.metric('Pending', counts['Pending'])
    b.metric('Completed', counts['Completed'])
    c.metric('Not indicated', counts['Not indicated'])
    st.subheader('Assign and review prevention tasks')
    for key, label in PREVENTION_ITEMS.items():
        task = record['tasks'][key]
        with st.expander(f"{label} · {task['status']} · {task['owner']}", expanded=task['status'] == 'Pending'):
            st.write(f"**Acknowledged:** {task['acknowledged_at'] or 'No'}")
            st.write(f"**Completed:** {task['completed_at'] or 'No'}")
            with st.form(f'handoff_{patient_id}_{key}'):
                owner = st.selectbox('Responsible person', OWNERS, index=OWNERS.index(task['owner']))
                status = st.selectbox('Task status', STATUS_OPTIONS, index=STATUS_OPTIONS.index(task['status']))
                reason = st.text_input('Reason if not indicated', value=task['not_indicated_reason']) if status == 'Not indicated' else ''
                update = st.form_submit_button('Update assignment / status')
            if update:
                if status == 'Not indicated' and not reason.strip():
                    st.error('Provide a reason for Not indicated.')
                else:
                    save_task(record, key, status, owner, reason.strip())
                    st.success('Task updated. Other pages use this same record.')
                    st.rerun()
            if task['status'] == 'Pending' and task['owner'] != 'Unassigned':
                if not task['acknowledged_at']:
                    if st.button('Acknowledge task (demo)', key=f'ack_{patient_id}_{key}'):
                        task['acknowledged_at'] = now()
                        event(record, 'Task acknowledged', key, task['owner'])
                        st.rerun()
                else:
                    st.info('Acknowledged does not mean completed.')
    st.divider()
    st.subheader('Escalation simulation')
    st.caption('30 minutes is an illustrative timer for nonurgent, unacknowledged tasks only. Immediate hazards require immediate human action.')
    minutes = st.slider('Simulated minutes since last assignment', 0, 90, 0, 5)
    pending_unack = [(key, task) for key, task in record['tasks'].items() if task['status'] == 'Pending' and task['acknowledged_at'] is None]
    if minutes >= 30 and pending_unack:
        st.error(f'{len(pending_unack)} unacknowledged pending task(s) meet the simulated escalation threshold. Notify charge nurse.')
        if st.button('Record simulated escalation to charge nurse'):
            for key, task in pending_unack:
                task['escalated_at'] = now()
                event(record, 'Escalation simulated', key, 'Charge nurse; no real message sent')
            st.success('Escalation recorded in this demo session. No external notification sent.')
    elif pending_unack:
        st.warning(f'{len(pending_unack)} pending task(s) not acknowledged. Escalation threshold not reached in simulation.')
    else:
        st.success('No pending unacknowledged tasks.')
    st.divider()
    st.subheader('Shift handoff summary')
    handoff_rows = [
        {
            'Prevention task': PREVENTION_ITEMS[key],
            'Status': task['status'],
            'Owner': task['owner'],
            'Acknowledged': 'Yes' if task['acknowledged_at'] else 'No',
            'Completed at': task['completed_at'] or '—',
        }
        for key, task in record['tasks'].items()
    ]
    st.dataframe(pd.DataFrame(handoff_rows), use_container_width=True, hide_index=True)
    st.subheader('Audit trail (current browser session)')
    if record['events']:
        st.dataframe(list(reversed(record['events'])), use_container_width=True, hide_index=True)
    else:
        st.info('No recorded activity yet.')

elif page == 'Quality Dashboard':
    st.header('Quality & Patient Safety Dashboard')
    st.caption('Live workflow metrics come from fictional patient records in this browser session. Fall events and patient-days below are a separate, illustrative dataset.')

    records = st.session_state.records
    total_patients = len(records)
    assessed = sum(rec['assessment'] is not None for rec in records.values())
    high_risk = sum(rec['risk'] == 'High' for rec in records.values())
    all_tasks = [task for rec in records.values() for task in rec['tasks'].values()]
    completed = sum(task['status'] == 'Completed' for task in all_tasks)
    pending = sum(task['status'] == 'Pending' for task in all_tasks)
    not_indicated = sum(task['status'] == 'Not indicated' for task in all_tasks)
    reviewed = completed + not_indicated
    task_total = len(all_tasks)
    assessment_rate = 100 * assessed / total_patients if total_patients else 0
    review_rate = 100 * reviewed / task_total if task_total else 0

    st.subheader('Current demo-session workflow measures')
    c1, c2, c3, c4 = st.columns(4)
    c1.metric('Assessment completion', f'{assessment_rate:.0f}%', f'{assessed}/{total_patients} patients', delta_color='off')
    c2.metric('Checklist items reviewed', f'{review_rate:.0f}%', f'{reviewed}/{task_total} items', delta_color='off')
    c3.metric('High-risk patients', high_risk)
    c4.metric('Pending prevention tasks', pending)
    st.caption('Checklist reviewed = Completed + Not indicated (with documented reason). It is not a measure of verified bedside adherence.')

    st.subheader('Prevention task status')
    status_df = pd.DataFrame([
        {'Status': 'Completed', 'Tasks': completed},
        {'Status': 'Pending', 'Tasks': pending},
        {'Status': 'Not indicated', 'Tasks': not_indicated},
    ])
    left, right = st.columns([1, 1])
    with left:
        fig = px.bar(status_df, x='Status', y='Tasks', text='Tasks', title='All fictional patients')
        fig.update_layout(showlegend=False, yaxis_title='Number of tasks')
        st.plotly_chart(fig, use_container_width=True)
    with right:
        rows = []
        for pid, rec in records.items():
            counts = task_counts(rec)
            rows.append({
                'Patient': pid,
                'Unit': PATIENTS[pid]['unit'],
                'Risk': rec['risk'],
                'Assessment': 'Complete' if rec['assessment'] is not None else 'Pending',
                'Completed': counts['Completed'],
                'Pending': counts['Pending'],
                'Not indicated': counts['Not indicated'],
            })
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

    st.subheader('Handoff accountability')
    unassigned = sum(t['status'] == 'Pending' and t['owner'] == 'Unassigned' for t in all_tasks)
    unacknowledged = sum(t['status'] == 'Pending' and not t['acknowledged_at'] for t in all_tasks)
    escalated = sum(t['escalated_at'] is not None for t in all_tasks)
    a, b, c = st.columns(3)
    a.metric('Pending and unassigned', unassigned)
    b.metric('Pending and unacknowledged', unacknowledged)
    c.metric('Currently flagged as escalated', escalated)
    st.caption('Acknowledged means accepted for follow-up, not completed. Escalations are simulated and do not send notifications.')

    st.divider()
    st.subheader('Illustrative fall incidence trend')
    st.info('The monthly figures below are invented teaching data, NOT calculated from P001–P003 and NOT actual hospital outcomes.')
    demo_months = pd.DataFrame({
        'Month': ['Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'],
        'Falls': [5, 4, 6, 3, 4, 2],
        'Patient-days': [1200, 1250, 1180, 1275, 1300, 1220],
    })
    demo_months['Falls per 1,000 patient-days'] = (
        demo_months['Falls'] / demo_months['Patient-days'] * 1000
    ).round(2)
    trend = px.line(
        demo_months, x='Month', y='Falls per 1,000 patient-days',
        markers=True, title='Synthetic monthly fall rates'
    )
    st.plotly_chart(trend, use_container_width=True)
    st.dataframe(demo_months, use_container_width=True, hide_index=True)
    st.latex(r'\text{Fall rate} = \frac{\text{Number of falls}}{\text{Patient-days}} \times 1000')
    st.caption('Synthetic rates are descriptive examples only. Six invented months cannot demonstrate that FallSafe reduces falls or establish a causal effect.')

    st.subheader('Quality improvement interpretation')
    st.write('Use assessment completion, unresolved tasks, handoff accountability, and fall incidence as separate signals. Review staffing, patient mix, workflow interruptions, and equipment availability before attributing any change in outcomes to an intervention.')
    st.caption('Prototype limitations: in-memory session data; no authentication, persistent database, EHR integration, real alert delivery, or validated clinical risk scoring.')

st.sidebar.divider()
if st.sidebar.button('Reset all fictional demo data'):
    st.session_state.records = {pid: new_record() for pid in PATIENTS}
    for key in list(st.session_state.keys()):
        if key.startswith(('check_', 'reason_')):
            del st.session_state[key]
    st.rerun()
