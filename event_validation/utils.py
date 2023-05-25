# DetChar Event Validation - Ronaldas Macas

import os, json, datetime, gitlab
import pandas as pd
import numpy as np

from astropy.time import Time
from mdutils.mdutils import MdUtils


def assign_people(event_data, time, git_dir, vol_file, contact_file, validator, expert, mitigation, review, logger):

    # determine which time to use
    if time:
        valid_time = time
    else:
        now = datetime.datetime.now()
        now_str = now.strftime("%Y-%m-%dT%H:%M:%S")
        valid_time = Time(now_str, format='isot', scale='utc').gps

    # determine when volunteers are available
    vol_file = f'{git_dir}/data/{vol_file}'
    vol_data = pd.read_csv(vol_file)

    t_starts = []
    for t in vol_data['date_start']:
        t_starts.append(Time(t, format='iso', scale='utc').gps)
    dt = t_starts - valid_time
    vol_idx = np.where(dt <= 0)[0][-1]

    # read in contact list
    contact_file = f'{git_dir}/data/{contact_file}'
    contact_data = pd.read_csv(contact_file)

    if validator:
        contact_idx = contact_data.index[contact_data['name'] == validator][0]
    else:
        contact_idx = contact_data.index[contact_data['name'] == vol_data.iloc[vol_idx,:]['validator']][0]
    event_data['contacts']['validator_name'] = contact_data.iloc[contact_idx,:]['name']
    event_data['contacts']['validator_email'] = contact_data.iloc[contact_idx,:]['email']

    if expert:
        contact_idx = contact_data.index[contact_data['name'] == expert][0]
    else:
        contact_idx = contact_data.index[contact_data['name'] == vol_data.iloc[vol_idx,:]['expert']][0]
    event_data['contacts']['expert_name'] = contact_data.iloc[contact_idx,:]['name']
    event_data['contacts']['expert_email'] = contact_data.iloc[contact_idx,:]['email']

    if mitigation:
        contact_idx = contact_data.index[contact_data['name'] == mitigation][0]
    else:
        contact_idx = contact_data.index[contact_data['name'] == vol_data.iloc[vol_idx,:]['mitigation']][0]
    event_data['contacts']['mitigation_name'] = contact_data.iloc[contact_idx,:]['name']
    event_data['contacts']['mitigation_email'] = contact_data.iloc[contact_idx,:]['email']

    if review:
        contact_idx = contact_data.index[contact_data['name'] == review][0]
    else:
        contact_idx = contact_data.index[contact_data['name'] == vol_data.iloc[vol_idx,:]['review']][0]
    event_data['contacts']['review_name'] = contact_data.iloc[contact_idx,:]['name']
    event_data['contacts']['review_email'] = contact_data.iloc[contact_idx,:]['email']

    contact_idx = contact_data.index[contact_data['name'] == vol_data.iloc[vol_idx,:]['lead1']][0]
    event_data['contacts']['lead1_name'] = contact_data.iloc[contact_idx,:]['name']
    event_data['contacts']['lead1_email'] = contact_data.iloc[contact_idx,:]['email']
    contact_idx = contact_data.index[contact_data['name'] == vol_data.iloc[vol_idx,:]['lead2']][0]
    event_data['contacts']['lead2_name'] = contact_data.iloc[contact_idx,:]['name']
    event_data['contacts']['lead2_email'] = contact_data.iloc[contact_idx,:]['email']

    logger.info(f"Assigned event validation team: validator {event_data['contacts']['validator_name']}, "
                f"expert {event_data['contacts']['expert_name']}, "
                f"noise mitigation {event_data['contacts']['mitigation_name']}, "
                f"review {event_data['contacts']['review_name']}, "
                f"lead {event_data['contacts']['lead1_name']}, "
                f"lead {event_data['contacts']['lead2_name']}")

    return event_data


def update_data(event_data, git_dir, events_file, md_file, logger):

    superevent_url_md = f"[GraceDB]({event_data['links']['gracedb']})"
    detector_url_md = f"[Detectors]({event_data['links']['detector']})"
    dqr_url_md = f"[DQR]({event_data['links']['dqr']})"
    eval_url_md = f"[EV]({event_data['links']['summary']})"
    url_string = superevent_url_md + ', ' + detector_url_md + ', ' + dqr_url_md + ', ' + eval_url_md
    contact_md = f'([contact](mailto:{event_data["contacts"]["validator_email"]}))'

    # create new event dict
    new_event = {
                 'Event': [event_data['event_name']],
                 'Next step': f'Event validation {contact_md}',
                 'Validation conclusion': 'Not ready',
                 'Review conclusion': 'Not ready',
                 'Glitch subtraction': 'N/A',
                 'Finalized': 'No',
                 'Links': [url_string]
                 }

    # list_fname = f'{git_dir}/data/event_list.csv'
    # new_event_df = pd.DataFrame.from_dict(new_event)
    # new_event_df.to_csv(list_fname, index=False)
    # read outdated data frame
    old_event_list = pd.read_csv(f'{git_dir}/data/{events_file}', keep_default_na=False)

    # make new event as a pd DFrame
    new_event_df = pd.DataFrame.from_dict(new_event)

    # merge data frames
    new_event_list = pd.concat([old_event_list, new_event_df], ignore_index=True)

    # write to csv
    new_event_list.to_csv(f'{git_dir}/data/{events_file}', index=False)

    # update website's md table
    md_fname = f'{git_dir}/data/{md_file}'
    with open(md_fname, 'w') as md:
        new_event_list.to_markdown(buf=md, numalign="center", index=False)

    logger.info(f"Updated data files")

    return


def git_issue(event_data, gitlab_url, token, pid, label, logger):

    lead1_name = event_data['contacts']['lead1_name'].split(' ')
    lead1_handle = f'{lead1_name[0].lower()}.{lead1_name[1].lower()}'
    lead2_name = event_data['contacts']['lead2_name'].split(' ')
    lead2_handle = f'{lead2_name[0].lower()}.{lead2_name[1].lower()}'

    text = (f"A place to discuss event validation for {event_data['event_name']}.\n\n"
            f"Assigned volunteer {event_data['contacts']['validator_name']} ({event_data['contacts']['validator_email']}), DetChar expert {event_data['contacts']['expert_name']} ({event_data['contacts']['expert_email']}), noise mitigation {event_data['contacts']['mitigation_name']} ({event_data['contacts']['mitigation_email']}), and reviewer {event_data['contacts']['review_name']} ({event_data['contacts']['review_email']}).\n\n"
            f"For any questions, contact @{lead1_handle} ({event_data['contacts']['lead1_email']}) and @{lead2_handle} ({event_data['contacts']['lead2_email']})."
            )

    gl = gitlab.Gitlab(url='https://git.ligo.org', private_token=token)
    project = gl.projects.get(pid)

    issue = project.issues.create({'title':event_data['event_name'], 'description': text})
    issue.labels = ['validation', label]
    issue.save()

    # update git issue url since the issue was created
    try:
        issues = project.issues.list(get_all=True)
        issue_dict = {issue.title: issue for issue in issues}
        issue_iid = issue_dict[event_data['event_name']].iid
        event_data['links']['issue'] = f'{gitlab_url}/{issue_iid}'
    except:
        print(f"Issues assigning id to the gitlab issue url for {event_data['event_name']}, leaving default gitlab URL.")

    logger.info('Created a git issue')

    return event_data

def emails(event_data, ev_forms_url, logger):

    valid_email = event_data['contacts']['validator_email']
    expert_email = event_data['contacts']['expert_email']
    mitigation_email = event_data['contacts']['mitigation_email']
    review_email = event_data['contacts']['review_email']
    lead1_email = event_data['contacts']['lead1_email']
    lead2_email = event_data['contacts']['lead2_email']

    valid_name = event_data['contacts']['validator_name']
    expert_name = event_data['contacts']['expert_name']
    mitigation_name = event_data['contacts']['mitigation_name']
    review_name = event_data['contacts']['review_name']
    lead1_name = event_data['contacts']['lead1_name']
    lead2_name = event_data['contacts']['lead2_name']

    subject = f"A request to validate {event_data['event_name']}"

    pre_body_lead = f"Validator: {valid_email}, expert: {expert_email}, noise mitigation: {mitigation_email}, review: {review_email}.\n\n"
    pre_body_valid = f"You are assigned to validate candidate event {event_data['event_name']}. For more technical event validation questions, please refer to the DetChar expert {expert_name} ({expert_email}) or the Mattermost DetChar - Event Validation channel (https://chat.ligo.org/ligo/channels/detchar---event-validation); we advise to use the Mattermost channel instead of contacting a DetChar expert if possible. More information about the event is given below.\n\n"
    pre_body_valid2 = (f"Validation checklist:\n"
                       f"1. View the GraceDB SuperEvent and preferred event pages\n"
                       f"2. View the Detector Status Summary pages\n"
                       f"3. View the Data Quality Report\n"
                       f"4. Fill in the event validation form\n\n"
                       )
    pre_body_expert = f"{valid_name} ({valid_email}) has been assigned to validate candidate event {event_data['event_name']}, while you are assigned to act a DetChar expert. More information about the event is given below.\n\n"
    body = (f"Candidate event: {event_data['event_name']}\n"
            f"GraceDB Superevent: {event_data['links']['gracedb']}\n"
            f"DQR: {event_data['links']['dqr']}\n"
            f"Event validation form: {ev_forms_url}\n"
            f"GitLab issue: {event_data['links']['issue']}\n\n"
            f"Validator: {valid_name} ({valid_email})\n"
            f"DetChar expert: {expert_name} ({expert_email})\n"
            f"Noise mitigation: {mitigation_name} ({mitigation_email})\n"
            f"Review: {review_name} ({review_email})\n\n")
    post_body = f"For any questions, contact {lead1_name} ({lead1_email}) and {lead2_name} ({lead2_email})."

    send_email(valid_email, subject, pre_body_valid+pre_body_valid2+body+post_body)
    send_email(expert_email, subject, pre_body_expert+body+post_body)
    send_email(lead1_email, subject, pre_body_lead+body)
    send_email(lead2_email, subject, pre_body_lead+body)

    logger.info('Sent emails')

    return


def get_events_dict(list_fname, wdir):

    list_content = pd.read_csv(list_fname)
    list_events = list_content['Event']

    events = {}
    for event in list_events:

        fname = f'{wdir}/data/events/{event}.json'
        with open(fname, 'r') as event_json:
            event_data = json.load(event_json)


        event_dict = {}
        for key in event_data:
            if key != 'event_name':
                event_dict.update({f'{key}':event_data[key]})

        events.update({event_data['event_name']:event_dict})

    return events


def first_upper(string):
    final_string = f'{string[0].upper()}{string[1:]}'
    return final_string


def first_lower(string):
    final_string = f'{string[0].lower()}{string[1:]}'
    return final_string

def Nonestr(oldlist):
    newlist = []
    for ele in oldlist:
        if ele is None:
            ele = ''
        newlist.append(ele)
    return newlist

def send_email(email, subject, body):

    sender = os.environ.get('USER')
    sender = f'{sender}@ligo.org'

    os.system(f'Mail -v -s "{subject}" -r {sender} {email} <<< "{body}"')

    return

def get_dets(h1, l1, v1):

    dets = []
    if h1:
        dets.append('H1')
    if l1:
        dets.append('L1')
    if v1:
        dets.append('V1')

    return dets
