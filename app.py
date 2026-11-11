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
    for key, task in record['tasks'].items():
        st.write(f"**{PREVENTION_ITEMS[key]}:** {task['status']} | Owner: {task['owner']} | Ack: {'Yes' if task['acknowledged_at'] else 'No'}")
    st.subheader('Audit trail (current browser session)')
    if record['events']:
        st.dataframe(list(reversed(record['events'])), use_container_width=True, hide_index=True)
    else:
        st.info('No recorded activity yet.')

elif page == 'Quality Dashboard':
    st.header('Quality Dashboard')
    st.info('Next phase: quality measures, simulated incident trends, and patient-day-adjusted fall rates.')
    rows = []
    for pid, rec in st.session_state.records.items():
        counts = task_counts(rec)
        rows.append({'Patient': pid, 'Unit': PATIENTS[pid]['unit'], 'Risk': rec['risk'], **counts})
    st.dataframe(rows, use_container_width=True, hide_index=True)

st.sidebar.divider()
if st.sidebar.button('Reset all fictional demo data'):
    st.session_state.records = {pid: new_record() for pid in PATIENTS}
    for key in list(st.session_state.keys()):
        if key.startswith(('check_', 'reason_')):
            del st.session_state[key]
    st.rerun()
