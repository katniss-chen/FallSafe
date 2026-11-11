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
